import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ta
import yfinance as yf

def get_forex_data(pairsymbol, start, end, interval="1d"):
    data = yf.download(pairsymbol, start=start, end=end, interval=interval)
    data.reset_index(inplace=True)
    #Handle missing/incomplete data
    data.dropna(inplace=True)
    return data

#Build backtesting engine
class BacktestingEngine:
    def __init__(self, data, original_portfolio_cash, position_size_limit, max_loss_threshold):
        self.data = data
        self.portfolio = {"cash": original_portfolio_cash}
        self.trades = []
        self.position_size_limit = position_size_limit * self.portfolio["cash"]
        self.max_loss_threshold = max_loss_threshold * self.portfolio["cash"]
        self.total_loss = 0

    def calculate_moving_average(self, window):
        return self.data["Close"].rolling(window=window).mean()
    
    def execute_trades(self):
        short_window = 20
        long_window = 50

        #Calculate moving averages and store them in data frame
        short_moving_averages = self.calculate_moving_average(short_window)
        long_moving_averages = self.calculate_moving_average(long_window)
        value = self.portfolio["cash"]

        for i in range(len(self.data)):
            price = self.data["Close"].iloc[i]
            max_position = (self.portfolio["cash"]/price)
            position_size = min(max_position, self.position_size_limit/price)
            if ((short_moving_averages.iloc[i] > long_moving_averages.iloc[i]) and (len(self.trades) == 0 or self.trades[-1][0] == "sell")):
                #Buy
                self.portfolio["cash"] -= position_size * price
                self.trades.append(("buy", position_size, price))
            elif ((short_moving_averages.iloc[i] < long_moving_averages.iloc[i]) and (len(self.trades) == 0 or self.trades[-1][0] == "buy")):
                #Sell
                self.portfolio["cash"] += position_size * price
                self.trades.append(("sell", position_size, price))
           
            #Update value and loss calculation to determine if trading can continue
            if len(self.trades) != 0 and self.trades[-1][0] == "buy":
                value+=self.trades[-1][1]*self.trades[-1][2]
            elif len(self.trades) != 0 and self.trades[-1][0] == "sell":
                value-=self.trades[-1][1]*self.trades[-1][2]
            
            loss = self.portfolio["cash"] - value
            self.total_loss += loss

            if self.total_loss > self.max_loss_threshold:
                print("Total losses is in excess so trading has stopped")
                return Exception()

def evaluate_performance(trades):
    profit_loss = sum([trades[i][1] * (trades[i+1][2]-trades[i][2]) for i in range(0, len(trades)-1, 2)])
    total_trades = len(trades)
    profitable_trades = sum([1 for i in range(0, len(trades)-1, 2) if trades[i+1][2] > trades[i][2]])
    percent_profitable_trades = (profitable_trades/total_trades) * 100

    print(f"Total Profit/Loss: {profit_loss}")
    print(f"Total Trades: {total_trades//2}")
    print(f"Winning Percentage: {percent_profitable_trades}%")

def plot_equity_curve(original_portfolio_cash, trades):
    equity = [original_portfolio_cash]
    for trade in trades:
        if trade[0] == "buy":
            equity.append(equity[-1] - (trade[1]*trade[2]))
        elif trade[0] == "sell":
            equity.append(equity[-1] + (trade[1]*trade[2]))
    plt.plot(equity)
    plt.title("Equity Curve")
    plt.xlabel("Trades")
    plt.ylabel("Account Balance")
    plt.show()
            
def main():
    #Fetch historical price data
    forex_usd_jpy = get_forex_data("USDJPY=X", "2021-09-01", "2024-09-01", "1d")
    original_portfolio_cash = 100000

    engine = BacktestingEngine(forex_usd_jpy, original_portfolio_cash, 0.05, 0.10)
    engine.execute_trades()
    evaluate_performance(engine.trades)
    plot_equity_curve(original_portfolio_cash, engine.trades)

if __name__ == "__main__":
    main()