# Import Libraries:
from stock import stockInvestment
import pandas as pd
from options import option
from datetime import date

# Define portfolio class to manage multiple stock investments.
class portfolio:
    def __init__(self, stock_list, monthly_budget=1500):
        self.stocks = {}
        self.current_options = {
            "sell": {},
            "buy": {}
        }
        self.cash = 0
        self.option_trade_balance = 0 # how much profit have we made with our option trading

        self.benchmark_tickers = ["^GSPC", "^IRX"] # S&P 500 and treasury bills for rf rate
        self.benchmark_stocks = {} # to hold index funds for market comparison

        self.monthly_budget = monthly_budget
        self.weekly_budget = monthly_budget/4
        self.current_value = 0.0
        self.total_invested = 0.0 # how money do we have tied in equities?
        self.total_contributed = 0.0 # how much have we contributed in our funds?
        self.profit = 0.0
        self.roe_portfolio = 0.0
        self.start_date = pd.Timestamp(date(1900, 1, 1))
        self.end_date = pd.Timestamp(date.today())
        self.dates = None

        # Initialize stock investments
        self.init_equities(stock_list)
        # Initialize benchmark stock investments (i.e S&P 500 to be used for comparative analysis)
        self.init_benchmarks()
        # Determine which dates to simulate investments on (monthly intervals)
        self.init_dates()

        # Initialize dataset to track performance of portfolio
        self.historical_data = {}

    # Buy & Sell stocks given amount of stocks and 
    # Params:
    #   ticker: "AAPL"
    #   trade_type: "buy" or "sell"
    #   dollar_amount: ex. 1500. Must be >= 0. Represents how much of the equity you would like to buy or sell.
    #       - note, if you do not own the dollar amount given (i.e dollar amount is greater), function sells
    #         maximum position. Equivalently, if dollar_amount > cash, dollar_amount = cash.
    def trade_stocks(self, ticker, trade_type, dollar_amount):
        stock = self.stocks[ticker]
        stock_total_score = stock.current_scoring["total_adj_score"]
        stock_market_adj = stock.current_scoring["market_adj_factor"]

        if (trade_type == "buy"):
            dollar_amount = min(dollar_amount, self.cash)
            if (dollar_amount <= 0):
                return

            trade_shares = dollar_amount/stock.current_price
            self.cash -= dollar_amount
            stock.total_invested += dollar_amount
            stock.total_shares += trade_shares

            print(f"Bought {trade_shares:,.4f} shares of {stock.ticker} on {stock.current_date.strftime('%Y-%m-%d')}:")
            print(f"  {stock.ticker}:")
            print(f"    current price: ${stock.current_price:,.2f}")                     
            print(f"    current market_adj_factor: {stock_market_adj:,.4f}")
            print(f"    current total_score: {stock_total_score:,.4f}")
            print(f"  # of shares: {trade_shares:,.4f}")     
            print(f"  Total cost: ${dollar_amount:,.2f}")
            print("")
            
        else: # sell shares
            own_shares = stock.total_shares
            trade_shares = min(dollar_amount/stock.current_price, own_shares)
            if (trade_shares <= 0):
                return
            
            trade_value = trade_shares * stock.current_price
            cost_removed = trade_shares * (stock.total_invested / stock.total_shares)

            stock.total_invested -= cost_removed
            stock.total_shares -= trade_shares
            self.cash += trade_value

            print(f"Sold {trade_shares:,.4f} shares of {stock.ticker} on {stock.current_date.strftime('%Y-%m-%d')}:")
            print(f"  {stock.ticker}:")  
            print(f"    current price: ${stock.current_price:,.2f}")                     
            print(f"    current market_adj_factor: {stock_market_adj:,.4f}")
            print(f"    current total_score: {stock_total_score:,.4f}")
            print(f"  # of shares: {trade_shares:,.4f}")    
            print(f"  Total gain: ${trade_value:,.2f}")
            print("")
        
        self.update_portfolio_metrics()

    # Buy & Sell options before expiration date to open a position. Note that after expiration date contract dissapears.
    # Assuming no leverage/margin. So 'buy' must have enough cash, and 'sell' must be either cash secured or covered.
    # Also, assuming that as a writer you are not assigned to sell or buy shares.
    # Also note that the option class automatically chooses a valid expiration date (i.e >= date_of_purchase)
    # Params:
    #   ticker: "AAPL"
    #   option_type: "put" or "call"
    #   side: "buy" or "sell" i.e are we writing calls/puts or buying them from someone else
    #   num_shares: the amount of shares you would like to be covered in the contract (standard is 100)
    #   rest self explanatory
    def open_option_position(self, ticker, option_type, side, strike_price, date_of_purchase, num_shares=100, contract_length="1M"):
        op = option(self, ticker, option_type, side, strike_price, date_of_purchase, num_shares, contract_length)

        # Check if purchase_date == expiration date (i.e option premium will be 0)
        if (op.premium == 0):
            return

        # Otherwise, engage.
        if (side == "buy"):
            total_cost = num_shares * op.premium
            if (self.cash >= total_cost):
                self.cash -= total_cost
                self.current_options["buy"][op.id] = op

                stock_total_score = op.stock.current_scoring["total_adj_score"]
                stock_market_adj = op.stock.current_scoring["market_adj_factor"]

                print(f"Bought {op.stock.ticker} option on {date_of_purchase.strftime('%Y-%m-%d')}: ")
                print(f"  {op}")
                print(f"  {op.stock.ticker}:")
                print(f"    current price: ${op.stock.current_price:,.2f}")
                print(f"    current market_adj_factor: {stock_market_adj:,.4f}")
                print(f"    current total_score: {stock_total_score:,.4f}")
                print(f"  Cost: ${total_cost:,.2f}")
                print("")
                self.option_trade_balance -= total_cost

        else: # i.e writing puts and calls
            if (side == "put"):
                # Must be cash-secured i.e have enough to buy at strike price
                cost_at_strike = strike_price * num_shares
                if (self.cash >= cost_at_strike):
                    self.cash += op.premium * num_shares # immediately earn premium
                    self.current_options["sell"][op.id] = op
            else: # covered call
                # Must be covered i.e have enough shares to sell to buyer
                stock = self.stocks[ticker]
                if (stock.total_shares >= num_shares):
                    self.cash += op.premium * num_shares # immediately earn premium
                    self.current_options["sell"][op.id] = op
        
        self.update_portfolio_metrics()

    # Closes an existing position
    # Params:
    #   curr_date: date that you attempt to close the option.
    #   op: an option of type option
    #   close_decision: "sell" or "exercise"
    #       - "sell": you offset your position and recieve premium from that option contract
    #       - "exercise": 
    def close_option_position(self, curr_date, curr_option, close_decision="sell"):
        # Check if option is expired:
        if (curr_date > curr_option.expiration_date):
            # Remove the option from portfolio.
            del self.current_options[curr_option.side][curr_option.id]
            return

        # Note always best to just sell the option on the market instead of exercising.
        if (close_decision == "sell"):
            offset_side = "buy" if curr_option.side == "sell" else "sell"
            offset_option = option(self, curr_option.stock.ticker, curr_option.type, offset_side, curr_option.strike_price, 
                                    curr_date, curr_option.shares_covered, curr_option.contract_length)
            offset_premium = offset_option.premium
            offset_shares = offset_option.shares_covered
            offset_cost = offset_premium * offset_shares
            curr_option_cost = curr_option.premium * curr_option.shares_covered

            profit = offset_cost - curr_option_cost # investigate get_profit function
            #profit = curr_option.get_profit(curr_date) # trying profit function to see if it works correctly
            #offset_cost = profit + curr_option_cost
            roe = profit/curr_option_cost

            stock_total_score = curr_option.stock.current_scoring["total_adj_score"]
            stock_market_adj = curr_option.stock.current_scoring["market_adj_factor"]

            print(f"Sold {curr_option.stock.ticker} option on {curr_date.strftime('%Y-%m-%d')}: ")
            print(f"  {curr_option}")
            print(f"  {curr_option.stock.ticker}:")
            print(f"    current price: ${curr_option.stock.current_price:,.2f}")
            print(f"    current market_adj_factor: {stock_market_adj:,.4f}")
            print(f"    current total_score: {stock_total_score:,.4f}")
            print(f"  Sold for: ${offset_cost:,.2f}")
            print(f"  Profit: ${profit:,.2f}")
            print(f"  Roe: {roe:.2%}")
            print("")
            
            # Remove the option from portfolio.
            del self.current_options[curr_option.side][curr_option.id]

            # Add funds from selling to market
            self.cash += offset_cost
            self.option_trade_balance += offset_cost
        
        # Exercising may only be used for auto-exercise at expiration date
        elif (close_decision == "exercise" and curr_option.side == "buy"): # cannot exercise as the writer
            # For theoretical sake you just get intrinsic value
            intrinsic_val = 0
            strike_price = curr_option.strike_price
            curr_price = curr_option.stock.current_price

            if (curr_option.type == "put"):
                intrinsic_val = strike_price - curr_price
            else: 
                intrinsic_val =  curr_price - strike_price
            
            # Remove the option from portfolio.
            del self.current_options[curr_option.side][curr_option.id]

            # Add funds from exercising
            self.cash += intrinsic_val
        
        self.update_portfolio_metrics()

    # Initialize equities in portfolio
    def init_equities(self, stock_list):    
        max_start = self.start_date
        min_end = self.end_date
        for i in range(len(stock_list)):
            # Fetch data for each stock in list.
            ticker = stock_list[i]
            try:
                # Fetch all individual data sources for stock
                investment = stockInvestment(ticker)
                investment.fetch_fundamentals()
                investment.fetch_historical_prices(self.start_date, self.end_date)
                investment.fetch_historical_dividends(self.start_date, self.end_date)
                investment.consolidate_df()
                self.stocks[ticker] = investment

                # Determine common start date among all data
                max_start = max(max_start,
                                investment.stock_price_df.index[0],
                                investment.ratios_df.index[0],
                                investment.qual_df.index[0],
                                )
                # Determine common end date for all price data (ratios and qual will front fill)
                min_end = min(min_end,
                              investment.stock_price_df.index[-1]
                              )
            except Exception as e:
                print(f"Error adding {ticker} to portfolio: {e}")
        
        self.start_date = max_start
        self.end_date = min_end

    # Init benchmark stocks used for comparison
    def init_benchmarks(self):
        # Initialize benchmark stock investments (i.e S&P 500 to be used for comparative analysis)
        for ticker in self.benchmark_tickers:
            try:
                investment = stockInvestment(ticker)
                investment.fetch_historical_prices(self.start_date, self.end_date)
                self.benchmark_stocks[ticker] = investment

            except Exception as e:
                print(f"Error initializing {ticker} as benchmark stock: {e}")

    # initialize the dates the backtest will be running on
    def init_dates(self):
        #dates = list(self.benchmark_stocks["^GSPC"].stock_price_df.index)
        dates = [d for d in self.benchmark_stocks["^GSPC"].stock_price_df.index if self.start_date <= d <= self.end_date]

        if (len(dates) == 0):
            raise Exception("No dates available to simulate on.")
        self.dates = dates

    # Records performance of the portfolio alongside all scoring and analytics for a point in time.
    # Note: only call this after all investments have been made for that date.
    def record_snapshot(self, curr_date):
        # Record snapshots for all stocks
        for stock in self.stocks.values():
            stock.record_snapshot()  

        # Record snapshot of portfolio
        self.historical_data[curr_date] = {
            "total_invested": self.total_invested,
            "total_contributed": self.total_contributed,
            "cash": self.cash,
            "option_trade_balance": self.option_trade_balance,
            "current_value": self.current_value,
            "profit": self.profit,
            "roe": self.roe_portfolio,
            "stocks_data": {ticker: stock.historical_data[curr_date] for ticker, stock in self.stocks.items()}
        }
    
    # Updates date and price of stock
    def update_stock_data(self, dt):
        from scoring import calculate_totalScore

        # Update all dates, prices for stocks in portfolio
        for investment in self.stocks.values():
            investment.current_date = dt
            investment.get_closing_price()
            
            # Update scoring info
            #market_adjustment_factor(investment, self.benchmark_stocks["^GSPC"]) # to save time just update market adjustment factor
            calculate_totalScore(investment, self.benchmark_stocks["^GSPC"])

    # Updates all portfolio bookkeeping variables
    def update_portfolio_metrics(self):
        total_invested = 0 
        current_value = 0

        # Keep track of stock investments
        for investment in self.stocks.values():
            total_invested += investment.total_invested 
            current_value += investment.total_shares * investment.current_price
        # Add any remaining cash to current_value of portfolio
        current_value += self.cash

        # Update portfolio-level totals
        self.total_invested = total_invested
        self.current_value = current_value

        # Compute “return on equity” — i.e. profit relative to invested capital
        self.profit = self.current_value - self.total_contributed
        self.roe_portfolio = self.profit / self.total_contributed if self.total_contributed > 0 else 0

    # Print stock score summary
    def print_score_summary(self):
        from scoring import print_score_summary as print_scores

        # Calculate budgeting weights based on stock scores
        for ticker, investment in self.stocks.items():
            print("============================================================")
            print(f"Date: {investment.current_date.date()}")
            print(f"{ticker} - ${investment.current_price:,.2f}")
            print_scores(investment)
    
    # Print monthly summary of results
    def print_monthly_summary(self):
        # Print summary of equity results:
        print("------------------------------------------------------------")
        print(f"Monthly Investment Summary")
        print("------------------------------------------------------------")
        invested_this_month = 0
        for ticker, investment in self.stocks.items():
            score = investment.current_scoring["total_adj_score"]
            investment_amount = investment.curr_month_investment
            invested_this_month += investment_amount
            perc_of_budget = (investment_amount / self.monthly_budget) * 100 if self.monthly_budget > 0 else 0
            closing_price = investment.current_price
            shares = investment.total_shares
            value = shares * closing_price
            invested = investment.total_invested
            print(f"{ticker}:")
            print(f"  Closing Price     = ${closing_price:,.2f}")
            print(f"  Score             = {score:.2f}")
            print(f"  Invested Amount   = ${investment_amount:,.2f}")
            print(f"  % of Budget       = {perc_of_budget:,.2f}%")
            print(f"  Shares Bought     = {investment_amount / closing_price:.4f}")
            print(f"  Total Shares      = {shares:.4f}")
            print(f"  Value             = ${value:,.2f}")
            print(f"  Total Invested    = ${invested:,.2f}")
            print("------------------------------------------------------------")

        # Print option summaries
        print(f"Monthly Option Positions Summary")
        print("------------------------------------------------------------")
        # Start with buy side.
        print("Options Bought:")
        for option in self.current_options["buy"].values():
            print(f"  Date of Purchase: {option.date_of_purchase}")
            print(f"  {option.stock.ticker} current price: {option.stock.current_price}")
            print(f"  {option}")
            print(f"  Total Cost: {option.premium * option.shares_covered}")
            print("")

        # Continue with sell side.
        print("Options Written:")
        for option in self.current_options["sell"].values():
            print(f"  Date of Purchase: {option.date_of_purchase}")
            print(f"  {option}")
            print(f"  Total Cost: {option.premium * option.shares_covered}")
            print("")

        # Print current trade balance (net profit for option trading)
        print(f"Option Trading Net Profit: {self.option_trade_balance}")
        print("------------------------------------------------------------")

        # Print Portfolio Summary
        print("Portfolio Summary:")
        print(f"  Invested This Month = ${invested_this_month:,.2f}")
        print(f"  Total Invested      = ${self.total_invested:,.2f}")
        print(f"  Total Cash          = ${self.cash:,.2f}")
        print(f"  Total Contributed   = ${self.total_contributed:,.2f}")
        print(f"  Current Value       = ${self.current_value:,.2f}")
        print(f"  ROE                 = {self.roe_portfolio:.2%}")
        print("------------------------------------------------------------")

    # Print all-time summary of portfolio
    def print_all_time_summary(self):
        # Print ALL TIME summary of results:
        print("\n================= ALL-TIME SUMMARY =========================")
        # total_portfolio_value = 0
        total_equity_value = 0
        for ticker, investment in self.stocks.items():
            starting_price = investment.stock_price_df.loc[self.start_date, 'Close']
            closing_price = investment.stock_price_df.loc[self.end_date, 'Close']
            total_shares = investment.total_shares
            total_invested = investment.total_invested
            final_value = total_shares * closing_price
            total_profit = final_value - total_invested
            final_roe = total_profit / total_invested if total_invested > 0 else 0

            print(f"\n{ticker} Summary from {self.start_date.date()} to {self.end_date.date()}:")
            print(f"  Starting Price:          ${starting_price:,.2f}")
            print(f"  Final Closing Price:     ${closing_price:,.2f}")
            print(f"  Total Shares Held:       {total_shares:.4f}")
            print(f"  Total Invested:          ${total_invested:,.2f}")
            print(f"  Final Value:             ${final_value:,.2f}")
            print(f"  Total Profit:            ${total_profit:,.2f}")
            print(f"  All-Time ROE:            {final_roe:.2%}")
            
            # Update total equity value since closing price may have changed
            # total_portfolio_value += final_value 
            total_equity_value += final_value

        # Final Portfolio Summary
        self.current_value = total_equity_value + self.cash 
        self.profit = self.current_value - self.total_contributed
        self.roe_portfolio = self.profit / self.total_contributed if self.total_contributed > 0 else 0
        years = (self.end_date - self.start_date).days / 365.25
        average_annual_roe = self.roe_portfolio / years if years > 0 else 0

        print("\n----------------- Portfolio Summary -----------------")
        print(f"  Total Contributed:       ${self.total_contributed:,.2f}")
        print(f"    Invested in Equities:  ${self.total_invested:,.2f}")     
        print("")  
        print(f"  Option Trading Net Profit: {self.option_trade_balance}")
        print("")
        print(f"  Final Portfolio Value:   ${self.current_value:,.2f}")
        print(f"    Equities:              ${total_equity_value:,.2f}")
        print(f"    Cash:                  ${self.cash:,.2f}")
        print(f"  Total Profit:            ${self.profit:,.2f}")
        print(f"  Average Annual ROE:      {average_annual_roe:.2%}")
        print(f"  All-Time Portfolio ROE:  {self.roe_portfolio:.2%}")
        print("============================================================\n")

 
