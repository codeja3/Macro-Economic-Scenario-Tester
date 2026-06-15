# TODO: MEST Execution Tasks

This document lists the step-by-step implementation tasks mapped to the development phases in [SPEC.md](file:///Users/yiannis/Projects/myFinances/mest/SPEC.md).

---

## Phase 1: Data Engine & Simulation Core (TDD)
- [x] **Task 1.1**: Prepare local historical data file: `data/historical_regimes.csv` containing date, S&P 500 total return, CPI index, and 10-Yr Treasury yield.
- [x] **Task 1.2**: Write failing unit tests in `tests/test_core.py` for data ingestion and loader logic.
- [x] **Task 1.3**: Implement `mest/core/data_loader.py` to pass tests.
- [x] **Task 1.4**: Write failing unit tests in `tests/test_core.py` for the Monte Carlo simulation core (verifying path generation, success probability logic, and edge cases like zero withdrawals or total depletion).
- [x] **Task 1.5**: Implement vectorized Polars simulation core in `mest/core/simulator.py`.
- [ ] **Task 1.6**: Audit test coverage on `core` engine to verify $\ge 95\%$ coverage and measure simulation runtime to ensure sub-2-second performance.

## Phase 2: Orchestration Layer & LLM Integration (TDD)
- [ ] **Task 2.1**: Write failing unit tests in `tests/test_llm.py` for the deterministic scenario classifier.
- [ ] **Task 2.2**: Implement `mest/llm/classifier.py` scenario classification rules.
- [ ] **Task 2.3**: Write failing unit tests in `tests/test_llm.py` for the Ollama integration, verifying the reasoning loop (Decomposed routing, CoT parsing, Self-Reflection parsing) using complete API mocks.
- [ ] **Task 2.4**: Implement `mest/llm/orchestrator.py` logic.

## Phase 3: Streamlit Interface & Visualizations
- [ ] **Task 3.1**: Create Streamlit layout in `mest/ui/dashboard.py` (including sidebar parameters and tooltips).
- [ ] **Task 3.2**: Hook up the Polars simulation core to Streamlit with caching.
- [ ] **Task 3.3**: Integrate the Ollama orchestration layer into the UI with asynchronous streaming of CoT, Self-Reflection, and final output.

## Phase 4: Integration, Verification & Optimization
- [ ] **Task 4.1**: Execute integration tests and perform manual UI verification.
- [ ] **Task 4.2**: Verify that Ollama calls are fully blocked/mocked in tests.
- [ ] **Task 4.3**: Perform final documentation updates in [MEMORY.md](file:///Users/yiannis/Projects/myFinances/mest/MEMORY.md).
