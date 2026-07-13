import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np  
import matplotlib.pyplot as plt
import datetime

class StockPricePredictor:

    """
    Handles live market data ingestion, statistical parameter calibration,
    and matrix-based Monte Carlo price forecasting.
    """

    def __init__(self, ticker: str):
        self.ticker = ticker
        self.price_history = pd.Series(dtype=float)  # Initialize an empty Series to store price history
        self.mu = 0.0  # Mean of daily returns
        self.sigma = 0.0  # Standard deviation of daily returns

    def fetch_price_history(self, lookback_years: int =1) -> bool:

        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=lookback_years * 365)

        data = yf.download(self.ticker, start=start_date, end=end_date, progress=False)

        if data.empty:
            return False  # Return False if no data is fetched
        
        self.price_history = data['Close'].squeeze()  # Store the adjusted close prices as a Series
        log_returns = np.log(self.price_history / self.price_history.shift(1)).dropna()

        daily_mean = log_returns.mean()
        daily_std = log_returns.std()

        self.sigma = daily_std * np.sqrt(252)  # Annualized standard deviation
        self.mu = (daily_mean * 252) + (0.5 * self.sigma ** 2)  # Annualized mean return adjusted for volatility

        return True  # Return True if data is successfully fetched and parameters are calculated
    
    def monte_carlo_simulation(self, num_simulations: int = 1000, forecast_days: int = 252) -> np.ndarray:
        """
        Performs Monte Carlo simulations to forecast future stock prices.

        Parameters:
        - num_simulations: Number of simulation paths to generate.
        - forecast_days: Number of days to forecast into the future.

        Returns:
        - A 2D numpy array where each row represents a simulation path and each column represents a day in the forecast period.
        """
        dt = 1/252  # Time increment for daily steps
        last_price = self.price_history.iloc[-1]  # Get the last known price

        price_matrrix = np.zeros((forecast_days + 1, num_simulations))
        price_matrrix[0] = last_price  # Set the initial price for all simulations

        Z = np.random.standard_normal((forecast_days, num_simulations))  # Generate random shocks
        R = (self.mu - 0.5 * self.sigma ** 2) * dt + (self.sigma * np.sqrt(dt) * Z)  # Calculate returns

        for t in range(1, forecast_days + 1):
            price_matrrix[t] = price_matrrix[t - 1] * np.exp(R[t - 1])  # Update prices based on returns
        
        return price_matrrix
    

# ==================================
# STREAMLIT WEB APP UI & CONFIGURATION
# ==================================

st.set_page_config(page_title="Stock Price Predictor", page_icon="📈", layout="wide")
st.title("📈 Stock Price Predictor")
st.markdown("Interactive Stock Price Prediction using Monte Carlo Simulations")
st.divider()

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Stock Parameters")
    ticker = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT):", value="AAPL").upper()
    lookback_years = st.slider("Historical Lookback Period (Years):", min_value=1, max_value=5, value=1, step=1)

    st.markdown("**Monte Carlo Simulation Parameters**")
    num_simulations = st.number_input("Number of Simulations:", min_value=100, max_value=10000, value=1000, step=100)
    forecast_days = st.number_input("Forecast Horizon (Days):", min_value=30, max_value=252, value=90, step=1)

    button_clicked = st.button("Run Simulation")

with col2:
    st.subheader("Simulation Results")

    if button_clicked:
        with st.spinner("Fetching data and running simulations..."):
            engine = StockPricePredictor(ticker)
            if not engine.fetch_price_history(lookback_years):
                st.error(f"Failed to fetch data for ticker '{ticker}'. Please check the ticker symbol and try again.")
            else:
                price_matrix = engine.monte_carlo_simulation(num_simulations, forecast_days)

                current_price = engine.price_history.iloc[-1]
                final_day_vector = price_matrix[-1, :]

                expected_mean = np.mean(final_day_vector)
                downside_5pct = np.percentile(final_day_vector, 5)
                upside_95pct = np.percentile(final_day_vector, 95)

                st.info(f"📊 **Calibrated Parameters from Past {lookback_years} Year(s):** \n* **Annualized Drift (μ):** {engine.mu:.2%}\n* **Annualized Volatility (σ):** {engine.sigma:.2%}\n* **Current Spot Price (S₀):** ₹{current_price:,.2f}")

                m1, m2, m3 = st.columns(3)
                m1.metric(label="Current Live Price", value=f"₹{current_price:,.2f}")
                m2.metric(label="Simulated Mean Value", value=f"₹{expected_mean:,.2f}", delta=f"{(expected_mean/current_price - 1):+.2%}")
                m3.metric(label="Value at Risk (5th Pct)", value=f"₹{downside_5pct:,.2f}", delta=f"{(downside_5pct/current_price - 1):.2%}", delta_color="inverse")
                
                st.info(f"**95% Confidence Interval for Forecasted Price after {forecast_days} Days:** ₹{downside_5pct:,.2f} - ₹{upside_95pct:,.2f}")
                st.markdown("----")

                st.write(f"Displaying top 100 simulated paths expanding out of today's live stock spot price over {forecast_days} trading days:")
                fig, ax = plt.subplots(figsize=(10, 4.5))
                ax.plot(price_matrix[:, :100], color='lightblue', alpha=0.5)
                ax.axhline(y=current_price, color='red', linestyle='--', label='Current Price')
                ax.axhline(y=expected_mean, color='green', linestyle='--', label='Expected Mean')
                ax.set_title(f"Monte Carlo Simulations for {ticker} Stock Price Forecast")
                ax.set_xlabel("Trading Days")
                ax.set_ylabel("Simulated Stock Price (₹)")
                ax.legend()
                ax.grid(True, alpha=0.3)

                st.pyplot(fig, use_container_width=True)

                var_rupee = current_price - downside_5pct
                st.warning(f"🛡️ **MSc Risk Management Insights:** Based on our calibrated matrix engine, there is a **5% risk probability** that market shocks could drop {ticker} below **₹{downside_5pct:,.2f}** within this time horizon, causing a localized loss asset stress of **₹{var_rupee:,.2f}** per unit share position.")
    else:
        st.info("Input a valid National Stock Exchange of India ticker symbol on the left sidebar profile and launch the execution pipeline.")