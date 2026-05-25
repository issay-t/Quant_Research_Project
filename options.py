# PURPOSE: This module assists in creating an option
import calendar
import pandas as pd
import math
import numpy as np
from scipy.stats import norm

# Class to create an option (simulated and theoretical, not actually pulled from historical options data)
# stock is a class stock mentioned in portfolio_sim
    # contract_length options:
    # - "1D" : next business day (cannot do same day due to lack of intraday data)
    # - "1W" : current or next Friday (skip 3rd Fridays)
    # - "1M" : 3rd Friday of current or next month
    # - "3M" : 3rd Friday three months ahead
class option:
    def __init__(self, portfolio, symbol, type, side, strike_price, date_of_purchase, shares_covered=100, contract_length="1M"):
        self.portfolio = portfolio
        self.stock = self.portfolio.stocks[symbol]
        self.type = type # call or put
        self.side = side # buy or sell
        self.strike_price = strike_price
        self.date_of_purchase = pd.to_datetime(date_of_purchase)
        self.shares_covered = shares_covered
        self.contract_length = contract_length

        self.expiration_date = self.closest_expiration_date()
        self.rf_rate = self.get_rf_rate(self.date_of_purchase)
        self.q = self.get_d_yield(self.date_of_purchase)
        self.id = self.create_option_id()
        self.RV = self.calc_RV(self.date_of_purchase)
        self.IV = self.calc_IV(self.date_of_purchase) 
        self.premium = self.calc_premium(self.date_of_purchase) # per share

        # self.invalid = False # measures if the option has been sold or exercised

    # ===== Helper Methods =====
    # ex. third friday would be n = 3
    def nth_friday(self, year, month, n):
        c = calendar.Calendar(firstweekday=calendar.MONDAY)
        monthcal = c.monthdatescalendar(year, month)
        fridays = [day for week in monthcal for day in week if day.weekday() == calendar.FRIDAY and day.month == month]
        return pd.to_datetime(fridays[n-1])  # third Friday

    # Calculates the expiration date of the option given the purchase date and contract length
        # contract_length options:
        # - "1D" : next business day (cannot do same day due to lack of intraday data)
        # - "1W" : current or next Friday (skip 3rd Fridays and days where exp date and purchase date are same)
        # - "1M" : 3rd Friday of current or next month
        # - "3M" : 3rd Friday three months ahead
    def closest_expiration_date(self):
        """
        Determine option expiration date based on contract length.
        """
        purchase_date = self.date_of_purchase

        # --- DAILY ---
        if self.contract_length == "1D":
            exp_date = purchase_date + pd.tseries.offsets.BDay(1)
            return exp_date

        # --- WEEKLY ---
        elif self.contract_length == "1W":
            weekday = purchase_date.weekday()
            days_until_friday = (4 - weekday) % 7
            exp_date = purchase_date + pd.Timedelta(days=days_until_friday)
            third_friday = self.nth_friday(exp_date.year, exp_date.month, 3)        

            # Skip 3rd Friday
            if (exp_date == third_friday):
                exp_date += pd.Timedelta(days=7)
            return exp_date

        # --- MONTHLY ---
        elif self.contract_length == "1M":
            third_friday = self.nth_friday(purchase_date.year, purchase_date.month, 3)
            if purchase_date <= third_friday:
                return third_friday
            else:
                next_month = purchase_date + pd.DateOffset(months=1)
                return self.nth_friday(next_month.year, next_month.month, 3)

        # --- QUARTERLY ---
        elif self.contract_length == "3M":
            quarterly_months = [3, 6, 9, 12]
            year = purchase_date.year

            # Loop until we find a 3rd Friday that is >= purchase_date
            for m in quarterly_months:
                exp_date = self.nth_friday(year, m, 3)
                if exp_date >= purchase_date:
                    next_quarter_expiration = exp_date
                    break
            else:
                # If none found in current year, go to the first quarter of next year
                year += 1
                exp_date = self.nth_friday(year, quarterly_months[0], 3)
                next_quarter_expiration = exp_date

            return next_quarter_expiration

        else:
            raise ValueError(f"Unsupported contract length: {self.contract_length}")
        
    def get_rf_rate(self, purchase_date):
        irx_df = self.portfolio.benchmark_stocks["^IRX"].stock_price_df
        return get_risk_free_rate(irx_df, purchase_date)
    
    def get_d_yield(self, purchase_date):
        stock_df = self.stock.stock_price_df
        div_df = self.stock.dividends
        if (div_df.empty):
            return 0
        q = get_dividend_yield(purchase_date, stock_df, div_df)
        return q
        
    def create_option_id(self):
        """
        Create a unique ID in the format similar to Yahoo Finance:
        AAPL251031C00247500
        where:
        - AAPL = symbol
        - 25 10 31 = expiration date (yy mm dd)
        - C = call or P = put
        - 00247500 = strike in thousands of a dollar (8 chars total)
        """
        date_code = self.expiration_date.strftime("%y%m%d")
        option_type_code = "C" if self.type == "call" else "P"
        strike_code = f"{int(self.strike_price * 1000):08d}"  # *1000 like Yahoo's convention
        return f"{self.stock.ticker}{date_code}{option_type_code}{strike_code}"

    def calc_RV(self, purchase_date):
        rv = get_realized_vol(purchase_date, self.stock.stock_price_df)
        return rv

    def calc_IV(self, purchase_date):
        iv = estimate_iv_proxy(purchase_date, self.expiration_date, self.stock.stock_price_df, self.strike_price, self.type)
        return iv
    
    def calc_premium(self, date_of_purchase):
        # simulate Black-Scholes premium
        stock_price_df = self.stock.stock_price_df
        S = stock_price_df[stock_price_df.index <= date_of_purchase].iloc[-1]["Close"]
        K = self.strike_price
        t = (self.expiration_date - date_of_purchase).days / 365
        r = self.rf_rate 
        iv = self.IV
        type = self.type
        q = self.q
        return black_scholes_price(S, K, t, r, iv, type, q)
    
    # Returns the profit of an option per share held given a close_decision ("exercise" or "sell")
    def get_profit(self, date, close_decision="sell"):
        """
        Calculate profit or loss of the option at expiration (or when sold early).

        Parameters
        ----------
        date: pandasDateTime; 
        close_decision : str
            "exercise" - Option is exercised at date (american options can be exercised early).
            "sell"      - Option is closed out at market (premium-based) on date.

        Returns
        -------
        float : Profit in dollars per contract.
        
        """
        # If invalid date return 0
        if (not (self.date_of_purchase <= date <= self.expiration_date)):
            return 0
        
        # Get all necessary updated vars to approximate fair value
        stock_price_df = self.stock.stock_price_df
        S_T = stock_price_df[stock_price_df.index <= date].iloc[-1]["Close"]
        t = (date - self.date_of_purchase).days / 365
        K = self.strike_price
        current_iv = self.calc_IV(date)
        r = self.get_rf_rate(date)
        q = self.get_d_yield(date) 

        # Option premium paid/received at purchase
        premium_paid = self.premium

        # === CASE 1: Exercise at date ===
        if close_decision == "exercise":
            if self.type == "call":
                intrinsic = max(S_T - K, 0)
            else:  # put
                intrinsic = max(K - S_T, 0)
            payoff = intrinsic

        # === CASE 2: Sell option (mark-to-market) === approximate fair value with updated metrics
        else:
            payoff = black_scholes_price(S_T, K, t, r, current_iv, self.type, q)

        # === Side: buy or sell ===
        # If you bought the option, profit = payoff - premium
        # If you sold (wrote) the option, profit = premium - payoff
        if self.side == "buy":
            profit = payoff - premium_paid
        else:  # sell (writer)
            profit = premium_paid - payoff

        return profit

    # Allows fundamental option info to be shown when class instance is printed
    def __repr__(self):
        return (f"{self.id} | {self.stock.ticker.upper()} {self.type.upper()} "
                f"Strike={self.strike_price:.2f} Exp={self.expiration_date.date()} "
                f"Prem={self.premium:.2f} IV={self.IV:.2f} r={self.rf_rate:.3f}")

###############################################################################################
# HELPER FUNCTIONS

# Example function to get historical volatility from your stock (returns in decimal, e.g., 0.25 = 25%)
# date: pandas date time object
def get_realized_vol(date, stock_price_df, window=60):
    realized_vol = 0

    # Filter prices for dates up to the given date
    stock_prices = stock_price_df[stock_price_df.index <= date]["Close"]
    if len(stock_prices) < window:
        #print(f"Historical volatility could not be calculated, resorting to 0.17.")
        return 0.17  # Return average for the market based on the VIX
    
    stock_returns = stock_prices.pct_change().dropna()

    realized_vol = stock_returns[-window:].std() * np.sqrt(252)
    return realized_vol 

import math

# Function to estimate implied volatility proxy for an option
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
    dividend_yield=0.0
):
    """
    Conservative institutional-style implied volatility proxy.
    Designed to OVERPRICE convexity rather than underprice it.
    """

    # --- Time to expiration ---
    T_days = (expiration_date - purchase_date).days
    T = T_days / 252.0  # trading years
    if T <= 0:
        return 0.0

    # --- Spot price on purchase date ---
    stock_price = (
        stock_price_df[stock_price_df.index <= purchase_date]
        .iloc[-1]["Close"]
    )

    # --- Realized volatility anchor ---
    realized_vol = get_realized_vol(purchase_date, stock_price_df)

    # --- Moneyness distance ---
    # Absolute % distance from ATM
    d = abs(1.0 - (strike_price / stock_price))

    # ------------------------------------------------------------------
    # Volatility Risk Premium (VRP)
    # ------------------------------------------------------------------

    # Short-dated options are structurally expensive
    tenor_contrib = min(vrp_tenor / math.sqrt(T), 0.08)

    vrp_ratio = (
        1.0
        + vrp_base
        + tenor_contrib
        + vrp_vol * (realized_vol - sigma_ref)
    )

    # IMPORTANT FIX:
    # Downside convexity becomes MORE expensive as strike moves OTM
    if option_type.lower() == "put" and strike_price < stock_price:
        vrp_ratio *= (1.0 + 1.2 * d)

    # Cap VRP explosion for stability
    vrp_ratio = min(vrp_ratio, 2.5)

    # ATM-level implied vol
    sigma_atm = realized_vol * vrp_ratio

    # ------------------------------------------------------------------
    # Skew adjustment (multiplicative, not additive)
    # ------------------------------------------------------------------

    if option_type.lower() == "put":
        # Steep downside skew
        skew_adj = min(max_skew_pts, kappa * d * 1.5)
    else:
        # Calls have much flatter skew
        skew_adj = -min(max_skew_pts, kappa * d * 0.5)

    sigma_iv = sigma_atm * (1.0 + skew_adj)

    # ------------------------------------------------------------------
    # Crisis / realism floor
    # ------------------------------------------------------------------

    # Prevent unrealistically cheap weekly convexity
    sigma_floor = max(0.25, 1.2 * realized_vol)
    sigma_iv = max(sigma_iv, sigma_floor)

    # --- Absolute floor ---
    sigma_iv = max(0.001, sigma_iv)

    return sigma_iv

# OLDER VERSION
# # Function to estiamte implied volatility for an option
# def estimate_iv_proxy(
#     purchase_date,
#     expiration_date,
#     stock_price_df,
#     strike_price,
#     option_type,
#     vrp_base=0.06,
#     vrp_tenor=0.04,
#     vrp_vol=0.2,
#     sigma_ref=0.20,
#     kappa=0.18,
#     max_skew_pts=0.12,
#     dividend_yield=0.0):
#     """
#     Estimate implied volatility for a given stock and option parameters.

#     Args:
#         purchase_date (datetime): date of option purchase
#         expiration_date (datetime): option expiration date
#         stock_price_df (DataFrame): historical stock prices with DatetimeIndex
#         strike_price (float): option strike
#         option_type (str): "call" or "put"
#         vrp_base (float): baseline volatility risk premium
#         vrp_tenor (float): time-to-expiry dependent VRP
#         vrp_vol (float): VRP sensitivity to realized volatility deviation
#         sigma_ref (float): reference volatility
#         kappa (float): skew coefficient
#         max_skew_pts (float): maximum skew adjustment
#         dividend_yield (float): optional continuous dividend yield
#     Returns:
#         float: estimated implied volatility (annualized)
#     """
#     # --- Compute time to expiration in trading days ---
#     T_days = (expiration_date - purchase_date).days

#     # --- Get current stock price on purchase date ---
#     stock_price = stock_price_df[stock_price_df.index <= purchase_date].iloc[-1]["Close"]
#     #print(f"Working with stock_price {stock_price}")

#     # --- Compute realized (historical) volatility up to purchase date ---
#     realized_vol = get_realized_vol(purchase_date, stock_price_df)

#     # --- Convert time to expiry from days to years ---
#     T = T_days / 252.0  # assuming 252 trading days per year
#     if T <= 0:
#         return realized_vol

#     # --- Compute moneyness (distance of strike from current price) ---
#     d = abs(1.0 - (strike_price / stock_price))

#     # --- Volatility Risk Premium (VRP) adjustment ---
#     # Cap vrp_tenor contribution to avoid large short-term blow-ups
#     tenor_contrib = min(vrp_tenor / math.sqrt(T), 0.08)
#     vrp_ratio = 1.0 + vrp_base + tenor_contrib + vrp_vol * (realized_vol - sigma_ref)

#     # Reduce VRP for OTM puts (strike < spot)
#     if option_type.lower() == "put" and strike_price < stock_price:
#         vrp_ratio *= 1 - 0.99 * d  # scale down based on distance

#     # ATM-level implied vol
#     sigma_atm = realized_vol * vrp_ratio

#     # --- Skew adjustment ---
#     gamma = 1.0 if option_type.lower() == "put" else -0.15
#     skew_adj = kappa * d * gamma
#     # Optional: cap skew
#     skew_adj = max(-max_skew_pts, min(skew_adj, max_skew_pts))

#     # --- Combine ATM vol and skew ---
#     sigma_iv = sigma_atm + skew_adj

#     # --- Floor to prevent negative or near-zero vol ---
#     sigma_iv = max(0.001, sigma_iv)

#     # --- Debug print ---
#     #print(sigma_iv)

#     return sigma_iv

# Black-Scholes European option pricing
def black_scholes_price(S, K, t, r, sigma, option_type="call", q=0.0, min_premium=0.01):
    """
    Compute the Black-Scholes theoretical option price with continuous dividend yield q.
    """
    if(t <= 0 or sigma <= 0):
        if option_type.lower() == "call":
            return max(0, S - K)
        else:
            return max(0, K - S)

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
        #print(f"length of the rf-rate df: {len(irx_df)}")

        if len(irx_df) == 0:
            # fallback if no data before date
            print(f"Warning: could not fetch rf rate for this date, defaulting to 0.03")
            return 0.03
        
        last_rate = irx_df["Close"].iloc[-1] / 100.0  # convert from percent to decimal
        #print(f"Last rate: {last_rate}")
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
    




