# PURPOSE: Determine what combination of weighting factors maximizes ROE for multiple stocks
from archived_scripts.single_stock_sim import *
from scipy.optimize import minimize
import numpy as np
import os
from contextlib import redirect_stdout
import pandas as pd
import matplotlib.pyplot as plt

# Silent call to suppress print statements during optimization
def silent_call(func, *args, **kwargs):
    with open(os.devnull, 'w') as f, redirect_stdout(f):
        return func(*args, **kwargs)

# Objective: maximize final_roe (minimize -final_roe)
def objective(weights, ticker, monthly_budget):
    w = {
        "roe": weights[0],
        "de": weights[1],
        "pe": weights[2],
        "management_quality": weights[3],
        "competitive_edge": weights[4],
        "longevity": weights[5]
    }
    final_roe = silent_call(invest_stock, ticker, monthly_budget, w=w)
    return -final_roe

# Optimization per ticker
def optimize_weights(ticker, budget):
    cons = {"type": "eq", "fun": lambda x: np.sum(x) - 1}
    bounds = [(0.05, 0.5)] * 6  # diversification constraint
    x0 = np.array([1/6] * 6)

    print("---------------------------------------------------")
    print(f"Starting optimization for {ticker}...")
    print("---------------------------------------------------")

    result = minimize(objective, x0, args=(ticker, budget),
                      bounds=bounds, constraints=cons, method="SLSQP")

    if result.success:
        weights = {
            "roe": result.x[0],
            "de": result.x[1],
            "pe": result.x[2],
            "management_quality": result.x[3],
            "competitive_edge": result.x[4],
            "longevity": result.x[5],
            "expected_final_roe": -result.fun
        }
        print(f"✅ Optimization successful for {ticker}")
        return weights
    else:
        print(f"❌ Optimization failed for {ticker}: {result.message}")
        return None

# Run on a list of tickers and visualize results
def run_all_optimizations(symbols, monthly_budget):
    results = {}
    for ticker in symbols:
        res = optimize_weights(ticker, monthly_budget)
        if res:
            results[ticker] = res

    # Convert to DataFrame
    df = pd.DataFrame(results).T  # tickers as rows
    print("\nFinal Optimization Results:")
    print(df)

    # Plot: stacked bar chart of weights
    weight_cols = ["roe", "de", "pe", "management_quality", "competitive_edge", "longevity"]
    df[weight_cols].plot(kind="bar", stacked=True, figsize=(12, 6))
    plt.title("Optimal Weight Distribution by Stock")
    plt.ylabel("Weight")
    plt.xlabel("Ticker")
    plt.legend(title="Factor", bbox_to_anchor=(1.05, 1))
    plt.tight_layout()
    plt.show()

    return df

def main():
    symbols = ["AAPL", "MSFT", "UNH", "RIVN", "ADBE", "AMZN"]  # example list
    monthly_budget = 1500
    results_df = run_all_optimizations(symbols, monthly_budget)

    # Optionally save to file
    #results_df.to_excel("optimized_weights_summary.xlsx")
    #print("\nSaved results to optimized_weights_summary.xlsx")

if __name__ == "__main__":
    main()
