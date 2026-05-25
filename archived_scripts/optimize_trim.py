import os
# import numpy as np
# import pandas as pd
from contextlib import redirect_stdout
from strategies import *
from skopt import gp_minimize
from skopt.space import Real
from skopt.utils import use_named_args


# Suppress backtest printouts
def silent_call(func, *args, **kwargs):
    with open(os.devnull, 'w') as f, redirect_stdout(f):
        return func(*args, **kwargs)


# Objective function for Bayesian optimization
def evaluate_backtest(params, symbols, monthly_budget=1500):
    """
    params ordering:
    [trim_perc, equity_thresh, put_thresh, call_thresh,
     strike_perc_dif, min_loss, max_profit, agg_cash_thresh]
    """
    (trim_perc, equity_thresh, put_thresh, call_thresh,
     strike_perc_dif, min_loss, max_profit,
     agg_cash_thresh) = params

    def run():
        strategy = OP2_SBA_strategy(
            symbols,
            trim_perc=trim_perc,
            equity_thresh=equity_thresh,
            put_thresh=put_thresh,
            call_thresh=call_thresh,
            strike_perc_dif=strike_perc_dif,
            min_loss=min_loss,
            max_profit=max_profit,
            agg_cash_thresh=agg_cash_thresh,
            monthly_budget=monthly_budget  # ✅ fixed, not optimized
        )

        strategy.run_backtest()
        return strategy.total_profit, strategy.total_roe

    return silent_call(run)


def optimize_bayesian(symbols, objective="profit", n_calls=40):
    
    # ✅ Full parameter search space (8 optimized params)
    space = [
        Real(0.01, 0.20, name="trim_perc"),
        Real(0.30, 0.60, name="equity_thresh"),
        Real(0.10, 0.50, name="put_thresh"),
        Real(0.50, 0.90, name="call_thresh"),
        Real(0.005, 0.05, name="strike_perc_dif"),
        Real(-5.0, -0.1, name="min_loss"),
        Real(0.1, 5.0, name="max_profit"),
        Real(0.0, 0.5, name="agg_cash_thresh")
    ]

    @use_named_args(space)
    def objective_func(**params):

        print("Starting backtest with params:", params)

        # ✅ Ordered list matching evaluate_backtest
        param_list = [
            params["trim_perc"],
            params["equity_thresh"],
            params["put_thresh"],
            params["call_thresh"],
            params["strike_perc_dif"],
            params["min_loss"],
            params["max_profit"],
            params["agg_cash_thresh"]
        ]

        profit, roe = evaluate_backtest(param_list, symbols)

        # ✅ Optimizer minimizes → negate
        score = -profit if objective == "profit" else -roe

        print(
            f"Tested: {params} "
            f"=> profit={profit:.2f}, roe={roe:.4f}"
        )

        return score

    print(f"\n🔍 Starting Bayesian Optimization for max {objective.upper()}...\n")

    result = gp_minimize(
        objective_func,
        dimensions=space,
        n_calls=n_calls,
        n_initial_points=10,
        acq_func="EI",
        random_state=42
    )

    best_params = dict(zip(
        ["trim_perc", "equity_thresh", "put_thresh", "call_thresh",
         "strike_perc_dif", "min_loss", "max_profit", "agg_cash_thresh"],
        result.x
    ))

    # ✅ Evaluate best result
    best_profit, best_roe = evaluate_backtest(result.x, symbols)

    print("\n===========================")
    print("     OPTIMIZATION DONE     ")
    print("===========================")
    for k, v in best_params.items():
        print(f"{k}: {v:.4f}")
    print(f"Profit at best: {best_profit:.2f}")
    print(f"ROE at best:    {best_roe:.4f}")

    return {
        "best_params": best_params,
        "best_profit": best_profit,
        "best_roe": best_roe,
        "objective": objective
    }


def main():
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

    results_profit = optimize_bayesian(
        working_symbols,
        objective="profit",
        n_calls=25
    )

    print(results_profit)


if __name__ == "__main__":
    main()
