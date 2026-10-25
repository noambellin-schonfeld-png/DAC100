# Rubric-to-feature and evidence map

| Rubric area | DAC100 feature / deliverable | Current evidence status |
|---|---|---|
| Idea: novelty and real-world value (21) | Case 0B cost reproduction; source-labeled research claims; constrained evidence-to-calculation handoff; research follow-up questions | Source/document workflow is now implemented. No practitioner trial is available; workflow differentiation remains a design contribution, not proven user value. |
| Application works (15) | Standard-library local app; NETL annual cost calculation; three-denominator COC comparison; one-at-a-time sensitivity; bounded scenarios; evidence extractor; reviewed claim-to-tool flow; local activity/usage log | Current Python functions reproduce the rounded source values, reject an injection pattern and unreviewed claim, and validate bounds. HTTP/browser route is unavailable in the sandbox because socket binding is denied. AI connection previously failed; no successful model run or token usage. Screenshots absent. |
| Staff can run (5) | README, `.env.example`, repository-first then parent `.env` lookup, bundled source PDF, Python stdlib | Current committed repo cloned locally; parent/repository placeholder `.env` priority, bundled PDF, Python import, and calculation passed. Could not start the HTTP server or browser because the sandbox denies local socket binding. Public GitHub clone pending. |
| Look and feel (10) | Source-tagged input editor, cost breakdown, scenario sliders, published result cross-check, evidence review and activity log | UI refactored around Case 0B. No browser rendering/screenshot check yet. |
| Motivation + what is new (8) | Report sections 2–3 | NETL report and direct Case 0B comparators are now identified. CarbonPlan product audit and comparative ChatGPT trial remain to be done; practitioner trial unavailable. |
| Agent design (10) | Report section 4, evidence-to-tool diagram, source claims and bounded deterministic tool | Workflow is implemented. A real Luna run and screenshots of each step remain unavailable. |
| Tokenomics (8) | API log records input, cached-input, output tokens and rate-based cost | No successful response returned usage. Do not report invented tokens or per-user/scale dollar totals. |
| Safety (8) | Input validation, excerpt cap, instruction-pattern block, human approval, exact-unit/condition validation, bounded cost reductions, ≤2 requests/≤1 calc call, timeout and daily spend caps | Current direct Python checks rejected a prompt-injection pattern and unreviewed claim and validated the storage-fraction bound. HTTP/UI presentation still needs a browser check. Detector is narrow and does not guarantee universal prompt-injection prevention. |
| Impact + metrics (5) | Report section 7; quantified Case 0B cost decomposition | NETL modeled estimate is reported evidence, not DAC100 user impact. User confirms no practitioner can test before deadline; no impact or user-trial claim will be made. |
| Report design (2) | Self-contained 10–15 print-page `report.html`; embedded diagram/screenshots | 11 explicit page sections with source data, reconciliation, and inline diagram. Genuine app screenshots and pagination check pending. |
| Slides (8) | <=10-slide Reveal.js `slides.html`, source-backed result, diagram, demo visual and cost evidence | 9 slides with Case 0B values and inline diagram. Real screenshots, key navigation, CDN, and F-key checks pending. |
| Submission hygiene | Public repository, no committed keys, supported `.env` arrangement, single-file HTML deliverables | `.env` is ignored; `.env.example` is a placeholder. Public repo is pending. Source PDF is bundled. Verify `git status` and GitHub URL before Canvas. |

## Case 0B reproduction and reconciliation

- Source: Valentine & Zoelle (2022), DOE/NETL-2021/2865. Main cost result: Exhibit 5-16, printed p. 50 / PDF viewer p. 62. Supporting §§3.5–3.6 and Exhibits 5-4, 5-7, 5-13, 5-14.
- Annual DAC gross capture: 113,900 tCO₂/year; residual NGCC stack emissions: 13,900 t/year; NETL-boundary net atmospheric removal: 100,000 t/year.
- Total CO₂ product sent to T&S: 238,990 t/year (113,900 DAC + 125,090 NGCC flue-gas capture).
- Annual costs at the Case 0B point: $34.944m capital charges (printed Exhibit 5-13 TASC $494.258m × §3.6 FCR 0.0707), $15.343999m fixed O&M, $6.143693m variable O&M, $11.399160m fuel, and $2.390000m T&S in the Exhibit 5-16 2019-dollar basis.
- Formula in code: `(annual capital + fixed O&M + variable O&M + fuel + T&S + entered verification cost) / modeled net atmospheric tonnes`. Capture-only cost excludes T&S and verification. DAC100 uses actual 85%-CF annual outputs and annual variable/fuel values directly; no second capacity-factor multiplication.
- One-at-a-time sensitivity function evaluates each cost lever separately at its analyst-set maximum and reports the resulting NETL-boundary cost and savings. It holds output and boundary fixed; it is not an engineering compatibility analysis.
- Reproduction from printed support values: capture $595.53 / DAC gross t; project $616.51 / DAC gross t including T&S; $702.21 / NETL-boundary net atmospheric t; $293.82 / total plant CO₂ product t. These are within $0.2/t of Exhibit 5-16's $595.7, $616.7, $702.4, $293.9.
- Capital reconciliation: printed Exhibit 5-13 TASC $494.258m × FCR 0.0707 gives $34.944m annual charges / $349.44 per net t. Exhibit 5-16's rounded capital COC row is $349.6, a $0.16/t difference. DAC100 applies the published TASC and FCR formula and documents the discrepancy; it does not use the published COC as a back-solved input.
- Exhibit 5-4/5-7 residual stack emissions differ by one tonne/year due rounding (13,900 versus 13,901); the calculation follows Exhibit 5-4's net-flow reconciliation.
- §3.5 labels its Midwest T&S assumption as $10/t in 2018 dollars; Exhibit 5-16 reports COC in 2019 dollars. DAC100 uses the rounded Exhibit 5-16 $23.9/net-t line to derive $2.39m/y in 2019 dollars. Applying §3.5's $10 to 238,990 t/y gives $2.3899m in 2018 dollars, $100/y lower before conversion. No undocumented inflation adjustment is invented.
- NETL's net boundary is a modeled plant balance, not a complete LCA. Separate verification/MRV, construction/supply-chain emissions, leakage, and independently established durable storage are absent. DAC100 labels the $702.21 result “NETL-boundary modeled cost”; complete lifecycle net-removal cost is unquantified.

## Remaining evidence to collect

1. On a regular local machine, follow README exactly and verify that the HTTP app starts and the UI opens; this sandbox denied socket binding. Then repeat the HTTP invalid-input, injection, and claim-approval checks and clone the public repo.
2. Obtain a successful course Portkey GPT-6 Luna extraction and reviewed calculation-agent run from a network-enabled environment. Keep actual usage JSONL without exposing the key; report returned token counts and rate-card cost.
3. Capture genuine running-app screenshots for baseline, successful agent, and blocked injection. Do not use diagrams or mockups as application screenshots.
4. Audit CarbonPlan's DAC calculator and ChatGPT on the same task; cite checked pages and date, and acknowledge overlapping capabilities.
5. Create the public GitHub repository, replace the placeholder URL, verify no `.env`/credentials are tracked, and clone/run the actual public repo.
6. Print-check `report.html` at letter size for 10–15 pages. Open `slides.html`, check every slide, arrow navigation, and F-key full screen; CDN requires a network-enabled browser.
