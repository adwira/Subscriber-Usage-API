# Technical Test Submission - Arya Dwi Putra

This repository contains the implementation and documentation for the four technical assessment tasks.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Q1: Subscriber Usage API](#q1-subscriber-usage-api)
   - [Architecture & Storage Design](#architecture--storage-design)
   - [Modular Calculation Functions](#modular-calculation-functions)
   - [API Endpoints & Schemas](#api-endpoints--schemas)
   - [Running the Service](#running-the-service)
4. [Q2: Usage Snapshot Automation](#q2-usage-snapshot-automation)
   - [File Naming & CSV Schema](#file-naming--csv-schema)
   - [create_snapshot.py](#create_snapshotpy)
   - [cleanup_snapshots.py](#cleanup_snapshotspy)
   - [Crontab Configuration](#crontab-configuration)
5. [Q3: SQL Queries](#q3-sql-queries)
   - [1. Insert New Subscriber (Fajar)](#1-insert-new-subscriber-fajar)
   - [2. Update Plan to Premium](#2-update-plan-to-premium)
   - [3. Total Data Usage for Premium Subscribers](#3-total-data-usage-for-premium-subscribers)
   - [4. Top 3 Subscribers by Total Data Usage](#4-top-3-subscribers-by-total-data-usage)
   - [5. Subquery: Average Call Minutes <= 30](#5-subquery-average-call-minutes--30)
6. [Q4: JavaScript Reduce Bug Analysis & Fix](#q4-javascript-reduce-bug-analysis--fix)
   - [Root Causes](#root-causes)
   - [Fixed Implementation](#fixed-implementation)

---

## Project Overview

| Task | Topic | Tech Stack | Location |
|---|---|---|---|
| **Q1** | Subscriber Usage API | FastAPI, Pydantic v2, In-Memory Store| [`./usage-record-service`](./usage-record-service) |
| **Q2** | Snapshot & Cleanup Scripts | Python 3 Standard Library, Crontab | [`./scripts`](./scripts) |
| **Q3** | SQL Queries | ANSI SQL (PostgreSQL / MySQL compatible) | [`./subscriber & usage.sql`](./subscriber%20&%20usage.sql) |
| **Q4** | Code Troubleshooting | JavaScript / TypeScript | Documented below |

---

## Repository Structure

```text
.
├── README.md                          # Primary technical documentation (this file)
├── subscriber & usage.sql             # SQL solutions for Q3
├── scripts/                           # Automation scripts for Q2
│   ├── README.md                      # Detailed script documentation
│   ├── create_snapshot.py             # Pulls usage API data and exports to CSV
│   ├── cleanup_snapshots.py           # Removes snapshots older than 30 days
│   └── crontab.txt                    # Cron schedule configurations (WIB & UTC)
└── usage-record-service/              # Backend service for Q1
    ├── README.md                      # Service documentation
    ├── pyproject.toml                 # Dependencies (uv / Python)
    ├── uv.lock                        # Dependency lockfile
    ├── snapshots/                     # Generated CSV snapshots
    └── app/
        ├── __init__.py
        ├── main.py                    # API routes and application setup
        ├── models.py                  # Pydantic schemas and validation
        ├── store.py                   # In-memory dictionary store
        └── services.py                # Standalone calculation functions
```

---

## Q1: Subscriber Usage API

The service is built with **FastAPI** and uses an **in-memory** data store to record subscriber activity and return both raw logs and aggregated usage metrics.

### Architecture & Storage Design

The in-memory storage is defined in [`./usage-record-service/app/store.py`](./usage-record-service/app/store.py) using the `InMemoryUsageStore` class. Data is structured as a hash map where keys are `subscriberId` strings and values are lists of record objects:

```json
{
  "sub-1001": [
    {
      "callMinutes": 25,
      "smsCount": 10,
      "dataUsageMB": 512.5,
      "timestamp": "2026-10-16T16:21:08.969771+00:00"
    },
    {
      "callMinutes": 15,
      "smsCount": 5,
      "dataUsageMB": 350.25,
      "timestamp": "2026-10-16T16:30:12.112040+00:00"
    }
  ]
}
```

Design choices:
- Authentication is omitted per requirements. The `subscriberId` is supplied in the request body (the schema accepts both `subscriberId` and `subscriber_id`).
- Input validation in [`./usage-record-service/app/models.py`](./usage-record-service/app/models.py) ensures metrics (`callMinutes`, `smsCount`, `dataUsageMB`) cannot be negative numbers (`ge=0`).

### Modular Calculation Functions

Per requirement, each usage metric calculation is isolated in its own function inside [`./usage-record-service/app/services.py`](./usage-record-service/app/services.py):
1. `calculate_total_call_minutes(usages: list[dict]) -> int`: Sums total call duration in minutes.
2. `calculate_total_sms_count(usages: list[dict]) -> int`: Sums total SMS messages sent.
3. `calculate_total_data_usage_mb(usages: list[dict]) -> float`: Sums total data consumed in MB, rounded to 2 decimal places.
4. `calculate_subscriber_summary(usages: list[dict]) -> dict`: Aggregator calling the individual functions above to produce a single summary object.

### API Endpoints & Schemas

#### 1. `POST /usages`
Records a single usage event for a subscriber.

- **Request Body**:
  ```json
  {
    "subscriberId": "sub-1001",
    "callMinutes": 25,
    "smsCount": 10,
    "dataUsageMB": 512.5
  }
  ```
- **Response (`201 Created`)**:
  ```json
  {
    "message": "Usage recorded successfully",
    "subscriberId": "sub-1001",
    "record": {
      "callMinutes": 25,
      "smsCount": 10,
      "dataUsageMB": 512.5,
      "timestamp": "2026-10-16T16:21:08.969771+00:00"
    }
  }
  ```
- **Response (`422 Unprocessable Entity`)**: Returned when payload types are invalid or values are negative.

#### 2. `GET /usages`
Returns all usage records across all subscribers.

- **Response (`200 OK`)**:
  ```json
  {
    "sub-1001": [
      {
        "callMinutes": 25,
        "smsCount": 10,
        "dataUsageMB": 512.5,
        "timestamp": "2026-10-16T16:21:08.969771+00:00"
      }
    ],
    "sub-1002": [
      {
        "callMinutes": 60,
        "smsCount": 20,
        "dataUsageMB": 1024.0,
        "timestamp": "2026-10-16T16:25:00.000000+00:00"
      }
    ]
  }
  ```

#### 3. `GET /usages/{subscriberId}`
Returns the usage history and calculated summary for a specific subscriber.

- **Path Parameter**: `subscriberId` (string)
- **Response (`200 OK`)**:
  ```json
  {
    "subscriberId": "sub-1001",
    "summary": {
      "totalCallMinutes": 40,
      "totalSmsCount": 20,
      "totalDataUsageMB": 862.75
    },
    "usages": [
      {
        "callMinutes": 15,
        "smsCount": 10,
        "dataUsageMB": 350.25,
        "timestamp": "2026-10-16T16:00:00+00:00"
      },
      {
        "callMinutes": 25,
        "smsCount": 10,
        "dataUsageMB": 512.5,
        "timestamp": "2026-10-16T16:21:08.969771+00:00"
      }
    ]
  }
  ```
- **Response (`404 Not Found`)**:
  ```json
  {
    "detail": "Subscriber 'unknown-id' not found."
  }
  ```

### Running the Service

Navigate to the `usage-record-service` directory:

```bash
cd usage-record-service

# Using uv
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or using standard python
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation is accessible at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Q2: Usage Snapshot Automation

This solution exports usage records from the API into timestamped CSV files on a recurring schedule and removes snapshot archives older than 30 days. Both scripts use only the **Python Standard Library** (no third-party dependencies required).

### File Naming & CSV Schema

- **File Name Pattern**: `usages_snapshot_YYYYMMDD_HHMMSS.csv`  
  *(Example: `usages_snapshot_20261016_120000.csv`)*
- **CSV Headers and Data Rows**:
  ```csv
  subscriberId,callMinutes,smsCount,dataUsageMB,timestamp
  sub-1001,25,10,512.5,2026-10-16T16:21:08.969771+00:00
  sub-1001,15,10,350.25,2026-10-16T16:00:00+00:00
  sub-1002,60,20,1024.0,2026-10-16T16:25:00.000000+00:00
  ```

### create_snapshot.py
File: [`./scripts/create_snapshot.py`](./scripts/create_snapshot.py)

- **Workflow**: Calls `GET /usages` using `urllib.request`, flattens the nested JSON structure into CSV rows, and writes the output into the configured snapshots directory.
- **Usage**:
  ```bash
  # Run with defaults (API at http://localhost:8000/usages, output to ../usage-record-service/snapshots)
  python scripts/create_snapshot.py

  # Custom API URL or destination directory:
  python scripts/create_snapshot.py --api-url http://localhost:8000/usages --output-dir ./snapshots
  ```

### cleanup_snapshots.py
File: [`./scripts/cleanup_snapshots.py`](./scripts/cleanup_snapshots.py)

- **Workflow**: Scans the snapshot directory using the regex `^usages_snapshot_(\d{8}_\d{6})\.csv$`. It parses the timestamp suffix into a `datetime` object and compares it with `now - 30 days`. Files strictly older than 30 days are unlinked.
- **Usage**:
  ```bash
  # Delete files older than 30 days
  python scripts/cleanup_snapshots.py

  # Dry-run mode (preview without deleting files)
  python scripts/cleanup_snapshots.py --dry-run

  # Custom retention threshold (e.g. 14 days)
  python scripts/cleanup_snapshots.py --days 14
  ```

### Crontab Configuration
File reference: [`./scripts/crontab.txt`](./scripts/crontab.txt)

To set up recurring execution on a Linux environment, edit crontab:
```bash
crontab -e
```

#### Option A: Server in WIB Timezone (`Asia/Jakarta` / UTC+7)
Run snapshot at 08:00, 12:00, and 15:00 WIB, and run cleanup daily at midnight:

```cron
# Snapshot: 08:00, 12:00, 15:00 WIB
0 8,12,15 * * * /usr/bin/python3 /path/to/project/scripts/create_snapshot.py >> /path/to/project/scripts/cron_snapshot.log 2>&1

# Cleanup: Daily at 00:00 WIB
0 0 * * * /usr/bin/python3 /path/to/project/scripts/cleanup_snapshots.py >> /path/to/project/scripts/cron_cleanup.log 2>&1
```

#### Option B: Server in UTC Timezone
Converting WIB (UTC+7) to UTC:
- `08:00 WIB` = `01:00 UTC`
- `12:00 WIB` = `05:00 UTC`
- `15:00 WIB` = `08:00 UTC`

```cron
0 1,5,8 * * * /usr/bin/python3 /path/to/project/scripts/create_snapshot.py >> /path/to/project/scripts/cron_snapshot.log 2>&1
0 17 * * * /usr/bin/python3 /path/to/project/scripts/cleanup_snapshots.py >> /path/to/project/scripts/cron_cleanup.log 2>&1
```

---

## Q3: SQL Queries

The full SQL script is stored in [`./subscriber & usage.sql`](./subscriber%20&%20usage.sql). Below are the queries and explanations.

### 1. Insert New Subscriber (Fajar)
Insert a subscriber named Fajar on the Basic plan, activated on 24 January 2024.

```sql
INSERT INTO subscribers (id, name, plan, activation_date)
VALUES ('SUB07', 'Fajar', 'Basic', '2024-01-24');
```
*Note*: Inserts a new record into `subscribers` using ISO date format `YYYY-MM-DD`.

### 2. Update Plan to Premium
Update Fajar's plan to Premium.

```sql
UPDATE subscribers
SET plan = 'Premium'
WHERE id = 'SUB07';
```
*Note*: Targeted update using the subscriber primary key to preserve relational integrity.

### 3. Total Data Usage for Premium Subscribers
Calculate total data usage (`SUM(data_usage_mb)`) across all snapshots for all Premium plan subscribers.

```sql
SELECT SUM(u.data_usage_mb) AS total_data_usage_mb
FROM usages u
JOIN subscribers s ON u.subscriber_id = s.id
WHERE s.plan = 'Premium';
```
*Note*: Uses an `INNER JOIN` to associate usage records with subscriber plans, filtering specifically for `s.plan = 'Premium'`.

### 4. Top 3 Subscribers by Total Data Usage
Sort and display the top 3 subscribers by total data usage across all snapshots.

```sql
SELECT 
    s.id, 
    s.name, 
    s.plan, 
    COALESCE(SUM(u.data_usage_mb), 0) AS total_data_usage_mb
FROM subscribers s
LEFT JOIN usages u ON s.id = u.subscriber_id
GROUP BY s.id, s.name, s.plan
ORDER BY total_data_usage_mb DESC
LIMIT 3;
```
*Note*:
- `LEFT JOIN` ensures subscribers who have zero recorded usage remain visible in reports.
- `COALESCE(SUM(u.data_usage_mb), 0)` replaces potential `NULL` sums with `0`.
- Groups by subscriber identifiers, sorts descending, and limits results to 3.

### 5. Subquery: Average Call Minutes <= 30
Find subscribers whose average call minutes per snapshot is less than or equal to 30.

```sql
SELECT s.id, s.name, s.plan 
FROM subscribers s
WHERE s.id IN (
    SELECT subscriber_id 
    FROM usages
    GROUP BY subscriber_id
    HAVING AVG(call_minutes) <= 30
);
```
*Note*:
- **Inner Query**: Groups `usages` by `subscriber_id` and filters grouped records with `HAVING AVG(call_minutes) <= 30`.
- **Outer Query**: Selects matching subscriber details matching those IDs.

---

## Q4: JavaScript Reduce Bug Analysis & Fix

### Original Code

```javascript
function getTotalUsageMB(records) {
  return records.reduce((total, record) => {
    total += record.dataUsageMB;
  });
}
```

### Root Causes

1. **Missing Return Statement in Reducer Callback**:
   In JavaScript, `Array.prototype.reduce` requires the callback to return the updated accumulator on each iteration. The arrow function uses a block `{ total += record.dataUsageMB; }` but lacks a `return` keyword. Without an explicit return, the function returns `undefined`.
   - Iteration 1: `total` receives the initial value or first element. The block evaluates the addition, but returns `undefined`.
   - Iteration 2: `total` is now `undefined`. Computing `undefined + record.dataUsageMB` evaluates to `NaN`.
   - Final result: `getTotalUsageMB` evaluates to `undefined` or `NaN`.

2. **Missing `initialValue` Parameter**:
   The second argument to `.reduce()` was omitted.
   - Calling `getTotalUsageMB([])` on an empty array immediately throws a runtime error:
     `TypeError: Reduce of empty array with no initial value`.
   - On a single-element array `[{ dataUsageMB: 100 }]`, `.reduce` returns the first object itself without executing the callback, returning an Object instead of a Number.

3. **In-Place Mutation of Accumulator Parameter**:
   Writing `total += ...` attempts to mutate the accumulator variable parameter. In functional reduction, this is an anti-pattern flagged by ESLint rule `no-param-reassign`.

4. **Missing Input Validation & Defensive Handling**:
   - If `records` is not an array (`null`, `undefined`, or a plain object), `records.reduce` throws `TypeError: records.reduce is not a function`.
   - If `record.dataUsageMB` is missing, `null`, or formatted as a string, it can lead to `NaN` or unintended string concatenation.

---

### Fixed Implementation

```javascript

function getTotalUsageMB(records = []) {
  if (!Array.isArray(records)) {
    return 0;
  }

  return records.reduce((total, record) => {
    const usage = Number(record?.dataUsageMB) || 0;
    return total + usage;
  }, 0);
}
```
---

### Long-Term Prevention Strategy
To prevent this class of bug from reaching production:

1. **Linter Rules (ESLint)**:
   Add the following rules to `.eslintrc.json`:
   - `array-callback-return`: Enforces return statements in callbacks of array methods (`reduce`, `map`, `filter`).
```javascript
   // eslint.config.js (ESLint v9+; use .eslintrc.json on older versions)
   export default [{ rules: { "array-callback-return": "error" } }];
```
2. **TypeScript / Static Type Checking**:
   Define strict models so that missing properties and return types are flagged at compile time:
   ```typescript
   interface UsageRecord {
     callMinutes: number;
     smsCount: number;
     dataUsageMB: number;
     timestamp?: string;
   }
   function getTotalUsageMB(records: UsageRecord[] = []): number {
     return records.reduce<number>((total, record) => total + (record.dataUsageMB), 0);
   }
   ```
3. **Unit tests and CI:** Cover empty, single-element, and multi-element arrays.
   The multi-element test fails immediately against the original code
   (`undefined` instead of a number). Run lint, `tsc --noEmit`, and the tests in
   CI on every pull request so these checks cannot be skipped.
---