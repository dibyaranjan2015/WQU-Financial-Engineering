import streamlit as st
import datetime
import pandas as pd

# ==========================================
# 1. CORE FINANCIAL MATHEMATICS (OOP CLASSES)
# ==========================================

class CreditRiskEngine:
    def __init__(self, base_rate: float):
        self.base_rate = base_rate

    def evaluate_counterparty(self, principal: float, credit_score: int, has_bankruptcy: bool) -> dict:
        risk_premium = 0.0
        if credit_score < 600:
            risk_premium += 0.05
        elif credit_score < 700:
            risk_premium += 0.02
        if has_bankruptcy:
            risk_premium += 0.08

        final_rate = self.base_rate + risk_premium
        total_due = principal * (1 + final_rate)
        
        if credit_score < 600 or has_bankruptcy:
            pd_rate = 0.25
        elif credit_score < 700:
            pd_rate = 0.08
        else:
            pd_rate = 0.02
            
        expected_loss = total_due * pd_rate
        expected_recovery = total_due * (1 - pd_rate)

        return {
            "final_rate": final_rate,
            "total_due": total_due,
            "probability_of_default": pd_rate,
            "expected_loss": expected_loss,
            "expected_recovery": expected_recovery
        }


class CollateralManager:
    @staticmethod
    def calculate_loss_given_default(outstanding_balance: float, collateral_market_value: float, haircut: float) -> dict:
        liquidation_value = collateral_market_value * (1 - haircut)
        recovered_amount = min(outstanding_balance, liquidation_value)
        net_credit_loss = outstanding_balance - recovered_amount
        return {
            "liquidation_value": liquidation_value,
            "recovered_amount": recovered_amount,
            "net_credit_loss": net_credit_loss
        }


class FixedIncomeAsset:
    def __init__(self, notional: float, annual_coupon_rate: float, maturity_years: int):
        self.notional = notional
        self.annual_coupon_rate = annual_coupon_rate
        self.maturity_years = maturity_years

    def generate_coupon_schedule(self) -> list:
        semi_annual_coupon = (self.annual_coupon_rate / 2) * self.notional
        total_periods = self.maturity_years * 2
        schedule = []
        current_date = datetime.date.today()
        
        for period in range(1, total_periods + 1):
            current_date += datetime.timedelta(days=182)
            payment = semi_annual_coupon
            if period == total_periods:
                payment += self.notional
            schedule.append({
                "Period": period,
                "Payment Date": current_date.strftime("%Y-%m-%d"),
                "Cash Flow Amount ($)": round(payment, 2)
            })
        return schedule


# ==========================================
# 2. STREAMLIT WEB APP UI & USER INTERFACE
# ==========================================

st.set_page_config(page_title="Risk & Fixed Income Analytics", layout="wide")

st.title("📊 Financial Risk & Fixed Income Analytics Platform")
st.markdown("Interactive risk engineering dashboard built from **WQU Lesson 2** modules.")
st.divider()

# Sidebar navigation menu
module_choice = st.sidebar.radio(
    "Select Analytics Engine Module:",
    ["1. Counterparty Credit Risk Engine", "2. Collateral & LGD Simulator", "3. Fixed-Income Bond Scheduler"]
)

# --- MODULE 1 UI ---
if module_choice == "1. Counterparty Credit Risk Engine":
    st.header("🏢 Counterparty Credit Risk Pricing Engine")
    
    col1, col2 = st.columns(2)
    with col1:
        base_rate = st.slider("Base Macroeconomic Risk-Free Rate (%)", 0.0, 20.0, 5.0, step=0.25) / 100.0
        principal = st.number_input("Requested Loan Principal ($)", min_value=1000.0, value=100000.0, step=5000.0)
    with col2:
        credit_score = st.slider("Counterparty Credit Score (FICO range)", 300, 850, 720)
        has_bankruptcy = st.checkbox("History of legal bankruptcy declarations?")
        
    if st.button("Execute Credit Assessment"):
        engine = CreditRiskEngine(base_rate=base_rate)
        res = engine.evaluate_counterparty(principal, credit_score, has_bankruptcy)
        
        st.subheader("Assessment Metrics Report")
        m1, m2, m3 = st.columns(3)
        m1.metric("Final Priced Interest Rate", f"{res['final_rate']:.2%}")
        m2.metric("Total Nominal Due", f"${res['total_due']:,.2f}")
        m3.metric("Probability of Default (PD)", f"{res['probability_of_default']:.2%}")
        
        st.markdown("---")
        m4, m5 = st.columns(2)
        m4.metric("Expected Credit Loss (ECL)", f"${res['expected_loss']:,.2f}", delta_color="inverse")
        m5.metric("Expected Portfolio Recovery Value", f"${res['expected_recovery']:,.2f}")

# --- MODULE 2 UI ---
elif module_choice == "2. Collateral & LGD Simulator":
    st.header("🛡️ Collateral Liquidation & LGD Simulator")
    
    col1, col2 = st.columns(2)
    with col1:
        balance = st.number_input("Outstanding Balance Owed ($)", min_value=0.0, value=50000.0)
        market_val = st.number_input("Current Fair Market Value of Collateral ($)", min_value=0.0, value=60000.0)
    with col2:
        haircut = st.slider("Asset Liquidation Haircut Discount (%)", 0, 100, 20) / 100.0
        
    if st.button("Simulate Asset Recovery"):
        res = CollateralManager.calculate_loss_given_default(balance, market_val, haircut)
        
        st.subheader("Liquidation & Loss Results")
        m1, m2, m3 = st.columns(3)
        m1.metric("Post-Haircut Cash Realized", f"${res['liquidation_value']:,.2f}")
        m2.metric("Net Capital Recovered", f"${res['recovered_amount']:,.2f}")
        
        # Color coding net losses
        loss = res['net_credit_loss']
        if loss > 0:
            st.error(f"⚠️ Net Loss Given Default (LGD): ${loss:,.2f}")
        else:
            st.success(f"✅ Full Recovery Achieved! Net Credit Loss: $0.00")

# --- MODULE 3 UI ---
elif module_choice == "3. Fixed-Income Bond Scheduler":
    st.header("📈 Fixed-Income Bond Cash Flow Planner")
    
    col1, col2 = st.columns(2)
    with col1:
        notional = st.number_input("Bond Notional / Par Value ($)", min_value=1000.0, value=1000000.0, step=50000.0)
        coupon_rate = st.slider("Annual Nominal Coupon Rate (%)", 0.0, 15.0, 4.5, step=0.1) / 100.0
    with col2:
        maturity = st.number_input("Asset Term-to-Maturity (Years)", min_value=1, max_value=50, value=5)
        
    if st.button("Generate Distribution Schedule"):
        bond = FixedIncomeAsset(notional, coupon_rate, maturity)
        schedule_data = bond.generate_coupon_schedule()
        
        # Convert list of dicts directly to a clean Streamlit Data Table
        df = pd.DataFrame(schedule_data)
        st.subheader("Amortization & Coupon Distribution Ledger")
        st.dataframe(df, use_container_width=True)