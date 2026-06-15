# PRD: Macro-Economic Scenario Tester
## 1. Project Overview
**Name:** Macro-Economic Scenario Tester (MEST)
**Type:** Financial Analytics Dashboard
**Objective:** Develop a reactive, high-performance decumulation stress-testing application. The tool will evaluate custom withdrawal strategies—specifically multi-stage bridge periods—against both historical economic regimes and stochastic (Monte Carlo) simulations.

## 2. Problem Statement
Standard decumulation calculators rely on deterministic, linear return assumptions, which mask Sequence of Returns Risk (SORR). Furthermore, off-the-shelf tools poorly handle complex early decumulation phases where withdrawals are staged across different account types before standard retirement age. There is a need for a highly responsive, local-first engine that strictly evaluates these phased withdrawal strategies against massive probabilistic datasets and historical market shocks.

## 3. Target User & Use Case
**User:** Computer-literate professionals managing their own complex financial modeling. Assume no prior knowledge of economics. The UI will define technical terms natively, and the LLM will provide plain-English translations of the simulation scenarios.

**Primary Use Case:** Stress-testing a multi-year decumulation strategy using precise withdrawal rates, variable inflation inputs, and distinct portfolio parameters to identify vulnerability thresholds.

## 4. Core Features & Requirements
### 4.1. Data Ingestion & Processing
**Engine:** All data manipulation must utilize polars for vectorized performance. All statistical derivations (best, worst, most probable outcomes, and success probabilities) MUST be calculated entirely within Polars before being passed to the LLM.

**Public Data Sets:** Ingest historical time-series data covering inflation (CPI), equity total returns (S&P 500), and bond yields (10-Year Treasury) sourced from public repositories like FRED or the Shiller dataset.

**Simulation Generation:** Generate in-memory Monte Carlo matrices capable of evaluating a minimum of 10,000 distinct paths over a flexible horizon ranging from 60 to 360 months.

### 4.2. Reactive Frontend Interface
**Framework:** streamlit (or dash), running purely locally.

**Input Controls:** Sidebar toggles and sliders for portfolio starting value, bridge duration, withdrawal rates, and macroeconomic assumptions (volatility, mean return). All technical inputs must include inline definitions/tooltips to assist users without an economics background.

**Visualizations:** Render decumulation paths dynamically. The UI must clearly highlight strategy failures (principal depletion) and update smoothly without full-engine recalculation overhead.

### 4.3. Local LLM Integration with Ollama
**Orchestration:** The pre-calculated summary metrics (from Polars) and the user's parameter settings will be fed to a local LLM served by Ollama.

**LLM Output (Scenario Translation & Analysis):**
* The LLM will first read the parameter settings and output a plain-English explanation of what the chosen simulation scenario entails.
* It will then provide a qualitative explanation of the statistical realities calculated by Polars (the worst, best, and most probable scenarios).

**Cognitive Architecture:** The local LLM will be enhanced using cognitive architectures referenced from the Oracle AI Developer Hub's agent-reasoning module. The reasoning loop will utilize Chain of Thought (CoT) followed by Self-Reflection (SR) to ensure high-quality synthesis. For queries exceeding 50 tokens, a Decomposed architecture will be triggered prior to the CoT/SR loop.

**Chat Frame:** A separate frame below the analysis will open as a communication window with the local LLM. The application must stream the LLM's CoT and Reflection steps asynchronously to prevent UI freezing. Memory of the conversation between the user and the local LLM should only be kept in RAM.

## 5. Engineering & Methodological Constraints
* **Strict TDD:** Tests must be written and executed before implementation code. No exceptions.

* **Component Isolation:** The Polars data engine must be 100% decoupled from the Streamlit UI, ensuring tests can run instantly offline without invoking the UI layer.

* **Mocking:** All API/subprocess calls to the local Ollama LLM must be mocked in the testing suite to ensure fast, reliable routine CI/CD runs and prevent test suite latency.

* **State Caching:** Heavy matrix calculations must utilize aggressive frontend caching (@st.cache_data) to maintain a reactive UI.

## 6. Out of Scope
* Predictive machine learning models or temporal forecasting.

* External cloud database deployments (state remains local/in-memory).

* Live API connections for real-time stock ticking.

## 7. Success Metrics
* **Performance:** 10,000 Monte Carlo paths over a user-defined period between 60 and 360 months generate and aggregate in under 2 seconds.

* **Coverage:** 95%+ test coverage on all Polars logic and decumulation math.

* **Utility:** Successfully output an actionable, LLM-generated insight analyzing the specific vulnerabilities of the configured decumulation bridge.