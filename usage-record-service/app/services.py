from typing import Any


def calculate_total_call_minutes(usages: list[dict[str, Any]]) -> int:
    """Calculate the total call minutes from a list of usage records."""
    return sum(int(item.get("callMinutes", 0)) for item in usages)


def calculate_total_sms_count(usages: list[dict[str, Any]]) -> int:
    """Calculate the total SMS count from a list of usage records."""
    return sum(int(item.get("smsCount", 0)) for item in usages)


def calculate_total_data_usage_mb(usages: list[dict[str, Any]]) -> float:
    """Calculate the total data usage in MB from a list of usage records."""
    total = sum(float(item.get("dataUsageMB", 0.0)) for item in usages)
    return round(total, 2)


def calculate_subscriber_summary(usages: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate individual usage calculations into a unified summary object."""
    return {
        "totalCallMinutes": calculate_total_call_minutes(usages),
        "totalSmsCount": calculate_total_sms_count(usages),
        "totalDataUsageMB": calculate_total_data_usage_mb(usages),
    }
