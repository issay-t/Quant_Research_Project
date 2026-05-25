# PURPOSE: Provide functions to load quantitative data (roe, d/e, p/e) from API
# - using financial modeling prep API 
# - 250 calls max per day free
################################################################################

# Import Libraries:
import requests
import pandas as pd
import os
import json
import re
import math
import numpy as np
import yfinance as yf
from scipy.stats import norm
from google import genai
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Load Gemini API client
client = genai.Client()

############################################################################################
# FETCHING DATA FROM APIs

# get_quant_data fetches quantitative data from financial modeling prep API
# and turns it into a pandas dataframe.
def get_quant_data(symbol, base_url, params, use_cache=True):
    # Check cache first for data
    content = base_url.split("/")[-1] # e.g. "ratios"
    filename = os.path.join("cached_data", f"{symbol}_data_fmp_{content}.json")
    
    data = None
    # Try load from cache
    if use_cache and os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                print(f"Loading {symbol} FMP data from cache...")
                data = json.load(f)
        except Exception as e:
            print("Failed to read cache file, will fetch from API:", e)

    if (data == None):
        response = requests.get(base_url, params=params)
        data = response.json()
        # Save to cache
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("Warning: failed to save cache file:", e)
    df = pd.DataFrame(data)
    if df.empty:
        raise ValueError(f"Quantitative data is empty for {symbol}.")
    return df

# Helper function to parse Gemini response and create a json file.
def gemini_to_json(response_text):
    # Regex pattern to extract JSON code block
    match = re.search(r"```json(.*?)```", response_text, re.DOTALL)

    if not match:
        print("No JSON code block found.")
        return None

    json_str = match.group(1).strip()

    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Error parsing JSON:", e)
        return None

# get_qual_data uses google gemini api to evaluate and score qualitative factors. Produces a 
# json file that contains the scores for each qualitative factor. The function then saves the
# data to cache and returns a pandas dataframe.
#   symbol: ticker symbol of the company
#   dates: list of dates to evaluate qualitative data for
def get_qual_data(symbol, dates, use_cache=True):
    filename = os.path.join("cached_data", f"{symbol}_data_gemini.json")
    
    data = None
    # Try load from cache
    if use_cache and os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                print(f"Loading {symbol} Gemini data from cache...")
                data = json.load(f)
        except Exception as e:
            print("Failed to read cache file, will fetch from API:", e)
    
    if (data == None):
        prompt = f"""
            You are a financial analyst AI.

            Definitions for scoring on a scale of 0 to 1:

            1. Management Quality:
            - Leadership based on passion, integrity, intelligence.
            - Evaluate past decisions, strategic vision (long-term focus), and communication transparency.
            - Consider CEO/executive track record: background, past performance, tenure.
            - Assess capital allocation: investments, buybacks, dividends, debt management.
            - Compare financial performance to industry: revenue growth, ROE, ROIC, free cash flow.
            - Evaluate consistency and clarity of strategy via annual reports.
            - Analyze governance and ethics: employee turnover, insider trading.
            - Consider employee & customer feedback, reputation, media coverage.

            2. Competitive Advantage:
            - Unique factors protecting the company long-term (brand, cost advantages, etc.).
            - Assess market positioning and barriers to entry (patents, proprietary technology, network effects).
            - Evaluate pricing power and customer loyalty.
            - Consider operational efficiency relative to competitors.
            - Analyze adaptability to market changes and innovation track record.
            - Review supply chain resilience and partnerships.
            - Consider regulatory advantages or challenges.
            - Assess diversification of product lines or revenue streams.

            3. Company Longevity and Stability:
            - Ability to maintain profitability and stability over 20-30 years.
            - Review historical financial resilience during economic downturns.
            - Analyze debt levels and capital structure stability.
            - Assess consistency of dividend payments and cash flow generation.
            - Consider management succession planning and institutional knowledge.
            - Evaluate exposure to cyclical risks and market volatility.
            - Review reputation for compliance and risk management.
            - Consider long-term strategic investments and R&D focus.

            ---

            Task:

            Given a ticker symbol \"{symbol}\" and an array of dates {dates}, for each date:

            - Provide scores (0-1) for the three metrics above.
            - For backtesting purposes, assume you only have access to public information up to that date. You do not know future events.
            - Return a JSON object with date keys and metric scores as values.

            Example output format: (strictly follow this format, no extra text)

            {{
            "2025-09-31": {{
                "management_quality": 0.8,
                "competitive_edge": 0.73,
                "longevity": 0.92
            }},
            "2025-10-31": {{
                ...
            }}
            }}
        """
        #reasoning = "Separate from the json output, can you separately provide your reasoning for each score for each date?"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt 
        )
        #print(response.text)
        data = gemini_to_json(response.text)
        # Save to cache
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print("Warning: failed to save cache file:", e)

    df = pd.DataFrame(data)
    if df.empty:
        raise ValueError(f"Qualitative data is empty for {symbol}.")
    df = df.copy()
    df.columns = pd.to_datetime(df.columns, format="%Y-%m-%d")  # convert columns (dates) to datetime
    df = df.T                                  # transpose to have dates as rows
    df.index.name = 'date'
    df = df.sort_index()

    # Verify column names are correct:
    expected_cols = {"management_quality", "competitive_edge", "longevity"}
    if set(df.columns) != expected_cols:
        raise ValueError(f"Expected columns are not correct for {symbol} qualitative data.")
    print(df)
    return df

# get_finRatios fetches financial ratios from financial modeling prep API (roe, de, pe)
# and turns it into a pandas dataframe.
# due to api limitations, can only retrieve up to 5 years of data in the past.
def get_finRatios(symbol):
    base_url = "https://financialmodelingprep.com/stable/ratios"
    params = {
            "symbol": symbol,
            "limit": 5,
            "period": "FY",
            "apikey": FMP_API_KEY,
    }
    # Clean data and convert to universal format
    df = get_quant_data(symbol, base_url, params)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d") # Convert string dates to datetime
    df = df.drop(columns=['symbol'])         # drop symbol since you have it in the class
    df = df.set_index('date')                # set date as index
    df = df.sort_index() # sort in chronological order
    df = df[["netIncomePerShare","shareholdersEquityPerShare","debtToEquityRatio","priceToEarningsRatio"]] # filter for only needed data
    df.index = df.index + pd.Timedelta(days=60) # to simulate public information being available 60 days after FY ended
    print(df)
    return df

# get_closing_prices fetches historical daily closing prices from yfinance API
# and turns it into a pandas dataframe.
def get_closing_prices(symbol, start_date, end_date, use_cache=True):
    filename = os.path.join("cached_data", f"{symbol}_data_yf.pkl")
    raw_data = None
    if use_cache and os.path.exists(filename):
        print(f"Loading {symbol} historical yf prices from cache...")
        raw_data = pd.read_pickle(filename)
    else:
        try:
            print(f"Fetching {symbol} historical yf prices from yfinance API...")
            raw_data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=True)
            raw_data.to_pickle(filename)
        except Exception as e:
            print("Failed to fetch data from yfinance:", e)
    
    if raw_data.empty:
        raise ValueError(f"No historical price data available for {symbol}.")
    
    # Clean data and change to universal format
    df = raw_data.copy()
    df.index = pd.to_datetime(df.index, format="%Y-%m-%d") # convert into date objects
    df = df.sort_index()
    df = df.droplevel(1, axis=1)  # remove second level which is ticker symbol
    df.index.name = "date"
    df.columns.name = None
    df = df[["Close"]] # Filter for only close prices
    print(df)
    return df

# get_dividends fetches dividends from yfinance API
# and turns it into a pandas dataframe.
def get_dividends(symbol, start_date, end_date, use_cache=True):
    filename = os.path.join("cached_data", f"{symbol}_dividends_yf.pkl")
    raw_data = None
    if use_cache and os.path.exists(filename):
        print(f"Loading {symbol} yf dividends from cache...")
        raw_data = pd.read_pickle(filename)
    else:
        try:
            print(f"Fetching {symbol} dividends from yfinance API...")
            ticker = yf.Ticker(symbol)
            divs = ticker.dividends

            if divs.empty:
                print(f"No dividend data found for {symbol}.")
                return pd.DataFrame(columns=["dividend"])
            
            divs.index = divs.index.tz_localize(None)
            raw_data = divs[(pd.to_datetime(divs.index) >= start_date) & (pd.to_datetime(divs.index) <= end_date)]
            raw_data.to_pickle(filename)
        except Exception as e:
            print("Failed to fetch data from yfinance:", e)
    
    # Clean data and change to universal format
    df = raw_data.copy()
    df.index = pd.to_datetime(df.index, format="%Y-%m-%d") # convert into date objects
    df = df.sort_index()
    df.index.name = "date"
    df.columns = ["dividend"]
    #print(df)
    return df

############################################################################################
# SCORING FUNDAMENTALS AND MARKET ADJUSTMENT FACTORS

def score_roe(master_df, date, good_roe=0.20, k=25): 
    """
    Scores ROE:
    - Linear up to `good_roe` (e.g. 20%) → max score of 1.0
    - Above `good_roe`, apply diminishing bonus using logistic curve
    - Final score capped at `bonus_cap` (e.g. 1.2)
    """
    ratios_row = master_df.loc[date]
    roe = ratios_row['netIncomePerShare']/ratios_row['shareholdersEquityPerShare']

    if roe <= 0:
        return 0.0  # Negative ROE = worst
    
    if roe <= good_roe:
        return roe / good_roe  # Linear up to 1.0
    
    # Bonus range: logistic from ROE just above good_roe
    x = roe - good_roe
    logistic = 1 / (1 + math.exp(-k * x))
    
    # Map logistic output (0.5 → 1.0) to (1.0 → 1.0)
    # so it just flattens out smoothly near 1
    score = 1 - (1 - logistic) * 0.2  # optional soft flattening
    return min(score, 1.0)

def score_de(master_df,
             date,
             good_de=0.6,
             max_linear=2.0,
             alpha=2.0,
             min_score=0.05):
    """
    Score a debt-to-equity ratio:
    - Negative D/E → score = min_score (bad: negative equity)
    - de ≤ good_de → score = 1.0
    - de ∈ (good_de, max_linear] → linear decline
    - de > max_linear → power decay, floored at min_score
    """
    ratios_row = master_df.loc[date]
    de_ratio = ratios_row['debtToEquityRatio']
    if de_ratio < 0:
        return min_score  # Negative equity = worst case
    
    if de_ratio == 0:
        return 1.0  # No debt = best case
    
    if de_ratio <= good_de:
        return 1.0
    
    if de_ratio <= max_linear:
        linear_score = (max_linear - de_ratio) / (max_linear - good_de)
        return max(linear_score, min_score)
    
    excess = de_ratio / max_linear
    decay_score = 1.0 / (excess ** alpha)
    return max(decay_score, min_score)

def score_pe(master_df, date, min_score=0.01, s=0.15, c=40):
    """
    Logistic P/E scoring function — tuned to your preference:
      - Flat near 1.0 for fair P/E (≈15–20)
      - Drops sharply past ~37
      - Floor at min_score (default 0.01)

    Formula:
        score = min_score + (1 - min_score) / (1 + e^(s * (pe_ratio - c)))
    """
    ratios_row = master_df.loc[date]
    pe_ratio = ratios_row['priceToEarningsRatio']
    if pe_ratio <= 0:
        return 0.0  # Invalid or negative earnings
    #print(f"pe_ratio: {pe_ratio}")

    score = min_score + (1 - min_score) / (1 + math.exp(s * (pe_ratio - c)))
    return score

def score_momentum(date, master_df, window=60, k=15, midpoint=0.0, min_score=0.05, max_score=0.95):
    """
    Calculates smoothed price momentum using a Simple Moving Average (SMA).

    Parameters:
    - prices: pd.Series of daily closing prices (indexed by date, ascending order)
    - window: number of trading days for SMA (default 60 ≈ 3 months)

    Returns:
    - momentum: float (ratio of (current price - SMA) / SMA)
    """
    # Filter prices for dates up to the given date
    stock_prices = master_df[master_df.index <= date]['Close']
    if len(stock_prices) < window:
        return 0.5  # Not enough data
    #print(f"Calculating momentum for date {date} with window {window}")
    #print(stock_prices)
    sma = stock_prices[-window:].mean()
    #print(f"SMA over last {window} days: {sma}")
    momentum = (stock_prices.iloc[-1] - sma) / sma
    #print(f"Momentum: {momentum}")
    """
    Convert momentum (based on SMA) into a 0–1 score using a logistic curve.
    
    Parameters:
    - momentum: float, e.g. 0.08 = +8% above SMA
    - k: steepness (higher = more exponential punishment/reward)
    - midpoint: the momentum value where score ≈ 0.5 (default 0)
    - min_score, max_score: bounds for output
    
    Returns:
    - float between min_score and max_score
    """
    # Logistic scaling from negative to positive momentum
    raw = 1 / (1 + math.exp(-k * (momentum - midpoint)))
    
    # Rescale to [min_score, max_score]
    scaled = min_score + (max_score - min_score) * raw
    #print("Scaled momentum score:", scaled)
    
    return scaled

def score_volatility(date, master_df, market_price_df, window=60, k=10, midpoint=1.0, min_score=0.05, max_score=0.95): 
    """
    Computes the ratio of the stock's volatility to the benchmark's volatility.

    Parameters:
    - stock_prices: pd.Series of stock daily close prices
    - benchmark_prices: pd.Series of benchmark daily close prices
    - window: number of trading days (default 60 ≈ 3 months)

    Returns:
    - ratio: float (vol_stock / vol_benchmark)
    """
    # Filter prices for dates up to the given date
    stock_prices = master_df[master_df.index <= date]["Close"]
    market_prices = market_price_df[market_price_df.index <= date]["Close"]
    if len(stock_prices) < window or len(market_prices) < window:
        return 0.5  # Not enough data
    
    stock_returns = stock_prices.pct_change().dropna()
    #print(f"Stock returns:\n{stock_returns}")
    market_returns = market_prices.pct_change().dropna()
    #print(f"Market returns:\n{market_returns}")

    vol_stock = stock_returns[-window:].std() * np.sqrt(252)
    #print(f"Stock volatility (annualized): {vol_stock}")
    vol_market = market_returns[-window:].std() * np.sqrt(252)
    #print(f"Market volatility (annualized): {vol_market}")

    vol_ratio = vol_stock / vol_market if vol_market != 0 else 1.0
    #print(f"Volatility ratio (stock/market): {vol_ratio}")

    """
    Converts relative volatility ratio into a 0–1 score.
    Lower ratios (less volatile than benchmark) get higher scores.
    """

    # Invert the ratio so higher = better (more stable)
    inv_ratio = vol_market / vol_stock if vol_stock != 0 else 1.0

    # Inverse logistic so high ratios are penalized
    raw = 1 / (1 + math.exp(-k * (inv_ratio - midpoint)))
    scaled = min_score + (max_score - min_score) * raw
    #print(f"Scaled volatility score: {scaled}")
    return scaled
    
def score_rel_performance(date, master_df, market_price_df, window=60, k=8, midpoint=0.0, min_score=0.05, max_score=0.95):
    """
    Calculates relative performance between stock and benchmark over a time window.

    Parameters:
    - stock_prices: pd.Series of stock close prices
    - benchmark_prices: pd.Series of benchmark close prices
    - window: number of trading days (default 60 ≈ 3 months)

    Returns:
    - rel_perf: relative performance ratio (positive means outperformance)
    """ 
    # Filter prices for dates up to the given date
    stock_prices = master_df[master_df.index <= date]["Close"]
    market_prices = market_price_df[market_price_df.index <= date]["Close"]
    if len(stock_prices) < window or len(market_prices) < window:
        return 0.5  # Not enough data

    stock_return = (stock_prices.iloc[-1] / stock_prices.iloc[-window]) - 1
    #print(f"Stock return over last {window} days: {stock_return}")
    market_return = (market_prices.iloc[-1] / market_prices.iloc[-window]) - 1
    #print(f"Market return over last {window} days: {market_return}")

    # active return = difference (positive => outperformance)
    rel_perf = stock_return - market_return

    """
    Converts relative performance ratio into a 0–1 score.
    Outperformance gives higher scores; underperformance gives lower ones.
    """
    # logistic scaling
    raw = 1 / (1 + math.exp(-k * (rel_perf - midpoint)))
    scaled = min_score + (max_score - min_score) * raw
    return scaled

############################################################################################
# OPTIONS TRADING FUNCTIONS

# Example function to get historical volatility from your stock (returns in decimal, e.g., 0.25 = 25%)
# date: pandas date time object
def get_realized_vol(date, stock_price_df, window=60):
    realized_vol = 0

    # Filter prices for dates up to the given date
    stock_prices = stock_price_df[stock_price_df.index <= date]["Close"]
    if len(stock_prices) < window:
        print(f"Historical volatility could not be calculated, resorting to 0.17.")
        return 0.17  # Return average for the market based on the VIX
    
    stock_returns = stock_prices.pct_change().dropna()

    realized_vol = stock_returns[-window:].std() * np.sqrt(252)
    return realized_vol 

# Function to estiamte implied volatility for an option
def estimate_iv_proxy(
    purchase_date,
    expiration_date,
    stock_price_df,
    strike_price,
    option_type,
    vrp_base=0.06,
    vrp_tenor=0.04,
    vrp_vol=0.2,
    sigma_ref=0.20,
    kappa=0.18,
    max_skew_pts=0.12,
    dividend_yield=0.0):
    """
    Estimate implied volatility for a given stock and option parameters.

    Args:
        purchase_date (datetime): date of option purchase
        expiration_date (datetime): option expiration date
        stock_price_df (DataFrame): historical stock prices with DatetimeIndex
        strike_price (float): option strike
        option_type (str): "call" or "put"
        vrp_base (float): baseline volatility risk premium
        vrp_tenor (float): time-to-expiry dependent VRP
        vrp_vol (float): VRP sensitivity to realized volatility deviation
        sigma_ref (float): reference volatility
        kappa (float): skew coefficient
        max_skew_pts (float): maximum skew adjustment
        dividend_yield (float): optional continuous dividend yield
    Returns:
        float: estimated implied volatility (annualized)
    """
    # --- Compute time to expiration in trading days ---
    T_days = (expiration_date - purchase_date).days

    # --- Get current stock price on purchase date ---
    stock_price = stock_price_df[stock_price_df.index <= purchase_date].iloc[-1]["Close"]
    #print(f"Working with stock_price {stock_price}")

    # --- Compute realized (historical) volatility up to purchase date ---
    realized_vol = get_realized_vol(purchase_date, stock_price_df)

    # --- Convert time to expiry from days to years ---
    T = T_days / 252.0  # assuming 252 trading days per year
    if T <= 0:
        return realized_vol

    # --- Compute moneyness (distance of strike from current price) ---
    d = abs(1.0 - (strike_price / stock_price))

    # --- Volatility Risk Premium (VRP) adjustment ---
    # Cap vrp_tenor contribution to avoid large short-term blow-ups
    tenor_contrib = min(vrp_tenor / math.sqrt(T), 0.08)
    vrp_ratio = 1.0 + vrp_base + tenor_contrib + vrp_vol * (realized_vol - sigma_ref)

    # Reduce VRP for OTM puts (strike < spot)
    if option_type.lower() == "put" and strike_price < stock_price:
        vrp_ratio *= 1 - 0.99 * d  # scale down based on distance

    # ATM-level implied vol
    sigma_atm = realized_vol * vrp_ratio

    # --- Skew adjustment ---
    gamma = 1.0 if option_type.lower() == "put" else -0.15
    skew_adj = kappa * d * gamma
    # Optional: cap skew
    skew_adj = max(-max_skew_pts, min(skew_adj, max_skew_pts))

    # --- Combine ATM vol and skew ---
    sigma_iv = sigma_atm + skew_adj

    # --- Floor to prevent negative or near-zero vol ---
    sigma_iv = max(0.001, sigma_iv)

    # --- Debug print ---
    #print(sigma_iv)

    return sigma_iv

# Black-Scholes European option pricing
def black_scholes_price(S, K, t, r, sigma, option_type="call", q=0.0, min_premium=0.05):
    """
    Compute the Black-Scholes theoretical option price with continuous dividend yield q.
    """
    if t <= 0 or sigma <= 0:
        # intrinsic value only
        if option_type.lower() == "call":
            return max(0.0, S - K)
        else:
            return max(0.0, K - S)

    d1 = (math.log(S / K) + (r - q + 0.5 * sigma ** 2) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)

    if option_type.lower() == "call":
        price = S * math.exp(-q * t) * norm.cdf(d1) - K * math.exp(-r * t) * norm.cdf(d2)
    else:
        price = K * math.exp(-r * t) * norm.cdf(-d2) - S * math.exp(-q * t) * norm.cdf(-d1)

    return max(price, min_premium)

# Calculates the rf rate at the given date
# irx_df: stock_price_df of the ^IRX
# date: pd date time object
def get_risk_free_rate(irx_df, date):
    """
    Returns the risk-free rate (annualized) at or before the given date.
    Uses the 13-week Treasury Bill (^IRX) from Yahoo Finance.
    
    Parameters:
        date (str or datetime): Date string (e.g. '2025-10-31') or datetime.
        
    Returns:
        float: risk-free rate as a decimal (e.g., 0.0512 = 5.12%)
    """
    try:
        irx_df = irx_df[irx_df.index <= date] # filter for all dates smaller or equal to date

        if len(irx_df) == 0:
            # fallback if no data before date
            print(f"Warning: could not fetch rf rate for this date, defaulting to 0.03")
            return 0.03
        
        last_rate = irx_df["Close"].iloc[-1] / 100.0  # convert from percent to decimal
        return last_rate
    
    except Exception as e:
        print(f"Warning: could not fetch ^IRX data ({e}), defaulting to 0.03")
        return 0.03  # fallback 5%
    
def get_dividend_yield(date, stock_price_df, div_df):
    """
    Estimate the annual dividend yield (as decimal) as of a given date.
    Uses trailing 12 months of dividend payments relative to stock price.
    """
    div_df = div_df[div_df.index <= date] # filter for all dates smaller or equal to date
    past_year = date - pd.DateOffset(years=1)
    recent_divs = div_df[(div_df.index >= past_year) & (div_df.index <= date)]
    if (recent_divs.empty):
        return 0

    # Total dividends paid in past year
    annual_div = recent_divs.sum()

    # Stock price at or before date
    stock_prices = stock_price_df[stock_price_df.index <= date]
    price = stock_prices["Close"].iloc[-1]
    return annual_div / price

############################################################################################


