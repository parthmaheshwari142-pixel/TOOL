import streamlit as st
import pandas as pd

st.set_page_config(page_title="InvestEasy Portfolio Tracker", layout="wide")

SAMPLE_PORTFOLIO = [
    {"fund": "BlueChip Equity", "category": "Equity", "risk": "High", "monthly_sip": 5000,
     "months": 36, "invested": 180000, "current_value": 246000},
    {"fund": "MidCap Growth", "category": "Equity", "risk": "High", "monthly_sip": 3000,
     "months": 24, "invested": 72000, "current_value": 68500},
    {"fund": "Balanced Advantage", "category": "Hybrid", "risk": "Medium", "monthly_sip": 4000,
     "months": 36, "invested": 144000, "current_value": 171000},
    {"fund": "Corporate Bond", "category": "Debt", "risk": "Low", "monthly_sip": 2000,
     "months": 48, "invested": 96000, "current_value": 112000},
    {"fund": "Liquid Fund", "category": "Debt", "risk": "Low", "monthly_sip": 6000,
     "months": 12, "invested": 72000, "current_value": 74500},
    {"fund": "SmallCap Opportunities", "category": "Equity", "risk": "High",
     "monthly_sip": 2500, "months": 18, "invested": 45000, "current_value": 39000},
]


# ---------- core calculation functions (Part A logic) ----------

def absolute_return(invested, current_value):
    if invested is None or invested <= 0:
        return 0.0
    return ((current_value - invested) / invested) * 100


def cagr(invested, current_value, months):
    if invested is None or invested <= 0 or months is None or months <= 0:
        return 0.0
    if current_value < 0:
        return -100.0
    return ((current_value / invested) ** (12 / months) - 1) * 100


def classify_fund(return_pct):
    if return_pct > 15:
        return "Outperformer"
    elif return_pct >= 8:
        return "Average"
    elif return_pct >= 0:
        return "Underperformer"
    else:
        return "Loss Making"


def sip_future_value(monthly_sip, annual_return, years):
    if monthly_sip is None or monthly_sip <= 0 or years is None or years <= 0:
        return 0.0
    i = annual_return / 12 / 100
    n = years * 12
    if i == 0:
        return monthly_sip * n
    return monthly_sip * (((1 + i) ** n - 1) / i) * (1 + i)


# ---------- session state: the editable portfolio ----------

if "portfolio_df" not in st.session_state:
    st.session_state.portfolio_df = pd.DataFrame(SAMPLE_PORTFOLIO)

st.title("InvestEasy — SIP & Mutual Fund Portfolio Tracker")
st.caption("Edit the table below with your own fund data — every number on this page recalculates live.")

top_left, top_right = st.columns([5, 1])
with top_right:
    if st.button("Reset to sample data", use_container_width=True):
        st.session_state.portfolio_df = pd.DataFrame(SAMPLE_PORTFOLIO)
        st.rerun()

# ---------- editable holdings table ----------

st.subheader("Holdings")
edited_df = st.data_editor(
    st.session_state.portfolio_df,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "fund": st.column_config.TextColumn("Fund", required=True),
        "category": st.column_config.SelectboxColumn("Category", options=["Equity", "Debt", "Hybrid", "Other"], required=True),
        "risk": st.column_config.SelectboxColumn("Risk", options=["Low", "Medium", "High"], required=True),
        "monthly_sip": st.column_config.NumberColumn("Monthly SIP (Rs.)", min_value=0, step=500),
        "months": st.column_config.NumberColumn("Months invested", min_value=0, step=1),
        "invested": st.column_config.NumberColumn("Invested (Rs.)", min_value=0, step=1000),
        "current_value": st.column_config.NumberColumn("Current value (Rs.)", min_value=0, step=1000),
    },
    key="portfolio_editor",
)
st.session_state.portfolio_df = edited_df

df = edited_df.copy()
df = df.dropna(subset=["fund"])
for col in ["monthly_sip", "months", "invested", "current_value"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

if df.empty:
    st.info("Add at least one fund above to see the portfolio report.")
    st.stop()

# map(): compute return %, CAGR %, status for every fund
df["return_pct"] = df.apply(lambda r: round(absolute_return(r["invested"], r["current_value"]), 2), axis=1)
df["cagr_pct"] = df.apply(lambda r: round(cagr(r["invested"], r["current_value"], r["months"]), 2), axis=1)
df["status"] = df["return_pct"].apply(classify_fund)

# reduce(): portfolio totals
total_invested = df["invested"].sum()
total_current_value = df["current_value"].sum()
total_monthly_sip = df["monthly_sip"].sum()
overall_return_pct = absolute_return(total_invested, total_current_value)
overall_gain = total_current_value - total_invested

df["portfolio_share_pct"] = df["current_value"].apply(
    lambda v: round((v / total_current_value) * 100, 2) if total_current_value > 0 else 0.0
)

# ---------- summary strip ----------

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Invested", f"Rs. {total_invested:,.0f}")
col2.metric("Current Value", f"Rs. {total_current_value:,.0f}")
col3.metric("Overall Return", f"{overall_return_pct:.2f}%", delta=f"Rs. {overall_gain:,.0f}")
col4.metric("Monthly SIP Outflow", f"Rs. {total_monthly_sip:,.0f}")

if overall_return_pct > 0:
    st.success(f"Overall PROFIT of Rs. {overall_gain:,.0f} ({overall_return_pct:.2f}%)")
elif overall_return_pct < 0:
    st.error(f"Overall LOSS of Rs. {abs(overall_gain):,.0f} ({overall_return_pct:.2f}%)")
else:
    st.info("Portfolio is break-even.")

# ---------- holding-wise report ----------

st.subheader("Holding-wise report")
st.dataframe(
    df[["fund", "category", "risk", "invested", "current_value", "return_pct",
        "cagr_pct", "status", "portfolio_share_pct"]],
    use_container_width=True,
    hide_index=True,
)

# ---------- filter() views ----------

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Loss-making funds")
    loss_df = df[df["return_pct"] < 0]
    if loss_df.empty:
        st.write("No fund is currently in loss.")
    else:
        st.dataframe(loss_df[["fund", "invested", "current_value", "return_pct"]],
                     use_container_width=True, hide_index=True)

with col_b:
    st.subheader("Equity funds")
    equity_df = df[df["category"] == "Equity"]
    if equity_df.empty:
        st.write("No Equity funds in this portfolio.")
    else:
        st.dataframe(equity_df[["fund", "invested", "current_value", "return_pct"]],
                     use_container_width=True, hide_index=True)

# ---------- category allocation ----------

st.subheader("Category-wise allocation")
cat_alloc = df.groupby("category")["current_value"].sum()
st.bar_chart(cat_alloc)

st.subheader("Current value by fund")
st.bar_chart(df.set_index("fund")["current_value"])

# ---------- SIP future value projection ----------

st.subheader("SIP future value projection")
proj_col1, proj_col2 = st.columns(2)
with proj_col1:
    expected_return = st.slider("Assumed annual return for projection (%)", 1, 30, 12)
with proj_col2:
    years = st.slider("Investment horizon (years)", 1, 30, 10)

df["projected_fv"] = df["monthly_sip"].apply(lambda sip: sip_future_value(sip, expected_return, years))
st.dataframe(df[["fund", "monthly_sip", "projected_fv"]], use_container_width=True, hide_index=True)
st.bar_chart(df.set_index("fund")["projected_fv"])

total_projected = df["projected_fv"].sum()
st.metric(f"Projected total corpus in {years} year(s)", f"Rs. {total_projected:,.0f}")

st.caption("Figures are illustrative. Projections assume the selected return holds steady every year, which real markets don't do.")
