import csv
from datetime import datetime
import argparse


def load_rows(csv_file: str):
    """Load rows from CSV and parse numeric fields."""
    rows = []
    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["date"] = datetime.strptime(row["date"], "%Y-%m-%d")
                row["total_lines"] = int(row["total_lines"])
                row["cost_estimate"] = float(row["cost_estimate"])
                rows.append(row)
            except Exception:
                continue
    return rows


def monthly_max(rows):
    """Return list of (YYYY-MM, row) for highest cost each month."""
    data = {}
    for row in rows:
        month = row["date"].strftime("%Y-%m")
        current = data.get(month)
        if current is None or row["cost_estimate"] > current["cost_estimate"]:
            data[month] = row
    return [(m, data[m]) for m in sorted(data.keys())]


def plot_scatter(data, output="loc_vs_cost.png"):
    """Create scatter plot of lines vs cost for the monthly data."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is required for plotting")
        return

    lines = [row["total_lines"] for _, row in data]
    cost = [row["cost_estimate"] for _, row in data]

    plt.figure(figsize=(6, 4))
    plt.scatter(lines, cost)
    plt.xlabel("Lines of Code")
    plt.ylabel("Cost Estimate")
    plt.title("Lines of Code vs Cost (Monthly Max)")
    plt.tight_layout()
    plt.savefig(output)
    print(f"Saved {output}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="List highest value repo for each month"
    )
    parser.add_argument(
        "--csv", default="first_day_analysis.csv", help="Input CSV file"
    )
    parser.add_argument(
        "--plot", action="store_true", help="Generate scatter plot"
    )
    args = parser.parse_args(argv)

    rows = load_rows(args.csv)
    if not rows:
        raise SystemExit("No data found")

    data = monthly_max(rows)
    for month, row in data:
        print(
            f"{month}: {row['repo']} - {row['total_lines']} lines, ${row['cost_estimate']:.2f}"
        )

    if args.plot:
        plot_scatter(data)


if __name__ == "__main__":
    main()
