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

