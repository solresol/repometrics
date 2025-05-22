#!/usr/bin/env python

import os
import subprocess
import tempfile
import shutil
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path
import argparse


class FirstDayAnalysisError(Exception):
    """Custom exception for analysis errors"""
    pass


def find_git_repos(base_dir):
    """Find all git repositories in the base directory"""
    repos = []
    base_path = Path(base_dir).expanduser()
    
    for item in base_path.iterdir():
        if item.is_dir() and (item / '.git').exists():
            repos.append(item)
    
    return repos


def get_first_commit_info(repo_path):
    """Get the hash and timestamp of the first commit"""
    try:
        print(f"  DEBUG: Getting first commit info for {repo_path}")
        
        # First check if the repository has any commits at all
        has_commits = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD'], 
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        print(f"  DEBUG: Number of commits: {has_commits.stdout.strip() if has_commits.returncode == 0 else 'unknown'}")
        
        if has_commits.returncode != 0 or not has_commits.stdout.strip() or has_commits.stdout.strip() == '0':
            print(f"  DEBUG: Repository appears to have no commits")
            raise FirstDayAnalysisError(f"No commits found in {repo_path}")
        
        # Get the first commit info
        result = subprocess.run(
            ['git', 'log', '--reverse', '--format=%H %ci', '--max-count=1'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        
        if not result.stdout.strip():
            print(f"  DEBUG: No output from git log command")
            raise FirstDayAnalysisError(f"No commits found in {repo_path}")
        
        line = result.stdout.strip()
        print(f"  DEBUG: First commit info: {line}")
        
        parts = line.split(' ', 1)
        if len(parts) < 2:
            print(f"  DEBUG: Unexpected git log format: {line}")
            raise FirstDayAnalysisError(f"Unexpected git log format: {line}")
            
        commit_hash = parts[0]
        timestamp_str = parts[1]
        
        # Parse the timestamp (format: 2023-01-15 14:30:45 +0000)
        print(f"  DEBUG: Parsing timestamp: {timestamp_str}")
        timestamp = datetime.fromisoformat(timestamp_str.replace(' +', '+').replace(' -', '-'))
        print(f"  DEBUG: Parsed timestamp: {timestamp}")
        
        return commit_hash, timestamp
        
    except subprocess.CalledProcessError as e:
        print(f"  DEBUG: Git command failed: {e}")
        print(f"  DEBUG: Error output: {e.stderr}")
        raise FirstDayAnalysisError(f"Git command failed in {repo_path}: {e}")


def find_last_commit_within_24h(repo_path, first_commit_time):
    """Find the last commit within 24 hours of the first commit"""
    end_time = first_commit_time + timedelta(hours=24)
    
    try:
        # Get all commits from first commit onwards, ordered by time
        result = subprocess.run([
            'git', 'log', 
            '--since', first_commit_time.isoformat(),
            '--until', end_time.isoformat(),
            '--format=%H %ci',
            '--reverse'
        ], cwd=repo_path, capture_output=True, text=True, check=True)
        
        if not result.stdout.strip():
            raise FirstDayAnalysisError(f"No commits found in first 24 hours for {repo_path}")
        
        lines = result.stdout.strip().split('\n')
        last_line = lines[-1]
        last_commit_hash = last_line.split(' ', 1)[0]
        
        return last_commit_hash
        
    except subprocess.CalledProcessError as e:
        raise FirstDayAnalysisError(f"Git command failed in {repo_path}: {e}")


def extract_repo_at_commit(repo_path, commit_hash, extract_dir):
    """Extract repository contents at specific commit using git archive"""
    repo_name = repo_path.name
    target_dir = extract_dir / f"{repo_name}_{commit_hash[:8]}"
    target_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"  DEBUG: Extracting {repo_path.name} at commit {commit_hash[:8]} to {target_dir}")
        
        # Check if the commit exists
        commit_check = subprocess.run(
            ['git', 'cat-file', '-t', commit_hash],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if commit_check.returncode != 0 or 'commit' not in commit_check.stdout:
            print(f"  DEBUG: Commit verification failed: {commit_check.stderr}")
        
        # Use git archive to get clean copy
        print(f"  DEBUG: Running git archive command for {commit_hash}")
        archive_cmd = ['git', 'archive', '--format=tar', commit_hash]
        print(f"  DEBUG: Command: {' '.join(archive_cmd)}")
        
        archive_process = subprocess.run(
            archive_cmd,
            cwd=repo_path, 
            capture_output=True, 
            check=True
        )
        
        print(f"  DEBUG: Archive size: {len(archive_process.stdout)} bytes")
        
        if len(archive_process.stdout) == 0:
            print(f"  DEBUG: WARNING - Archive is empty!")
            
            # Get list of files in that commit
            file_list = subprocess.run(
                ['git', 'ls-tree', '-r', '--name-only', commit_hash],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            print(f"  DEBUG: Files in commit: {file_list.stdout[:500]}")
        
        # Extract using tar
        print(f"  DEBUG: Extracting archive to {target_dir}")
        tar_process = subprocess.run(
            ['tar', '-xf', '-', '-C', str(target_dir)],
            input=archive_process.stdout,
            capture_output=True,
            check=False  # Don't raise exception to capture error
        )
        
        if tar_process.returncode != 0:
            print(f"  DEBUG: Tar extraction error (code {tar_process.returncode}): {tar_process.stderr}")
            
            # Try alternative approach - save to file first
            print(f"  DEBUG: Trying alternative extraction approach")
            tar_path = target_dir / f"{repo_name}.tar"
            with open(tar_path, 'wb') as f:
                f.write(archive_process.stdout)
            
            subprocess.run(
                ['tar', '-xf', str(tar_path), '-C', str(target_dir)],
                capture_output=True,
                check=True
            )
            
            # Remove tar file after extraction
            tar_path.unlink()
        
        # Check if anything was extracted
        files = list(target_dir.glob('**/*'))
        files_count = len(files)
        print(f"  DEBUG: Extracted {files_count} files/directories to {target_dir}")
        
        # Print first few files for debugging
        if files:
            print("  DEBUG: First few extracted files:")
            for f in files[:5]:
                if f.is_file():
                    print(f"    - {f.relative_to(target_dir)} ({f.stat().st_size} bytes)")
                else:
                    print(f"    - {f.relative_to(target_dir)}/ (dir)")
            if len(files) > 5:
                print(f"    ... and {len(files)-5} more")
        else:
            print("  DEBUG: No files were extracted!")
        
        return target_dir
        
    except subprocess.CalledProcessError as e:
        print(f"  DEBUG: Extraction failed: {e}")
        print(f"  DEBUG: Error output: {e.stderr}")
        raise FirstDayAnalysisError(f"Failed to extract {repo_path} at {commit_hash}: {e}")


def run_sloccount(directory):
    """Run sloccount on directory and parse results"""
    try:
        # List directory contents for debugging
        print(f"  DEBUG: Directory contents of {directory}:")
        dir_list = list(Path(directory).glob('**/*'))[:20]  # Limit to first 20 entries
        for item in dir_list:
            if item.is_file():
                print(f"    - {item.relative_to(directory)} ({item.stat().st_size} bytes)")
            else:
                print(f"    - {item.relative_to(directory)}/ (dir)")
        if len(list(Path(directory).glob('**/*'))) > 20:
            print(f"    ... and more files (showing first 20 only)")
        
        # Count files of different types for debugging
        source_extensions = ['.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.go', '.rs', '.ts', '.rb', '.php']
        source_files = sum(1 for ext in source_extensions for _ in Path(directory).glob(f'**/*{ext}'))
        print(f"  DEBUG: Found {source_files} potential source files")
        
        # Try running find command to verify directory is accessible
        try:
            find_cmd = f"find {str(directory)} -type f -name '*.*' | head -10"
            find_result = subprocess.run(
                find_cmd,
                shell=True, capture_output=True, text=True
            )
            print(f"  DEBUG: Find command result: {find_result.stdout[:200]}")
        except Exception as e:
            print(f"  DEBUG: Find command failed: {e}")
        
        # Run sloccount with verbose output
        print(f"  DEBUG: Running sloccount on {directory}")
        
        # Run sloccount with explicit --follow options to ensure it follows symlinks and counts all files
        # Also run with verbose output for debugging
        result = subprocess.run([
            'sloccount', '--duplicates', '--wide', '--details', '--follow', str(directory)
        ], capture_output=True, text=True, check=True)
        
        output = result.stdout
        print(f"  DEBUG: sloccount raw output (first 500 chars): {output[:500]}")
        print(f"  DEBUG: sloccount output length: {len(output)} chars")
        
        # Also print the end of the output which typically has the summary
        if len(output) > 1000:
            print(f"  DEBUG: sloccount last 500 chars: {output[-500:]}")
        
        # Alternative approach: Sum up the lines directly from sloccount output
        total_lines = 0
        cost_estimate = 0.0
        
        # Extract individual file results directly from the detailed output
        file_results = re.findall(r'^(\d+)\s+\w+\s+\w+\s+', output, re.MULTILINE)
        if file_results:
            print(f"  DEBUG: Found {len(file_results)} files with line counts in sloccount output")
            for count in file_results:
                total_lines += int(count)
            print(f"  DEBUG: Calculated total lines by summing individual files: {total_lines}")
            
            # Estimate cost using COCOMO model (similar to how sloccount does it)
            if total_lines > 0:
                # Simple COCOMO estimation: person-months = 2.4 * (KSLOC^1.05)
                # At $56,286 per person-month (sloccount's default rate)
                ksloc = total_lines / 1000
                person_months = 2.4 * (ksloc ** 1.05)
                cost_estimate = person_months * 56286
                print(f"  DEBUG: Calculated cost estimate: ${cost_estimate:,.2f}")
        else:
            # Try with the original regex pattern, but fix the escape sequences
            lines_match = re.search(r'Total Physical Source Lines of Code [(]SLOC[)]\s*=\s*([0-9,]+)', output)
            if lines_match:
                total_lines = int(lines_match.group(1).replace(',', ''))
                print(f"  DEBUG: Found total lines with fixed regex: {total_lines}")
            
            # Try to find cost estimate with fixed regex
            cost_match = re.search(r'Total Estimated Cost to Develop\s*=\s*\$\s*([0-9,]+)', output)
            if cost_match:
                cost_estimate = float(cost_match.group(1).replace(',', ''))
                print(f"  DEBUG: Found cost estimate with fixed regex: ${cost_estimate:,.2f}")
        
        # If we still have zero lines but found source files, something's wrong
        if total_lines == 0 and source_files > 0:
            print(f"  DEBUG: WARNING: Found {source_files} source files but calculated 0 lines of code")
            
        return total_lines, cost_estimate
        
    except subprocess.CalledProcessError as e:
        print(f"  DEBUG: sloccount failed with error: {e}")
        print(f"  DEBUG: stderr: {e.stderr}")
        raise FirstDayAnalysisError(f"sloccount failed on {directory}: {e}")
    except FileNotFoundError:
        raise FirstDayAnalysisError("sloccount not found - please install it (apt install sloccount)")


def analyze_repository(repo_path, extract_base_dir):
    """Analyze a single repository and return results"""
    print(f"Analyzing {repo_path.name}...")
    
    try:
        # Get first commit info
        first_commit_hash, first_commit_time = get_first_commit_info(repo_path)
        print(f"  First commit: {first_commit_hash[:8]} at {first_commit_time}")
        
        # Find last commit within 24 hours
        last_commit_hash = find_last_commit_within_24h(repo_path, first_commit_time)
        print(f"  Last commit in first 24h: {last_commit_hash[:8]}")
        
        # Try a direct check of what files exist at that commit
        try:
            files_at_commit = subprocess.run(
                ['git', 'ls-tree', '-r', '--name-only', last_commit_hash],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            file_count = len(files_at_commit.stdout.strip().split('\n')) if files_at_commit.stdout.strip() else 0
            print(f"  DEBUG: Found {file_count} files at commit {last_commit_hash[:8]}")
            if file_count == 0:
                print(f"  DEBUG: No files found in commit. This might be an empty commit.")
                return {
                    'repo': repo_path.name,
                    'date': first_commit_time.strftime('%Y-%m-%d'),
                    'first_commit': first_commit_hash,
                    'analysis_commit': last_commit_hash,
                    'total_lines': 0,
                    'cost_estimate': 0.0
                }
        except subprocess.CalledProcessError:
            print(f"  DEBUG: Failed to get file list at commit")
        
        # Extract repository at that commit
        extracted_dir = extract_repo_at_commit(repo_path, last_commit_hash, extract_base_dir)
        print(f"  Extracted to: {extracted_dir}")
        
        # Check if extraction was successful
        extracted_files = list(extracted_dir.glob('**/*'))
        if not extracted_files:
            print(f"  DEBUG: Extraction appears to have failed - no files found")
            print(f"  DEBUG: Trying a different method")
            
            # Alternative approach: Use git show to check out each file directly
            try:
                files_to_checkout = files_at_commit.stdout.strip().split('\n') if files_at_commit.stdout.strip() else []
                for file_path in files_to_checkout[:20]:  # Limit to first 20 files for debugging
                    if not file_path.strip():
                        continue
                        
                    target_file = extracted_dir / file_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Get file content at that commit
                    try:
                        content = subprocess.run(
                            ['git', 'show', f"{last_commit_hash}:{file_path}"],
                            cwd=repo_path,
                            capture_output=True,
                            check=True
                        )
                        
                        # Write content to file
                        with open(target_file, 'wb') as f:
                            f.write(content.stdout)
                            
                        print(f"  DEBUG: Manually extracted {file_path}")
                    except subprocess.CalledProcessError:
                        print(f"  DEBUG: Failed to extract {file_path}")
            except Exception as e:
                print(f"  DEBUG: Alternative extraction failed: {e}")
        
        # Run sloccount
        total_lines, cost_estimate = run_sloccount(extracted_dir)
        print(f"  Results: {total_lines} lines, ${cost_estimate:,.2f}")
        
        return {
            'repo': repo_path.name,
            'date': first_commit_time.strftime('%Y-%m-%d'),
            'first_commit': first_commit_hash,
            'analysis_commit': last_commit_hash,
            'total_lines': total_lines,
            'cost_estimate': cost_estimate
        }
        
    except FirstDayAnalysisError as e:
        print(f"  ERROR: {e}")
        return None


def load_skiplist(skiplist_path=None):
    """Load repositories to skip from a config file or use defaults"""
    # Default skiplist
    default_skiplist = [
        "narrative-learning-nextgen",  # Large initial commit from another repo
    ]
    
    if skiplist_path and Path(skiplist_path).exists():
        try:
            with open(skiplist_path, 'r') as f:
                # Each line is a repo name, ignore empty lines and comments
                skiplist = [line.strip() for line in f.readlines() 
                           if line.strip() and not line.strip().startswith('#')]
            print(f"Loaded {len(skiplist)} repositories to skip from {skiplist_path}")
            return skiplist
        except Exception as e:
            print(f"Error loading skiplist file: {e}")
            print(f"Using default skiplist instead")
            return default_skiplist
    else:
        return default_skiplist


def main(argv=None):
    """Main analysis function"""
    parser = argparse.ArgumentParser(
        description="Analyze first day commits of git repositories"
    )
    parser.add_argument(
        "-d",
        "--directory",
        default="~/devel",
        help="Directory containing repositories (default: ~/devel)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="first_day_analysis.csv",
        help="Path for the output CSV file (default: first_day_analysis.csv)",
    )
    args = parser.parse_args(argv)

    devel_dir = args.directory
    output_csv = Path(args.output)
    
    # Configuration
    skiplist_path = Path.cwd() / 'skiplist.txt'
    skiplist = load_skiplist(skiplist_path)
    
    if skiplist:
        print(f"Skipping the following repositories: {', '.join(skiplist)}")
    else:
        print("No repositories will be skipped")
    
    # Check for sloccount installation first
    try:
        version_check = subprocess.run(
            ['sloccount', '--version'],
            capture_output=True,
            text=True
        )
        print(f"DEBUG: SLOCCount version info: {version_check.stdout.strip()}")
    except FileNotFoundError:
        print("ERROR: sloccount not found - please install it (apt install sloccount)")
        print("DEBUG: Checking sloccount path:")
        path_check = subprocess.run(['which', 'sloccount'], capture_output=True, text=True)
        print(f"DEBUG: which sloccount result: {path_check.stdout or 'not found'}")
        return
    
    # Create temporary directory for extractions
    with tempfile.TemporaryDirectory(prefix='sloccount_analysis_') as temp_dir:
        temp_path = Path(temp_dir)
        extract_dir = temp_path / 'extracted_repos'
        extract_dir.mkdir()
        
        print(f"Working directory: {temp_dir}")
        print(f"Looking for repositories in: {Path(devel_dir).expanduser()}")
        
        # Find all git repositories
        all_repos = find_git_repos(devel_dir)
        print(f"Found {len(all_repos)} repositories total")
        
        # Filter out repositories in the skiplist
        repos = [repo for repo in all_repos if repo.name not in skiplist]
        print(f"Analyzing {len(repos)} repositories (skipped {len(all_repos) - len(repos)})")
        
        if not repos:
            print("No git repositories to analyze after applying skiplist!")
            return
        
        # Analyze each repository
        results = []
        for repo_path in repos:
            result = analyze_repository(repo_path, extract_dir)
            if result:
                results.append(result)
        
        # Write results to CSV
        if results:
            csv_path = output_csv if output_csv.is_absolute() else Path.cwd() / output_csv
            with open(csv_path, 'w', newline='') as csvfile:
                fieldnames = ['repo', 'date', 'first_commit', 'analysis_commit', 'total_lines', 'cost_estimate']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            
            print(f"\nResults written to: {csv_path}")
            print(f"Successfully analyzed {len(results)} repositories")
            
            # Print summary
            total_lines = sum(r['total_lines'] for r in results)
            total_cost = sum(r['cost_estimate'] for r in results)
            print(f"Total first-day output: {total_lines:,} lines, ${total_cost:,.2f}")
        else:
            print("No repositories could be analyzed successfully")


if __name__ == '__main__':
    main()
