# Import Libraries:
from archived_scripts.quant_data import *
from datetime import date, datetime, timedelta
    
# calculate_score calculates the score given to the company based on qualitative and quantitative factors.
# note: date will always be greater or equal to the earliest date in ratios_df
def calculate_totalScore(date, ratios_df, qual_df, 
                         w = {
                            "roe": 1/6,
                            "de": 1/6,
                            "pe": 1/6,
                            "management_quality": 1/6,
                            "competitive_edge": 1/6,
                            "longevity": 1/6
                         }):
    # Find the row in ratios_df appropriate for the given date
    dt = datetime.strptime(date, "%Y-%m-%d")
    most_recent_date = ratios_df.loc[(len(ratios_df) - 1), 'date'] # latest data is at the last index.
    data_exists = False
    
    for i in reversed(range(len(ratios_df))):
        curr_date = datetime.strptime(ratios_df.loc[i, 'date'], "%Y-%m-%d")
        if (dt >= curr_date and (dt - curr_date).days >= 60): # to account for when the public actually gets the annual report.
            most_recent_date = ratios_df.loc[i, 'date']
            data_exists = True
        else:
            break
    
    if (data_exists == False):
        #available_date = datetime.strptime(most_recent_date, "%Y-%m-%d") + timedelta(days=60)
        #print(f"Data is not available for {date}. Closest available date is {available_date.strftime('%Y-%m-%d')}.")
        return 0
    #print(f"Using data from FY report ending at {most_recent_date} for calculations.")

    # Extract ratios for the given date:
    ratios_row = ratios_df[ratios_df['date'] == most_recent_date]
    roe = ratios_row['netIncomePerShare'].values[0]/ratios_row['shareholdersEquityPerShare'].values[0]
    #print(f"ROE: {roe}")
    debt_to_equity = ratios_row['debtToEquityRatio'].values[0]
    #print(f"D/E: {debt_to_equity}")
    pe_ratio = ratios_row['priceToEarningsRatio'].values[0]
    #print(f"P/E: {pe_ratio}")

    # Calculate scores for ratios:
    roe_score = score_roe(roe)
    #print(f"ROE Score: {roe_score}")
    de_score = score_de(debt_to_equity)
    #print(f"D/E Score: {de_score}")
    pe_score = score_pe(pe_ratio)
    #print(f"P/E Score: {pe_score}")

    # Extract qualitative factors:
    management_quality = qual_df.loc['management_quality', most_recent_date]
    #print(f"Management Quality score: {management_quality}")
    competitive_edge = qual_df.loc['competitive_edge', most_recent_date]
    #print(f"Competitive Edge score: {competitive_edge}")
    longevity = qual_df.loc['longevity', most_recent_date]
    #print(f"Longevity score: {longevity}")

    # Combine scores (weights can be adjusted as needed)
    total_score = (
        w["roe"] * roe_score +                  # Strong profitability indicator
        w["de"] * de_score +                    # Financial leverage and risk
        w["pe"] * pe_score +                    # Valuation multiple (market sentiment)
        w["management_quality"] * management_quality +   # Leadership quality & execution
        w["competitive_edge"] * competitive_edge +       # Moat and differentiation
        w["longevity"] * longevity              # Stability and history
    )
    return total_score

# # allocate_budget determines how much to invest based on score and monthly budget. 
# # used for one stock.
# def allocate_budget(score, monthly_budget, threshold=0.5, power=1.5):
#     if score < threshold:
#         return 0  # don't invest
#     else:
#         adjusted_score = (score - threshold) / (1 - threshold)  # scale 0.7–1.0 → 0–1
#         scaled_weight = adjusted_score ** power  # amplify high scores
#         return scaled_weight * monthly_budget
def allocate_budget(score, monthly_budget, k=20, midpoint=0.8, threshold=0.5):
    """
    Allocate investment budget based on score using a logistic curve.
    
    - Below midpoint → minimal investment
    - Around midpoint → rapid increase
    - Above midpoint → near full allocation
    """
    if score < threshold:
        return 0  # invalid score

    # Logistic curve: sharply rises near midpoint (default 0.8)
    scaled_weight = 1 / (1 + math.exp(-k * (score - midpoint)))
    
    return scaled_weight * monthly_budget

# Helper function to extract dates from FMP dataframe and prepare a sorted list.
def fmp_extract_dates(df):
    # Extract unique dates
    unique_dates = df['date'].unique()
    # Convert to list and sort
    dates_list = sorted(unique_dates.tolist())
    return dates_list

# simulates backtesting investment strategy for a one stock ticker and monthly budget.
def invest_stock(ticker, monthly_budget, 
                 w = {
                    "roe": 1/6,
                    "de": 1/6,
                    "pe": 1/6,
                    "management_quality": 1/6,
                    "competitive_edge": 1/6,
                    "longevity": 1/6
                }):
    # Get data from APIs
    ratios_df = get_finRatios(ticker)
    dates = fmp_extract_dates(ratios_df)
    qual_df = get_qual_data(ticker, dates)

    # Determine investment start and end dates.
    today = date.today()
    end_date = today.strftime("%Y-%m-%d") # today's date
    earliest_date = ratios_df.loc[4, 'date'] # earliest date we have data for is 5 years from this year
    date_obj = datetime.strptime(earliest_date, "%Y-%m-%d").date()
    start_date = date_obj.strftime("%Y-%m-%d") # Format back to string

    # Get monthly budget for investing.
    #monthly_budget = float(input("Enter your monthly investment budget (e.g., 1500): "))
    print("You will be backtesting the investment strategy for {} from {} to {}.".format(ticker, start_date, end_date))

    # Introduce book keeping variables:
    total_invested = 0.0         # how much money you've put in so far
    total_shares = 0.0           # how many shares you currently hold
    closing_price = 0.0         # latest closing price

    # Fetch historical data
    stock_price_df = get_closing_prices(ticker, start_date, end_date)

    # Simulate monthly investments based on the calculated score
    print("Starting backtest simulation...")
    for i in range(len(stock_price_df.index) - 1):  
        dt = stock_price_df.index[i]
        date_str = dt.strftime("%Y-%m-%d")
        #print("Date in yfinance:", date_str)
        score = calculate_totalScore(date_str, ratios_df, qual_df, w)
        investment_amount = allocate_budget(score, monthly_budget)
        closing_price = stock_price_df.loc[dt, ('Close', ticker)] # note yfinance already adjusts for splits/dividends
        #print(f"Date: {date_str}, Closing Price: ${closing_price:,.2f}")

        # Check if next day is a new month
        curr_day = dt.date()
        if i == len(stock_price_df.index) - 2: # if this date is the last in the index, we can't check the next date directly
            dt_next = curr_day + timedelta(days=1) # must check the next calendar day after the current day
        else:
            dt_next = stock_price_df.index[i + 1].date() # just check the next date in the index

        # Buy shares at closing price if the next day is a new month
        if (dt_next.month != curr_day.month):
            shares_bought = investment_amount / closing_price

            # Update holdings
            total_invested += investment_amount
            total_shares += shares_bought

            # Compute current portfolio value
            current_value = total_shares * closing_price

            # Compute “return on equity” — i.e. profit relative to invested capital
            profit = current_value - total_invested
            roe_portfolio = profit / total_invested if total_invested > 0 else 0

            # Print summary of results:
            print("--------------------------------------------------")
            print(
                f"On {date_str}, Score: {score:.2f}, "
                f"Closing Price: ${closing_price:,.2f}, "
                f"Invested this month: ${investment_amount:,.2f}, "
                f"Shares Bought: {shares_bought:.4f}, "
                f"Total shares: {total_shares:.4f}, "
                f"Current Value: ${current_value:,.2f}, "
                f"Total Invested: ${total_invested:,.2f}, "
                f"All-Time Portfolio ROE: {roe_portfolio:.2%}"
            )
            print("--------------------------------------------------")
    
    # Print ALL TIME summary of results:
    print("--------------------------------------------------")
    print(f"ALL TIME SUMMARY for {ticker} from {start_date} to {end_date}:")
    print(f"Final Closing Price: ${closing_price:,.2f}")
    print(f"Total Shares Held: {total_shares:.4f}")
    print(f"Total Invested: ${total_invested:,.2f}")
    final_value = total_shares * closing_price
    print(f"Final Portfolio Value: ${final_value:,.2f}")
    total_profit = final_value - total_invested
    print(f"Total Profit: ${total_profit:,.2f}")
    final_roe_portfolio = total_profit / total_invested if total_invested > 0 else 0
    print(f"All-Time Portfolio ROE: {final_roe_portfolio:.2%}")
    avg_annual_roe = final_roe_portfolio / len(dates) 
    print(f"Average Annual ROE: {avg_annual_roe:.2%}")
    print("--------------------------------------------------")
    return final_roe_portfolio

def main():
    # Get ticker symbol and fetch quantitative data.
    ticker = input("Enter a ticker symbol (e.g., AAPL): ").upper()
    # Get monthly budget for investing.
    monthly_budget = float(input("Enter your monthly investment budget (e.g., 1500): "))
    invest_stock(ticker, monthly_budget)

if __name__ == "__main__":
    main()