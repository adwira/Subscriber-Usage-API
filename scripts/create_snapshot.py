#!/usr/bin/env python3
"""Script to fetch all subscriber usage data from API and export to CSV snapshot.

File naming convention: usages_snapshot_YYYYMMDD_HHMMSS.csv
Columns: subscriberId,callMinutes,smsCount,dataUsageMB,timestamp
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_API_URL = os.environ.get("USAGE_API_URL", "http://localhost:8000/usages")
DEFAULT_SNAPSHOT_DIR = Path(__file__).resolve().parent.parent / "usage-record-service" / "snapshots"


def fetch_usages(api_url: str) -> dict:
    """Fetch usage data from the FastAPI service."""
    req = urllib.request.Request(
        url=api_url,
        headers={"Accept": "application/json", "User-Agent": "UsageSnapshotBot/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP error {response.status}: {response.read().decode('utf-8')}")
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"Failed to connect to API at {api_url}: {e}") from e


def create_snapshot(api_url: str = DEFAULT_API_URL, output_dir: Path = DEFAULT_SNAPSHOT_DIR) -> Path:
    """Fetch usages and write them into a timestamped CSV file."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # File naming convention: usages_snapshot_YYYYMMDD_HHMMSS.csv
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"usages_snapshot_{timestamp_str}.csv"
    filepath = output_dir / filename

    print(f"[*] Fetching subscriber usages from {api_url} ...")
    data = fetch_usages(api_url)

    row_count = 0
    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write CSV header row
        writer.writerow(["subscriberId", "callMinutes", "smsCount", "dataUsageMB", "timestamp"])

        # Data structure from API: { "subscriberId": [ {callMinutes, smsCount, dataUsageMB, timestamp}, ... ] }
        for subscriber_id, usages in data.items():
            for item in usages:
                writer.writerow([
                    subscriber_id,
                    item.get("callMinutes", 0),
                    item.get("smsCount", 0),
                    item.get("dataUsageMB", 0.0),
                    item.get("timestamp", ""),
                ])
                row_count += 1

    print(f"[+] Snapshot saved successfully: {filepath}")
    print(f"[+] Total records written: {row_count}")
    return filepath


def main() -> None:
    parser = argparse.ArgumentParser(description="Create CSV snapshot of subscriber usage data.")
    parser.add_argument(
        "--api-url",
        default=DEFAULT_API_URL,
        help=f"URL of GET /usages endpoint (default: {DEFAULT_API_URL})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_SNAPSHOT_DIR,
        help=f"Target directory for CSV files (default: {DEFAULT_SNAPSHOT_DIR})",
    )
    args = parser.parse_args()

    try:
        create_snapshot(api_url=args.api_url, output_dir=args.output_dir)
    except Exception as exc:
        print(f"[!] Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
