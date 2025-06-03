import os
import subprocess
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse
import argparse


def find_git_repos(base_dir: Path):
    """Yield all git repositories under base_dir."""
    for root, dirs, files in os.walk(base_dir):
        if '.git' in dirs:
            yield Path(root)
            dirs[:] = []  # don't recurse into subdirs of a repo


def collect_commits(repo: Path, since: datetime):
    """Return a list of (hash, timestamp, message) from repo since given time."""
    fmt = '%H\x1f%cI\x1f%s\x1e'
    cmd = ['git', 'log', '--since', since.isoformat(), f'--format={fmt}']
    result = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    data = result.stdout.strip('\x1e')
    commits = []
    if not data:
        return commits
    for record in data.split('\x1e'):
        parts = record.split('\x1f')
        if len(parts) != 3:
            continue
        h, ts, msg = parts
        commits.append((h, ts, msg))
    return commits


def repo_identifier(repo: Path) -> str:
    """Return a consistent identifier for the repository based on its remote."""
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return str(repo)
    url = result.stdout.strip()

    if url.startswith("git@github.com:"):
        url = url[len("git@github.com:") :]
    else:
        parsed = urlparse(url)
        if "github.com" in parsed.netloc:
            url = parsed.path.lstrip("/")
        else:
            return url

    if url.endswith(".git"):
        url = url[:-4]
    return url


def ensure_db(db_path: Path):
    conn = sqlite3.connect(db_path)
    conn.execute(
        'CREATE TABLE IF NOT EXISTS commits (repo TEXT, hash TEXT, timestamp TEXT, message TEXT, '
        'PRIMARY KEY (repo, hash))'
    )
    return conn


def main():
    parser = argparse.ArgumentParser(description='Collect recent git commits into SQLite DB.')
    parser.add_argument('directories', nargs='*', default=['~/devel'], help='Directories to scan')
    parser.add_argument('--db', default='git_commits.sqlite', help='SQLite database file')
    parser.add_argument('--days', type=int, default=14, help='How many days back to scan')
    args = parser.parse_args()

    since = datetime.now() - timedelta(days=args.days)
    db_path = Path(args.db)
    conn = ensure_db(db_path)

    for directory in args.directories:
        base = Path(directory).expanduser()
        for repo in find_git_repos(base):
            commits = collect_commits(repo, since)
            if not commits:
                continue
            repo_name = repo_identifier(repo)
            with conn:
                conn.executemany(
                    'INSERT OR IGNORE INTO commits (repo, hash, timestamp, message) VALUES (?, ?, ?, ?)',
                    ((repo_name, h, ts, msg) for h, ts, msg in commits)
                )
            print(f'Logged {len(commits)} commits from {repo_name}')


if __name__ == '__main__':
    main()
