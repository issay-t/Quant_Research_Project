# PURPOSE: This module holds all functions used to fetch and organize data
################################################################################
import requests
import pandas as pd
import os
import json
import re
import yfinance as yf
from google import genai
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()
FMP_API_KEY = os.getenv("FMP_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Load Gemini API client
client = genai.Client()
################################################################################

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
    # print(df)
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
    # print(df)
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
    # print(df)
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