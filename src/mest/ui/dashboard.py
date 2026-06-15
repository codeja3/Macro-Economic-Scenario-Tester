"""Reactive frontend dashboard for the Macro-Economic Scenario Tester (MEST).

This module implements the user interface using Streamlit, featuring sidebars
for portfolio decumulation planning, parameter tooltips, and responsive layout.
"""

import streamlit as st

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
# MAIN INTERFACE LAYOUT
# ==========================================

# 1. Summary Metrics Header
st.subheader("🏁 Stress Test Results")
m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)

# Placeholders for statistics cards
with m_col1:
    st.markdown(
        """
        <div class="metric-card">
            <p class="metric-title">Success Probability</p>
            <p class="metric-value">-- %</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m_col2:
    st.markdown(
        """
        <div class="metric-card">
            <p class="metric-title">Median End Balance</p>
            <p class="metric-value">$ --</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m_col3:
    st.markdown(
        """
        <div class="metric-card">
            <p class="metric-title">Worst 10% Balance</p>
            <p class="metric-value">$ --</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m_col4:
    st.markdown(
        """
        <div class="metric-card">
            <p class="metric-title">Best 10% Balance</p>
            <p class="metric-value">$ --</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m_col5:
    st.markdown(
        """
        <div class="metric-card">
            <p class="metric-title">Avg Failure Month</p>
            <p class="metric-value">--</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# 2. Main Dashboard Visualization & Analysis Area
tab1, tab2 = st.tabs(["📉 Simulation Paths", "🤖 AI Scenario Analyst"])

with tab1:
    st.subheader("Portfolio Value Over Time")
    # Placeholder for chart
    st.info("📊 Chart showing 100 sample simulation paths will be rendered here. Failed paths (balance hits $0) will be highlighted in red.")
    
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
    # Placeholder for LLM Analysis
    st.warning("🤖 AI Analysis is loading... The local Ollama LLM will synthesize findings using Chain-of-Thought (CoT) and Self-Reflection (SR).")
    
    # Placeholder for LLM Chat Window
    st.markdown("---")
    st.subheader("💬 Ask LLM Analyst")
    st.chat_input("Ask a question about this scenario (e.g. 'What makes this portfolio fail?')")
