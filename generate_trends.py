import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np


def main():
    df = pd.read_csv("first_day_analysis.csv", parse_dates=["date"])
    df.sort_values("date", inplace=True)

    # Consider data from 2021 onward only
    df = df[df["date"] >= pd.Timestamp("2021-01-01")]

    if df.empty:
        raise SystemExit("No data after 2021-01-01")

    # Aggregate by month taking the maximum cost within each month
    monthly = df.resample("ME", on="date").max()
    monthly = monthly.dropna(subset=["cost_estimate"])

    dates = monthly.index
    cost = monthly["cost_estimate"]
    x = np.arange(len(cost)).reshape(-1, 1)

    # Plot cost trend
    plt.figure(figsize=(10, 4))
    plt.plot(dates, cost, "o-", label="Max Monthly Cost")
    if len(cost) >= 2:
        model = LinearRegression()
        model.fit(x, cost)
        trend = model.predict(x)
        plt.plot(dates, trend, "--", label="Trend")
    plt.xlabel("Date")
    plt.ylabel("Cost Estimate")
    plt.title("Monthly Max First Day Cost Trend")
    plt.legend()
    plt.tight_layout()
    plt.savefig("cost_trend.png")

    # Plot log of cost with regression
    log_cost = np.log(cost)
    plt.figure(figsize=(10, 4))
    plt.plot(dates, log_cost, "o-", label="Log Max Monthly Cost")
    if len(log_cost) >= 2:
        model = LinearRegression()
        model.fit(x, log_cost)
        trend = model.predict(x)
        plt.plot(dates, trend, "--", label="Trend")
    plt.xlabel("Date")
    plt.ylabel("Log Cost Estimate")
    plt.title("Log Monthly Max First Day Cost Trend")
    plt.legend()
    plt.tight_layout()
    plt.savefig("log_cost_trend.png")


if __name__ == '__main__':
    main()

