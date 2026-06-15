"""Reactive frontend dashboard for the Macro-Economic Scenario Tester (MEST).

This module implements the user interface using Streamlit, featuring sidebars
for portfolio decumulation planning, parameter tooltips, and responsive layout,
integrated with the Polars simulation core and Altair visualizations.
"""

from pathlib import Path
import altair as alt
import pandas as pd
import polars as pl
import streamlit as st

from mest.core.data_loader import load_historical_data, DataLoaderError
from mest.core.simulator import SimulationConfig, run_simulation
from mest.llm.classifier import classify_scenario

# Configure page settings
st.set_page_config(
    page_title="MEST | Decumulation Scenario Tester",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom premium CSS styling (glassmorphism, vibrant colors, premium fonts)
st.markdown(
    """
    <style>
    /* Main Background & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    h1, h2, h3, [class*="stHeader"] {
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
    }

    /* Premium Title Banner */
    .banner-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        border-radius: 16px;
        padding: 30px;
        margin-bottom: 25px;
        border: 1px solid rgba(99, 102, 241, 0.2);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }
    
    .banner-title {
        background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0;
    }
    
    .banner-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-top: 5px;
        margin-bottom: 0;
    }

    /* Glassmorphism Metric Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 0;
    }

    /* Sidebar Custom styling */
    .css-163t7ea {
        background-color: #0b0f19;
    }
    
    /* Help tooltips */
    .stTooltipIcon {
        color: #6366f1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Banner
st.markdown(
    """
    <div class="banner-container">
        <h1 class="banner-title">MEST</h1>
        <p class="banner-subtitle">Macro-Economic Scenario Tester for Phased Decumulation & Sequence of Returns Risk (SORR)</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# CACHED FUNCTIONS FOR PERFORMANCE
# ==========================================
@st.cache_data
def cached_load_data(path: Path) -> pl.DataFrame:
    """Loads historical macroeconomic data with caching."""
    return load_historical_data(path)


@st.cache_data
def cached_run_simulation(config: SimulationConfig, _historical_df: pl.DataFrame | None = None) -> Any:
    """Runs Monte Carlo decumulation simulation with caching on config hash."""
    return run_simulation(config, _historical_df)


# Ingest data
csv_path = Path("data") / "historical_regimes.csv"
try:
    hist_df = cached_load_data(csv_path)
except Exception as e:
    st.error(f"Failed to load historical data: {e}")
    st.stop()


# ==========================================
# SIDEBAR CONTROLS (Layout & Inputs)
# ==========================================
st.sidebar.markdown("## 🎯 Decumulation Plan")

# 1. Starting Principal
starting_principal = st.sidebar.slider(
    "Starting Principal ($)",
    min_value=100_000,
    max_value=5_000_000,
    value=1_000_000,
    step=50_000,
    format="%d",
    help=(
        "The initial value of your investment portfolio at the moment retirement decumulation starts. "
        "All withdrawals will deplete this sum."
    ),
)

# 2. Bridge Period Duration
bridge_duration_months = st.sidebar.slider(
    "Bridge Duration (Months)",
    min_value=0,
    max_value=120,
    value=60,
    step=6,
    help=(
        "The early retirement phase (e.g. before pension, annuities, or Social Security kicks in). "
        "This is typically a high-withdrawal bridge phase."
    ),
)

# 3. Bridge Monthly Spend
bridge_monthly_withdrawal = st.sidebar.slider(
    "Bridge Monthly Withdrawal ($)",
    min_value=0,
    max_value=25_000,
    value=6_000,
    step=250,
    help="The nominal monthly dollar amount you plan to withdraw during the bridge period.",
)

# 4. Post-Bridge Monthly Spend
post_bridge_monthly_withdrawal = st.sidebar.slider(
    "Post-Bridge Monthly Withdrawal ($)",
    min_value=0,
    max_value=25_000,
    value=4_000,
    step=250,
    help=(
        "The nominal monthly dollar amount you plan to withdraw after the bridge period has ended "
        "(e.g., once other stable retirement incomes begin)."
    ),
)

st.sidebar.markdown("---")
st.sidebar.markdown("## 📊 Macroeconomic Parameters")

# 5. Simulation Mode
simulation_mode = st.sidebar.selectbox(
    "Simulation Mode",
    options=["stochastic", "historical_bootstrap"],
    index=0,
    format_func=lambda x: "Monte Carlo Stochastic" if x == "stochastic" else "Historical Bootstrap",
    help=(
        "Monte Carlo Stochastic: Generates random futures using lognormal stock growth assumptions.\n\n"
        "Historical Bootstrap: Re-samples directly from historical U.S. stock (S&P 500) and bond yields (10-Yr Treasury) since 1871."
    ),
)

# Conditionally display inputs based on mode
if simulation_mode == "stochastic":
    # 6. Mean return
    mean_return_annual = st.sidebar.slider(
        "Expected Annual Portfolio Return (%)",
        min_value=-5.0,
        max_value=15.0,
        value=7.0,
        step=0.25,
        format="%.2f",
        help="The expected long-term average annual rate of portfolio growth (arithmetic nominal mean).",
    ) / 100.0

    # 7. Volatility
    volatility_annual = st.sidebar.slider(
        "Expected Annual Portfolio Volatility (%)",
        min_value=0.0,
        max_value=30.0,
        value=12.0,
        step=0.5,
        format="%.1f",
        help=(
            "The expected annual fluctuation (risk) of portfolio returns. Higher volatility represents "
            "greater Sequence of Returns Risk (SORR), which can lead to early depletion even if average returns are good."
        ),
    ) / 100.0

    # 8. Inflation
    inflation_annual = st.sidebar.slider(
        "Expected Annual Inflation (%)",
        min_value=0.0,
        max_value=15.0,
        value=3.0,
        step=0.25,
        format="%.2f",
        help="The expected long-term average annual increase in prices.",
    ) / 100.0
else:
    # Set defaults for bootstrap mode
    mean_return_annual = 0.0
    volatility_annual = 0.0
    inflation_annual = 0.0
    st.sidebar.info(
        "💡 **Historical Bootstrap** utilizes actual Shiller S&P 500 total returns, CPI inflation index changes, "
        "and 10-Year Treasury yield sequences directly. Stated parameters are derived from the historical regime."
    )

# 9. Simulation Duration
simulation_duration_months = st.sidebar.slider(
    "Simulation Duration (Months)",
    min_value=60,
    max_value=360,
    value=360,
    step=12,
    help="The total length of the stress test. Ranges from 5 years (60 months) to 30 years (360 months).",
)

# 10. Advanced Settings
with st.sidebar.expander("🛠️ Advanced Settings"):
    num_paths = st.slider(
        "Number of Paths",
        min_value=1_000,
        max_value=20_000,
        value=10_000,
        step=1_000,
        help="The number of simulated portfolio lifetimes. 10,000 paths provides stable probability convergence.",
    )
    seed = st.number_input(
        "Random Seed",
        min_value=1,
        value=42,
        step=1,
        help="Seed for the random number generator. Lock this to compare scenarios deterministically.",
    )


# ==========================================
# EXECUTE SIMULATION
# ==========================================
config = SimulationConfig(
    starting_principal=float(starting_principal),
    bridge_duration_months=bridge_duration_months,
    bridge_monthly_withdrawal=float(bridge_monthly_withdrawal),
    post_bridge_monthly_withdrawal=float(post_bridge_monthly_withdrawal),
    simulation_duration_months=simulation_duration_months,
    simulation_mode=simulation_mode,
    mean_return_annual=mean_return_annual,
    volatility_annual=volatility_annual,
    inflation_annual=inflation_annual,
    seed=seed,
    num_paths=num_paths,
)

with st.spinner("Calculating simulation paths..."):
    results = cached_run_simulation(config, hist_df)


# ==========================================
# SUMMARY METRICS DISPLAY
# ==========================================
st.subheader("🏁 Stress Test Results")
m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

# Format outputs
success_str = f"{results.success_probability * 100:.1f} %"
median_str = f"${results.median_ending_balance:,.0f}"
p10_str = f"${results.percentile_10th_ending_balance:,.0f}"
p90_str = f"${results.percentile_90th_ending_balance:,.0f}"
failure_month_str = f"Month {results.average_failure_month:.1f}" if results.average_failure_month > 0 else "N/A"

with m_col1:
    st.markdown(
        f"""
        <div class="metric-card">
            <p class="metric-title">Success Probability</p>
            <p class="metric-value" style="color: {'#ef4444' if results.success_probability < 0.8 else '#22c55e'}">{success_str}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m_col2:
    st.markdown(
        f"""
        <div class="metric-card">
            <p class="metric-title">Median End Balance</p>
            <p class="metric-value">{median_str}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m_col3:
    st.markdown(
        f"""
        <div class="metric-card">
            <p class="metric-title">Worst 10% Balance</p>
            <p class="metric-value" style="color: #ef4444">{p10_str}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m_col4:
    st.markdown(
        f"""
        <div class="metric-card">
            <p class="metric-title">Best 10% Balance</p>
            <p class="metric-value">{p90_str}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m_col5:
    st.markdown(
        f"""
        <div class="metric-card">
            <p class="metric-title">Avg Failure Month</p>
            <p class="metric-value">{failure_month_str}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)


# ==========================================
# MAIN INTERFACE TABS
# ==========================================
tab1, tab2 = st.tabs(["📉 Simulation Paths", "🤖 AI Scenario Analyst"])

with tab1:
    st.subheader("Portfolio Value Over Time (100 Sample Paths)")
    
    # 1. Transform monthly path dictionary to Pandas DataFrame
    paths_df = pd.DataFrame(results.monthly_paths)
    
    # 2. Map path failure status (Failure if ending balance is $0)
    # results.monthly_paths keys: 'month', 'path_0', 'path_1', etc.
    num_paths_drawn = len(results.monthly_paths) - 1
    path_statuses = {}
    for i in range(num_paths_drawn):
        path_key = f"path_{i}"
        path_statuses[path_key] = "Failed" if results.monthly_paths[path_key][-1] == 0.0 else "Success"
        
    # 3. Melt to long format for Altair plotting
    long_df = paths_df.melt(id_vars=["month"], var_name="path_id", value_name="balance")
    long_df["status"] = long_df["path_id"].map(path_statuses)

    # 4. Draw Altair chart
    # Successful paths are steel-blue, failed paths are red
    chart = (
        alt.Chart(long_df)
        .mark_line(opacity=0.45, strokeWidth=1.5)
        .encode(
            x=alt.X("month:Q", title="Month"),
            y=alt.Y("balance:Q", title="Portfolio Balance ($)"),
            detail="path_id:N",
            color=alt.Color(
                "status:N",
                scale=alt.Scale(domain=["Success", "Failed"], range=["#3b82f6", "#ef4444"]),
                legend=alt.Legend(title="Path Status"),
            ),
        )
        .properties(width="100%", height=450)
        .interactive()
    )
    
    st.altair_chart(chart, use_container_width=True)

    with st.expander("💡 Understanding the Math"):
        st.markdown(
            """
            This simulator runs **vectorized, in-memory simulations** using Polars. 
            For each month $t$ and path:
            1. **Withdrawal ($W_t$):** We deduct $W_{\\text{bridge}}$ if $t \\le D_{\\text{bridge}}$, else we deduct $W_{\\text{post}}$ from the start-of-month balance.
            2. **Growth ($1+R_t$):** The remaining balance is compounded by the random/historical return $R_t$.
            3. **Vectorized Loop:** $S_t = \\max(0, (S_{t-1} - W_t) \\times (1 + R_t))$
            """
        )

with tab2:
    st.subheader("Local LLM Scenario Narrative")
    
    # Classify the scenario deterministically to display in UI
    regime = classify_scenario(mean_return_annual, volatility_annual, inflation_annual)
    st.info(f"📋 **Deterministic Regime Classification:** {regime}")
    
    # Placeholder for LLM Analysis
    st.warning("🤖 AI Analysis is loading... The local Ollama LLM will synthesize findings using Chain-of-Thought (CoT) and Self-Reflection (SR).")
    
    # Placeholder for LLM Chat Window
    st.markdown("---")
    st.subheader("💬 Ask LLM Analyst")
    st.chat_input("Ask a question about this scenario (e.g. 'What makes this portfolio fail?')")
