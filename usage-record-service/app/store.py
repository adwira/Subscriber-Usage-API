from datetime import datetime, timezone
from typing import Any


class InMemoryUsageStore:
    """In-memory data store for subscriber usage records.
    
    Structure:
    {
        "subscriberId": [
            {
                "callMinutes": 20,
                "smsCount": 5,
                "dataUsageMB": 100.5,
                "timestamp": "2026-10-16T16:15:00Z"
            },
            ...
        ]
    }
    """

    def __init__(self) -> None:
        self._data: dict[str, list[dict[str, Any]]] = {}

    def add_record(
        self,
        subscriber_id: str,
        call_minutes: int,
        sms_count: int,
        data_usage_mb: float,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        """Record usage under the given subscriberId."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        record = {
            "callMinutes": call_minutes,
            "smsCount": sms_count,
            "dataUsageMB": float(data_usage_mb),
            "timestamp": timestamp,
        }

        if subscriber_id not in self._data:
            self._data[subscriber_id] = []

        self._data[subscriber_id].append(record)
        return record

    def get_all(self) -> dict[str, list[dict[str, Any]]]:
        """Return all subscribers and their recorded usages."""
        return self._data

    def get_by_subscriber(self, subscriber_id: str) -> list[dict[str, Any]] | None:
        """Return usage records for a specific subscriberId, or None if not found."""
        return self._data.get(subscriber_id)

    def clear(self) -> None:
        """Clear all in-memory data (primarily for testing purposes)."""
        self._data.clear()


# Global in-memory singleton store instance
usage_store = InMemoryUsageStore()
