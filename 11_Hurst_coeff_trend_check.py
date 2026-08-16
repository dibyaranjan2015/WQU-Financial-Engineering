import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- App Configuration ---
st.set_page_config(page_title="Regime Radar: Hurst Exponent", layout="wide")
st.title("Regime Radar: The Hurst Exponent")
st.markdown("""
Applying a trend-following algorithm to a mean-reverting asset is statistical suicide. 
This engine calculates the rolling **Hurst Exponent (H)** to mathematically classify the market regime before you deploy capital.
""")

# --- Sidebar Inputs ---
st.sidebar.header("Radar Parameters")

# Pre-defined Nifty 50 / Indian Equities
sector_tickers = {
    # Broad Market
    "Broad Market: Nifty 50 Index": "^NSEI",
    "Broad Market: Nifty 50 ETF (NIFTYBEES)": "NIFTYBEES.NS",
    "Midcap 150 Index": "^NSEMDCP50",
    "Midcap 150 ETF (MID150BEES)": "MID150BEES.NS",

    # Banking & Financials
    "Banking Index": "^NSEBANK",
    "Banking ETF (BANKBEES)": "BANKBEES.NS",
    "Financial Services Index": "^CNXFIN",
    "Financial Services ETF (FINNIFTY)": "FINNIFTY.NS",
    "PSU Banks Index": "^CNXPSUBANK",
    "PSU Banks ETF (PSUBNKBEES)": "PSUBNKBEES.NS",

    # Technology & Consumer
    "IT Index": "^CNXIT",
    "IT ETF (ITBEES)": "ITBEES.NS",
    "FMCG Index": "^CNXFMCG",
    "FMCG ETF (FMCGBEES)": "FMCGBEES.NS",
    "Automobiles Index": "^CNXAUTO",
    "Automobiles ETF (AUTOBEES)": "AUTOBEES.NS",

    # Healthcare & Infrastructure
    "Pharma & Healthcare Index": "^CNXPHARMA",
    "Pharma ETF (PHARMABEES)": "PHARMABEES.NS",
    "Infrastructure Index": "^CNXINFRA",
    "Infrastructure ETF (INFRABEES)": "INFRABEES.NS",

    # Heavy Industries & Real Estate
    "Metals & Mining Index": "^CNXMETAL",
    "Metals ETF Proxy (SETFNN50)": "SETFNN50.NS",
    "Energy Index": "^CNXENERGY",
    "Energy Proxy (RELIANCE)": "RELIANCE.NS",
    "Real Estate Index": "^CNXREALTY",
    "Real Estate Proxy (DLF)": "DLF.NS",

    "Custom Ticker...": ""
}

ticker_selection = st.sidebar.selectbox("Select an Asset:", list(sector_tickers.keys()))

if ticker_selection == "Custom Ticker...":
    symbol = st.sidebar.text_input("Asset Ticker (e.g., INFY.NS)", "INFY.NS").upper()
else:
    symbol = sector_tickers[ticker_selection]

# Rolling window for the Hurst calculation
rolling_window = st.sidebar.slider("Rolling Window (Days)", min_value=60, max_value=252, value=126, step=1, help="126 days = approx. 6 months of trading data.")

start_date = st.sidebar.date_input("Start Date", datetime.today() - timedelta(days=365*3))
end_date = st.sidebar.date_input("End Date", datetime.today())

# --- Mathematical Engine ---
def calculate_hurst(ts, max_lag=20):
    """
    Calculates the Hurst Exponent using the Variance of Lagged Differences method.
    Math: The standard deviation of price differences scales as tau^H.
    """
    ts = np.asarray(ts)
    if len(ts) < max_lag:
        return np.nan
    
    lags = range(2, max_lag)
    # Calculate standard deviation of lagged differences
    tau = [np.std(ts[lag:] - ts[:-lag]) for lag in lags]
    
    # Run a log-log regression (OLS) to find the slope
    # X = log(lags), Y = log(tau)
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    
    # The slope is the Hurst Exponent
    return poly[0]

def calculate_hurst_ema(ts, max_lag=20, half_life=21):
    """
    Calculates the Hurst Exponent using an Exponentially Weighted Variance of Lagged Differences.
    This aggressively reduces lag by prioritizing recent price action.
    """
    ts = np.asarray(ts)
    if len(ts) < max_lag:
        return np.nan
    
    lags = range(2, max_lag)
    tau = []
    
    # Calculate the decay rate (lambda)
    decay_rate = np.log(2) / half_life
    
    for lag in lags:
        # 1. Calculate the raw price differences for this lag
        diffs = ts[lag:] - ts[:-lag]
        
        # 2. Create the exponential weights array
        # ts is oldest to newest, so diffs[-1] is today. 
        days_ago = np.arange(len(diffs))[::-1] 
        weights = np.exp(-decay_rate * days_ago) 
        
        # 3. Calculate Weighted Mean
        weighted_mean = np.average(diffs, weights=weights)
        
        # 4. Calculate Weighted Variance & Standard Deviation
        weighted_var = np.average((diffs - weighted_mean)**2, weights=weights)
        weighted_std = np.sqrt(weighted_var)
        
        tau.append(weighted_std)
        
    # Run the log-log regression (OLS) to find the slope (H)
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    
    return poly[0]

# --- Data Fetching & Processing ---
@st.cache_data(show_spinner=False)
def get_processed_data(ticker, start, end, window):
    # Fetch data
    raw_data = yf.download(ticker, start=start, end=end)
    
    # Safely extract 'Close' and force it into a DataFrame
    df = pd.DataFrame(raw_data['Close']).dropna()
    
    # Explicitly rename the column to 'Price'
    df.columns = ['Price']
    
    # Calculate Rolling Hurst Exponent
    df['Hurst'] = df['Price'].rolling(window=window).apply(calculate_hurst, raw=True)
    # df['Hurst_EMA'] = df['Price'].rolling(window=window).apply(calculate_hurst_ema, raw=True)
    return df.dropna()

if st.sidebar.button("Run Regime Radar"):
    with st.spinner(f"Running log-log regressions for {symbol}..."):
        df = get_processed_data(symbol, start_date, end_date, rolling_window)
        
        if df.empty:
            st.error("Error fetching data. Check the ticker or date range.")
        else:
            current_hurst = df['Hurst'].iloc[-1]
            current_price = df['Price'].iloc[-1]
            # current_hurst_ema = df['Hurst_EMA'].iloc[-1]

            # --- Regime Logic ---
            if current_hurst > 0.55:
                regime = "Trending (Persistent)"
                icon = "🏄‍♂️"
                strategy = "Momentum, Trend-Following, Breakouts"
                color = "normal"
            elif current_hurst < 0.45:
                regime = "Mean-Reverting (Anti-Persistent)"
                icon = "🏓"
                strategy = "Statistical Arbitrage, Pairs Trading, RSI Fade"
                color = "inverse"
            else:
                regime = "Random Walk (Noise)"
                icon = "🎲"
                strategy = "None. Stay in cash or hunt for other alphas."
                color = "off"

            # --- Dashboard Layout ---
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Price", f"₹{current_price:.2f}")
            col2.metric("Current Hurst Exponent (H)", f"{current_hurst:.3f}", regime, delta_color=color)
            # col3.metric("Current Hurst EMA (H)", f"{current_hurst_ema:.3f}", regime, delta_color=color)
            st.markdown("---")
            
            st.info(f"{icon} **Alpha Strategy Alignment:** Based on the current regime, quantitative models should prioritize **{strategy}**.")
            st.markdown("---")

            # --- Visualizations ---
            # Chart 1: Price History
            st.subheader(f"1. Price Action: {symbol}")
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(x=df.index, y=df['Price'], name='Price', line=dict(color='blue', width=1.5)))
            fig1.update_layout(height=350, template="plotly_dark", margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig1, use_container_width=True)

            # Chart 2: Rolling Hurst Exponent
            st.subheader(f"2. Market Regime (Rolling {rolling_window}-Day Hurst)")
            
            fig2 = go.Figure()
            
            # Add the Hurst line
            fig2.add_trace(go.Scatter(x=df.index, y=df['Hurst'], name='Hurst (H)', line=dict(color='cyan', width=2)))
            
            # Add horizontal regime boundaries
            fig2.add_hline(y=0.5, line_dash="solid", line_color="gray", annotation_text="0.5 (Random Walk)")
            fig2.add_hline(y=0.55, line_dash="dash", line_color="green", annotation_text="> 0.55 (Trend Zone)")
            fig2.add_hline(y=0.45, line_dash="dash", line_color="red", annotation_text="< 0.45 (Mean-Reversion Zone)")
            
            # Highlight Zones
            fig2.add_hrect(y0=0.55, y1=1.0, fillcolor="green", opacity=0.1, layer="below", line_width=0)
            fig2.add_hrect(y0=0.45, y1=0.55, fillcolor="gray", opacity=0.1, layer="below", line_width=0)
            fig2.add_hrect(y0=0.0, y1=0.45, fillcolor="red", opacity=0.1, layer="below", line_width=0)

            fig2.update_layout(
                height=400, 
                template="plotly_dark", 
                yaxis=dict(range=[0.1, 0.9], title="Hurst Exponent (H)"),
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig2, use_container_width=True)

            # fig3 = go.Figure()
            # fig3.add_trace(go.Scatter(x=df.index, y=df['Hurst_EMA'], name='Hurst EMA (H)', line=dict(color='cyan', width=2)))
                        
            # # Add horizontal regime boundaries
            # fig3.add_hline(y=0.5, line_dash="solid", line_color="gray", annotation_text="0.5 (Random Walk)")
            # fig3.add_hline(y=0.55, line_dash="dash", line_color="green", annotation_text="> 0.55 (Trend Zone)")
            # fig3.add_hline(y=0.45, line_dash="dash", line_color="red", annotation_text="< 0.45 (Mean-Reversion Zone)")
            
            # # Highlight Zones
            # fig3.add_hrect(y0=0.55, y1=1.0, fillcolor="green", opacity=0.1, layer="below", line_width=0)
            # fig3.add_hrect(y0=0.45, y1=0.55, fillcolor="gray", opacity=0.1, layer="below", line_width=0)
            # fig3.add_hrect(y0=0.0, y1=0.45, fillcolor="red", opacity=0.1, layer="below", line_width=0)

            # fig3.update_layout(
            #     height=400, 
            #     template="plotly_dark", 
            #     yaxis=dict(range=[0.1, 0.9], title="Hurst Exponent EMA(H)"),
            #     margin=dict(l=0, r=0, t=30, b=0)
            # )
            # st.plotly_chart(fig3, use_container_width=True)
            
            # st.caption("⚙️ *Note: H is calculated using the variance of lagged differences. A spike into the green zone indicates the asset is ignoring gravity and trending heavily. A drop into the red zone indicates tight, bound trading ranges.*")