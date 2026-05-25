from portfolio import portfolio
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt

# # --------------------------------------------------------------------------------------------------------------------
# APOSBA_strategy (Alpha Probing Options, score-based-allocation model):
# - invests consistently with a universe of companies with 90% of budget. Calculates their total score (f + m),
#   and allocates a certain amount of the budget towards the stocks with the highest scores using an
#   exponential allocation model
#     - conversly, trims existing positions with poor total scores and uses the cash to hedge the position with long puts
# - allocates 10% of remaining budget to alpha probing option trading (not hedging, opportunity seeking)
#     - searches for stocks in the universe which we do not own.
#     - systematically buys cheap otm (delta 0.1-0.3 or strike_price +-4% current) options based on market_adj_factor
# # --------------------------------------------------------------------------------------------------------------------
# class APOSBA_strategy:
#     def __init__(self, stock_list, trim_perc=0.12, equity_thresh=0.45, put_thresh=0.48, call_thresh=0.83, strike_perc_dif = 0.04, min_loss = -2.35, max_profit = 2.97, agg_cash_thresh=0.1, monthly_budget=1500):
#         self.trim = trim_perc
#         self.equity_thresh = equity_thresh
#         self.put_thresh = put_thresh # relative to market adj factor (0.5 is norm, 0.3 is bad, 0.7 is good)
#         self.call_thresh = call_thresh
#         self.strike_perc_dif = strike_perc_dif
#         self.min_loss = min_loss
#         self.max_profit = max_profit
#         self.agg_cash_thresh = agg_cash_thresh
#         self.portfolio = portfolio(stock_list, monthly_budget)
#         self.total_profit = 0
#         self.total_roe = 0
        
#     # handle_option_positions() handles all open option positions. Auto closes options that 
#     # are ITM by a threshold or OTM by a threshold and auto sells positions at the expiration date.
#     # note: only handles purchased options so far not written puts and calls
#     def handle_option_positions(self, curr_date, min_loss = -2, max_profit = 2):
#         p = self.portfolio
#         dates = p.dates

#         del_bought_options = []
#         for option in p.current_options["buy"].values():
#             expiration_date = option.expiration_date

#             # In two scenarios we must sell automatically:
#             # - curr_date == expiration_date
#             # - curr_date == last date in dates.
#             # - next date in array is greater or equal to the expiration date.
#             curr_date_index = dates.index(curr_date) # curr_date comes from p.dates in the backtest so no need to check
#             curr_date_is_last = curr_date_index == len(dates) - 1
#             next_date =  -1 if curr_date_is_last else dates[curr_date_index + 1]

#             # Get index of expiration date in dates if it exists
#             try:
#                 exp_index = dates.index(expiration_date)
#             except ValueError:
#                 exp_index = -1
            
#             # Conditions for a sell based on threshold.
#             premium_paid = option.premium 
#             profit = option.get_profit(curr_date)
#             roe = profit/premium_paid if premium_paid != 0 else 0
#             # AUTOSELL
#             if ((curr_date == expiration_date) or 
#                  curr_date_is_last or
#                  ((exp_index == -1) and (next_date > expiration_date))):
#                 del_bought_options.append(option)
#             # SELL BASED ON THRESHOLD
#             elif (not (min_loss <= roe <= max_profit)):
#                 del_bought_options.append(option)
        
#         # Delete all options
#         for option in del_bought_options:
#             p.close_option_position(curr_date, option)

#         # Print current trade balance (net profit for option trading)
#         if (len(del_bought_options) > 0):
#             equity_value = 0
#             for stock in p.stocks.values():
#                 equity_value += stock.current_price * stock.total_shares
#             print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#             print(f"Option Trading Net Profit: {p.option_trade_balance}")
#             print(f"Current Portfolio Value: {p.current_value}")
#             print(f"    Total contributed: {p.total_contributed}")
#             print(f"    Total Invested in equities: {p.total_invested}")
#             print(f"    Total Value of Equities: {equity_value}")
#             print(f"    Total Cash: {p.cash}")
#             print(f"Profit: {p.profit}")
#             print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
#             print("")

#     # Buy options based on cash and stock score
#     def buy_options(self, strike_perc_dif=0.04):
#         p = self.portfolio
        
#         # Determine available cash for options in this sleeve. Only can trade with up to agg_cash_thresh % of portfolio value.
#         agg_cash_sleeve = min(p.current_value * self.agg_cash_thresh, p.cash)
#         best_scores = []

#         for stock in p.stocks.values():
#             score = stock.current_scoring["market_adj_factor"]
            
#             # Open option position if score reaches threshold levels for call and put. 
#             # If cash is not there transaction will not go through.
#             if (score >= self.call_thresh):
#                 best_scores.append({
#                     "type": "call",
#                     "score": score,
#                     "stock": stock
#                 })
#                 #p.open_option_position(stock.ticker, "call", "buy", strike_price, stock.current_date, num_shares=100, contract_length="1W")
#             elif (score <= self.put_thresh):
#                 best_scores.append({
#                     "type": "put",
#                     "score": 1-score,
#                     "stock": stock
#                 })
#                 #p.open_option_position(stock.ticker, "put", "buy", strike_price, stock.current_date, num_shares=100, contract_length="1W")
        
#         from options import option 
#         sorted_scores = sorted(best_scores, key=lambda x: x["score"], reverse=True)
#         for s in sorted_scores: # sorted from best to worst
#             type = s["type"]
#             stock = s["stock"]
#             strike_price = stock.current_price*(1+strike_perc_dif) if type == "call" else stock.current_price*(1-strike_perc_dif)
#             num_shares = 100
#             op = option(p, stock.ticker, type, "buy", strike_price, stock.current_date, num_shares, contract_length="1W")
#             total_cost = op.premium * num_shares
#             if (total_cost <= agg_cash_sleeve):
#                 p.open_option_position(stock.ticker, type, "buy", strike_price, stock.current_date, num_shares=100, contract_length="1W")
#                 agg_cash_sleeve -= total_cost
#             else: 
#                 break

#     # transfer_cash(cash) inputs the amount of cash needed for an investment.
#     # If cash is available and represents a percentage greater than 10% of the portfolio value, it deducts from the portfolio fund.
#     # Otherwise, it returns the amount requested via contribution. 
#     def transfer_cash(self, cash): 
#         p = self.portfolio
#         cash_perc = p.cash / p.current_value if p.current_value > 0 else 0

#         # Add funds if cash is below threshold percentage.
#         # Directly tied to contribution tracking.
#         # Otherwise, no action needed as cash is already there and using it will help rebalance portfolio.
#         if (cash_perc < self.agg_cash_thresh):
#             p.cash += cash
#             p.total_contributed += cash

#     # Initiates purchasing of all stocks in portfolio with a given budget.
#     # Invests/trims once at the end of each week.
#     def invest(self, power=2):
#         p = self.portfolio
        
#         total_invested = 0
#         for stock in p.stocks.values():
#             score = stock.current_scoring["total_adj_score"]
#             if score >= self.equity_thresh:
#                 adjusted_score = (score - self.equity_thresh) / (1 - self.equity_thresh)
#                 scaled = adjusted_score ** power
#                 stock.curr_week_investment = scaled * p.weekly_budget  # scaled to weekly budget directly
#             else: # Sell trim% of position
#                 stock.curr_week_investment = 0
#                 trade_amount = self.trim * stock.total_shares * stock.current_price
#                 p.trade_stocks(stock.ticker, "sell", trade_amount)
#             total_invested += stock.curr_week_investment

#         for stock in p.stocks.values():
#             # Optionally normalize so total ≤ monthly_budget
#             if total_invested > p.weekly_budget and total_invested > 0:
#                 stock.curr_week_investment *= p.weekly_budget / total_invested
            
#             # Minimum $1 stock purchase
#             stock.curr_week_investment = 0 if stock.curr_week_investment < 1 else stock.curr_week_investment
            
#             # Add funds for trade_amount from budget and buy stock
#             self.transfer_cash(stock.curr_week_investment)
#             p.trade_stocks(stock.ticker, "buy", stock.curr_week_investment)


#     # Check if curr_date represents the beginning of the week in the date series
#     # Returns true if the current_date is monday or the date before was a different week.
#     def check_bow(self, curr_date):
#         p = self.portfolio

#         # Check if current date is the bow.
#         first_date = p.dates[0]
#         if (curr_date == first_date and curr_date.dayofweek == 0):
#             return True
#         else:
#             curr_date_index = p.dates.index(curr_date)
#             dt_before = p.dates[curr_date_index - 1] # just check the date before in the index
#             return (dt_before.week != curr_date.week)
    
#     # Check if curr_date represents the end of the week in the date series
#     # Returns true if the subsequent date is a new week or if it is a friday.
#     def check_eow(self, curr_date):
#         p = self.portfolio

#         # Check if next day is a new week
#         last_date = p.dates[-1]
#         if (curr_date == last_date and curr_date.dayofweek == 4): # if this date is the last in the index, we can't check the next date directly so check if it is friday.
#             return True
#         else:
#             curr_date_index = p.dates.index(curr_date)
#             dt_next = p.dates[curr_date_index + 1] # just check the next date in the index
#             return (dt_next.week != curr_date.week)
    
#     # Check if curr_date represents the end of its month in the date series
#     # Returns true if the subsequent date is a new month or if its the EOM in the calender
#     def check_eom(self, curr_date):
#         p = self.portfolio

#         # Check if next day is a new month
#         last_date = p.dates[-1]
#         if curr_date == last_date: # if this date is the last in the index, we can't check the next date directly
#             dt_next = curr_date + timedelta(days=1) # must check the next calendar day after the current day
#         else:
#             curr_date_index = p.dates.index(curr_date)
#             dt_next = p.dates[curr_date_index + 1] # just check the next date in the index

#         return (dt_next.month != curr_date.month) 
    
#     # Graph results:
#     def graph_results(self):
#         p = self.portfolio
#         records = []
#         for date, port_snapshot in p.historical_data.items():
#             for ticker, stock_data in port_snapshot["stocks_data"].items():
#                 records.append({
#                     "date": date,
#                     "ticker": ticker,
#                     "closing_price": stock_data["closing_price"],
#                     "score": stock_data["scoring"]["total_adj_score"],
#                     "portfolio_profit": port_snapshot["profit"]
#                 })
#         df = pd.DataFrame(records).sort_values(["ticker", "date"])

#         # Create figure
#         fig, ax1 = plt.subplots(figsize=(14, 8), constrained_layout=True)

#         # --- Left axis: Stock prices (normalized) ---
#         for ticker, sub_df in df.groupby("ticker"):
#             sub_df = sub_df.sort_values("date")
#             norm_price = sub_df["closing_price"] / sub_df["closing_price"].iloc[0] * 100
#             ax1.plot(sub_df["date"], norm_price, label=ticker, linewidth=1, alpha=0.6)

#         ax1.set_xlabel("Date")
#         ax1.set_ylabel("Normalized Price (Start=100)", color="tab:blue")
#         ax1.tick_params(axis="y", labelcolor="tab:blue")
#         ax1.grid(alpha=0.3)

#         # --- Add S&P 500 (normalized) ---
#         sp500_df = p.benchmark_stocks["^GSPC"].stock_price_df.copy()
#         if "date" not in sp500_df.columns:
#             sp500_df = sp500_df.reset_index()

#         close_col = "Close" if "Close" in sp500_df.columns else "close"
#         sp500_df = sp500_df.sort_values("date")
#         sp500_norm = sp500_df[close_col] / sp500_df[close_col].iloc[0] * 100

#         ax1.plot(
#             sp500_df["date"],
#             sp500_norm,
#             color="black",
#             linewidth=2,
#             linestyle="-",
#             label="S&P 500"
#         )

#         # --- Right axis: Portfolio profit (not normalized) ---
#         ax2 = ax1.twinx()
#         profit_series = (
#             df.groupby("date")["portfolio_profit"]
#             .mean()
#             .reset_index()
#             .sort_values("date")
#         )

#         ax2.plot(
#             profit_series["date"],
#             profit_series["portfolio_profit"],
#             color="tab:green",
#             linestyle="--",
#             linewidth=2.5,
#             label="Portfolio Profit ($)"
#         )
#         ax2.set_ylabel("Portfolio Profit ($)", color="tab:green")
#         ax2.tick_params(axis="y", labelcolor="tab:green")

#         # --- Title ---
#         fig.suptitle(
#             "Portfolio Overview — Normalized Stock Prices, Portfolio Profit, and S&P 500",
#             fontsize=14,
#             fontweight="bold"
#         )

#         # --- Legend: show first 10 stocks, then summarize ---
#         lines_1, labels_1 = ax1.get_legend_handles_labels()
#         lines_2, labels_2 = ax2.get_legend_handles_labels()

#         max_show = 10
#         if len(labels_1) > max_show:
#             total_extra = len(labels_1) - max_show
#             lines_1 = lines_1[:max_show]
#             labels_1 = labels_1[:max_show] + [f"... and {total_extra} more"]

#         ax1.legend(
#             lines_1 + lines_2,
#             labels_1 + labels_2,
#             loc="upper left",
#             fontsize=9,
#             title="Tickers",
#             title_fontsize=10,
#             frameon=False
#         )

#         plt.show()

#     #Get stock score on a given date.
#     def get_score(self):
#         from scoring import calculate_totalScore

#         p = self.portfolio
#         for stock in p.stocks.values():
#             calculate_totalScore(stock, p.benchmark_stocks["^GSPC"])

#     # Run backtest simulation over the portfolio's date range.
#     def run_backtest(self):
#         p = self.portfolio

#         print(f"You will be backtesting your investment strategy with the following portfolio of stocks:")
#         for key in p.stocks.keys():
#             print(f"- {key}")
#         print("------------------------------------------------------------------------------------------")
#         start_backtest = input("Proceed with backtest simulation? (Y/N): ").upper()
#         if start_backtest != 'Y':
#             print("Backtest simulation cancelled.")
#             return

#         print("\n------------------------------------------------------------------------------------------")
#         # Simulate monthly investments based on the calculated score
#         print(f"Starting backtest simulation from {p.start_date.date()} to {p.end_date.date()} with a budget of ${p.monthly_budget:.2f} per month.")
#         for dt in p.dates: 
#             # Update stock data and portfolio metrics.
#             p.update_stock_data(dt)

#             # Handle all active option positions
#             self.handle_option_positions(dt, self.min_loss, self.max_profit)
            
#             # Buy options at the bow.
#             if (self.check_bow(dt)): 
#                 self.buy_options(self.strike_perc_dif)
            
#             # If it is eow we invest in equities and trim bad positions.
#             elif(self.check_eow(dt)): 
#                 self.invest()
                
#             # If we've reached the end of the month we print results
#             if (self.check_eom(dt)): 
#                 #p.print_score_summary()
#                 #p.print_monthly_summary()
#                 print(f"Mid-Month Activity: ")
            
#         # Print ALL TIME summary of results:
#         p.print_all_time_summary()
        
#         # Update profit results
#         self.total_profit = p.profit
#         self.total_roe = p.roe_portfolio

#         # Graph results for analysis
#         # self.graph_results()
