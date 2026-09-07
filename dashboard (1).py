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


# ---------- core calculation functions (Part A logic, unchanged) ----------

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


# ---------- state: a plain list of fund dicts, each with a stable id ----------

def make_fund(data, fund_id):
    f = dict(data)
    f["id"] = fund_id
    return f


if "funds" not in st.session_state:
    st.session_state.funds = [make_fund(f, i) for i, f in enumerate(SAMPLE_PORTFOLIO)]
if "next_id" not in st.session_state:
    st.session_state.next_id = len(st.session_state.funds)


def reset_portfolio():
    st.session_state.funds = [make_fund(f, i) for i, f in enumerate(SAMPLE_PORTFOLIO)]
    st.session_state.next_id = len(st.session_state.funds)
    # clear any stale widget state left over from the old rows
    for key in list(st.session_state.keys()):
        if key.startswith(("fund_", "cat_", "risk_", "sip_", "months_", "inv_", "cur_")):
            del st.session_state[key]


def add_fund():
    new_id = st.session_state.next_id
    st.session_state.funds.append(make_fund(
        {"fund": "New fund", "category": "Equity", "risk": "Medium",
         "monthly_sip": 0, "months": 12, "invested": 0, "current_value": 0}, new_id
    ))
    st.session_state.next_id += 1


def remove_fund(fund_id):
    st.session_state.funds = [f for f in st.session_state.funds if f["id"] != fund_id]
    for prefix in ("fund_", "cat_", "risk_", "sip_", "months_", "inv_", "cur_"):
        st.session_state.pop(f"{prefix}{fund_id}", None)


st.title("InvestEasy — SIP & Mutual Fund Portfolio Tracker")
st.caption("Edit any field below with your own fund data. Every figure on this page recalculates as soon as you change something.")

top_left, top_right = st.columns([5, 1])
with top_right:
    st.button("Reset to sample data", on_click=reset_portfolio, use_container_width=True)

# ---------- editable holdings, one widget per field, no data_editor ----------

st.subheader("Holdings")

header_cols = st.columns([2, 1.2, 1, 1.1, 1, 1.2, 1.2, 0.5])
for col, label in zip(header_cols, ["Fund", "Category", "Risk", "Monthly SIP (Rs.)", "Months", "Invested (Rs.)", "Current value (Rs.)", ""]):
    col.markdown(f"**{label}**")

current_funds = []
for f in st.session_state.funds:
    fid = f["id"]
    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([2, 1.2, 1, 1.1, 1, 1.2, 1.2, 0.5])
    name = c1.text_input("Fund", value=f["fund"], key=f"fund_{fid}", label_visibility="collapsed")
    category = c2.selectbox("Category", ["Equity", "Debt", "Hybrid", "Other"],
                             index=["Equity", "Debt", "Hybrid", "Other"].index(f["category"]) if f["category"] in ["Equity", "Debt", "Hybrid", "Other"] else 0,
                             key=f"cat_{fid}", label_visibility="collapsed")
    risk = c3.selectbox("Risk", ["Low", "Medium", "High"],
                         index=["Low", "Medium", "High"].index(f["risk"]) if f["risk"] in ["Low", "Medium", "High"] else 1,
                         key=f"risk_{fid}", label_visibility="collapsed")
    sip = c4.number_input("SIP", min_value=0, value=int(f["monthly_sip"]), step=500, key=f"sip_{fid}", label_visibility="collapsed")
    months = c5.number_input("Months", min_value=0, value=int(f["months"]), step=1, key=f"months_{fid}", label_visibility="collapsed")
    invested = c6.number_input("Invested", min_value=0, value=int(f["invested"]), step=1000, key=f"inv_{fid}", label_visibility="collapsed")
    current_value = c7.number_input("Current", min_value=0, value=int(f["current_value"]), step=1000, key=f"cur_{fid}", label_visibility="collapsed")
    c8.button("✕", key=f"del_{fid}", on_click=remove_fund, args=(fid,))

    current_funds.append({
        "id": fid, "fund": name, "category": category, "risk": risk,
        "monthly_sip": sip, "months": months, "invested": invested, "current_value": current_value,
    })

# keep the stored list's non-widget fields (name/category/etc.) in sync for the next rerun
st.session_state.funds = current_funds

st.button("+ Add fund", on_click=add_fund)

if not current_funds:
    st.info("Add at least one fund above to see the portfolio report.")
    st.stop()

# ---------- map(): compute return %, CAGR %, status for every fund ----------

for f in current_funds:
    f["return_pct"] = round(absolute_return(f["invested"], f["current_value"]), 2)
    f["cagr_pct"] = round(cagr(f["invested"], f["current_value"], f["months"]), 2)
    f["status"] = classify_fund(f["return_pct"])

# ---------- reduce(): portfolio totals ----------

total_invested = sum(f["invested"] for f in current_funds)
total_current_value = sum(f["current_value"] for f in current_funds)
total_monthly_sip = sum(f["monthly_sip"] for f in current_funds)
overall_return_pct = absolute_return(total_invested, total_current_value)
overall_gain = total_current_value - total_invested

for f in current_funds:
    f["portfolio_share_pct"] = round((f["current_value"] / total_current_value) * 100, 2) if total_current_value > 0 else 0.0

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

report_df = pd.DataFrame(current_funds)

# ---------- holding-wise report (read-only display of the computed numbers) ----------

st.subheader("Holding-wise report")
st.dataframe(
    report_df[["fund", "category", "risk", "invested", "current_value", "return_pct",
               "cagr_pct", "status", "portfolio_share_pct"]],
    use_container_width=True,
    hide_index=True,
)

# ---------- filter() views ----------

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Loss-making funds")
    loss_df = report_df[report_df["return_pct"] < 0]
    if loss_df.empty:
        st.write("No fund is currently in loss.")
    else:
        st.dataframe(loss_df[["fund", "invested", "current_value", "return_pct"]],
                     use_container_width=True, hide_index=True)

with col_b:
    st.subheader("Equity funds")
    equity_df = report_df[report_df["category"] == "Equity"]
    if equity_df.empty:
        st.write("No Equity funds in this portfolio.")
    else:
        st.dataframe(equity_df[["fund", "invested", "current_value", "return_pct"]],
                     use_container_width=True, hide_index=True)

# ---------- category allocation ----------

st.subheader("Category-wise allocation")
cat_alloc = report_df.groupby("category")["current_value"].sum()
st.bar_chart(cat_alloc)

st.subheader("Current value by fund")
st.bar_chart(report_df.set_index("fund")["current_value"])

# ---------- SIP future value projection ----------

st.subheader("SIP future value projection")
proj_col1, proj_col2 = st.columns(2)
with proj_col1:
    expected_return = st.slider("Assumed annual return for projection (%)", 1, 30, 12)
with proj_col2:
    years = st.slider("Investment horizon (years)", 1, 30, 10)

report_df["projected_fv"] = report_df["monthly_sip"].apply(lambda sip: sip_future_value(sip, expected_return, years))
st.dataframe(report_df[["fund", "monthly_sip", "projected_fv"]], use_container_width=True, hide_index=True)
st.bar_chart(report_df.set_index("fund")["projected_fv"])

total_projected = report_df["projected_fv"].sum()
st.metric(f"Projected total corpus in {years} year(s)", f"Rs. {total_projected:,.0f}")

st.caption("Figures are illustrative. Projections assume the selected return holds steady every year, which real markets don't do.")
