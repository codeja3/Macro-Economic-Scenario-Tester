# INSTRUCTIONS.md: MEST Engineering & AI Standards

This document defines the immutable rules of engagement for developing SpendSight. It governs both the architectural design of the software and the collaborative workflow between the developer and the AI assistant. 

## 1. Development Workflow & AI Collaboration
* **CLI-Exclusive Execution:** All development, testing, and execution must occur directly via the Command Line Interface (CLI). Workflows tailored for Graphical IDEs (like Jupyter Notebooks or VS Code integrated runners) are strictly prohibited.
* **Spec-Driven Development (SDD):** `SPEC.md` is the ultimate source of truth. System specifications, API contracts, and data schemas must be explicitly defined and locked in `SPEC.md` before pipeline construction begins.
* **Strict Test-Driven Development (TDD):** Tests strictly dictate implementation. For every task, xUnit-style tests must be written and executed *before* any core implementation logic is authored.
* Enforce RED-GREEN-Refactor cycle, with tests written first
* FORBIDDEN: Implementation before test, skipping RED phase
* FORBIDDEN: Changing the tests simply in order to pass. All changes to tests should reflect either a change in requirements or an error identified in the test.
* FORBIDDEN: Simplifying the problem to pass the test.
* **The "Ping-Pong" Protocol:** 
  1. Define task.
  2. AI writes the failing test.
  3. Developer executes via CLI and provides feedback.
  4. AI writes the minimum implementation to pass.
  5. Refactor and document.

## 2. Core Design Principles
* **Single Responsibility Principle (SRP):** One module, one class, one job. If a class's purpose cannot be described without using the word "and," it must be split. (e.g., Extract validation logic from extraction logic).
* **Defensive Programming (Fail-Fast):** Validate inputs immediately. Use custom exceptions for validation errors. Do not swallow exceptions; propagate them up or handle them explicitly. 
* **Encapsulation & Abstraction:** Hide internal state. Expose behavior, not data. Protect internal mechanisms from arbitrary modification.
* **Extensibility (Open/Closed):** Code should be open for extension but closed for modification. Use strategy patterns, interfaces, and composition over deep inheritance chains or monolithic `if/else` blocks.
* **Simplicity (KISS, DRY, YAGNI):** Prefer simple solutions. Extract common logic to maintain a single source of truth. Do not build abstractions for hypothetical future needs.  
* **Evaluation of Effectiveness:** Before creating code, brainstorm 5 different approaches to solve the problem and sort them by their probable effectiveness. Then choose the best approach and implement it.

## 3. Language & Environmental Standards

### Python Ecosystem Mandates
* **Cross-Platform Portability:** String concatenation for paths is prohibited. `pathlib` must be used for all file system interactions.
* **Type Safety:** Strict type hints are mandatory for all function signatures and class properties.
* **Docstrings:** Use google style docstrings on each function you are writing. 
* **Data Structures:** Use `dataclasses` (or Pydantic models) for immutable data passing.
* **Resource Management:** Context managers (`with` statements) are mandatory for file I/O and database connections to ensure automatic cleanup.
* **Interface Design:** Use the `abc` module to define clear abstract base classes for swappable components.
* **Script execution:**  use `uv run` to execute Python scripts and commands.   
* **Code testing:**  use `pytest` for testing your code.  
        * **Test fixtures:** Collect pytest fixtures in a conftest.py file to avoid duplication.
* **Logging:** Use logging to provide insight into failures. Don't use print for debugging. Don't use logging to hide stack traces if you are going to fail anyway. Prefer simpler packages for logging where possible such as `loguru` over native logging libraries. 


## 4. Workflow Context (Spec-Driven)
*   **Context Reading:** Before writing code, always read the project's memory files, including the Project Requirements Document (`PRD.md`), specifications (`SPEC.md`), and the active task list (`TODO.md`).
*   **Bounded Execution:** Only implement the specific, bounded task assigned to you. Do not engage in "gold-plating," scope creep, or attempting to solve problems outside the current requirement.

## 4. MEST Domain Rules
* **Absolute Privacy:** The system must never make external network calls for data processing unless otherwise and **explicitly** instructed to do so. All LLM inference must occur via the local server (Ollama).
* **MEMORY.md:** 
    * Use the `MEMORY.md` file to record all major decisions and justification for those for each phase of development. If a recorded decision changes the entry should be changed accordingly. 
    * IMPORTANT: `MEMORY.md` should remain reasonable in size. There should be a section for each phase of the development process. Only the important information for the project's reproduction shall be recorded.
    * IMPORTANT: `MEMORY.md` should be ingestable both by an LLM and a human. 
    * IMPORTANT: `MEMORY.md` along with other contracts should be structured in a way that allows accurate reproduction of the project from scratch. 

## 5. Package Management & Environment
* **No Monolithic Environments:** Monolithic environment managers (like Conda) and full-stack containerization (like Docker) are explicitly rejected to preserve bare-metal hardware access for local LLM inference on Apple Silicon.
* **Python Dependency Management:** `uv` is the mandated package manager for the Python extraction layer. Standard `requirements.txt` or `pyproject.toml` will be used, and execution will occur within a `uv`-managed virtual environment.

