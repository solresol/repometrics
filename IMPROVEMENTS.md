# IMPROVEMENTS.md

*Analysis date: 2026-07-11*

Repometrics is a small collection of Python scripts that measure "first-day productivity" across all Git repos under `~/devel/`: `firstday.py` extracts each repo's first 24 hours of commits and runs SLOCCount, `cost_estimator.py` applies a COCOMO-like cost model, and `generate_trends.py` / `repo_barchart.py` / `monthly_top_repo.py` produce trend charts. Last substantive commit was June 2025 (PR #17, "Identify repos by remote"); the working tree is currently dirty in ways that suggest an abandoned or half-reverted piece of work.

## Bugs & Fixes

1. **Resolve the staged deletions of `commit_logger.py` and `daily_timesheet.py`.** `git status` shows both files staged for deletion (`D`), yet they were added only two commits ago (PR #16, "commit logging and timesheet scripts") and the README still documents them. Either commit the deletion *and* remove their README section, or restore them. Right now the repo and its docs disagree.
2. **README contradicts reality on chart images.** README says "The images are not committed to version control" but `cost_trend.png`, `loc_trend.png`, `log_cost_trend.png`, and `repo_barchart.png` are all tracked (and there are "Auto-update trend charts" commits). `cost_trend.png` is also currently modified but uncommitted, and `log_cost_trend_corrected.png` is untracked — decide whether that corrected chart supersedes `log_cost_trend.png`, wire it into whatever generates it, and commit or delete it.
3. **`generate_trends.py` p-value approximation is wrong for small n.** `_regression_stats` uses a normal approximation for t-statistics, but monthly aggregation gives small samples where this materially understates p-values. `scipy` is already a declared dependency — use `scipy.stats.linregress` and delete the hand-rolled math.
4. **Cost model duplication/inconsistency.** `firstday.py` records SLOCCount's COCOMO estimate while `cost_estimator.py` recomputes with different constants (`PM_A=2.5`, `PERSON_MONTH_COST=56286`) and an ad-hoc `LANGUAGE_FACTOR` table. Two sources of truth for `cost_estimate`; pick one and document the assumptions (that per-month cost figure is uncited).
5. **`firstday.py` only finds repos one level deep.** `find_git_repos` iterates `base_path.iterdir()`; nested repos (e.g. `devel/inventory/...`) are silently missed. Use `Path.rglob('.git')` with a depth cap, or at least document the limitation.

## Improvements

- **Strip the DEBUG print noise from `firstday.py`.** The 523-line script is littered with `print(f"  DEBUG: ...")` calls. Replace with the `logging` module and a `--verbose` flag.
- **SLOCCount is dead software (last release 2004) and Ubuntu-only per the README.** Consider `scc`, `tokei`, or `cloc` — `scc` even has a built-in COCOMO estimate, which would let you delete `cost_estimator.py` entirely.
- **Unify the three plotting scripts.** `generate_trends.py`, `repo_barchart.py`, and `monthly_top_repo.py` each re-read `first_day_analysis.csv` with their own boilerplate; a shared loader (date parsing, 2021 cutoff, skiplist handling) would remove drift like the hardcoded `pd.Timestamp("2021-01-01")` cutoff — make that a CLI flag.
- **Hardcoded CSV filename everywhere.** `firstday.py` accepts `-o` but every downstream script hardcodes `first_day_analysis.csv`; thread the path through as an argument.

## Testing

- There are **no tests at all**. The highest-value targets are pure functions that need no fixtures: `cost_estimator.estimate_cost`, `generate_trends._regression_stats` (or its scipy replacement), and skiplist parsing in `firstday.py`. Add `pytest` as a dev dependency (`uv add --dev pytest`) and a handful of unit tests plus one integration test that runs `firstday.py` against a synthetic repo created with `git init` in a tmpdir.
- Add a GitHub Actions workflow to run the tests; the repo already assumes GHA exists (`sweep.yaml` has `gha_enabled: True`) but none is present.

## Documentation

- `pyproject.toml` still says `description = "Add your description here"` — fill it in.
- README's install instruction `uv pip install pandas matplotlib scikit-learn` is obsolete: dependencies are already in `pyproject.toml`/`uv.lock`, so `uv run generate_trends.py` just works. Delete that paragraph.
- README mentions Python 3.6+ but `pyproject.toml` requires >=3.11; align them.
- `AGENTS.md` and `CLAUDE.md` both exist — check they don't diverge (keep one, symlink or reference the other).

## Security

- No committed secrets found. `udara.csv` and `first_day_analysis.csv` expose private repo names and dates — fine for a private repo, worth a thought if this ever goes public (repo appears to be on GitHub under `solresol`).

## Housekeeping / Modernization

- **Good news: already on uv** (`pyproject.toml` + `uv.lock`, no `requirements.txt`) — keep it that way; run everything via `uv run script.py`.
- `uvbootstrap.py` is a 1-line file — likely vestigial; delete it or explain it.
- `sweep.yaml` configures Sweep AI, a service that shut down its bot product; if unused, delete it.
- Commit or clean the dirty working tree (see Bugs #1–2) so `git status` is clean — several stale states have been sitting since June 2025.

## Quick Wins

1. Decide fate of `commit_logger.py` / `daily_timesheet.py` and commit (5 min).
2. Commit or remove `log_cost_trend_corrected.png` and the modified `cost_trend.png` (5 min).
3. Fix `pyproject.toml` description and README Python-version/install-instruction rot (10 min).
4. Swap `_regression_stats` for `scipy.stats.linregress` (15 min).
5. Delete DEBUG prints from `firstday.py` (15 min).
