import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats


st.set_page_config(page_title="Asset Correlation Dashboard", layout="wide")

st.title("📊 Asset Correlation Dashboard")
st.write("Calculate and visualize **Pearson**, **Spearman**, and **Kendall's $\\tau$** correlations between two assets based on historical returns.")

# --- Sidebar Inputs ---
st.sidebar.header("User Settings")
ticker1 = st.sidebar.text_input("Asset 1 Ticker", "AAPL").upper()
ticker2 = st.sidebar.text_input("Asset 2 Ticker", "MSFT").upper()
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-01-01"))

@st.cache_data
def load_data(t1, t2, start, end):
    data = yf.download([t1, t2], start=start, end=end)['Close'].dropna()
    returns = data.pct_change().dropna()
    return data, returns



if st.sidebar.button("Run Analysis"):


            
    try:
        data, returns = load_data(ticker1, ticker2, start_date, end_date)

        # --- 1. Stock Price Trends ---
        st.subheader("📈 Historical Price & Performance Trends")
        
        price_tab1, price_tab2 = st.tabs(["Normalized Returns (%)", "Raw Stock Prices ($)"])
        
        with price_tab1:
            st.caption("Normalizes both assets to 0% starting point to compare relative performance side-by-side.")
            normalized_prices = (data / data.iloc[0] - 1) * 100
            
            fig_norm = px.line(
                normalized_prices,
                labels={"value": "Cumulative Growth (%)", "Date": "Date", "variable": "Ticker"},
                title=f"Cumulative Performance Comparison: {ticker1} vs {ticker2}"
            )
            st.plotly_chart(fig_norm, use_container_width=True)

        with price_tab2:
            st.caption("Raw daily adjusted closing prices in USD.")
            fig_prices = px.line(
                data,
                labels={"value": "Price (USD)", "Date": "Date", "variable": "Ticker"},
                title=f"Adjusted Close Prices: {ticker1} & {ticker2}"
            )
            st.plotly_chart(fig_prices, use_container_width=True)

        
        # --- 1. Compute Correlation Metrics ---
        pearson_corr = returns.corr(method='pearson').loc[ticker1, ticker2]
        spearman_corr = returns.corr(method='spearman').loc[ticker1, ticker2]
        kendall_corr = returns.corr(method='kendall').loc[ticker1, ticker2]

        st.subheader("Correlations Between Assets")
        # Display Metrics in Columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Pearson Correlation (Linear)", f"{pearson_corr:.4f}")
        col2.metric("Spearman Correlation (Monotonic)", f"{spearman_corr:.4f}")
        col3.metric("Kendall's Tau (Concordance)", f"{kendall_corr:.4f}")
        
        st.divider()
        
        # --- 2. Plots for Visualizing Correlations ---
        st.subheader("Correlation Visualizations")
        
        tab1, tab2, tab3 = st.tabs(["1. Pearson (Returns Scatter)", "2. Spearman (Rank Scatter)", "3. Kendall (Concordance Map)"])
        
        # Tab 1: Pearson Scatter Plot
        with tab1:
            st.markdown("### Pearson Correlation: Linear Returns Scatter")
            st.caption("Pearson evaluates the direct linear relationship between actual daily return percentages.")
            
            fig_pearson = px.scatter(
                returns, x=ticker1, y=ticker2,
                trendline="ols",
                title=f"Daily Returns: {ticker1} vs {ticker2}",
                labels={ticker1: f"{ticker1} Return", ticker2: f"{ticker2} Return"},
                opacity=0.7
            )
            st.plotly_chart(fig_pearson, use_container_width=True)

        # Tab 2: Spearman Rank Scatter Plot
        with tab2:
            st.markdown("### Spearman Correlation: Rank Scatter")
            st.caption("Spearman converts returns into relative ranks (1 to N) before computing correlation.")
            
            ranks_df = returns.rank()
            fig_spearman = px.scatter(
                ranks_df, x=ticker1, y=ticker2,
                trendline="ols",
                title=f"Return Ranks: {ticker1} vs {ticker2}",
                labels={ticker1: f"{ticker1} Rank", ticker2: f"{ticker2} Rank"},
                color_discrete_sequence=['#2CA02C'],
                opacity=0.7
            )
            st.plotly_chart(fig_spearman, use_container_width=True)

        # Tab 3: Kendall Concordance Heatmap / Matrix
        with tab3:
            st.markdown("### Correlation Matrix Comparison")
            st.caption("Side-by-side view comparing how each correlation measure scales for these two assets.")
            
            corr_summary = pd.DataFrame({
                "Method": ["Pearson", "Spearman", "Kendall Tau"],
                "Correlation": [pearson_corr, spearman_corr, kendall_corr]
            })
            
            fig_bar = px.bar(
                corr_summary, x="Method", y="Correlation", color="Method",
                text_auto=".4f", title="Comparison of Correlation Coefficients",
                range_y=[-1, 1]
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    except Exception as e:
        st.error(f"Error fetching data or calculating correlation: {e}")