#!/usr/bin/env python3
"""Script to remove CSV snapshot files older than 30 days based on the filename timestamp.

Target pattern: usages_snapshot_YYYYMMDD_HHMMSS.csv
Deletes files whose parsed timestamp is older than (current_time - 30 days).
"""

import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "usage-record-service" / "snapshots"
SNAPSHOT_FILENAME_REGEX = re.compile(r"^usages_snapshot_(\d{8}_\d{6})\.csv$")
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"


def cleanup_snapshots(
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
    days: int = 30,
    dry_run: bool = False,
) -> int:
    """Remove snapshot files older than `days` based on timestamp in filename."""
    if not snapshot_dir.exists():
        print(f"[!] Snapshot directory does not exist: {snapshot_dir}")
        return 0

    cutoff_datetime = datetime.now() - timedelta(days=days)
    print(f"[*] Scanning for snapshots older than {days} days (cutoff: {cutoff_datetime.strftime('%Y-%m-%d %H:%M:%S')}) in {snapshot_dir}")

    total_scanned = 0
    total_deleted = 0

    for file_path in snapshot_dir.glob("usages_snapshot_*.csv"):
        match = SNAPSHOT_FILENAME_REGEX.match(file_path.name)
        if not match:
            # File does not follow timestamp naming convention, skip safely
            continue

        total_scanned += 1
        raw_timestamp = match.group(1)

        try:
            file_datetime = datetime.strptime(raw_timestamp, TIMESTAMP_FORMAT)
        except ValueError:
            print(f"[-] Warning: Failed to parse timestamp from filename: {file_path.name}")
            continue

        if file_datetime < cutoff_datetime:
            age_days = (datetime.now() - file_datetime).days
            if dry_run:
                print(f"[DRY-RUN] Would delete: {file_path.name} (age: {age_days} days)")
            else:
                try:
                    os.remove(file_path)
                    print(f"[-] Deleted: {file_path.name} (age: {age_days} days)")
                except OSError as err:
                    print(f"[!] Error deleting {file_path.name}: {err}", file=sys.stderr)
                    continue
            total_deleted += 1
        else:
            print(f"[+] Retained: {file_path.name} (created: {file_datetime.strftime('%Y-%m-%d %H:%M:%S')})")

    status_str = "would be deleted (dry run)" if dry_run else "deleted"
    print(f"[*] Summary: {total_scanned} snapshot(s) found, {total_deleted} file(s) {status_str}.")
    return total_deleted


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Clean up CSV snapshots older than 30 days based on filename timestamp.",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help=f"Path to snapshots directory (default: {DEFAULT_SNAPSHOT_DIR})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Age threshold in days for deletion (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate deletion without actually removing files",
    )
    args = parser.parse_args()

    cleanup_snapshots(snapshot_dir=args.dir, days=args.days, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
