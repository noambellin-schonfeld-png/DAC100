# DAC100

**Repository URL:** pending GitHub repository setup<br>
**Hosted app:** not hosted; run locally as described below.

DAC100 is a research triage prototype for solid-sorbent direct air capture. It calculates capture and net-removal costs from explicit inputs, explores bounded improvement scenarios, and can extract candidate claims from a research excerpt for a person to review. Numerical results come from Python formulas, never from the language model.

> **Baseline status:** the checked-in starter case is an illustrative set of user assumptions, not a reproduction of a NETL case study. Replace its values and source notes with a specific published case before describing it as a published baseline.

## Requirements

- Python 3.10 or newer
- A modern browser
- For AI evidence extraction, a course Portkey key in `PORTKEY_API_KEY`; the calculator runs without a key

The app uses Python's standard library and has no package installation step.

## Run locally

1. Clone this repository and open a terminal in the `DAC100` folder.
2. (Optional, for evidence extraction) copy `.env.example` to `.env` and set `PORTKEY_API_KEY`. DAC100 also checks the folder immediately above the repository for `.env`, after checking its own folder. The project-folder `.env` takes priority.
3. Start the app:

   ```sh
   python3 app.py
   ```

4. Open <http://127.0.0.1:8765> in a browser.
5. Edit assumptions in the left panel and choose **Recalculate**. To use the AI, paste a short research excerpt in **Review a research excerpt** and choose **Extract candidate evidence**. Review the returned quotes, units, and conditions. After explicitly confirming a claim is comparable to the current baseline, you can ask Luna to select approved claim IDs for one bounded Python calculation-tool call. The tool result controls the displayed numbers; the model cannot directly change baseline inputs.
6. Press Control-C in the terminal to stop the app.

No full dataset is needed. `data/baseline.json` is the small, editable starter case. There is currently no larger dataset.

## Model and configuration

The AI request uses only `gpt-6-luna` through the course Portkey gateway at `https://api.portkey.ai/v1`. It reads `PORTKEY_API_KEY`; optional `PORTKEY_BASE_URL` and `PORTKEY_PROVIDER` settings default to the values used in course examples. It does not fall back to an OpenAI key. The source excerpt is untrusted data, is length-limited, and is never passed as instructions. The model has no network, filesystem, or calculation tools.

Each evidence extraction makes one request; the prioritization agent makes at most two requests and one calculation-tool call. Each request has a 40-second timeout and a 700- or 1,100-token output cap. The app records input, cached-input, and output counts when returned by the API. It caps the app at 20 AI runs per rolling 24 hours and blocks requests that would exceed its conservative $0.05 estimated daily AI-spend limit. Run logs are kept in `output/usage.jsonl` and are excluded from Git by default. See `docs/evidence-map.md` for the evidence still needed for final submission.

## Cost boundaries

DAC100 displays process capture cost separately from transport, storage, and verification; then it computes full net-removal cost by dividing total un-subsidized project cost per gross tonne by the net-removal fraction after modeled lifecycle emissions. Subsidies are excluded. DAC100's own AI API costs are logged separately and must not be confused with process costs.

The extractor estimates API cost using the course price sheet used in the course's Lecture 11 tokenomics example: GPT-6 Luna at $0.10 per million uncached input tokens, $0.01 per million cached input tokens, and $0.50 per million output tokens. This is a rate assumption, separate from the API-reported usage and cost evidence that a successful DAC100 run must supply.
