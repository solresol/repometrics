"""Generate a barchart of LOC and cost per repository using matplotlib."""

import pandas as pd
import matplotlib.pyplot as plt


def make_chart(csv_file: str, output: str = "repo_barchart.png") -> None:
    """Create a bar chart from the analysis CSV."""

    df = pd.read_csv(csv_file)
    if df.empty:
        raise ValueError("No data found")

    # Scale cost to thousands of dollars for readability
    df["cost_k"] = df["cost_estimate"] / 1000.0

    x = range(len(df))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar([i - width / 2 for i in x], df["total_lines"], width, label="LOC", color="steelblue")
    ax.bar([i + width / 2 for i in x], df["cost_k"], width, label="Cost ($k)", color="orange")

    ax.set_xlabel("Repository")
    ax.set_ylabel("LOC / Cost ($k)")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["repo"], rotation=45, ha="right")
    ax.legend()
    plt.tight_layout()
    plt.savefig(output)
    print(f"Saved {output}")


def main() -> None:
    make_chart("first_day_analysis.csv")


if __name__ == '__main__':
    main()
