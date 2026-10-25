# Rubric-to-feature and evidence map

This is a live checklist. A feature counts as implemented only after it works in this repository; an evidence item counts only after it is captured from a real run or real user.

| Rubric area | DAC100 feature or deliverable | Evidence status |
| --- | --- | --- |
| Idea: novelty and real-world value (21) | Link research claims to named, source-labeled cost inputs; calculate constrained, conditional scenarios; rank follow-up investigation questions | Product distinction is a design goal; compare CarbonPlan DAC calculator and ChatGPT with sourced, checked details in report |
| Application works (15) | Deterministic Python cost calculator, explicit capture/net boundaries, bounded scenario search, structured evidence extractor, human-reviewed evidence-to-tool agent, input validation, and append-only run log | Local HTTP smoke check: health/config/calculation returned 200; invalid range 400; injection 422 before API call; unreviewed evidence rejected. Stubbed tool protocol check passed but is not real model evidence. Portkey extraction could not connect. Browser screenshots still needed. |
| Staff can run (5) | Standard-library local server; README; `.env.example`; repository-first then parent `.env` lookup | Fresh-copy setup passed with placeholder `.env` one level above; repository `.env` priority passed. Fresh Git clone still required. |
| Look and feel (10) | Single-page dashboard with assumption editor, cost breakdown, scenario controls, and evidence review | UI built; no browser rendering check or actual screenshot could be captured in this environment |
| Motivation and novelty (8) | Report sections 2–3 | Need real user workflow/cost and researched alternatives |
| Agent design (10) | Report section 4, flow diagram, real trace and screenshots | Need captured actual Portkey run and UI trace |
| Tokenomics (8) | Usage log records API-returned input/cached/output tokens; rates and operating scenarios in report | One real request attempt failed with a connection-level `URLError`; no token counts were returned. Successful measured run and monthly/scale calculations remain pending. |
| Safety (8) | Excerpt size cap, deterministic injection rejection, fixed instructions, extraction without tools, reviewed values before tool use, one bounded calculation call, two model requests maximum, timeout/output cap, 20 AI runs/day and $0.05 estimated daily API-spend caps | Injection and range controls pass local HTTP checks; API block event logged. Screenshot still needed. Spend-cap path passes an in-memory check. Detector has narrow patterns; no claim of universal prompt-injection prevention. |
| Impact and metrics (5) | Compare task time/quality or scope before and after use | User reports no practitioner trial is available before the deadline. Do not claim a measured benefit or quote. |
| Report design (2) | Self-contained 10–15-page `report.html`, embedded screenshots/diagram | 11 print-page draft created with an embedded workflow diagram; explicitly marked incomplete. Real screenshots and print/pagination check still required. |
| Slides (8) | Self-contained reveal.js `slides.html`, <=10 slides, embedded visuals | 9-slide draft created with an inline diagram; screenshots and CDN/keyboard/F-key checks still required. |
| Submission hygiene | Public repo or private access for `zlisto`; no keys; same repo URL in README/report | Local Git repo created and clean at its first commit; user asked to create a public repo later. Final URL still needs inserting in README/report. |

## Initial findings and remaining gaps

- `Final Proect/` is empty and is not a Git repository.
- No NETL sorbent DAC case study or DAC-specific prior work was found in Downloads.
- External network access is unavailable in this environment, so source documents and current competitor details cannot be fetched here.
- NETL source is expected from the user; no practitioner trial is available before the deadline. Public GitHub creation, successful model usage evidence, final source-backed report, genuine browser screenshots, and presentation checks remain outstanding.
- Current starter inputs and scenario bounds are explicitly illustrative user assumptions, not published measurements or validated technical limits.
