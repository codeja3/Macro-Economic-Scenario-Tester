# MEST Project Memory & Development Log

## Project Summary
The **Macro-Economic Scenario Tester (MEST)** is a reactive, local-first financial analytics dashboard for decumulation stress-testing.

## Environment & Configuration
- **OS:** macOS
- **Language:** Python
- **Package Manager:** `uv`
- **Testing Framework:** `pytest`
- **Architecture:** Polars (Data Engine) + Streamlit (UI) + Ollama (Local LLM Reasoning via CoT/Self-Reflection)

## Development Phases

### Phase 1: Project Initialization & Requirements Analysis
- **Decisions & Justifications:**
  - **Spec-Driven & Test-Driven Development (SDD/TDD):** Adopted CLI-based TDD and SDD workflows to guarantee code robustness and keep the codebase decoupled (Polars separate from Streamlit).
  - **Verification & Testing Isolation:** Prohibited live network/API calls in test runs; Ollama local LLM integrations must be mocked to ensure quick and deterministic test runs.
  - **Memory Log Restructuring:** Reorganized [MEMORY.md](file:///Users/yiannis/Projects/myFinances/mest/MEMORY.md) into development phases to remain concise and readable for both LLMs and humans, storing only critical context for reconstruction.
  - **Simulation Engine Math Spec:** Selected start-of-month withdrawals as a conservative decumulation model, and defined two simulation modes: stochastic (lognormal) and historical bootstrap (sampling).
  - **Local CSV for Privacy:** Decided to store historical S&P 500, CPI, and Treasury returns in a local CSV file to eliminate external network calls.
  - **Cognitive Loop Specification:** Standardized the Ollama reasoning engine to use a Decomposed query parse step for inputs > 50 tokens, followed by Chain of Thought and Self-Reflection stages.
  - **Caching Mechanism**: Structured Streamlit's cache around a hashed `SimulationConfig` to meet the < 2 seconds latency constraint.
  - **Spec & Task Drafting:** Completed drafting [SPEC.md](file:///Users/yiannis/Projects/myFinances/mest/SPEC.md) and [TODO.md](file:///Users/yiannis/Projects/myFinances/mest/TODO.md), locking in system contracts and a 4-phase execution checklist to begin test-driven development.
  - **Git Branching Strategy:** Adopted a feature-branch workflow where each task in [TODO.md](file:///Users/yiannis/Projects/myFinances/mest/TODO.md) is executed on a dedicated task branch, then committed and merged back to `master` to preserve a clean history.

### Phase 2: Orchestration Layer & LLM Integration (TDD)
- **Decisions & Justifications:**
  - **Custom XML structural tags:** Adopted explicit `<thought>`, `<reflection>`, and `<response>` tags inside Ollama system instructions. This ensures we can easily parse the single LLM response stream into logical blocks.
  - **Word-Count-Based Decomposition threshold:** Used a simple 50-word split threshold to determine when to trigger the query decomposition step to keep short queries fast and low-latency.
  - **Failure-Safe connection catch blocks:** Implemented try-except wrappers around `requests.post` calls to gracefully capture socket connections failures and yield an error indicator, rather than crashing the UI stream.

### Phase 3: Streamlit Interface & Visualizations
- **Decisions & Justifications:**
  - **Safe-buffer streaming parser:** Created a 15-character trailing string buffer inside the token parser to ensure XML tags split across multiple chunks are never cut in half when flushing text to the Streamlit containers.
  - **Dynamic Altair Long-Melting:** Melted the transposed 100 paths into a long-form DataFrame with a pre-mapped `status` column, enabling high-performance GPU-accelerated rendering of multi-color paths in the Altair line chart.
  - **RAM-Only Session State Memory:** Restricted conversation memory storage strictly to `st.session_state` to safeguard user privacy and ensure chat contents are lost upon tab closure/page reload.

### Phase 4: Integration, Verification & Optimization
- **Decisions & Justifications:**
  - **Offline Socket connecting blocks:** Added an `autouse=True` fixture patching python's `socket.socket` constructor to raise a `RuntimeError` on connection attempts. This proves that the test suite runs fully offline and all API calls are fully mocked.
  - **Port 8501 Dashboard check:** Started the Streamlit dashboard on port 8501 via `uv run` in the background and parsed stdout/stderr logs to verify error-free startup, stopping the process after verification.
