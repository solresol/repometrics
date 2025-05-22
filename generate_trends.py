import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
from math import erf, sqrt


def _regression_stats(x: np.ndarray, y: np.ndarray) -> tuple:
    """Return intercept, slope, p-values for intercept and slope."""
    x = x.ravel()
    y = y.ravel()
    n = len(x)
    if n < 2:
        return float('nan'), float('nan'), float('nan'), float('nan')

    x_mean = x.mean()
    y_mean = y.mean()
    ssx = np.sum((x - x_mean) ** 2)
    slope = np.sum((x - x_mean) * (y - y_mean)) / ssx
    intercept = y_mean - slope * x_mean
    y_pred = intercept + slope * x
    residuals = y - y_pred
    sse = np.sum(residuals ** 2)
    se = sqrt(sse / (n - 2)) if n > 2 else float('inf')
    se_slope = se / sqrt(ssx)
    se_intercept = se * sqrt(1.0 / n + x_mean ** 2 / ssx)

    def _p_value(t: float) -> float:
        # Approximate two-sided p-value using the normal distribution.
        return 2 * (1 - (1 + erf(abs(t) / sqrt(2))) / 2)

    t_slope = slope / se_slope if se_slope != 0 else float('inf')
    t_intercept = intercept / se_intercept if se_intercept != 0 else float('inf')
    return intercept, slope, _p_value(t_intercept), _p_value(t_slope)


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
        icpt, slope, p_icpt, p_slope = _regression_stats(x, cost.values)
        info = f"slope={slope:.2f}, intercept={icpt:.2f}, p={p_slope:.3f}"
        plt.text(0.05, 0.95, info, transform=plt.gca().transAxes,
                 ha="left", va="top", fontsize=8,
                 bbox=dict(facecolor="white", alpha=0.5))
    plt.xlabel("Date")
    plt.ylabel("Cost Estimate")
    plt.title("Monthly Max First Day Cost Trend")
    plt.legend()
    plt.tight_layout()
    plt.savefig("cost_trend.png")

    # Plot log10 of cost with regression
    log_cost = np.log10(cost)
    plt.figure(figsize=(10, 4))
    plt.plot(dates, log_cost, "o-", label="Log10 Max Monthly Cost")
    if len(log_cost) >= 2:
        model = LinearRegression()
        model.fit(x, log_cost)
        trend = model.predict(x)
        icpt, slope, p_icpt, p_slope = _regression_stats(x, log_cost.values)
        # Extrapolate until log10(cost) == 6
        x_end = (6 - icpt) / slope
        x_line = np.linspace(0, x_end, 100).reshape(-1, 1)
        dates_line = dates[0] + pd.to_timedelta(x_line.ravel() * 30, unit="D")
        y_line = model.predict(x_line)
        plt.plot(dates_line, y_line, color="red", label="Exponential Extrapolation")
        info = f"slope={slope:.3f}, intercept={icpt:.3f}, p={p_slope:.3f}"
        plt.text(0.05, 0.95, info, transform=plt.gca().transAxes,
                 ha="left", va="top", fontsize=8,
                 bbox=dict(facecolor="white", alpha=0.5))
    plt.xlabel("Date")
    plt.ylabel("Log10 Cost Estimate")
    plt.title("Log Monthly Max First Day Cost Trend")
    plt.legend()
    plt.tight_layout()
    plt.savefig("log_cost_trend.png")


if __name__ == '__main__':
    main()

