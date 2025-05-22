#!/usr/bin/env python3
"""Simple cost estimator for repository LOC data.

This script reads `first_day_analysis.csv` and recalculates the
`cost_estimate` column using a lightweight COCOMO-like formula.
It does not require any external dependencies.
"""

import csv
from pathlib import Path
from typing import Dict

# Language productivity multipliers. Values < 1 reduce cost, > 1 increase cost.
LANGUAGE_FACTOR: Dict[str, float] = {
    "python": 0.7,
    "golang": 0.9,
    "haskell": 0.8,
    "pascal": 1.1,
    "c": 1.2,
}

# Constants for the COCOMO-style estimation
PM_A = 2.5  # coefficient
PM_B = 1.05  # exponent
PERSON_MONTH_COST = 56286  # dollars per person-month


def estimate_cost(lines: int, language: str) -> float:
    """Return a cost estimate for the given LOC and language."""
    if lines <= 0:
        return 0.0
    ksloc = lines / 1000.0
    person_months = PM_A * (ksloc ** PM_B)
    base_cost = person_months * PERSON_MONTH_COST
    factor = LANGUAGE_FACTOR.get(language.lower(), 1.0)
    return base_cost * factor


def update_csv(path: Path) -> None:
    """Recompute cost estimates in the CSV in place."""
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    for row in rows:
        try:
            lines = int(row.get("total_lines", 0))
        except ValueError:
            row["cost_estimate"] = ""
            continue
        language = row.get("language", "")
        cost = estimate_cost(lines, language)
        row["cost_estimate"] = f"{cost:.2f}"

    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    update_csv(Path("first_day_analysis.csv"))
