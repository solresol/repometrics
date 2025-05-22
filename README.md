# repometrics
A tool for measuring repository productivity metrics

## Purpose

Repometrics analyzes Git repositories to measure how much code is written during the first day of a project. The tool:

1. Finds all Git repositories in a specified directory (default: ~/devel/)
2. For each repository:
   - Identifies the first commit timestamp
   - Finds the last commit within 24 hours of that first commit
   - Extracts a clean copy of the codebase at that point in time
   - Runs SLOCCount to analyze lines of code and estimated development cost

The results are compiled into a CSV file with each row containing:
- Repository name
- First commit date
- First commit hash
- Last commit hash within the first 24 hours
- Total lines of code
- Estimated development cost (using SLOCCount's COCOMO model)

## Requirements

- Python 3.6+
- Git
- SLOCCount (`apt install sloccount` on Ubuntu)

## Usage

```
python firstday.py
```

Results are written to `first_day_analysis.csv` in the current directory.

### Repository Skiplist

You can exclude specific repositories from the analysis by creating a `skiplist.txt` file in the same directory as the script. This is useful for repositories that have large initial imports that would skew the results.

Format of `skiplist.txt`:
- One repository name per line
- Lines starting with `#` are treated as comments
- Empty lines are ignored

Example:
```
# Repositories to skip
narrative-learning-nextgen  # Large initial import from another project
imported-project            # Contains pre-existing code
```

If no `skiplist.txt` file is found, a default skiplist containing known problematic repositories is used.

## Results

After generating `first_day_analysis.csv`, you can visualize the trends using `generate_trends.py`.
This script relies on external packages, so install them first:

```
pip install pandas matplotlib scikit-learn
```

Then run:

```
python generate_trends.py
```

The script generates two images in the repository root:

- `loc_trend.png` – first day lines-of-code over time
- `cost_trend.png` – estimated first day cost over time

The images are not committed to version control but will appear locally after running the script.
