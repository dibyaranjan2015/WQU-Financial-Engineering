import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- App Configuration ---
st.set_page_config(page_title="Pairs Trading Engine: NSE Equities", layout="wide")
st.title("Statistical Arbitrage: Cointegration vs. Correlation")
st.markdown("""
A common trap in quantitative trading is building pairs trades based solely on **correlation**. 
This engine tests for **cointegration**—ensuring the spread between two Indian equities is actually stationary and mean-reverting.
""")

# --- Sidebar Inputs ---
st.sidebar.header("Model Parameters")

# Pre-defined Nifty pairs for easy testing
nifty_pairs = {
    "Banking: HDFC vs ICICI": ("HDFCBANK.NS", "ICICIBANK.NS"),
    "IT: TCS vs Infosys": ("TCS.NS", "INFY.NS"),
    "Metals: Tata Steel vs JSW": ("TATASTEEL.NS", "JSWSTEEL.NS"),
    "Custom Pair...": ("", "")
}

pair_selection = st.sidebar.selectbox("Select a standard NSE pair or choose Custom:", list(nifty_pairs.keys()))

if pair_selection == "Custom Pair...":
    asset_1 = st.sidebar.text_input("Asset 1 Ticker (e.g., RELIANCE.NS)", "RELIANCE.NS").upper()
    asset_2 = st.sidebar.text_input("Asset 2 Ticker (e.g., ONGC.NS)", "ONGC.NS").upper()
else:
    asset_1, asset_2 = nifty_pairs[pair_selection]

start_date = st.sidebar.date_input("Start Date", datetime.today() - timedelta(days=365*3))
end_date = st.sidebar.date_input("End Date", datetime.today())

# --- Data Fetching ---
@st.cache_data
def load_data(ticker1, ticker2, start, end):
    data = yf.download([ticker1, ticker2], start=start, end=end)['Close']
    data = data.dropna()
    return data

if st.sidebar.button("Run Statistical Test"):
    with st.spinner("Fetching data and calculating statistics..."):
        df = load_data(asset_1, asset_2, start_date, end_date)
        
        if df.empty or len(df.columns) < 2:
            st.error("Error fetching data. Please check the tickers and try again. (Ensure you use the .NS suffix for Indian stocks).")
        else:
            y = df[asset_1]
            x = df[asset_2]

            # --- Statistical Calculations ---
            # 1. Pearson Correlation
            correlation = y.corr(x)
            
           # 2. OLS Regression for Hedge Ratio
            x_with_const = sm.add_constant(x)
            model = sm.OLS(y, x_with_const).fit()
            hedge_ratio = model.params[asset_2] 
            
            # 3. Calculate the Spread
            spread = y - (hedge_ratio * x)
            
            # 4. Cointegration Test (Engle-Granger)
            score, p_value, _ = coint(y, x)
            
            # 5. Z-Score of the Spread
            z_score = (spread - spread.mean()) / spread.std()

            # --- Dashboard Layout ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Pearson Correlation", f"{correlation:.3f}", "Directional Similarity")
            col2.metric("Cointegration p-value", f"{p_value:.4f}", "Stationary" if p_value < 0.05 else "Non-Stationary", delta_color="inverse" if p_value > 0.05 else "normal")
            # 1. Display the clean metric
            col3.metric(
                label="Hedge Ratio (Beta)", 
                value=f"{hedge_ratio:.2f}", 
                help=f"Trade Sizing: You need {hedge_ratio:.2f} shares of {asset_2} to hedge 1 share of {asset_1}."
            )

            # --- Interpretation ---
            if p_value < 0.05:
                st.success(f"**Cointegrated:** The p-value is below 0.05. The spread between {asset_1} and {asset_2} is statistically mean-reverting. This is a valid statistical arbitrage pair.")
            else:
                st.error(f"**Not Cointegrated:** The p-value is above 0.05. Despite a correlation of {correlation:.2f}, the spread drifts. Trading this pair relies on directional risk, not statistical mean reversion.")

            # --- Visualizations ---
            st.subheader(f"1. Normalized Price Action: {asset_1} vs {asset_2}")
            
            # Normalize prices to start at 100 for visual comparison
            norm_y = (y / y.iloc[0]) * 100
            norm_x = (x / x.iloc[0]) * 100
            
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df.index, y=norm_y, name=asset_1, line=dict(color='blue')))
            fig1.add_trace(go.Scatter(x=df.index, y=norm_x, name=asset_2, line=dict(color='orange')))
            fig1.update_layout(height=400, template="plotly_dark", yaxis_title="Normalized Price (Base 100)")
            st.plotly_chart(fig1, use_container_width=True)

            st.subheader("2. The Mean-Reverting Spread (Z-Score)")
            st.markdown(f"When the Z-Score crosses **+2.0** (Short {asset_1}, Long {asset_2}) or **-2.0** (Long {asset_1}, Short {asset_2}).")
            
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=z_score.index, y=z_score, name='Z-Score', line=dict(color='cyan')))
            fig2.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Mean (0)")
            fig2.add_hline(y=2, line_dash="dash", line_color="red", annotation_text="Short Threshold (+2)")
            fig2.add_hline(y=-2, line_dash="dash", line_color="green", annotation_text="Long Threshold (-2)")
            fig2.update_layout(height=400, template="plotly_dark", yaxis_title="Z-Score")
            st.plotly_chart(fig2, use_container_width=True)