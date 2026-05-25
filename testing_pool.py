# Contains all testing pool symbols
all_symbols = [
    "AAL", "AAPL", "ABBV", "ADBE", "AMD", "AMZN", "ATVI", "BA", "BABA", "BAC", "BIDU", "BILI",
    "C", "CARR", "CCL", "COIN", "COST", "CPRX", "CSCO", "CVX",
    "DAL", "DIS", "DOCU",
    "ET", "ETSY",
    "F", "FDX", "FUBO",
    "GE", "GM", "GOOGL", "GS",
    "HCA", "HOOD",
    "INTC",
    "JNJ", "JPM",
    "KO",
    "LCID", "LMT",
    "META", "MGM", "MRNA", "MRO", "MSFT",
    "NFLX", "NIO", "NKE", "NOK", "NVDA",
    "PEP", "PFE", "PINS", "PLTR", "PYPL",
    "RBLX", "RIOT", "RIVN", "RKT", "ROKU",
    "SBUX", "SHOP", "SIRI", "SNAP", "SOFI", "SONY", "SPY", "SPYG", "SQ",
    "T", "TGT", "TLRY", "TSLA", "TSM", "TWTR",
    "UAL", "UBER", "UNH",
    "V", "VIAC", "VWO", "VZ",
    "WBA", "WFC", "WMT",
    "XOM", "ZM"
]
working_symbols = [
    "AAL", "AAPL", "ABBV", "ADBE", "AMD", "AMZN", "BA", "BABA", "BAC", "BIDU", "BILI",
    "C", "CARR", "CCL", "COIN", "COST", "CPRX", "CSCO", "CVX", "DAL", "DIS", "DOCU",
    "ET", "ETSY", "F", "FDX", "FUBO", "GE", "GM", "GOOGL", "GS", "HCA", "HOOD",
    "INTC", "JNJ", "JPM", "KO", "LCID", "LMT", "META", "MGM", "MRNA", "MSFT",
    "NFLX", "NIO", "NKE", "NOK", "NVDA", "PEP", "PFE", "PINS", "PLTR", "PYPL",
    "RBLX", "RIOT", "RIVN", "RKT", "ROKU", "SBUX", "SHOP", "SIRI", "SNAP",
    "SOFI", "SONY", "T", "TGT", "TLRY", "TSLA", "TSM", "UAL", "UBER", "UNH",
    "V", "VZ", "WFC", "WMT", "XOM", "ZM"
]

test_10 = [
    "AAPL", "MSFT", "NVDA",   # Tech
    "JPM", "BAC",             # Financials
    "XOM",                    # Energy
    "UNH",                    # Healthcare
    "TSLA",                   # Auto/growth
    "GE",                     # Industrials
    "AMZN"                    # Consumer/tech
]
test_20 = [
    # Tech
    "AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "META",
    # Consumer
    "AMZN", "WMT", "SBUX",
    # Financials
    "JPM", "BAC", "GS",
    # Healthcare
    "JNJ", "PFE",
    # Industrials
    "GE", "FDX",
    # Energy
    "XOM", "CVX",
    # High-vol/meme / alt exposure
    "TSLA", "RIOT"
]
test_35 = [
    # Tech
    "AAPL", "MSFT", "NVDA", "AMD", "ADBE", "INTC",
    "META", "GOOGL", "NFLX", "PYPL", "PLTR", "PINS",

    # Consumer & Retail
    "AMZN", "WMT", "TGT", "SBUX",

    # Financials
    "JPM", "BAC", "GS", "C", "WFC",

    # Industrials & Transport
    "GE", "BA", "FDX", "DAL", "UBER",

    # Healthcare
    "JNJ", "UNH", "PFE", "MRNA",

    # Energy
    "XOM", "CVX",

    # Higher Volatility Names
    "TSLA", "RBLX"
]
test_50 = [
    # Tech
    "AAPL", "MSFT", "NVDA", "AMD", "ADBE", "INTC", "META",
    "GOOGL", "NFLX", "PYPL", "PLTR", "PINS", "SHOP", "SQ", # if SQ not in your list ignore
    
    # Consumer
    "AMZN", "WMT", "TGT", "SBUX", "NKE", "MGM", "ROKU",

    # Financials
    "JPM", "BAC", "GS", "C", "WFC",

    # Healthcare
    "JNJ", "UNH", "PFE", "MRNA", "ABBV", "HCA",

    # Industrials & Transport
    "GE", "BA", "FDX", "DAL", "UBER",

    # Energy
    "XOM", "CVX", "ET",

    # Communications / Media
    "DIS", "T", "VZ",

    # Chinese ADRs
    "BABA", "NIO", "BIDU",

    # High-vol / meme
    "TSLA", "RIOT", "COIN"
]

large_cap_universe = [
    "AAPL", "MSFT", "NVDA", "AMD", "META", "GOOGL", "NFLX", "ADBE", "CSCO", "INTC",
    "AMZN", "WMT", "TGT", "NKE", "SBUX", "COST",
    "JPM", "BAC", "GS", "C", "WFC", "V",
    "JNJ", "UNH", "PFE", "ABBV", "MRNA",
    "GE", "BA", "FDX", "DAL",
    "XOM", "CVX",
    "T", "VZ",
    "LMT",
    "TSLA", "GM",
    "BABA", "BIDU", "SONY"
]

# near best almost 200% ROE
test_b_symbols = [
    "AAPL", "AMD", "AMZN", "NVDA", "MSFT",
    "META", "NFLX", "TSLA", "SHOP", "GOOGL"
]
test_c_symbols = [
    "KO", "PEP", "JNJ", "PG", "UNH",
    "XOM", "V", "MA", "WMT", "JPM"
]
high_vol = [ #crazy, almost 600% roe but could be based on crazy runs in the meme coins.
    "RIOT", "RBLX", "NIO", "LCID", "HOOD",
    "PLTR", "COIN", "FUBO", "SNAP", "RKT"
]
test_d_symbols = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "META",
    "NVDA", "TSLA", "AMD", "NFLX", "SHOP",
    "COIN", "PLTR", "RBLX", "SOFI", "UBER",
    "CRM", "AVGO", "SQ", "SMCI", "PANW"
]
test_e_symbols = [
    "PEP", "ADBE", "COST", "INTC", "GS",
    "CSCO", "WMT", "XOM", "TGT", "NKE",
    "BA", "GE", "PFE", "FDX", "HCA",
    "VZ", "WFC", "SBUX", "MGM", "BKNG"
]
test_f_symbols = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "NVDA", "TSLA", "CRM", "ADBE", "AVGO",
    "SHOP", "SQ", "UBER", "ABNB", "NET",
    "TTD", "ZS", "PANW", "MS", "V"
]
test_g_symbols = [
    "ZM", "ROKU", "PYPL", "SQ", "SHOP",
    "HOOD", "COIN", "NIO", "RIVN", "LCID",
    "CRM", "SNAP", "AFRM", "PTON", "DKNG",
    "TWLO", "CRWD", "NET", "TTD", "MELI"
]

test_high_vol = [
    "RIOT", "COIN", "HOOD", "PLTR", "RBLX",
    "NIO", "LCID", "RIVN", "FUBO", "SNAP",
    "TSLA", "SOFI", "ROKU", "SHOP", "PYPL",
    "UBER", "AMD", "NVDA", "META", "NFLX"
]

test3 = [
    # Technology & AI
    "AAPL", "MSFT", "NVDA", "AMD", "META", "GOOGL", "PLTR",

    # Consumer & Reopening
    "AMZN", "SBUX", "MGM", "UBER", "DIS",

    # Financials & Rates
    "JPM", "BAC", "GS", "WFC",

    # Energy & Inflation Hedges
    "XOM", "CVX", "ET",

    # Industrials & Cyclicals
    "GE", "BA", "FDX", "DAL",

    # Healthcare (Defensive)
    "JNJ", "UNH", "PFE",

    # High-Vol / Optionality
    "TSLA", "COIN"
]

test4 = [
    "AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "META", "PYPL", "PLTR", "SHOP", "ROKU", 
    "TSLA", "NFLX", "JNJ", "UNH", "PFE", "MRNA", "XOM", "CVX", "AMZN", "TGT", "WMT", 
    "SBUX", "JPM", "BAC", "GS"
]