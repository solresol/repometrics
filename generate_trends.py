import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np


def main():
    df = pd.read_csv('first_day_analysis.csv', parse_dates=['date'])
    df.sort_values('date', inplace=True)

    dates = df['date']
    x = np.arange(len(df)).reshape(-1, 1)

    # Plot lines of code
    plt.figure(figsize=(10, 4))
    plt.plot(dates, df['total_lines'], 'o-', label='Lines of Code')
    if len(df) >= 2:
        model = LinearRegression()
        model.fit(x, df['total_lines'])
        trend = model.predict(x)
        plt.plot(dates, trend, '--', label='Trend')
    plt.xlabel('Date')
    plt.ylabel('Total Lines')
    plt.title('First Day LOC Trend')
    plt.legend()
    plt.tight_layout()
    plt.savefig('loc_trend.png')

    # Plot cost
    plt.figure(figsize=(10, 4))
    plt.plot(dates, df['cost_estimate'], 'o-', label='Cost Estimate')
    if len(df) >= 2:
        model = LinearRegression()
        model.fit(x, df['cost_estimate'])
        trend = model.predict(x)
        plt.plot(dates, trend, '--', label='Trend')
    plt.xlabel('Date')
    plt.ylabel('Cost Estimate')
    plt.title('First Day Cost Trend')
    plt.legend()
    plt.tight_layout()
    plt.savefig('cost_trend.png')


if __name__ == '__main__':
    main()

