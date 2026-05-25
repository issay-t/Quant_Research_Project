from fetch_data import *
import copy

# Define stockInvestment class to keep track of investments in a single stock.
class stockInvestment:
    def __init__(self, ticker):
        self.ticker = ticker

        self.ratios_df = None
        self.qual_df = None
        self.stock_price_df = None 
        self.dividends = None
        self.master_df = None # CONTAINS ALL ABOVE DATA CONSOLIDATED

        # Initialize investment tracking
        self.total_invested = 0.0         # how much money you've put in so far
        self.total_shares = 0.0           # how many shares you currently hold
        self.curr_month_investment = 0
        self.curr_week_investment = 0

        # Initialize current scores and current date.
        self.current_date = None
        self.current_price = None
        self.current_scoring = {
            "roe": None,
            "de": None,
            "pe": None,
            "management_quality": None,
            "competitive_edge": None,
            "longevity": None,
            "base_score": None,
            "momentum": None, 
            "volatility": None, 
            "rel_performance": None,
            "market_adj_factor": None,
            "total_adj_score": None,
        }

        # Initialize weights and options:
        self.weighting = {
            "roe": 1/6,
            "de": 1/6,
            "pe": 1/6,
            "management_quality": 1/6,
            "competitive_edge": 1/6,
            "longevity": 1/6,
            "market_sensitivity": 0.5,
            "momentum": 0.4, 
            "volatility": 0.3, 
            "rel_performance": 0.3
        }

        # Initialize historical dataset (used for analysis and graphing)
        self.historical_data = {}

    def fetch_fundamentals(self):
        self.ratios_df = get_finRatios(self.ticker)

        # Extract dates and get qualitative data based on available data in ratios_df
        dates_list = list(self.ratios_df.index)
        self.qual_df = get_qual_data(self.ticker, dates_list)
    
    def fetch_historical_prices(self, start_date, end_date):
        self.stock_price_df = get_closing_prices(self.ticker, start_date, end_date)

    def fetch_historical_dividends(self, start_date, end_date):
        self.dividends = get_dividends(self.ticker, start_date, end_date)
    
    def get_closing_price(self):
        filtered_dates = self.stock_price_df[self.stock_price_df.index <= self.current_date]
        if filtered_dates.empty:
            print(f"No available stock price data on or before {self.current_date} for {self.ticker}.")
            return 0
        closest_date = filtered_dates.index[-1]
        self.current_price = self.stock_price_df.loc[closest_date, 'Close']

    # Consolidate data
    def consolidate_df(self):
        ratios_df = self.ratios_df
        qual_df = self.qual_df
        prices_df = self.stock_price_df
        dividends_df = self.dividends

        master = ratios_df.join([qual_df, prices_df, dividends_df], how="outer") # join all dataframes
        master = master.ffill().bfill()
        master = master.infer_objects(copy=False)
        master = master.fillna(0)
        self.master_df = master
        filename = os.path.join("master_archive", f"{self.ticker}_master_data.xlsx")
        master.to_excel(filename, index="True")
    
    # Records performance of the stock alongside all scoring and analytics for a point in time.
    # Note: only call this after all investments have been made for that date.
    def record_snapshot(self):  
        self.historical_data[self.current_date] = {
            "closing_price": self.current_price,
            "scoring": copy.deepcopy(self.current_scoring),
            "weighting": copy.deepcopy(self.weighting),
            "curr_month_investment": self.curr_month_investment,
            "curr_week_investment": self.curr_week_investment,
            "total_invested": self.total_invested,
            "total_shares": self.total_shares
        }