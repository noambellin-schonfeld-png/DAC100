# DAC100

**Repository URL:** <https://github.com/noambellin-schonfeld-png/DAC100><br>
**Hosted app:** not hosted; run locally using the steps below.

DAC100 is an R&D triage prototype for solid-sorbent direct air capture. It reproduces NETL's Case 0B cost-of-capture result from the published annual flows and cost breakdown, keeps the study's modeled net atmospheric-removal basis distinct from a full lifecycle claim, explores bounded cost scenarios, and uses GPT-6 Luna to extract candidate claims from research for human review and a constrained Python calculation.

## Case 0B source and boundary

The source PDF is included at [`sources/Valentine_Zoelle_NETL_DAC_Sorbent_2022.pdf`](sources/Valentine_Zoelle_NETL_DAC_Sorbent_2022.pdf) (5.8 MB): J. Valentine and A. Zoelle, *Direct Air Capture Case Studies: Sorbent System*, U.S. Department of Energy, National Energy Technology Laboratory, DOE/NETL-2021/2865, July 8, 2022. DAC100 uses Case 0B, Exhibit 5-16 (printed p. 50 / PDF viewer p. 62), with supporting §§3.5–3.6 and Exhibits 5-4, 5-7, 5-13 and 5-14.

The model's annual flows are 113,900 tonnes of gross DAC capture, 13,900 tonnes of residual NGCC emissions, and 100,000 tonnes of NETL-boundary net atmospheric removal. T&S applies to 238,990 tonnes/year of combined DAC and NGCC CO₂ product. NETL reports costs in 2019 dollars, a Midwest plant, and an 85% capacity factor. The annual flows and variable/fuel annual costs are already at 85% CF; DAC100 does not multiply them by the capacity factor again. See `data/baseline.json` for the source class and page note attached to every input.

Applying NETL §3.6's FCR to Exhibit 5-13 TASC and adding Exhibit 5-14 annual operating costs yields $595.53 per gross DAC tonne for capture, $616.51 per gross DAC tonne including T&S, and $702.21 per NETL-boundary net atmospheric tonne. These are within $0.2/tonne of Exhibit 5-16's independently rounded values ($595.7, $616.7, and $702.4). DAC100 shows the official three-denominator table verbatim and documents the capital reconciliation below rather than forcing the calculation to match rounded outputs.

See [`docs/case0b-reconciliation.md`](docs/case0b-reconciliation.md) for the component-by-component calculation against all three Exhibit 5-16 denominators, the source page map, and the capacity-factor and currency-year reconciliation.

**Reconciliation notes:** NETL Exhibit 5-13 reports rounded TASC of $494.258 million. Multiplying by §3.6's FCR of 0.0707 gives $34.944 million/year capital charges, or $349.44/net tonne. Exhibit 5-16 reports $349.6/net tonne; the difference is $0.16/net tonne (about 0.046%). DAC100 follows the printed TASC and FCR formula, so its reconstructed total is $702.21/net tonne versus Exhibit 5-16's $702.4; it does not reverse-engineer cost inputs to force a match. Exhibits 5-4 and 5-7 report residual emissions as 13,900 and 13,901 tonnes/year, respectively; DAC100 follows the 13,900 tonnes/year net-flow reconciliation in Exhibit 5-4. Section 3.5 labels its Midwest T&S price as $10/tonne in 2018 dollars. DAC100 uses Exhibit 5-16's rounded 2019-dollar line ($23.9/net tonne, or $2.39m/year on its 100,000-tonne denominator); the Section 3.5 calculation is $2.3899m/year in 2018 dollars, $100/year lower before conversion. The report does not provide a dollar-year conversion, so the app preserves the 2019-dollar table basis and documents the ambiguity.

NETL's modeled net-removal boundary includes on-site NGCC residual emissions and a saline-storage T&S assumption. It does not quantify full construction/supply-chain lifecycle emissions, leakage/permanence, or separate verification/MRV costs. The app therefore labels $702.21 as a **NETL-boundary modeled cost**, not a verified full lifecycle cost of durable removal. The separate full lifecycle result remains unquantified.

## Requirements

- Python 3.10 or newer
- A modern browser
- A Portkey course key in `PORTKEY_API_KEY` for evidence extraction and the AI prioritization workflow; baseline calculations run without a key

The calculator uses only Python's standard library. No packages, full dataset, external database, or background service are needed.

## Run locally

1. Clone the repository and open a terminal in the `DAC100` folder.
2. (Optional, for AI evidence extraction) set `PORTKEY_API_KEY` in a `.env` file either inside `DAC100/` or in its parent folder. The app checks the repository folder first, then the parent; the repository `.env` takes priority. You can copy `.env.example` and enter the key locally. Never commit `.env` or a real key.
3. Start the application:

   ```sh
   python3 app.py
   ```

4. Open <http://127.0.0.1:8765> in a browser.
5. Review the source-tagged Case 0B values and published Exhibit 5-16 cross-check. Adjust a value and press **Recalculate**, or use the scenario sliders to test conditional cost reductions. To review research, paste a short excerpt with its units and operating conditions into **Review a research excerpt** and choose **Extract candidate evidence**. Inspect the quote, condition, units, and source class. Check only a claim you have independently reviewed and confirmed comparable to the Case 0B input, then choose **Use selected claims in a scenario tool**. The code validates the claim, performs the arithmetic, and supplies the result for Luna's explanation; the model cannot directly edit the baseline.
6. Press Control-C in the terminal to stop the app.

There is no larger dataset to download. The full published source report is included for provenance and local grading.

## Model and configuration

The AI uses only `gpt-6-luna` through the course Portkey connection pattern verified in the course examples: `https://api.portkey.ai/v1`, the OpenAI provider, and the `x-portkey-api-key` header. The app reads `PORTKEY_API_KEY`. Optional `PORTKEY_BASE_URL` and `PORTKEY_PROVIDER` default to those values; it does not fall back to `OPENAI_API_KEY` or another model. `.env.example` lists all app-specific key and optional connection values.

The excerpt is untrusted, size-limited data. Extraction has no tools. Before any scenario tool call, the user must review and approve an exact claim, unit, and condition. The prioritization agent can make at most two model requests and one local calculation-tool call. Requests have a 40-second timeout and output-token limits. The app records API-reported token usage when a response is returned, caps use at 20 AI calls per rolling day, and blocks estimated daily spend above $0.05. Logs stay local in `output/usage.jsonl` and are excluded from Git. Seven GPT-6 Luna attempts have failed at the connection stage, including three extraction requests on October 25; no successful usage or token count is claimed. The latest requests were recorded as `URLError` after passing local input screening.

## Cost and scenario interpretation

Capture cost excludes T&S and verification. The reproduced NETL COC includes NETL's T&S assumption and divides annual system costs by its net atmospheric-removal flow after modeled NGCC residual emissions. The target search uses that same boundary, so it is not a claim that the full $100 durable-removal target is met or even fully measured. Separate verification/MRV and full lifecycle emissions are unquantified, and storage permanence is assumed rather than verified.

The scenario sliders reduce capital charges, fixed O&M, variable O&M, or fuel while holding the Case 0B flow and process-emissions balance constant. Their ceilings are analyst-set exploration bounds; they are not NETL sensitivity results or compatible engineering changes. Tax credits and subsidies are excluded.

DAC100's own API cost is separate from the DAC process cost per tonne. Its estimated call cost uses the course GPT-6 Luna rate card: $0.10 per million uncached input tokens, $0.01 per million cached input tokens, and $0.50 per million output tokens. A rate assumption is not evidence of measured usage or billing.

See [`docs/evidence-map.md`](docs/evidence-map.md) for implementation and evidence status.
