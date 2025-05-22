"""Generate a barchart of cost per repository using matplotlib."""

import pandas as pd
import matplotlib.pyplot as plt


def make_chart(csv_file: str, output: str = "repo_barchart.png") -> None:
    """Create a bar chart from the analysis CSV."""

    df = pd.read_csv(csv_file)
    if df.empty:
        raise ValueError("No data found")

    df = df[df.cost_estimate > 0]

    # Scale cost to thousands of dollars for readability
    df["cost_k"] = df["cost_estimate"] / 1000.0

    # Sort repositories by cost so the most expensive appear at the top.
    df.sort_values("cost_k", ascending=False, inplace=True)

    y = range(len(df))
    height = 0.6

    # Use a dynamic height so that all repositories are visible even if there
    # are many of them.
    fig_height = max(4, 0.3 * len(df) + 2)
    fig, ax = plt.subplots(figsize=(10, fig_height))

    ax.barh(list(y), df["cost_k"], height,
            label="Cost ($k)", color="orange")

    ax.set_ylabel("Repository")
    ax.set_xlabel("Cost ($k)")
    ax.set_yticks(list(y))
    ax.set_yticklabels(df["repo"])
    ax.invert_yaxis()  # Highest values at the top
    ax.legend()
    plt.tight_layout()
    plt.savefig(output)
    print(f"Saved {output}")


def main() -> None:
    make_chart("first_day_analysis.csv")


if __name__ == '__main__':
    main()
