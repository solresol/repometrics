import csv
from typing import List, Tuple


def read_csv(filename: str) -> Tuple[List[str], List[int], List[float]]:
    repos: List[str] = []
    locs: List[int] = []
    costs: List[float] = []
    with open(filename, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            repos.append(row['repo'])
            locs.append(int(float(row['total_lines'])))
            costs.append(float(row['cost_estimate']))
    return repos, locs, costs


def make_svg(repos: List[str], locs: List[int], costs: List[float], output: str = 'repo_barchart.svg') -> None:
    if not repos:
        raise ValueError('No data found')

    cost_scaled = [c / 1000.0 for c in costs]
    max_loc = max(locs)
    max_cost = max(cost_scaled)

    height = 400
    bar_width = 20
    group_width = bar_width * 2
    gap = 10
    width = 40 + (group_width + gap) * len(repos) + 40

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height + 80}">']
    parts.append('<style>text{font-family:sans-serif;font-size:10px;}</style>')
    parts.append(f'<line x1="40" y1="{height}" x2="{width - 10}" y2="{height}" stroke="black"/>')
    parts.append(f'<line x1="40" y1="20" x2="40" y2="{height}" stroke="black"/>')

    for i, repo in enumerate(repos):
        group_x = 40 + gap + i * (group_width + gap)
        loc_h = int(height * locs[i] / max_loc) if max_loc else 0
        cost_h = int(height * cost_scaled[i] / max_cost) if max_cost else 0

        parts.append(f'<rect x="{group_x}" y="{height - loc_h}" width="{bar_width}" height="{loc_h}" fill="steelblue"/>')
        parts.append(f'<rect x="{group_x + bar_width}" y="{height - cost_h}" width="{bar_width}" height="{cost_h}" fill="orange"/>')

        label_x = group_x + bar_width
        parts.append(
            f'<text x="{label_x}" y="{height + 12}" text-anchor="middle" transform="rotate(45 {label_x},{height + 12})">{repo}</text>'
        )

    parts.append(f'<text x="{width/2}" y="{height + 40}" text-anchor="middle">Repositories</text>')
    parts.append(
        f'<text x="15" y="{height/2}" text-anchor="middle" transform="rotate(-90 15,{height/2})">LOC / Cost ($k)</text>'
    )
    parts.append('</svg>')

    with open(output, 'w') as f:
        f.write('\n'.join(parts))

    print(f'Saved {output}')


def main() -> None:
    repos, locs, costs = read_csv('first_day_analysis.csv')
    make_svg(repos, locs, costs)


if __name__ == '__main__':
    main()
