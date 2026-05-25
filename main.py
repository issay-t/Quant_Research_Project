from strategies import *
from testing_pool import *

def main():
    strategy = OP2_SBA_strategy(working_symbols)
    strategy.run_backtest()
    profit = strategy.total_profit
    roe = strategy.total_roe
    print(profit)
    print(roe)

if __name__ == "__main__":
    main()