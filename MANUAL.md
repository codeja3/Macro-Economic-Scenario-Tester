# MEST User Manual: Macro-Economic Scenario Tester

Welcome to the **Macro-Economic Scenario Tester (MEST)** user manual. MEST is a high-performance, privacy-first, local-first decumulation stress-testing analytics application. It allows you to model custom phased retirement withdrawals (such as early-retirement bridge periods) and stress-test them against stochastic Monte Carlo distributions or 150+ years of historical U.S. economic data.

---

## 1. Prerequisites & Installation

Before running the application, ensure you have the following installed on your machine:
* **Python 3.12+**
* **`uv` Package Manager:** Used to manage virtual environments and dependencies.
* **Ollama (Optional but Recommended):** To use the **AI Scenario Analyst**, ensure you have a local Ollama server running with the `llama3` model. You can download Ollama from [ollama.com](https://ollama.com).

### Setup and Dependency Installation
1. Open your terminal and navigate to the project directory:
   ```bash
   cd /path/to/myFinances/mest
   ```
2. Install the package and dependencies inside a virtual environment using `uv`:
   ```bash
   uv sync
   ```
   This will automatically create a `.venv` directory and install `polars`, `streamlit`, `altair`, `pandas`, `requests`, and other required libraries.

---

## 2. Running the Application

To start the local Streamlit web server and open the dashboard:
```bash
uv run streamlit run src/mest/ui/dashboard.py
```
This will compile the packages, start the server, and automatically launch the dashboard in your default web browser (typically at [http://localhost:8501](http://localhost:8501)).

---

## 3. Using the Dashboard Sliders

The sidebar contains all parameters to configure your portfolio planning and simulation settings. Hovering over the small **"?"** icon next to any slider displays a description of the parameter.

### 🎯 Decumulation Plan
* **Starting Principal:** The total size of your investment portfolio at the moment retirement starts (e.g. $1,000,000).
* **Bridge Duration (Months):** The duration of your early retirement "bridge" phase. This is typically a period where you withdraw more money before other income streams (like pensions, Social Security, or annuities) kick in.
* **Bridge Monthly Withdrawal ($):** The nominal monthly dollar amount you withdraw during the bridge period.
* **Post-Bridge Monthly Withdrawal ($):** The nominal monthly dollar amount you withdraw after the bridge period has ended.

### 📊 Macroeconomic Parameters
* **Simulation Mode:**
  * **Monte Carlo Stochastic:** Generates random future returns based on a lognormal stock distribution.
  * **Historical Bootstrap:** Randomly samples months with replacement from actual U.S. stock (S&P 500 total return), CPI inflation, and bond yield data dating back to **1871**.
* **Expected Annual Portfolio Return (%):** *(Stochastic only)* The long-term average annual growth rate of your portfolio.
* **Expected Annual Portfolio Volatility (%):** *(Stochastic only)* The annual fluctuation (risk) of returns. Higher volatility represents greater **Sequence of Returns Risk (SORR)**—the risk that market drops occur early in retirement, permanently depleting your principal.
* **Expected Annual Inflation (%):** *(Stochastic only)* The long-term average annual rate at which prices rise.
* **Simulation Duration (Months):** The total length of the retirement test. Ranges from 5 years (60 months) to 30 years (360 months).

### 🛠️ Advanced Settings
* **Number of Paths:** The number of simulated lifetimes. Default is `10,000`. Higher numbers provide more stable probability outputs.
* **Random Seed:** A fixed number used to generate random returns. Keeping this number constant ensures you can compare different withdrawal plans deterministically.

---

## 4. Analyzing the Outputs

As soon as you adjust any sidebar parameter, the high-performance Polars engine updates the results in under **0.1 seconds**.

### 🏁 Stress Test Metrics
At the top of the screen, five metrics summarize your portfolio's performance:
1. **Success Probability:** The percentage of simulated paths where your portfolio balance remained above $0 at the end of the simulation. A success rate below 80% will highlight in **red** as a warning.
2. **Median End Balance:** The mid-point outcome (50th percentile). Half of the simulations ended with more than this amount, and half ended with less.
3. **Worst 10% Balance:** The 10th percentile outcome. Represents a severe economic downturn (e.g. a 2008-style crisis).
4. **Best 10% Balance:** The 90th percentile outcome. Represents a highly favorable market boom.
5. **Avg Failure Month:** The average month at which depleted portfolios hit $0 (calculated only for paths that failed). Helps identify how early your money might run out.

### 📉 Simulation Paths Chart
Under the **Simulation Paths** tab, MEST plots 100 sample portfolio lifetimes:
* **Blue Lines:** Successful paths where your money lasted the entire duration.
* **Red Lines:** Depleted paths where the portfolio hit $0.
* **Interactivity:** You can scroll to zoom in/out on the chart, click and drag to pan, and double-click to reset the view.

---

## 5. Using the AI Scenario Analyst

Navigate to the **AI Scenario Analyst** tab on the main page to interact with the local LLM reasoning model.

### 🚀 Running the Baseline Analysis
1. Click the **"Run AI Scenario Analysis"** button.
2. The application will query your local Ollama server. You will see the assistant's reasoning stream dynamically:
   * **Chain of Thought (CoT):** Displays the step-by-step financial reasoning and deductions under the `💭 Chain of Thought` expander.
   * **Self-Reflection (SR):** Displays the self-reflection steps under the `🤔 Self-Reflection` expander, where the model checks its calculations for errors or fallacies.
   * **Narrative:** The final plain-English translation of your scenario settings and statistical realities is streamed directly into the tab.

### 💬 Chatting with the LLM Analyst
At the bottom of the tab, a chat window allows you to ask the model specific questions:
* Ask questions like: *"Why does this portfolio fail?"* or *"How would increasing the bridge period by 2 years affect my worst-case scenario?"*
* The model will answer your question, streaming its thinking process, self-reflection, and final answer in real-time.
* **Privacy Check:** All chat histories are stored strictly in your computer's RAM (`st.session_state`) and are never written to disk or sent to external cloud servers.
