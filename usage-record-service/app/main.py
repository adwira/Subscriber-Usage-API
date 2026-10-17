from typing import Any
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.models import UsageCreate, SubscriberDetailResponse, UsageItem
from app.services import calculate_subscriber_summary
from app.store import usage_store

app = FastAPI(
    title="Subscriber Usage API",
    description="Service to record and retrieve subscriber usage data with in-memory storage.",
    version="1.0.0",
)

# Enable CORS for potential frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    """Health check endpoint to verify service status."""
    return {"status": "ok", "service": "Subscriber Usage API"}


@app.post(
    "/usages",
    status_code=status.HTTP_201_CREATED,
    tags=["Usage Records"],
    summary="Record subscriber usage",
)
def record_usage(payload: UsageCreate) -> dict[str, Any]:
    """Record subscriber usage in memory.
    
    Accepts subscriberId (or subcriberId), callMinutes, smsCount, and dataUsageMB.
    Automatically attaches an ISO 8601 timestamp.
    """
    record = usage_store.add_record(
        subscriber_id=payload.subscriber_id,
        call_minutes=payload.call_minutes,
        sms_count=payload.sms_count,
        data_usage_mb=payload.data_usage_mb,
    )
    return {
        "message": "Usage recorded successfully",
        "subscriberId": payload.subscriber_id,
        "record": record,
    }


@app.get(
    "/usages",
    response_model=dict[str, list[UsageItem]],
    tags=["Usage Records"],
    summary="Get all subscriber usage records",
)
def get_all_usages() -> dict[str, list[dict[str, Any]]]:
    """Retrieve all recorded usage entries grouped by subscriber ID."""
    return usage_store.get_all()


@app.get(
    "/usages/{subscriberId}",
    response_model=SubscriberDetailResponse,
    tags=["Usage Records"],
    summary="Get usage records and summary for a specific subscriber",
)
def get_subscriber_usage(subscriberId: str) -> dict[str, Any]:
    """Retrieve usage history and summary calculations for a specific subscriber.
    
    Calls individual calculation functions for total call minutes, SMS count,
    and data usage in MB.
    """
    records = usage_store.get_by_subscriber(subscriberId)
    if records is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscriber '{subscriberId}' not found.",
        )

    summary = calculate_subscriber_summary(records)
    return {
        "subscriberId": subscriberId,
        "summary": summary,
        "usages": records,
    }
