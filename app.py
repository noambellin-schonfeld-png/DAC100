"""DAC100 local application: auditable DAC cost math plus bounded evidence extraction."""

from __future__ import annotations

import json
import math
import os
import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
BASELINE_PATH = ROOT / "data" / "baseline.json"
WEB_PATH = ROOT / "static" / "index.html"
PROMPT_PATH = ROOT / "prompts" / "evidence_extractor.md"
LOG_PATH = ROOT / "output" / "usage.jsonl"
DEFAULT_MODEL = "gpt-6-luna"
DEFAULT_BASE_URL = "https://api.portkey.ai/v1"
MAX_BODY_BYTES = 40_000
MAX_EXCERPT_CHARS = 8_000
MAX_OUTPUT_TOKENS = 1_100
REQUEST_TIMEOUT_S = 40
MAX_AI_RUNS_PER_DAY = 20
MAX_ESTIMATED_DAILY_SPEND_USD = 0.05
MODEL_PRICES_PER_MILLION = {"input": 0.10, "cached_input": 0.01, "output": 0.50}
LOG_LOCK = threading.Lock()

INPUT_LIMITS = {
    "capacity_t_per_year": (1_000, 100_000_000),
    "capacity_factor": (0.01, 1.0),
    "capex_usd": (10_000, 1_000_000_000_000),
    "capital_recovery_rate": (0.0, 0.5),
    "fixed_om_fraction": (0.0, 0.5),
    "electricity_mwh_per_t": (0.0, 50.0),
    "electricity_usd_per_mwh": (0.0, 10_000.0),
    "heat_gj_per_t": (0.0, 100.0),
    "heat_usd_per_gj": (0.0, 10_000.0),
    "sorbent_om_usd_per_t": (0.0, 1_000_000.0),
    "transport_storage_usd_per_t": (0.0, 100_000.0),
    "verification_usd_per_t": (0.0, 100_000.0),
    "electricity_kgco2e_per_mwh": (0.0, 100_000.0),
    "heat_kgco2e_per_gj": (0.0, 100_000.0),
    "other_lifecycle_kgco2e_per_t": (0.0, 1_000_000.0),
    "durable_storage_fraction": (0.0, 1.0),
}
IMPROVEMENT_LIMITS = {
    "capex": "capex_reduction_max",
    "electricity": "electricity_intensity_reduction_max",
    "heat": "heat_intensity_reduction_max",
    "sorbent": "sorbent_cost_reduction_max",
}
SCENARIO_INPUTS = {
    "capex": "capex_usd",
    "electricity": "electricity_mwh_per_t",
    "heat": "heat_gj_per_t",
    "sorbent": "sorbent_om_usd_per_t",
}
PROMPT_INJECTION = re.compile(
    r"(?:ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions"
    r"|reveal\s+(?:the\s+)?(?:system|developer|hidden)\s+prompt"
    r"|(?:print|show|expose|send|exfiltrate)\s+(?:the\s+)?(?:portkey\s+)?(?:api\s+)?key"
    r"|you\s+are\s+now\s+(?:a\s+)?(?:system|developer|admin)"
    r"|(?:call|invoke)\s+(?:the\s+)?(?:tool|function)\s+\w+)",
    re.IGNORECASE,
)


def load_env_files() -> None:
    """Load the repository .env, then its parent .env; file settings beat shell values."""
    loaded = {}
    for path in (ROOT / ".env", ROOT.parent / ".env"):
        if not path.is_file():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            name, value = name.strip(), value.strip()
            if value[:1] in ("'", '"') and value[-1:] == value[:1]:
                value = value[1:-1]
            if name not in loaded:
                loaded[name] = value
    os.environ.update(loaded)


load_env_files()
BASELINE = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
INPUT_META = BASELINE["inputs"]
SOURCE_KINDS = ("Reported measurement", "Published modeling assumption", "User assumption", "Unknown")


def append_event(event: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    item = {"time_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **event}
    with LOG_LOCK:
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")


def _finite_number(value: object, label: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a number.")
    number = float(value)
    if not math.isfinite(number) or not low <= number <= high:
        raise ValueError(f"{label} must be between {low:g} and {high:g}.")
    return number


def validate_inputs(raw_inputs: object) -> dict[str, float]:
    if not isinstance(raw_inputs, dict):
        raise ValueError("Inputs must be a named object.")
    if set(raw_inputs) != set(INPUT_LIMITS):
        raise ValueError("The input list does not match the supported DAC model.")
    values = {}
    for key, bounds in INPUT_LIMITS.items():
        label = INPUT_META[key]["label"]
        values[key] = _finite_number(raw_inputs[key], label, *bounds)
    return values


def calculate(values: dict[str, float], improvements: dict[str, float] | None = None) -> dict:
    """Calculate unit costs per gross tonne and per net tonne using code only."""
    changes = improvements or {key: 0.0 for key in IMPROVEMENT_LIMITS}
    bounds = BASELINE["scenario_bounds"]
    if set(changes) != set(IMPROVEMENT_LIMITS):
        raise ValueError("The improvement fields do not match the supported scenario controls.")
    reductions = {}
    for key, bound_key in IMPROVEMENT_LIMITS.items():
        reductions[key] = _finite_number(changes[key], f"{key} reduction", 0.0, bounds[bound_key])

    annual_gross_tonnes = values["capacity_t_per_year"] * values["capacity_factor"]
    capex = values["capex_usd"] * (1 - reductions["capex"])
    electricity_intensity = values["electricity_mwh_per_t"] * (1 - reductions["electricity"])
    heat_intensity = values["heat_gj_per_t"] * (1 - reductions["heat"])
    sorbent_cost = values["sorbent_om_usd_per_t"] * (1 - reductions["sorbent"])
    rows = {
        "Annualized capital": capex * values["capital_recovery_rate"] / annual_gross_tonnes,
        "Fixed O&M": capex * values["fixed_om_fraction"] / annual_gross_tonnes,
        "Electricity": electricity_intensity * values["electricity_usd_per_mwh"],
        "Process heat": heat_intensity * values["heat_usd_per_gj"],
        "Sorbent and variable O&M": sorbent_cost,
    }
    capture_cost = sum(rows.values())
    post_capture = {
        "Transport and storage": values["transport_storage_usd_per_t"],
        "Verification (MRV)": values["verification_usd_per_t"],
    }
    gross_project_cost = capture_cost + sum(post_capture.values())
    lifecycle_tonnes = (
        electricity_intensity * values["electricity_kgco2e_per_mwh"]
        + heat_intensity * values["heat_kgco2e_per_gj"]
        + values["other_lifecycle_kgco2e_per_t"]
    ) / 1_000
    net_fraction = values["durable_storage_fraction"] - lifecycle_tonnes
    if net_fraction <= 0:
        raise ValueError("Modeled lifecycle emissions are at least one tonne per gross tonne; net removal is not positive.")
    full_net_cost = gross_project_cost / net_fraction
    return {
        "annual_gross_tonnes": annual_gross_tonnes,
        "capture_breakdown_usd_per_gross_t": rows,
        "capture_cost_usd_per_gross_t": capture_cost,
        "post_capture_usd_per_gross_t": post_capture,
        "full_project_usd_per_gross_t": gross_project_cost,
        "lifecycle_emissions_tco2e_per_gross_t": lifecycle_tonnes,
        "durable_storage_fraction": values["durable_storage_fraction"],
        "net_removal_fraction": net_fraction,
        "net_tonnes_per_year": annual_gross_tonnes * net_fraction,
        "full_net_removal_usd_per_net_t": full_net_cost,
        "improvements": reductions,
    }


def target_search(values: dict[str, float], target: float) -> dict:
    checked_target = _finite_number(target, "Net-removal cost target", 1.0, 100_000.0)
    max_changes = {key: BASELINE["scenario_bounds"][bound] for key, bound in IMPROVEMENT_LIMITS.items()}
    best = calculate(values, max_changes)
    return {
        "target_usd_per_net_t": checked_target,
        "all_bounds_scenario": best["full_net_removal_usd_per_net_t"],
        "reachable_within_entered_ranges": best["full_net_removal_usd_per_net_t"] <= checked_target,
        "max_reductions": max_changes,
        "qualification": "Arithmetic result only. Bounds are unvalidated user assumptions and simultaneous improvements are not shown to be technically compatible.",
    }


def eligible_scenario_claims(claims_raw: object, values: dict[str, float]) -> list[dict]:
    """Keep only reviewed, quoted, condition-matched numeric claims that map to a bounded reduction."""
    if not isinstance(claims_raw, list) or not 1 <= len(claims_raw) <= 20:
        raise ValueError("Select between 1 and 20 reviewed candidate claims.")
    eligible = []
    issues = []
    occupied = set()
    kinds = set(SOURCE_KINDS)
    for item in claims_raw:
        if not isinstance(item, dict) or item.get("human_reviewed") is not True:
            issues.append("Each selected claim needs explicit human review.")
            continue
        input_id = item.get("input_id")
        claim_id = item.get("claim_id")
        if input_id not in SCENARIO_INPUTS.values():
            issues.append("Only capital, electricity, heat, and sorbent cost claims can be scenario inputs.")
            continue
        if not isinstance(claim_id, str) or not re.fullmatch(r"c[0-9]{1,2}", claim_id):
            issues.append("A selected claim has an invalid local claim ID.")
            continue
        if item.get("classification") not in kinds - {"User assumption", "Unknown"}:
            issues.append(f"{claim_id} is not labeled as a reported measurement or published modeling assumption.")
            continue
        current = values[input_id]
        value = item.get("value")
        meta = INPUT_META[input_id]
        if not (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)):
            issues.append(f"{claim_id} has no explicit numeric value.")
            continue
        if item.get("unit") != meta["unit"]:
            issues.append(f"{claim_id} unit must exactly match {meta['unit']}; convert and document it before review.")
            continue
        quote, condition = item.get("evidence_quote"), item.get("condition")
        if not isinstance(quote, str) or not quote.strip() or not isinstance(condition, str) or len(condition.strip()) < 8 or re.search(r"not stated|unknown|unspecified", condition, re.I):
            issues.append(f"{claim_id} needs an evidence quote and stated study/operating conditions.")
            continue
        if current <= 0 or value < 0 or value >= current:
            issues.append(f"{claim_id} does not establish a positive reduction from the current input.")
            continue
        scenario_kind = next((kind for kind, mapped_input in SCENARIO_INPUTS.items() if mapped_input == input_id), None)
        reduction = (current - float(value)) / current
        max_reduction = BASELINE["scenario_bounds"][IMPROVEMENT_LIMITS[scenario_kind]]
        if reduction > max_reduction + 1e-9:
            issues.append(f"{claim_id} implies a {reduction:.1%} reduction, beyond the entered {max_reduction:.1%} scenario bound.")
            continue
        if scenario_kind in occupied:
            issues.append(f"Multiple selected claims map to {meta['label']}; select one comparable result.")
            continue
        occupied.add(scenario_kind)
        eligible.append({"claim_id": claim_id, "input_id": input_id, "scenario_kind": scenario_kind,
                         "value": float(value), "unit": meta["unit"], "reduction": reduction,
                         "evidence_quote": quote[:600], "condition": condition[:300],
                         "classification": item["classification"], "claim": str(item.get("claim", ""))[:300]})
    if issues:
        raise ValueError("Selected evidence needs review before the scenario tool can use it: " + " ".join(issues))
    if not eligible:
        raise ValueError("No selected claim supports a numeric reduction within the modeled range.")
    return eligible


def _post_portkey_responses(payload: dict) -> dict:
    key = _model_key()
    headers = {"Content-Type": "application/json", "x-portkey-api-key": key,
               "x-portkey-provider": os.getenv("PORTKEY_PROVIDER", "openai")}
    base = os.getenv("PORTKEY_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    request = Request(base + "/responses", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers=headers, method="POST")
    with urlopen(request, timeout=REQUEST_TIMEOUT_S) as response:
        return json.loads(response.read().decode("utf-8"))


def _usage_numbers(response: dict) -> dict:
    usage = response.get("usage") or {}
    details = usage.get("input_tokens_details") or {}
    return {"input_tokens": usage.get("input_tokens"), "cached_input_tokens": details.get("cached_tokens"),
            "output_tokens": usage.get("output_tokens")}


def _usage_cost(usage: dict) -> float | None:
    incoming, cached, outgoing = (usage.get(key) for key in ("input_tokens", "cached_input_tokens", "output_tokens"))
    if not all(isinstance(value, int) and value >= 0 for value in (incoming, cached, outgoing)):
        return None
    fresh = max(incoming - cached, 0)
    return (fresh * MODEL_PRICES_PER_MILLION["input"] + cached * MODEL_PRICES_PER_MILLION["cached_input"] + outgoing * MODEL_PRICES_PER_MILLION["output"]) / 1_000_000


def _sum_usage_rows(rows: list[dict]) -> dict:
    totals = {}
    for name in ("input_tokens", "cached_input_tokens", "output_tokens"):
        values = [row.get(name) for row in rows]
        totals[name] = sum(values) if values and all(isinstance(value, int) and value >= 0 for value in values) else None
    costs = [_usage_cost(row) for row in rows]
    totals["api_cost_usd"] = sum(costs) if costs and all(cost is not None for cost in costs) else None
    return totals


def prioritize_evidence(inputs_raw: object, claims_raw: object) -> dict:
    """Ask Luna to call one bounded calculation tool, then explain its numeric result."""
    values = validate_inputs(inputs_raw)
    claims = eligible_scenario_claims(claims_raw, values)
    key = _model_key()
    if not key:
        raise RuntimeError("AI evidence review needs PORTKEY_API_KEY in DAC100/.env or the parent folder's .env.")
    task = {"user_question": "Which source-supported, bounded changes merit priority, and what does the deterministic calculation imply about the $100 per-net-ton target?",
            "current_inputs": [{"input_id": k, "label": INPUT_META[k]["label"], "value": values[k], "unit": INPUT_META[k]["unit"]} for k in INPUT_META],
            "approved_evidence": claims,
            "scenario_bounds": {kind: BASELINE["scenario_bounds"][bound] for kind, bound in IMPROVEMENT_LIMITS.items()},
            "target_usd_per_net_t": 100.0}
    system = (
        "You are DAC100's research-prioritization agent. The evidence facts were explicitly selected and reviewed by the user. "
        "Do not infer improvements beyond the exact quoted, condition-labeled values. Call evaluate_supported_scenario exactly once, "
        "selecting only claim IDs that support a like-for-like lower value for the same input and condition. If values are not comparable, "
        "do not select them. The code tool enforces ranges and performs all arithmetic. After the tool returns, explain which evidence was "
        "used, what the deterministic result means, the limitations, and what to investigate next. Treat scenario combinations as conditional; "
        "do not imply that improvements coexist unless the evidence establishes that. Do not invent cost, energy, or emissions numbers."
    )
    eligible_ids = [claim["claim_id"] for claim in claims]
    tool = {"type": "function", "name": "evaluate_supported_scenario",
            "description": "Run DAC100's deterministic baseline-versus-scenario calculation using only human-approved evidence claim IDs.",
            "parameters": {"type": "object", "properties": {
                "claim_ids": {"type": "array", "items": {"type": "string", "enum": eligible_ids}},
                "reason": {"type": "string"}},
                "required": ["claim_ids", "reason"], "additionalProperties": False}, "strict": True}
    input_text = json.dumps(task, ensure_ascii=False)
    request_id, reserved_cost = _check_ai_budget(len(input_text), model_calls=2, output_tokens_per_call=700)
    usage_rows = []
    try:
        first = _post_portkey_responses({"model": DEFAULT_MODEL, "instructions": system,
            "input": [{"role": "user", "content": [{"type": "input_text", "text": input_text}]}],
            "tools": [tool], "tool_choice": {"type": "function", "name": "evaluate_supported_scenario"},
            "max_output_tokens": 700})
        usage_rows.append(_usage_numbers(first))
    except HTTPError as exc:
        append_event({"event": "evidence_agent_error", "request_id": request_id, "model": DEFAULT_MODEL, "http_status": exc.code, "reserved_cost_usd": reserved_cost, "api_called": True})
        raise RuntimeError(f"The model request failed with HTTP {exc.code}. Check Portkey access and model configuration.") from None
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        append_event({"event": "evidence_agent_error", "request_id": request_id, "model": DEFAULT_MODEL, "error_type": type(exc).__name__, "reserved_cost_usd": reserved_cost, "api_called": True})
        raise RuntimeError("The model request could not complete. Check your connection and try again.") from None

    calls = [item for item in first.get("output", []) if item.get("type") == "function_call"]
    if len(calls) != 1 or calls[0].get("name") != "evaluate_supported_scenario":
        usage = usage_rows[0]
        cost = _usage_cost(usage)
        append_event({"event": "evidence_agent_invalid_tool_call", "request_id": request_id, **usage, "api_cost_usd": cost, "reserved_cost_usd": reserved_cost, "api_called": True})
        raise RuntimeError("The model did not make the one permitted calculation-tool call. No scenario was run.")
    call = calls[0]
    try:
        args = json.loads(call.get("arguments", "{}"))
        ids = args.get("claim_ids")
        reason = args.get("reason", "")
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)) or any(value not in eligible_ids for value in ids):
            raise ValueError("The model selected invalid or repeated evidence IDs.")
        if not isinstance(reason, str):
            raise ValueError("The model tool rationale was invalid.")
        selected = [claim for claim in claims if claim["claim_id"] in ids]
        changes = {kind: 0.0 for kind in IMPROVEMENT_LIMITS}
        for claim in selected:
            changes[claim["scenario_kind"]] = claim["reduction"]
        baseline_result = calculate(values)
        scenario_result = calculate(values, changes)
        comparison = {"baseline": baseline_result, "scenario": scenario_result,
                      "target_search": target_search(values, 100.0), "selected_evidence": selected,
                      "model_selection_reason": reason[:300]}
    except (TypeError, KeyError, ValueError, json.JSONDecodeError) as exc:
        usage = usage_rows[0]
        append_event({"event": "evidence_agent_tool_rejected", "request_id": request_id, **usage, "api_cost_usd": _usage_cost(usage), "reserved_cost_usd": reserved_cost, "api_called": True})
        raise RuntimeError(f"The proposed evidence-to-calculation handoff was rejected: {exc}") from None

    call_id = call.get("call_id")
    if not isinstance(call_id, str) or not call_id:
        append_event({"event": "evidence_agent_tool_rejected", "request_id": request_id, "api_cost_usd": _usage_cost(usage_rows[0]), "reserved_cost_usd": reserved_cost, "api_called": True})
        raise RuntimeError("The model's calculation-tool call had no valid call ID.")
    followup_input = [
        {"role": "user", "content": [{"type": "input_text", "text": input_text}]},
        {"type": "function_call", "call_id": call_id, "name": "evaluate_supported_scenario", "arguments": json.dumps(args)},
        {"type": "function_call_output", "call_id": call_id, "output": json.dumps(comparison, ensure_ascii=False)},
    ]
    try:
        second = _post_portkey_responses({"model": DEFAULT_MODEL, "instructions": system,
            "input": followup_input, "max_output_tokens": 700})
        usage_rows.append(_usage_numbers(second))
    except HTTPError as exc:
        usage_rows.append({})
        totals = _sum_usage_rows(usage_rows)
        append_event({"event": "evidence_agent_followup_error", "request_id": request_id, **totals, "usage_by_request": usage_rows, "http_status": exc.code, "reserved_cost_usd": reserved_cost, "tool_executed": True, "complete_usage": False, "api_called": True})
        raise RuntimeError("The calculator ran, but the model could not finish its explanation. See the deterministic results and retry the explanation later.") from None
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        usage_rows.append({})
        totals = _sum_usage_rows(usage_rows)
        append_event({"event": "evidence_agent_followup_error", "request_id": request_id, **totals, "usage_by_request": usage_rows, "error_type": type(exc).__name__, "reserved_cost_usd": reserved_cost, "tool_executed": True, "complete_usage": False, "api_called": True})
        raise RuntimeError("The calculator ran, but the model could not finish its explanation. See the deterministic results and retry the explanation later.") from None

    explanation = _extract_output_text(second)
    totals = _sum_usage_rows(usage_rows)
    cost = totals["api_cost_usd"]
    if not explanation:
        append_event({"event": "evidence_agent_empty_explanation", "request_id": request_id, **totals, "api_cost_usd": cost, "reserved_cost_usd": reserved_cost, "tool_executed": True, "api_called": True})
        raise RuntimeError("The calculation ran, but the model returned no explanation. Review the deterministic comparison.")
    append_event({"event": "evidence_agent_success", "request_id": request_id, **totals, "api_cost_usd": cost, "reserved_cost_usd": reserved_cost,
                  "model_requests": 2, "tool_calls": 1, "selected_claims": len(selected), "capture_cost_usd_per_gross_t": scenario_result["capture_cost_usd_per_gross_t"],
                  "full_net_removal_usd_per_net_t": scenario_result["full_net_removal_usd_per_net_t"], "api_called": True})
    return {"explanation": explanation, "comparison": comparison,
            "usage": {"model": DEFAULT_MODEL, **totals, "api_cost_usd": cost, "model_requests": 2, "tool_calls": 1}}


def prioritized_questions(values: dict[str, float], result: dict) -> list[str]:
    questions_by_cost = {
        "Annualized capital": "What installed-cost evidence and financing assumptions support this capital cost and recovery rate at the modeled plant scale?",
        "Fixed O&M": "Which labor, maintenance, and replacement items are included in fixed O&M, and what plant data support the annual fraction?",
        "Electricity": "What pilot or vendor data establish electricity use per gross tonne, and what local power contract and grid emissions factor apply?",
        "Process heat": "What regeneration heat duty and supply temperature have been measured, and what low-carbon heat source is available at the site?",
        "Sorbent and variable O&M": "What measured sorbent working capacity, lifetime, degradation, and replacement cost support this annualized variable cost?",
    }
    ordered = sorted(result["capture_breakdown_usd_per_gross_t"].items(), key=lambda item: item[1], reverse=True)
    questions = [questions_by_cost[name] for name, _ in ordered[:3]]
    questions.append("What monitoring, leakage, and permanence evidence supports the durable-storage fraction, and which lifecycle-emissions sources remain outside the boundary?")
    questions.append("Are the selected cost and energy improvements independently demonstrated, and can they coexist at the same operating conditions?")
    return questions


def _model_key() -> str:
    return os.getenv("PORTKEY_API_KEY", "").strip()


def _check_ai_budget(excerpt_chars: int, model_calls: int = 1, output_tokens_per_call: int = MAX_OUTPUT_TOKENS) -> tuple[str, float]:
    """Apply a conservative per-day request and spend cap using the local append-only log."""
    now = datetime.now(timezone.utc)
    requests_today = 0
    spent_today = 0.0
    if LOG_PATH.is_file():
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines()[-5_000:]:
            try:
                event = json.loads(line)
                at = datetime.fromisoformat(event.get("time_utc", ""))
                if now - at > timedelta(days=1):
                    continue
                if event.get("api_called") is True or event.get("event", "").startswith("evidence_extraction_"):
                    requests_today += 1
                    spent_today += float(event.get("api_cost_usd", event.get("reserved_cost_usd", 0.0)) or 0.0)
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
    reserve_per_call = (max(excerpt_chars, 0) + 3_500) * MODEL_PRICES_PER_MILLION["input"] + output_tokens_per_call * MODEL_PRICES_PER_MILLION["output"]
    reserve = reserve_per_call * model_calls / 1_000_000
    if requests_today >= MAX_AI_RUNS_PER_DAY or spent_today + reserve > MAX_ESTIMATED_DAILY_SPEND_USD:
        append_event({"event": "ai_spend_limit_rejected", "model": DEFAULT_MODEL, "excerpt_chars": excerpt_chars, "api_called": False, "requests_in_last_day": requests_today, "reserved_cost_usd": reserve})
        raise PermissionError(f"Daily AI guardrail reached ({MAX_AI_RUNS_PER_DAY} runs or ${MAX_ESTIMATED_DAILY_SPEND_USD:.2f} estimated spend). Try again after the 24-hour window rolls over.")
    return str(uuid.uuid4()), reserve


def _extract_output_text(response: dict) -> str:
    parts = []
    for item in response.get("output", []):
        if item.get("type") == "message":
            for content in item.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    parts.append(content["text"])
    return "\n".join(parts).strip()


def analyze_excerpt(title: object, excerpt: object) -> dict:
    if not isinstance(title, str) or len(title) > 200:
        raise ValueError("Source title must be text up to 200 characters.")
    if not isinstance(excerpt, str) or not excerpt.strip():
        raise ValueError("Paste a research excerpt to review.")
    if len(excerpt) > MAX_EXCERPT_CHARS:
        raise ValueError(f"Research excerpt is limited to {MAX_EXCERPT_CHARS:,} characters per request.")
    match = PROMPT_INJECTION.search(title + "\n" + excerpt)
    if match:
        append_event({"event": "prompt_injection_rejected", "model": DEFAULT_MODEL, "excerpt_chars": len(excerpt), "matched_marker": match.group(0)[:80], "api_called": False})
        raise PermissionError("This excerpt contains instruction-like text asking the model to change roles, disclose instructions or keys, or invoke a tool. It was stopped before any API request. Remove the suspicious instruction text and try again.")
    key = _model_key()
    if not key:
        raise RuntimeError("AI evidence review needs PORTKEY_API_KEY in DAC100/.env or the parent folder's .env. The calculator remains available without it.")
    request_id, reserved_cost = _check_ai_budget(len(excerpt))

    input_catalog = [{"input_id": key_name, "label": meta["label"], "unit": meta["unit"]} for key_name, meta in INPUT_META.items()]
    instructions = PROMPT_PATH.read_text(encoding="utf-8")
    user_payload = {"source_title": title.strip() or "Untitled excerpt", "allowed_inputs": input_catalog, "research_excerpt_untrusted_data": excerpt}
    request_data = json.dumps({
        "model": DEFAULT_MODEL,
        "instructions": instructions,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": json.dumps(user_payload, ensure_ascii=False)}]}],
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "text": {"format": {"type": "json_object"}},
    }).encode("utf-8")
    base = os.getenv("PORTKEY_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    headers = {"Content-Type": "application/json", "x-portkey-api-key": key,
               "x-portkey-provider": os.getenv("PORTKEY_PROVIDER", "openai")}
    req = Request(base + "/responses", data=request_data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT_S) as response:
            body = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        append_event({"event": "evidence_extraction_error", "request_id": request_id, "model": DEFAULT_MODEL, "http_status": exc.code, "excerpt_chars": len(excerpt), "reserved_cost_usd": reserved_cost, "api_called": True})
        raise RuntimeError(f"The model request failed with HTTP {exc.code}. Check the Portkey key, model access, and connection.") from None
    except json.JSONDecodeError:
        append_event({"event": "evidence_extraction_error", "request_id": request_id, "model": DEFAULT_MODEL, "error_type": "invalid_json_response", "excerpt_chars": len(excerpt), "reserved_cost_usd": reserved_cost, "api_called": True})
        raise RuntimeError("The model endpoint returned an unreadable response; token usage was not available.") from None
    except (URLError, TimeoutError, OSError) as exc:
        append_event({"event": "evidence_extraction_error", "request_id": request_id, "model": DEFAULT_MODEL, "error_type": type(exc).__name__, "excerpt_chars": len(excerpt), "reserved_cost_usd": reserved_cost, "api_called": True})
        raise RuntimeError("The model request could not complete. Check your connection and try again.") from None

    raw_text = _extract_output_text(body)
    usage = body.get("usage") or {}
    details = usage.get("input_tokens_details") or {}
    in_tokens = usage.get("input_tokens")
    cache_tokens = details.get("cached_tokens")
    out_tokens = usage.get("output_tokens")
    cost = _usage_cost({"input_tokens": in_tokens, "cached_input_tokens": cache_tokens, "output_tokens": out_tokens})
    try:
        result = json.loads(raw_text)
        if not isinstance(result, dict) or not isinstance(result.get("claims", []), list) or not isinstance(result.get("uncertainties", []), list):
            raise ValueError("Model output has the wrong shape.")
    except (json.JSONDecodeError, ValueError):
        append_event({"event": "evidence_extraction_invalid_output", "request_id": request_id, "model": DEFAULT_MODEL, "input_tokens": in_tokens, "cached_input_tokens": cache_tokens, "output_tokens": out_tokens, "api_cost_usd": cost, "reserved_cost_usd": reserved_cost, "excerpt_chars": len(excerpt), "api_called": True})
        raise RuntimeError("The model replied, but its result was not valid JSON in the expected shape. No inputs were changed.") from None

    allowed_ids = set(INPUT_META) | {"unknown"}
    allowed_kinds = set(SOURCE_KINDS)
    claims = []
    for index, claim in enumerate(result.get("claims", [])[:20], start=1):
        if not isinstance(claim, dict):
            continue
        if claim.get("input_id") not in allowed_ids:
            claim["input_id"] = "unknown"
        if claim.get("classification") not in allowed_kinds:
            claim["classification"] = "Unknown"
        value = claim.get("value")
        if not (value is None or (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value))):
            claim["value"] = None
        for field in ("claim", "unit", "evidence_quote", "condition", "confidence"):
            field_value = claim.get(field)
            claim[field] = field_value[:600] if isinstance(field_value, str) else ""
        claim["claim_id"] = f"c{index}"
        claims.append(claim)
    result["claims"] = claims
    append_event({"event": "evidence_extraction_success", "request_id": request_id, "model": DEFAULT_MODEL, "input_tokens": in_tokens, "cached_input_tokens": cache_tokens, "output_tokens": out_tokens, "api_cost_usd": cost, "reserved_cost_usd": reserved_cost, "excerpt_chars": len(excerpt), "claims_returned": len(claims), "api_called": True})
    return {"result": result, "usage": {"model": DEFAULT_MODEL, "input_tokens": in_tokens, "cached_input_tokens": cache_tokens, "output_tokens": out_tokens, "api_cost_usd": cost}}


class Handler(BaseHTTPRequestHandler):
    server_version = "DAC100/0.1"

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep the terminal activity log useful without printing request bodies or credentials.
        print(f"{self.log_date_time_string()} {self.address_string()} {fmt % args}")

    def _send(self, status: int, payload: object, content_type: str = "application/json; charset=utf-8") -> None:
        if isinstance(payload, (dict, list)):
            raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        elif isinstance(payload, str):
            raw = payload.encode("utf-8")
        else:
            raw = b""
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def _json_body(self) -> dict:
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Request size was invalid.") from None
        if size <= 0 or size > MAX_BODY_BYTES:
            raise ValueError(f"Request body must be between 1 and {MAX_BODY_BYTES:,} bytes.")
        try:
            result = json.loads(self.rfile.read(size))
        except json.JSONDecodeError:
            raise ValueError("Request body must be valid JSON.") from None
        if not isinstance(result, dict):
            raise ValueError("Request body must be a JSON object.")
        return result

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            try:
                self._send(200, WEB_PATH.read_text(encoding="utf-8"), "text/html; charset=utf-8")
            except OSError:
                self._send(500, "Could not read the application page.", "text/plain; charset=utf-8")
        elif self.path == "/api/config":
            self._send(200, {"case": {"name": BASELINE["case_name"], "status": BASELINE["baseline_status"], "source": BASELINE["source"], "currency_year": BASELINE["currency_year"], "scenario_bounds_note": BASELINE["scenario_bounds_note"]}, "inputs": INPUT_META, "limits": BASELINE["scenario_bounds"], "source_kinds": SOURCE_KINDS, "model_configured": bool(_model_key()), "model": DEFAULT_MODEL})
        elif self.path == "/api/activity":
            rows = []
            if LOG_PATH.is_file():
                for line in LOG_PATH.read_text(encoding="utf-8").splitlines()[-15:]:
                    try:
                        entry = json.loads(line)
                        rows.append({key: entry.get(key) for key in ("time_utc", "event", "model", "input_tokens", "cached_input_tokens", "output_tokens", "api_cost_usd", "reserved_cost_usd", "api_called", "claims_returned", "model_requests", "tool_calls", "capture_cost_usd_per_gross_t", "full_net_removal_usd_per_net_t", "http_status", "error_type") if key in entry})
                    except json.JSONDecodeError:
                        continue
            self._send(200, {"events": rows})
        elif self.path == "/api/health":
            self._send(200, {"ok": True, "model_configured": bool(_model_key()), "model": DEFAULT_MODEL})
        else:
            self._send(404, {"error": "Not found."})

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in ("/api/calculate", "/api/analyze", "/api/prioritize"):
            self._send(404, {"error": "Not found."})
            return
        try:
            body = self._json_body()
            if self.path == "/api/calculate":
                values = validate_inputs(body.get("inputs"))
                changes = body.get("improvements", {key: 0.0 for key in IMPROVEMENT_LIMITS})
                result = calculate(values, changes)
                result["target_search"] = target_search(values, body.get("target_usd_per_net_t", 100))
                result["investigation_questions"] = prioritized_questions(values, calculate(values))
                append_event({"event": "calculation", "improvements": result["improvements"], "capture_cost_usd_per_gross_t": result["capture_cost_usd_per_gross_t"], "full_net_removal_usd_per_net_t": result["full_net_removal_usd_per_net_t"]})
                self._send(200, result)
            else:
                if self.path == "/api/analyze":
                    answer = analyze_excerpt(body.get("title", ""), body.get("excerpt", ""))
                    self._send(200, answer)
                else:
                    answer = prioritize_evidence(body.get("inputs"), body.get("claims"))
                    self._send(200, answer)
        except PermissionError as exc:
            self._send(422, {"error": str(exc), "blocked": True})
        except ValueError as exc:
            self._send(400, {"error": str(exc)})
        except RuntimeError as exc:
            self._send(502, {"error": str(exc)})
        except Exception as exc:  # keep the local UI responsive to unexpected malformed requests
            append_event({"event": "request_error", "path": self.path, "error_type": type(exc).__name__})
            self._send(500, {"error": "The request could not be completed. No model inputs were changed."})


def main() -> None:
    host = "127.0.0.1"
    port = int(os.getenv("DAC100_PORT", "8765"))
    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError as exc:
        raise SystemExit(f"Could not start DAC100 at {host}:{port}: {exc}") from None
    print(f"DAC100 ready at http://{host}:{port} — press Control-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDAC100 stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
