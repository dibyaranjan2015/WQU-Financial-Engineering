import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

st.set_page_config(page_title="NSE Sector Correlation Analysis", layout="wide")

st.title("Indian Equity Markets: Volatility-Induced Correlation Breakdown")
st.markdown("""
This application tests **Hypothesis**:*Do pairwise return correlations across Nifty sector indices spike significantly during high market volatility regimes (measured by India VIX)?*
""")

# --- Sidebar Inputs ---
st.sidebar.header("Parameters")
start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2018-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("2024-06-30"))

low_vix_pct = st.sidebar.slider("Low Volatility Percentile (VIX)", 10, 40, 25) / 100.0
high_vix_pct = st.sidebar.slider("High Volatility Percentile (VIX)", 60, 90, 75) / 100.0

# Define NSE Sector Tickers and India VIX
SECTOR_TICKERS = {
    'Nifty Bank': '^NSEBANK',
    'Nifty IT': '^CNXIT',
    'Nifty Auto': '^CNXAUTO',
    'Nifty Pharma': '^CNXPHARMA',
    'Nifty FMCG': '^CNXFMCG',
    'Nifty Metal': '^CNXMETAL'
}
VIX_TICKER = '^INDIAVIX'

@st.cache_data
def load_data(start, end):
    all_tickers = list(SECTOR_TICKERS.values()) + [VIX_TICKER]
    raw_data = yf.download(all_tickers, start=start, end=end)['Close'].dropna()
    
    # Extract VIX and Sector prices
    vix_series = raw_data[VIX_TICKER]
    sector_prices = raw_data[list(SECTOR_TICKERS.values())]
    sector_prices.columns = list(SECTOR_TICKERS.keys())
    
    # Calculate daily percentage returns
    sector_returns = sector_prices.pct_change().dropna()
    vix_aligned = vix_series.loc[sector_returns.index]
    
    return sector_returns, vix_aligned

if st.sidebar.button("Run Hypothesis Test"):
    with st.spinner("Fetching data and computing correlations..."):
        try:
            sector_returns, vix_series = load_data(start_date, end_date)
            
            # --- 1. Regime Partitioning ---
            low_thresh = vix_series.quantile(low_vix_pct)
            high_thresh = vix_series.quantile(high_vix_pct)
            
            low_vol_returns = sector_returns[vix_series <= low_thresh]
            high_vol_returns = sector_returns[vix_series >= high_thresh]
            
            corr_low = low_vol_returns.corr()
            corr_high = high_vol_returns.corr()
            
            # Metrics Overview
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Low VIX Threshold", f"≤ {low_thresh:.2f}")
            col2.metric("High VIX Threshold", f"≥ {high_thresh:.2f}")
            col3.metric("Low Vol Days", f"{len(low_vol_returns)} days")
            col4.metric("High Vol Days", f"{len(high_vol_returns)} days")
            
            st.divider()

            # --- 2. Heatmap Visualizations ---
            st.subheader("Sector Correlation Heatmaps by Volatility Regime")
            
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown(f"### Low Volatility Regime (VIX ≤ {low_thresh:.2f})")
                fig_low = px.imshow(
                    corr_low,
                    text_auto=".2f",
                    color_continuous_scale="Purples",
                    zmin=-0.2, zmax=1.0,
                    title="Correlation Matrix (Calm Markets)"
                )
                st.plotly_chart(fig_low, use_container_width=True)
                
            with col_right:
                st.markdown(f"### High Volatility Regime (VIX ≥ {high_thresh:.2f})")
                fig_high = px.imshow(
                    corr_high,
                    text_auto=".2f",
                    color_continuous_scale="Reds",
                    zmin=-0.2, zmax=1.0,
                    title="Correlation Matrix (Stress Markets)"
                )
                st.plotly_chart(fig_high, use_container_width=True)
                
            st.divider()

            # --- 3. Statistical Testing (Fisher Z-Transform) ---
            st.subheader("Fisher Z-Transformation Hypothesis Test Results")
            
            n_low, n_high = len(low_vol_returns), len(high_vol_returns)
            results = []
            sectors = list(SECTOR_TICKERS.keys())
            
            for i in range(len(sectors)):
                for j in range(i + 1, len(sectors)):
                    sec1, sec2 = sectors[i], sectors[j]
                    r_low = corr_low.loc[sec1, sec2]
                    r_high = corr_high.loc[sec1, sec2]
                    
                    r_low_c = np.clip(r_low, -0.9999, 0.9999)
                    r_high_c = np.clip(r_high, -0.9999, 0.9999)
                    
                    z_low = np.arctanh(r_low_c)
                    z_high = np.arctanh(r_high_c)
                    
                    se_diff = np.sqrt((1 / (n_low - 3)) + (1 / (n_high - 3)))
                    z_stat = (z_high - z_low) / se_diff
                    p_val = 1 - stats.norm.cdf(z_stat)
                    
                    results.append({
                        'Sector Pair': f"{sec1} ↔ {sec2}",
                        'Low VIX Corr': round(r_low, 4),
                        'High VIX Corr': round(r_high, 4),
                        'Delta (High - Low)': round(r_high - r_low, 4),
                        'Z-Statistic': round(z_stat, 2),
                        'P-Value (1-tailed)': round(p_val, 4),
                        'Statistically Significant (p < 0.05)': "✅ Yes" if p_val < 0.05 else "❌ No"
                    })
                    
            results_df = pd.DataFrame(results)
            
            avg_low = results_df['Low VIX Corr'].mean()
            avg_high = results_df['High VIX Corr'].mean()
            
            st.info(f"""
            **Summary Decision:**
            * **Average Low-Volatility Correlation:** `{avg_low:.4f}`
            * **Average High-Volatility Correlation:** `{avg_high:.4f}`
            * **Overall Sector Correlation Increase:** `+{avg_high - avg_low:.4f}`
            """)
            
            st.dataframe(results_df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Error executing analysis: {e}")