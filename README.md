# Quant_Research_Project

A systematic equity and options trading research platform built from scratch in Python. Designed for point-in-time accurate backtesting, multi-factor alpha research, and live execution via the Interactive Brokers API.

> **Status:** Live execution infrastructure complete — strategies connected to Interactive Brokers paper trading API, executable on-demand via automated order generation scripts.

---

## Overview

Most backtesting tools treat strategy research and execution as separate concerns. This platform unifies them - from raw data ingestion and factor scoring, to strategy simulation, options overlay construction, and live brokerage execution — into a single modular Python system.

The platform was built to answer a specific research question: *can a composite scoring model combining quantitative fundamentals, qualitative LLM-derived signals, and market sentiment factors systematically identify mispriced equities and generate risk-adjusted alpha?*

Based on backtesting across multiple universes (2021–2025), the answer appears to be yes.

---

## Key Features

- **Point-in-time accurate backtesting** — explicitly controls for look-ahead bias via reporting lag adjustments, missing data handling, and dynamic universe membership
- **Multi-factor composite scoring** — integrates quantitative fundamental ratios, LLM-generated qualitative scores, and a market adjustment factor into a single ranked signal
- **Black-Scholes options overlay** — simulates option pricing to construct asymmetric short-side strategies (OTM puts on lowest-scoring names) with explicit position sizing controls
- **Modular architecture** — separable layers for data ingestion, scoring, strategy logic, and execution enable independent testing and iteration

---

## Architecture
quant_research_project/
├── fetch_data.py      # Data ingestion, cleaning, and normalization
├── stock.py           # Stock class — price history, fundamentals, factor inputs
├── portfolio.py       # Portfolio class — buy/sell/rebalance logic, performance tracking
├── options.py         # Options contract class — Black-Scholes pricing simulation
├── scoring.py         # Factor scoring — fundamental score, market adjustment factor, composite score
└── strategies.py      # Strategy classes — systematic trading logic built on top of infrastructure

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

The core insight driving the platform is that **lagging financial statements systematically diverge from real-time investor sentiment** — and that divergence is exploitable.

The composite score addresses this with three layers:
Fundamental Score  =  Quantitative Ratios  +  LLM Qualitative Factors
Market Adj. Factor =  Momentum  +  Volatility  +  Benchmark-Relative Performance
Adjusted Score     =  f(Fundamental Score, Market Adj. Factor)
Stocks are ranked by Adjusted Score each rebalancing period. Capital is allocated proportionally to highest-scoring names. The options overlay systematically targets lowest-scoring names with OTM puts — position sizing capped at 10% of held cash to bound compounded downside.

---

## Backtesting Results

Tested across three distinct universes over the 2021–2025 period. All tests started with approximately $56,000–$60,000 contributed capital.

| Test Universe | Stocks | Total Profit | Avg. Annual ROE | All-Time ROE |
|---|---|---|---|---|
| Large Diversified (78 stocks) | Broad U.S. + international, mixed sectors | $45,990 | 22.31% | 81.98% |
| High-Volatility Stress (20 stocks) | Meme stocks, speculative growth, high drawdown names | $152,612 | 86.08% | 318.40% |
| Factor-Based Momentum & Quality (25 stocks) | High-momentum, high-quality names | $43,727 | 20.12% | 73.97% |

> **Note:** Results reflect backtested performance and are not indicative of future returns. The high-volatility universe result is outsized due to the nature of the test universe — concentrated speculative names during a period of significant market recovery. The diversified universe result is the more conservative and realistic performance benchmark.

*Full output reports including P&L curves and portfolio vs. S&P 500 comparisons are available in the `/output` folder.*

---

## Strategy Evolution

The platform was developed iteratively across 5 strategy generations, each addressing a specific weakness of the prior:

1. **Base Strategy** — monthly rebalancing, allocating proportionally to fundamental score
2. **Market-Adjusted Strategy** — added market adjustment factor to correct for sentiment divergence from lagging fundamentals
3. **Options Overlay** — added Black-Scholes simulated OTM put positions on lowest-scoring names
4. **Position Sizing Controls** — capped options bets at 10% of held cash to prevent compounded losses wiping out equity gains
5. **Trimming Logic** — added dynamic trimming of fundamentally strong positions when market adjustment scores deteriorated, recycling capital into the short-side options pool

---

## Live Deployment

Core strategies are deployed live via the **Interactive Brokers API (TWS/IB Gateway)**. The execution layer translates backtested signals into automated order generation and portfolio rebalancing in a live brokerage environment.

---

## Tech Stack

- **Python** — Pandas, NumPy, SciPy, Matplotlib
- **LLM Integration** — Gemini API (qualitative factor scoring)
- **Brokerage** — Interactive Brokers API (live execution)
- **Options Pricing** — Black-Scholes simulation (custom implementation)

---

## Disclaimer

This project is for research and educational purposes. Backtested results do not guarantee future performance. Nothing here constitutes financial advice.
