import streamlit as st
import scipy.optimize as opt
import pandas as pd

class BondYieldCalculator:
    def __init__(self, face_value: float, coupon_rate: float, years_to_maturity: int, market_price: float, frequency: int = 1):
        self.face_value = face_value
        self.coupon_rate = coupon_rate
        self.years_to_maturity = years_to_maturity
        self.market_price = market_price
        self.frequency = frequency

    def calculate_ytm(self) -> float:  
        def bond_price(ytm):
            coupon_payment = self.face_value * self.coupon_rate / self.frequency
            total_periods = self.years_to_maturity * self.frequency
            price = sum([coupon_payment / (1 + ytm / self.frequency) ** (self.frequency * t) for t in range(1, total_periods + 1)])
            price += self.face_value / (1 + ytm / self.frequency) ** total_periods
            return price

        def objective_function(ytm):
            return bond_price(ytm) - self.market_price

        initial_guess = 0.05  
        try:
            ytm_solution = opt.newton(objective_function, initial_guess)
            return ytm_solution * 100
        except ValueError as e:
            raise ValueError("Failed to converge on a solution for YTM.") from e
        
    def cashflow_table(self) -> list:
        coupon_payment = self.face_value * self.coupon_rate / self.frequency
        total_periods = int(self.years_to_maturity * self.frequency)
        cashflows = []
        for period in range(1, total_periods + 1):
            cashflow = coupon_payment
            if period == total_periods:
                cashflow += self.face_value
            cashflows.append({
                "Period": period,
                "Type": "Coupon" if period < total_periods else "Coupon + Principal",
                "Cashflow Amount ($)": cashflow
            })
        return cashflows
        
# ==========================================
#STREAMLIT WEB APP UI & CONFIGURATION
# ==========================================

st.set_page_config(page_title="Bond Yield Calculator", page_icon="💰", layout="wide")
st.title("💰 Bond Yield Calculator")
st.markdown("Calculate the Yield to Maturity (YTM) of a bond and view its cashflow schedule.")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Bond Parameters")

    face_value = st.number_input("Face Value ($):", min_value=0.0, value=1000.0, step=100.0)
    coupon_rate = st.number_input("Annual Coupon Rate (%):", min_value=0.0, value=5.0, step=0.1) / 100
    years_to_maturity = st.number_input("Years to Maturity:", min_value=1, value=10, step=1)
    market_price = st.number_input("Current Market Price ($):", min_value=0.0, value=950.0, step=10.0)
    frequency = st.selectbox("Coupon Payment Frequency:", options=[1, 2], format_func=lambda x: "Annual" if x == 1 else "Semi-Annual")

    execute_button = st.button("Calculate YTM & Cashflows" , type="primary")

with col2:

    if execute_button:
        try:
            calculator = BondYieldCalculator(face_value, coupon_rate, years_to_maturity, market_price, frequency)
            ytm = calculator.calculate_ytm()
            current_yield = (coupon_rate * face_value) / market_price * 100

            st.success("✅ Results Calculated Successfully!")
            m1,m2 = st.columns(2)
            m1.metric(label="Yield to Maturity (YTM)", value=f"{ytm:.2f}%")
            m2.metric(label="Current Yield", value=f"{current_yield:.2f}%")

            st.markdown("---")
            if market_price < face_value:
                st.info(f"💡 **Asset Pricing Status: Discount** \n\nThe market price is below face value. Consequently, your **YTM ({ytm:.2f}%)** is higher than the coupon rate ({coupon_rate * 100 :.2f}%) because you gain capital appreciation at maturity.")
            elif market_price > face_value:
                st.warning(f"💡 **Asset Pricing Status: Premium** \n\nThe market price is above face value. Consequently, your **YTM ({ytm:.2f}%)** is lower than the coupon rate ({coupon_rate * 100 :.2f}%) because you pay a premium up front.")
            else:
                st.success(f"💡 **Asset Pricing Status: Par Value** \n\nThe market price exactly equals face value. Your YTM matches the coupon rate.")

            cashflows = calculator.cashflow_table()

            st.subheader("Cashflow Schedule")
            cashflow_df = pd.DataFrame(cashflows)
            st.dataframe(cashflow_df, use_container_width=True, hide_index=True)

        except ValueError as e:
            st.error(f"❌ Error in calculation: {str(e)}")
    else:
        st.info("Enter bond parameters and click 'Calculate YTM & Cashflows' to see results.")
