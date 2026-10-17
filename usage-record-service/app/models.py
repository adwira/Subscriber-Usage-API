from pydantic import BaseModel, Field, AliasChoices


class UsageCreate(BaseModel):
    """Schema for recording subscriber usage."""
    subscriber_id: str = Field(
        ...,
        validation_alias=AliasChoices("subscriberId", "subscriber_id"),
        description="Unique identifier for subscriber (supports both subscriberId and subscriber_id)",
    )
    call_minutes: int = Field(
        ...,
        ge=0,
        validation_alias=AliasChoices("callMinutes", "call_minutes"),
        description="Duration of calls in minutes",
    )
    sms_count: int = Field(
        ...,
        ge=0,
        validation_alias=AliasChoices("smsCount", "sms_count"),
        description="Number of SMS sent",
    )
    data_usage_mb: float = Field(
        ...,
        ge=0.0,
        validation_alias=AliasChoices("dataUsageMB", "data_usage_mb"),
        description="Data usage in megabytes",
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "subscriberId": "sub-1001",
                "callMinutes": 25,
                "smsCount": 10,
                "dataUsageMB": 512.5,
            }
        },
    }


class UsageItem(BaseModel):
    """Schema for a single usage log entry."""
    callMinutes: int
    smsCount: int
    dataUsageMB: float
    timestamp: str


class UsageSummary(BaseModel):
    """Schema for aggregated usage metrics."""
    totalCallMinutes: int
    totalSmsCount: int
    totalDataUsageMB: float


class SubscriberDetailResponse(BaseModel):
    """Schema for subscriber usage details and summary."""
    subscriberId: str
    summary: UsageSummary
    usages: list[UsageItem]
