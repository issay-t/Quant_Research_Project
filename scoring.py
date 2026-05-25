# PURPOSE: This module holds helper functions to calculate the score of a stock (fundamental, market, etc.)
#############################################################################################################
import math
import numpy as np

#############################################################################################################
# SCORING FUNDAMENTALS AND MARKET ADJUSTMENT FACTORS HELPERS
#############################################################################################################
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

def score_momentum(date, master_df, window=15, k=15, midpoint=0.0, min_score=0.05, max_score=0.95):
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

def score_volatility(date, master_df, market_price_df, window=15, k=10, midpoint=1.0, min_score=0.05, max_score=0.95): 
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
    
def score_rel_performance(date, master_df, market_price_df, window=15, k=8, midpoint=0.0, min_score=0.05, max_score=0.95):
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

#############################################################################################################
# CALCULATING SCORES:
# - fundamental score
# - market adjustment score
# - total adjusted score
#############################################################################################################

# Calculate fundamentals and market adjusted score
def final_adjusted_score(stock):
    market_sensitivity = stock.weighting["market_sensitivity"]
    market_adj_factor = stock.current_scoring["market_adj_factor"]
    base_score = stock.current_scoring["base_score"]

    total_adj_score = base_score * (1 + market_sensitivity * np.tanh((market_adj_factor - 0.5) * 3))
    stock.current_scoring["total_adj_score"] = min(1.0, total_adj_score) # cap at 1

# market_adjustment function to adjust score based on market conditions (not implemented here).
# Note: 0.5 = neutral market, >0.5 = favorable market, <0.5 = unfavorable market.
def market_adjustment_factor(stock, market):
    date = stock.current_date
    master_df = stock.master_df
    momentum = score_momentum(date, master_df)
    volatility = score_volatility(date, master_df, market.stock_price_df)
    rel_performance = score_rel_performance(date, master_df, market.stock_price_df)

    # Save scores to current stock
    stock.current_scoring["momentum"] = momentum
    stock.current_scoring["volatility"] = volatility
    stock.current_scoring["rel_performance"] = rel_performance

    # Calculate final market adjustment
    market_adj_factor = (
        stock.weighting["momentum"] * momentum +
        stock.weighting["volatility"] * volatility +
        stock.weighting["rel_performance"] * min(1, rel_performance)
    )
    stock.current_scoring["market_adj_factor"] = market_adj_factor

# gets the scores for fundamentals (ex. management quality, longevity, etc.)
def fundamentals_score(stock):
    date = stock.current_date
    master_df = stock.master_df
    # Extract quantitaitve scores for ratios:
    roe_score = score_roe(master_df, date)
    #print(f"ROE Score: {roe_score}")
    de_score = score_de(master_df, date)
    #print(f"D/E Score: {de_score}")
    pe_score = score_pe(master_df, date)
    #print(f"P/E Score: {pe_score}")

    # Extract qualitative factors:
    management_quality = master_df.loc[date,'management_quality']
    #print(f"Management Quality score: {management_quality}")
    competitive_edge = master_df.loc[date, 'competitive_edge']
    #print(f"Competitive Edge score: {competitive_edge}")
    longevity = master_df.loc[date, 'longevity']
    #print(f"Longevity score: {longevity}")
    
    # Save all computed scores into the stock's current scoring
    stock.current_scoring["roe"] = roe_score
    stock.current_scoring["de"] = de_score
    stock.current_scoring["pe"] = pe_score
    stock.current_scoring["management_quality"] = management_quality
    stock.current_scoring["competitive_edge"] = competitive_edge
    stock.current_scoring["longevity"] = longevity

    # Compute base score based off weighting
    base_score = (
        stock.weighting["roe"] * roe_score +                   # Strong profitability indicator
        stock.weighting["de"] * de_score +                     # Financial leverage and risk
        stock.weighting["pe"] * pe_score +                     # Valuation multiple (market sentiment)
        stock.weighting["management_quality"] * management_quality +   # Leadership quality & execution
        stock.weighting["competitive_edge"] * competitive_edge +       # Moat and differentiation
        stock.weighting["longevity"] * longevity               # Stability and history
    )
    stock.current_scoring["base_score"] = base_score
        
# calculate_totalScore calculates the score given to the company based on qualitative and quantitative factors.
# note: date will always be greater or equal to the earliest date in ratios_df
def calculate_totalScore(stock, market):
    # Get fundamentals score
    fundamentals_score(stock)

    # Fetch market_adj score (Qualitative and Quantitative)
    market_adjustment_factor(stock, market)

    final_adjusted_score(stock)
    # print(f"Final Adjusted Score: {stock.current_scoring['total_adj_score']:.3f}")

def print_score_summary(stock):
    # Print base score breakdown:
    print("------------------------------------------------------------")
    print(f"Score Calculation:")
    print("------------------------------------------------------------")
    print(f"ROE Score: {stock.current_scoring['roe']:.3f}")
    print(f"Debt-to-Equity Score: {stock.current_scoring['de']:.3f}")
    print(f"P/E Ratio Score: {stock.current_scoring['pe']:.3f}")
    print(f"Management Quality Score: {stock.current_scoring['management_quality']:.3f}")
    print(f"Competitive Edge Score: {stock.current_scoring['competitive_edge']:.3f}")
    print(f"Longevity Score: {stock.current_scoring['longevity']:.3f}")
    print(f"{stock.ticker} Weighted Base Score: {stock.current_scoring['base_score']:.3f}")
    print(" ")

    # Print market adjustment breakdown:
    print(f"Momentum Score: {stock.current_scoring['momentum']:.3f}")
    print(f"Volatility Score: {stock.current_scoring['volatility']:.3f}")
    print(f"Relative Performance Score: {stock.current_scoring['rel_performance']:.3f}")
    print(f"Market Adjustment Factor: {stock.current_scoring['market_adj_factor']:.3f}")
    print(" ")  
    
    # Print final adjusted score
    print(f"Final Adjusted Score: {stock.current_scoring['total_adj_score']:.3f}")

