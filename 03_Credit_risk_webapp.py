import streamlit as st
import datetime
import pandas as pd

# ==========================================
# 1. CORE FINANCIAL MATHEMATICS (OOP CLASSES)
# ==========================================

class CreditRiskEngine:
    def __init__(self, base_rate: float):
        self.base_rate = base_rate  # Base interest rate for credit risk calculations
    
    def evaluate_counterparty(self, principal: float, credit_score: int, has_bankruptcy: bool) -> dict:

        risk_premium = 0;
        if credit_score <600:
            risk_premium += 0.05  # High risk premium for low credit score
        elif credit_score <700:
            risk_premium += 0.02  # Moderate risk premium for average credit score

        if has_bankruptcy:
            risk_premium += 0.10  # Additional risk premium for bankruptcy history

        final_rate = self.base_rate + risk_premium
        total_due = principal * (1 + final_rate)

        if credit_score < 600 or has_bankruptcy:
            pd = 0.25 # High probability of default
        elif credit_score < 700:
            pd = 0.08 # Moderate probability of default
        else:
            pd = 0.02 # Low probability of default
        
        expected_loss = total_due * pd
        expected_recovery = total_due - expected_loss

        return {
            "final_rate": final_rate,  # Final interest rate after risk adjustments
            "total_due": total_due,    # Total amount due including principal and interest  
            "probability_of_default": pd,  # Probability of default based on credit score and history
            "expected_loss": expected_loss,  # Expected loss due to default 
            "expected_recovery": expected_recovery  # Expected amount recoverable after default
        }


class CollateralManager:
    @staticmethod

    def calculate_loss_given_default(outstanding_balance: float, collateral_market_value: float, haircut: float) -> dict:
        
        liquidation_value = collateral_market_value * (1 - haircut) # haircut is the percentage reduction in collateral value to account for market volatility and liquidation costs
        recovered_amount = min(liquidation_value, outstanding_balance)
        net_credit_loss = outstanding_balance - recovered_amount

        return {
            "liquidation_value": liquidation_value,  # Value of collateral after applying haircut
            "recovered_amount": recovered_amount,    # Amount recovered from collateral liquidation
            "net_credit_loss": net_credit_loss       # Net loss after accounting for recovered collateral
            }


# ==========================================
# 2. STREAMLIT WEB APP UI & USER INTERFACE
# ==========================================

st.set_page_config(page_title="Credit Risk Analytics", layout="wide")

st.title("📊 Financial Risk & Fixed Income Analytics Platform")
st.markdown("Interactive risk engineering dashboard")
st.divider()

# Sidebar navigation menu
module_choice = st.sidebar.radio(
    "Select Analytics Engine Module:",
    ["1. Counterparty Credit Risk Engine", "2. Collateral & LGD Simulator"]
)

# --- MODULE 1 UI ---
if module_choice == "1. Counterparty Credit Risk Engine":
    st.header("1️⃣ Counterparty Credit Risk Engine")
    st.markdown("Evaluate the credit risk of a counterparty based on their credit score, bankruptcy history, and principal amount.")

    # Input fields for credit risk evaluation
    principal = st.number_input("Principal Amount ($):", min_value=0.0, value=10000.0, step=1000.0)
    credit_score = st.number_input("Credit Score (300-850):", min_value=300, max_value=850, value=700, step=1)
    has_bankruptcy = st.checkbox("Has Bankruptcy History?", value=False)

    # Base interest rate input
    base_rate = st.number_input("Base Interest Rate (%):", min_value=0.0, value=5.0, step=0.1) / 100

    if st.button("Evaluate Credit Risk"):
        engine = CreditRiskEngine(base_rate)
        result = engine.evaluate_counterparty(principal, credit_score, has_bankruptcy)

        # Display results in a table
        result_df = pd.DataFrame([result])
        result_df.columns = ['Final Rate', 'Total Due', 'Probability of Default', 'Expected Loss', 'Expected Recovery']
        result_df.style.format({
            'Final Rate': '{:.2%}',
            'Total Due': '${:,.2f}',
            'Probability of Default': '{:.2%}',
            'Expected Loss': '${:,.2f}',
            'Expected Recovery': '${:,.2f}' 
        })
        st.subheader("Credit Risk Evaluation Results")
        st.dataframe(result_df, use_container_width=True, hide_index=True)

if module_choice == "2. Collateral & LGD Simulator":
    st.header("2️⃣ Collateral Liquidation & Loss Given Default (LGD) Simulator")
    st.markdown("Simulate the loss given default based on outstanding balance, collateral market value, and haircut percentage.")

    # Input fields for LGD simulation
    outstanding_balance = st.number_input("Outstanding Balance ($):", min_value=0.0, value=10000.0, step=1000.0)
    collateral_market_value = st.number_input("Collateral Market Value ($):", min_value=0.0, value=12000.0, step=1000.0)
    haircut = st.number_input("Haircut (%):", min_value=0.0, max_value=100.0, value=20.0, step=1.0) / 100

    if st.button("Simulate LGD"):
        lgd_result = CollateralManager.calculate_loss_given_default(outstanding_balance, collateral_market_value, haircut)

        # Display results in a table
        lgd_df = pd.DataFrame([lgd_result])
        lgd_df.columns = ['Liquidation Value', 'Recovered Amount', 'Net Credit Loss']
        st.subheader("Loss Given Default Simulation Results")
        st.table(lgd_df)