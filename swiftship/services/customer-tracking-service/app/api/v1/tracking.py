"""
Tracking API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from elasticsearch import AsyncElasticsearch

from app.db.session import get_db
from app.models.tracking import TrackingEvent, ShipmentTracking
from app.schemas.tracking import TrackingResponse, TrackingEventResponse, TrackingSearchResult
from app.core.elasticsearch import get_es_client

router = APIRouter()


@router.get("/{awb_number}", response_model=TrackingResponse)
async def track_shipment(
    awb_number: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Public endpoint — track any shipment by AWB number.
    No auth required (customer-facing).
    """
    result = await db.execute(
        select(ShipmentTracking).where(ShipmentTracking.awb_number == awb_number)
    )
    tracking = result.scalar_one_or_none()
    if not tracking:
        raise HTTPException(status_code=404, detail=f"Shipment {awb_number} not found")

    events_result = await db.execute(
        select(TrackingEvent)
        .where(TrackingEvent.awb_number == awb_number)
        .order_by(desc(TrackingEvent.event_time))
    )
    events = events_result.scalars().all()

    return TrackingResponse(
        awb_number=awb_number,
        current_status=tracking.current_status,
        current_location=tracking.current_location,
        origin=tracking.origin_city,
        destination=tracking.destination_city,
        expected_delivery=tracking.expected_delivery_date,
        last_updated=tracking.last_updated,
        events=[TrackingEventResponse.model_validate(e) for e in events],
    )


@router.get("/search/", response_model=List[TrackingSearchResult])
async def search_shipments(
    q: str = Query(..., min_length=3, description="AWB, phone, or reference number"),
    es: AsyncElasticsearch = Depends(get_es_client),
):
    """
    Full-text search across shipments using Elasticsearch.
    Ops/admin use — allows searching by phone, reference, address.
    """
    response = await es.search(
        index="shipments",
        body={
            "query": {
                "multi_match": {
                    "query": q,
                    "fields": [
                        "awb_number^3",
                        "receiver_phone^2",
                        "sender_phone^2",
                        "reference_number^2",
                        "receiver_name",
                        "sender_name",
                        "receiver_city",
                    ],
                }
            },
            "size": 20,
        },
    )

    return [
        TrackingSearchResult(
            awb_number=hit["_source"]["awb_number"],
            status=hit["_source"]["current_status"],
            origin=hit["_source"]["origin_city"],
            destination=hit["_source"]["destination_city"],
            receiver_name=hit["_source"]["receiver_name"],
            score=hit["_score"],
        )
        for hit in response["hits"]["hits"]
    ]


@router.get("/eta/{awb_number}")
async def get_eta(
    awb_number: str,
    db: AsyncSession = Depends(get_db),
):
    """Get estimated time of arrival for a shipment."""
    result = await db.execute(
        select(ShipmentTracking).where(ShipmentTracking.awb_number == awb_number)
    )
    tracking = result.scalar_one_or_none()
    if not tracking:
        raise HTTPException(status_code=404, detail="Shipment not found")

    return {
        "awb_number": awb_number,
        "expected_delivery_date": tracking.expected_delivery_date,
        "current_status": tracking.current_status,
        "is_delayed": tracking.is_delayed,
        "delay_reason": tracking.delay_reason,
    }
