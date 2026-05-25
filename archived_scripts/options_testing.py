from options import *
from portfolio import portfolio
import yfinance as yf

def get_option_data(symbol, strike, expiration=None):
    """
    Fetches option premium and implied volatility for a given strike.
    
    Parameters:
        symbol (str): Stock ticker, e.g., "AAPL"
        strike (float): Strike price to filter
        expiration (str or None): YYYY-MM-DD; if None, use first available expiry
    
    Returns:
        dict: {"call": {"lastPrice": ..., "impliedVolatility": ...},
               "put": {"lastPrice": ..., "impliedVolatility": ...}}
    """
    ticker = yf.Ticker(symbol)
    
    # pick expiration date
    if expiration is None:
        expiration = ticker.options[0]  # first available
    
    chain = ticker.option_chain(expiration)
    calls = chain.calls
    puts = chain.puts
    
    # filter by strike
    call_data = calls[calls["strike"] == strike]
    put_data = puts[puts["strike"] == strike]
    
    result = {}
    if not call_data.empty:
        result["call"] = {
            "lastPrice": float(call_data["lastPrice"].iloc[0]),
            "impliedVolatility": float(call_data["impliedVolatility"].iloc[0])
        }
    else:
        result["call"] = None
    
    if not put_data.empty:
        result["put"] = {
            "lastPrice": float(put_data["lastPrice"].iloc[0]),
            "impliedVolatility": float(put_data["impliedVolatility"].iloc[0])
        }
    else:
        result["put"] = None
    
    return result

import pandas as pd

def test_options_accuracy(stock_list, purchase_date, strike_price, expiration=None):
    p = portfolio(stock_list)
    
    put_premium_var = []
    call_premium_var = []
    put_iv_var = []
    call_iv_var = []

    # Collect detailed per-stock data for Excel export
    put_details = []
    call_details = []

    for stock in p.stocks.values():
        # Initialize simulated options
        put = option(p, stock.ticker, "put", "buy", strike_price, purchase_date)
        call = option(p, stock.ticker, "call", "sell", strike_price, purchase_date)

        sim_put = float(put.premium)
        sim_call = float(call.premium)
        sim_put_iv = float(put.IV)
        sim_call_iv = float(call.IV)
        
        # Initialize real options
        real_data = get_option_data(stock.ticker, strike_price, expiration=expiration)
        real_put = real_data['put']
        real_call = real_data['call']

        # Skip if real data is missing
        if real_put is None or real_call is None:
            print(f"Skipping {stock.ticker}: real option data not available for strike {strike_price}")
            continue

        real_put_price = real_put["lastPrice"]
        real_call_price = real_call["lastPrice"]
        real_put_iv = real_put["impliedVolatility"]
        real_call_iv = real_call["impliedVolatility"]

        # Calculate percentage differences
        put_var = abs(sim_put - real_put_price) / real_put_price
        call_var = abs(sim_call - real_call_price) / real_call_price
        iv_put_var = abs(sim_put_iv - real_put_iv) / real_put_iv
        iv_call_var = abs(sim_call_iv - real_call_iv) / real_call_iv

        put_premium_var.append(put_var)
        call_premium_var.append(call_var)
        put_iv_var.append(iv_put_var)
        call_iv_var.append(iv_call_var)

        # Example: Apple
        ticker = yf.Ticker(stock.ticker)
        # Get the most recent market price
        current_price = ticker.info["regularMarketPrice"]

        # Append detailed rows for Excel
        put_details.append({
            "ticker": stock.ticker,
            "purchase_date": purchase_date,
            "current_price": current_price,
            "strike_price": strike_price,
            "sim_premium": sim_put,
            "real_premium": real_put_price,
            "realized_iv": put.RV,
            "sim_iv": sim_put_iv,
            "real_iv": real_put_iv,
            "variance": put_var
        })
        call_details.append({
            "ticker": stock.ticker,
            "purchase_date": purchase_date,
            "current_price": current_price,
            "strike_price": strike_price,
            "sim_premium": sim_call,
            "real_premium": real_call_price,
            "realized_iv": call.RV,
            "sim_iv": sim_call_iv,
            "real_iv": real_call_iv,
            "variance": call_var
        })

    # Compute average variances
    avg_put_premium_var = sum(put_premium_var) / len(put_premium_var) if put_premium_var else None
    avg_call_premium_var = sum(call_premium_var) / len(call_premium_var) if call_premium_var else None
    avg_put_iv_var = sum(put_iv_var) / len(put_iv_var) if put_iv_var else None
    avg_call_iv_var = sum(call_iv_var) / len(call_iv_var) if call_iv_var else None

    print("Average percentage differences (simulated vs real):")
    print(f"Put Premium: {avg_put_premium_var:.2%}" if avg_put_premium_var is not None else "Put Premium: N/A")
    print(f"Call Premium: {avg_call_premium_var:.2%}" if avg_call_premium_var is not None else "Call Premium: N/A")
    print(f"Put IV: {avg_put_iv_var:.2%}" if avg_put_iv_var is not None else "Put IV: N/A")
    print(f"Call IV: {avg_call_iv_var:.2%}" if avg_call_iv_var is not None else "Call IV: N/A")

    # Export to Excel
    put_df = pd.DataFrame(put_details)
    call_df = pd.DataFrame(call_details)
    put_df.to_excel("options_puts_comparison.xlsx", index=False)
    call_df.to_excel("options_calls_comparison.xlsx", index=False)

    print("Excel files created: 'options_puts_comparison.xlsx', 'options_calls_comparison.xlsx'")

    # Optionally, return detailed results
    return {
        "put_premium_var": put_premium_var,
        "call_premium_var": call_premium_var,
        "put_iv_var": put_iv_var,
        "call_iv_var": call_iv_var,
        "put_details": put_df,
        "call_details": call_df
    }

###############################################################
symbols = [
    "AAL", "AAPL", "ABBV", "ADBE", "AMD", "AMZN", "ATVI", "BA", "BABA",
    "BAC", "BIDU", "BILI", "C", "CARR", "CCL", "COIN", "COST", "CPRX",
    "CSCO", "CVX", "DAL", "DIS", "DOCU", "ET", "ETSY", "F", "FDX", "FUBO",
    "GE", "GM", "GOOGL", "GS", "HCA", "HOOD", "INTC", "JNJ", "JPM", "KO",
    "LCID", "LMT", "META", "MGM", "MRNA", "MRO", "MSFT", "NFLX", "NIO",
    "NKE", "NOK", "NVDA", "PEP", "PFE", "PINS", "PLTR", "PYPL", "RBLX",
    "RIOT", "RIVN", "RKT", "ROKU", "SBUX", "SHOP", "SIRI", "SNAP", "SOFI",
    "SONY", "SPY", "SPYG", "SQ", "T", "TGT", "TLRY", "TSLA", "TSM", "TWTR",
    "UAL", "UBER", "UNH", "V", "VIAC", "VWO", "VZ", "WBA", "WFC", "WMT",
    "XOM", "ZM"
]
test = ["AAPL"]
purchase_date = "2025-12-15"
strike_price = 250
test_options_accuracy(symbols, purchase_date, strike_price, expiration=None)
        
