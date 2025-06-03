import sqlite3
from datetime import datetime
from pathlib import Path
import argparse


def load_commits(db_path: Path):
    conn = sqlite3.connect(db_path)
    cursor = conn.execute('SELECT repo, timestamp, message FROM commits ORDER BY timestamp')
    for repo, ts, msg in cursor:
        yield repo, ts, msg
    conn.close()


def group_by_day(commits):
    day_map = {}
    for repo, ts, msg in commits:
        day = ts.split('T')[0]
        day_map.setdefault(day, []).append((ts, repo, msg))
    return day_map


def main():
    parser = argparse.ArgumentParser(description='Print timesheet from commit log DB.')
    parser.add_argument('--db', default='git_commits.sqlite', help='Database file')
    args = parser.parse_args()

    commits = list(load_commits(Path(args.db)))
    if not commits:
        print('No commits found.')
        return
    days = group_by_day(commits)
    for day in sorted(days):
        print(day)
        for ts, repo, msg in sorted(days[day]):
            time = ts.split('T')[1][:8]
            print(f'  {time} {repo} - {msg}')
        print()


if __name__ == '__main__':
    main()
