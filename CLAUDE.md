# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Repometrics is a tool for analyzing Git repositories to measure code written in the first 24 hours of a project. It:

1. Finds all Git repositories in a specified directory (default: ~/devel)
2. Analyzes each repository to determine:
   - The first commit date and hash
   - The last commit within 24 hours of the first commit
   - The total lines of code written in that 24-hour period
   - An estimated development cost based on SLOCCount analysis
3. Exports results to a CSV file named 'first_day_analysis.csv'

## Development Commands

### Dependencies

The tool requires:
- Python 3
- SLOCCount (for code line counting)

To install SLOCCount on Debian/Ubuntu:
```
sudo apt install sloccount
```

### Running the Analysis

To run the analysis on all repositories in the default directory (~/devel):
```
python firstday.py
```

## Code Structure

The codebase is contained in a single Python script (`firstday.py`) with these main components:

1. **Repository Discovery** - The `find_git_repos` function scans a directory for Git repositories
2. **Git Operations**
   - `get_first_commit_info` - Retrieves the first commit hash and timestamp
   - `find_last_commit_within_24h` - Finds the last commit within 24 hours of the first
   - `extract_repo_at_commit` - Creates a clean copy of a repository at a specific commit
3. **Code Analysis** - The `run_sloccount` function analyzes code using the SLOCCount tool
4. **Main Processing** - The `analyze_repository` and `main` functions orchestrate the process

Results are written to `first_day_analysis.csv` with the following fields:
- repo: Repository name
- date: First commit date
- first_commit: First commit hash
- analysis_commit: Hash of the last commit within 24 hours
- total_lines: Total lines of code
- cost_estimate: Estimated development cost