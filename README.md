# Quant_Research_Project

A systematic equity and options trading research platform built from scratch in Python. Designed for point-in-time accurate backtesting, multi-factor alpha research, and live execution via the Interactive Brokers API.

> **Status:** Live execution infrastructure complete - strategies connected to Interactive Brokers paper trading API, executable on-demand via automated order generation scripts.

---

## Overview

Most backtesting tools treat strategy research and execution as separate concerns. This platform unifies them - from raw data ingestion and factor scoring, to strategy simulation, and options overlay construction - into a single modular Python system.

The platform originated from a simple goal: systematically evaluate hundreds of companies at once to identify the strongest long-term investments based on fundamental quality - something that would otherwise require manual analysis at scale. 

As the research evolved, it became clear that fundamental analysis alone was insufficient - short-term market dynamics, investor sentiment, and volatility could work against even the strongest positions at the wrong moment. This led to the development of the Market Adjustment Factor, which layers market-aware context on top of fundamental scoring to improve timing and reduce risk. 

In the final research phase, the platform was extended further to explore whether options trading could generate short-term profits alongside the core long-term equity strategy - leading to the Black-Scholes options overlay and asymmetric put strategy on lowest-scoring names.

---

## Key Features

- **Point-in-time accurate backtesting** — explicitly controls for look-ahead bias via reporting lag adjustments, missing data handling, and dynamic universe membership
- **Multi-factor composite scoring** — integrates quantitative fundamental ratios, LLM-generated qualitative scores, and a market adjustment factor into a single ranked signal
- **Black-Scholes options overlay** — simulates option pricing to construct asymmetric short-side strategies (OTM puts on lowest-scoring names) with explicit position sizing controls
- **Modular architecture** — separable layers for data ingestion, scoring, strategy logic, and execution enable independent testing and iteration

---

## Primary Architecture
```text
quant_research_project/
├── fetch_data.py      # Data ingestion, cleaning, and normalization
├── stock.py           # Stock class — price history, fundamentals, factor inputs
├── portfolio.py       # Portfolio class — buy/sell/rebalance logic, performance tracking
├── options.py         # Options contract class — Black-Scholes pricing simulation
├── scoring.py         # Factor scoring — fundamental score, market adjustment factor, composite score
└── strategies.py      # Strategy classes — systematic trading logic built on top of infrastructure
```
### Module Breakdown

**`fetch_data.py`**
Handles all data retrieval, organization, and cleaning. Normalizes data across sources and manages point-in-time accuracy constraints to prevent look-ahead bias during backtesting.

**`stock.py`**
Core `Stock` class representing an individual equity. Stores price history, financial statement data, and computed factor inputs. Provides all methods needed to create and manage a stock position.

**`portfolio.py`**
Core `Portfolio` class managing the full collection of positions. Handles buying and selling equities and options contracts, tracks cash, monitors real-time portfolio performance, and computes P&L across the backtesting period.

**`options.py`**
`Options` class that creates and prices option contracts using Black-Scholes simulation. Supports long puts and calls, simulates entry and exit pricing, and integrates directly with the portfolio for execution.

**`scoring.py`**
The alpha engine. Computes three layered signals:
- **Fundamental Score** — quantitative ratios (ROE, D/E, P/E) combined with LLM-generated qualitative assessments (management quality, competitive positioning, business longevity)
- **Market Adjustment Factor** — momentum, volatility, and benchmark-relative performance overlay
- **Adjusted Total Score** — composite ranking signal driving portfolio allocation decisions

**`strategies.py`**
Strategy classes that wire together the full infrastructure — fetch_data, scoring, portfolio, and options — into complete systematic trading strategies. Designed to be extensible: build custom strategies by combining the underlying components.

---

## Scoring Model

The platform is built on the premise that fundamental value and market context must be evaluated together. The Fundamental Score estimates intrinsic company quality through quantitative ratios and LLM-derived qualitative assessments. The Market Adjustment Factor captures short-term market dynamics — momentum, volatility, and benchmark-relative performance — to avoid entering positions during periods of adverse sentiment or extreme volatility, even when fundamentals are strong. The Adjusted Total Score combines both, producing a ranking signal that is fundamentally grounded but market-aware.

The composite score addresses this with three layers:
```text
Fundamental Score  =  Quantitative Ratios  +  LLM Qualitative Factors
Market Adj. Factor =  Momentum  +  Volatility  +  Benchmark-Relative Performance
Adjusted Score     =  f(Fundamental Score, Market Adj. Factor)
```
Stocks are ranked by Adjusted Score each rebalancing period. Capital is allocated proportionally to highest-scoring names. The options overlay systematically targets lowest-scoring names with OTM puts — position sizing capped at 10% of held cash to bound compounded downside.

---

## Backtesting Results

Tested across three distinct universes over the 2021–2025 period. In all tests, a $1500 monthly budget was granted, however, total contributed capital is dependent on the quality of the stocks chosen. Larger amounts of capital are invested based off stronger scores generated. This led to roughly $56,000–$60,000 in contributed capital over 5 years across all tests.

| Test Universe | Stocks | Total Profit | Avg. Annual ROE | All-Time ROE |
|---|---|---|---|---|
| Large Diversified (78 stocks) | Broad U.S. + international, mixed sectors | $45,990 | 22.31% | 81.98% |
| High-Volatility Stress (20 stocks) | Meme stocks, speculative growth, high drawdown names | $152,612 | 86.08% | 318.40% |
| Factor-Based Momentum & Quality (25 stocks) | High-momentum, high-quality names | $43,727 | 20.12% | 73.97% |

> **Note:** Results reflect backtested performance and are not indicative of future returns. The high-volatility universe result is outsized due to the nature of the test universe — concentrated speculative names during a period of significant market recovery. The diversified universe result is the more conservative and realistic performance benchmark.

*Full output reports including P&L curves and portfolio vs. S&P 500 comparisons are available in 'Backtest Output Summary.pdf'.*

---

## Strategy Evolution

The platform was developed iteratively across 5 strategy generations, each addressing a specific weakness of the prior:

1. **Base Strategy** — monthly rebalancing, allocating proportionally to fundamental score
2. **Market-Adjusted Strategy** — added market adjustment factor to correct for sentiment divergence from lagging fundamentals
3. **Options Overlay** — added Black-Scholes simulated OTM put positions on lowest-scoring names
4. **Position Sizing Controls** — capped options bets at 10% of held cash to prevent compounded losses wiping out equity gains
5. **Trimming Logic** — added dynamic trimming of fundamentally strong positions when market adjustment scores deteriorated, recycling capital into the short-side options pool

## Tech Stack

- **Python** — Pandas, NumPy, SciPy, Matplotlib
- **LLM Integration** — Gemini API (qualitative factor scoring)
- **Brokerage** — Interactive Brokers API (live execution)
- **Options Pricing** — Black-Scholes simulation (custom implementation)

---

## Disclaimer

This project is for research and educational purposes. Backtested results do not guarantee future performance. Nothing here constitutes financial advice.
