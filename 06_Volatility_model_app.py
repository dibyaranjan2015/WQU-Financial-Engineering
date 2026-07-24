import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

class AssetAnalyzer:
    """
    An object-oriented class to fetch asset data and compute statistical 
    properties of its returns.
    """
    def __init__(self, ticker: str, start_date: str, end_date: str):
        self.ticker = ticker
        self.start_date = start_date
        self.end_date = end_date
        self.data = pd.DataFrame()
        self.returns = pd.Series(dtype=float)

    def fetch_data(self):
        """Fetches historical data and calculates daily log returns."""
        df = yf.download(self.ticker, start=self.start_date, end=self.end_date, progress=False)
        if df.empty:
            raise ValueError(f"No data found for ticker {self.ticker}")
        
        self.data = df
        # Log returns are preferred in quantitative finance for time-additivity
        self.returns = np.log(self.data['Close'] / self.data['Close'].shift(1)).dropna().squeeze()
        
    def get_volatility(self, annualized: bool = True) -> float:
        """Calculates standard deviation (volatility)."""
        daily_vol = self.returns.std()
        if annualized:
            # Assuming 252 trading days in a year
            return daily_vol * np.sqrt(252)
        return daily_vol

    def get_skewness(self) -> float:
        """Calculates the skewness of the returns."""
        return stats.skew(self.returns)

    def get_kurtosis(self) -> float:
        """Calculates the excess kurtosis of the returns. A normal distribution has 0."""
        # Fisher=True returns Excess Kurtosis (Kurtosis - 3)
        return stats.kurtosis(self.returns, fisher=True)

    def test_normality(self) -> dict:
        """
        Uses the Jarque-Bera test to check for normality. 
        It specifically tests if skewness and kurtosis match a normal distribution.
        """
        jb_stat, p_value = stats.jarque_bera(self.returns)
        is_normal = p_value > 0.05
        return {
            "Statistic": jb_stat,
            "p-value": p_value,
            "Is_Normal": is_normal
        }

    def plot_distribution(self):
        """Plots the return distribution against a theoretical normal distribution."""
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Plot empirical distribution
        sns.histplot(self.returns, bins=50, kde=True, stat="density", 
                     color="steelblue", label="Empirical Returns", ax=ax)
        
        # Plot theoretical normal distribution for comparison
        mu, std = stats.norm.fit(self.returns)
        xmin, xmax = ax.get_xlim()
        x = np.linspace(xmin, xmax, 100)
        p = stats.norm.pdf(x, mu, std)
        ax.plot(x, p, 'k', linewidth=2, label=f"Normal Fit ($\mu={mu:.4f}$, $\sigma={std:.4f}$)")
        
        ax.set_title(f"Return Distribution for {self.ticker.upper()}")
        ax.set_xlabel("Daily Log Returns")
        ax.set_ylabel("Density")
        ax.legend()
        
        return fig


# ==========================================
# Streamlit Interface
# ==========================================

st.set_page_config(page_title="Asset Distribution Analyzer", layout="wide")

st.title("Financial Asset Distribution Analyzer")
st.write("Analyze the statistical properties of stock returns to identify non-Gaussian behavior, tail risks, and volatility.")

# Sidebar Inputs
st.sidebar.header("Parameters")
ticker_input = st.sidebar.text_input("Ticker Symbol", value="AAPL")
start_input = st.sidebar.date_input("Start Date", value=datetime.today() - timedelta(days=365*3))
end_input = st.sidebar.date_input("End Date", value=datetime.today())

if st.sidebar.button("Run Analysis"):
    with st.spinner(f"Fetching data and analyzing {ticker_input}..."):
        try:
            # Instantiate the object
            analyzer = AssetAnalyzer(
                ticker=ticker_input, 
                start_date=start_input.strftime("%Y-%m-%d"), 
                end_date=end_input.strftime("%Y-%m-%d")
            )
            
            # Execute methods
            analyzer.fetch_data()
            vol = analyzer.get_volatility()
            skew = analyzer.get_skewness()
            kurt = analyzer.get_kurtosis()
            normality = analyzer.test_normality()
            
            # Layout for metrics
            st.subheader(f"Statistical Moments for {ticker_input.upper()}")
            col1, col2, col3 = st.columns(3)
            
            col1.metric("Annualized Volatility", f"{vol * 100:.2f}%")
            col2.metric("Skewness", f"{skew:.4f}", 
                        help="Negative skew indicates a left tail (larger frequent losses).")
            col3.metric("Excess Kurtosis", f"{kurt:.4f}", 
                        help=">0 indicates Leptokurtic (fat tails). <0 indicates Platykurtic (thin tails).")

            # Layout for Normality Test
            st.divider()
            st.subheader("Normality Test (Jarque-Bera)")
            
            if normality["Is_Normal"]:
                st.success(f"**Result:** The returns appear to be Normally Distributed (p-value: {normality['p-value']:.4f}).")
            else:
                st.error(f"**Result:** The returns are NOT Normally Distributed (p-value: {normality['p-value']:.4f}).")
                
            st.write(
                "The Jarque-Bera test determines whether sample data has the skewness and kurtosis "
                "matching a normal distribution. In financial markets, a p-value < 0.05 typically "
                "rejects the null hypothesis, confirming the presence of heavy tails or skew."
            )

            # Plotting
            st.divider()
            st.subheader("Distribution Visualization")
            fig = analyzer.plot_distribution()
            st.pyplot(fig)
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    st.info("Enter a ticker symbol and dates in the sidebar, then click 'Run Analysis'.")