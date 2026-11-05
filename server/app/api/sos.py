"""
TyphoonLink Public Citizen SOS Beacon & Offline Sync API
Provides:
  - POST /api/sos       -> Individual SOS broadcast
  - POST /api/sos/sync  -> Batch sync for offline-buffered IndexedDB packets
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.rate_limiter import check_sos_rate_limit
from app.models.ticket import DistressTicket
from app.schemas.sos import (
    SOSCreate,
    SOSResponse,
    SOSSyncBatchRequest,
    SOSSyncBatchResponse,
)

router = APIRouter(prefix="/sos", tags=["Citizen SOS"])

# Default titles for quick 1-tap broadcasts when title is omitted
DEFAULT_TITLES = {
    "medical": ("Medical Emergency Distress", "వైద్య అత్యవసరం"),
    "flood": ("Flooding / Trapped Civilian", "వరదలో చిక్కుకున్నారు"),
    "supplies": ("Food & Clean Drinking Water Request", "ఆహారం & తాగునీరు"),
    "hazard": ("Wall / Tree Fall / Hazard Blockade", "కూలిన చెట్లు / గోడలు"),
}


def _process_single_sos(payload: SOSCreate, db: Session) -> SOSResponse:
    """
    Core idempotent processor for an SOS packet.
    1. Checks if client_packet_id already exists in SQLite.
    2. If existing, returns ACKNOWLEDGED_EXISTING without duplicating.
    3. If new, commits to database within an atomic transaction.
    """
    # 1. Idempotency Check: Query by unique client packet UUID
    existing = (
        db.query(DistressTicket)
        .filter(DistressTicket.client_packet_id == payload.client_packet_id)
        .first()
    )

    if existing:
        return SOSResponse(
            delivery_status="ACKNOWLEDGED_EXISTING",
            ticket_id=existing.id,
            client_packet_id=existing.client_packet_id,
            packet_tag=existing.packet_tag or "PKT-SAVED",
            category=existing.category,
            landmark=existing.landmark,
            status=existing.status,
            urgency_tier=existing.urgency_tier,
            server_timestamp=datetime.utcnow(),
            is_duplicate=True,
            is_simulated_data=existing.is_simulated,
            message="Packet already received and acknowledged. Existing ticket returned without duplication.",
        )

    # Resolve default headlines if omitted
    default_en, default_te = DEFAULT_TITLES.get(
        payload.category, ("Distress Alert", "అత్యవసరం")
    )
    final_title = payload.title or default_en
    final_telugu = payload.telugu_title or default_te

    # 2. Construct new distress ticket
    new_ticket = DistressTicket(
        client_packet_id=payload.client_packet_id,
        packet_tag=payload.packet_tag,
        category=payload.category,
        title=final_title,
        telugu_title=final_telugu,
        description=payload.description or "Automated 1-tap SOS distress beacon broadcast.",
        landmark=payload.landmark,
        latitude=payload.latitude,          # Optional: Nullable when GPS is unavailable
        longitude=payload.longitude,        # Optional: Nullable when GPS is unavailable
        gps_accuracy_meters=payload.gps_accuracy_meters,
        contact_phone=payload.contact_phone,
        urgency_tier=payload.urgency_tier or "red",
        status="pending",
        is_simulated=False,                 # Actual incoming citizen submission (not mock demo data)
    )

    # 3. Atomic Database Transaction
    try:
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)
    except IntegrityError:
        # Handle concurrent race condition gracefully
        db.rollback()
        existing = (
            db.query(DistressTicket)
            .filter(DistressTicket.client_packet_id == payload.client_packet_id)
            .first()
        )
        if existing:
            return SOSResponse(
                delivery_status="ACKNOWLEDGED_EXISTING",
                ticket_id=existing.id,
                client_packet_id=existing.client_packet_id,
                packet_tag=existing.packet_tag or "PKT-SAVED",
                category=existing.category,
                landmark=existing.landmark,
                status=existing.status,
                urgency_tier=existing.urgency_tier,
                server_timestamp=datetime.utcnow(),
                is_duplicate=True,
                is_simulated_data=existing.is_simulated,
                message="Packet committed concurrently by peer node. Acknowledged without duplication.",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database integrity failure while committing SOS distress beacon.",
        )

    return SOSResponse(
        delivery_status="DELIVERED_SERVER",
        ticket_id=new_ticket.id,
        client_packet_id=new_ticket.client_packet_id,
        packet_tag=new_ticket.packet_tag or "PKT-NEW",
        category=new_ticket.category,
        landmark=new_ticket.landmark,
        status=new_ticket.status,
        urgency_tier=new_ticket.urgency_tier,
        server_timestamp=new_ticket.created_at or datetime.utcnow(),
        is_duplicate=False,
        is_simulated_data=new_ticket.is_simulated,
        message="Distress beacon successfully committed to SQLite server triage queue.",
    )


@router.post(
    "",
    response_model=SOSResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Broadcast Single SOS Beacon",
    description=(
        "Public endpoint for citizens to submit an urgent SOS beacon. "
        "Landmark is mandatory; GPS latitude and longitude are optional. "
        "Guarantees idempotent de-duplication based on unique client_packet_id."
    ),
    dependencies=[Depends(check_sos_rate_limit)],
)
def broadcast_sos(payload: SOSCreate, db: Session = Depends(get_db)):
    """Single SOS beacon submission handler."""
    return _process_single_sos(payload, db)


@router.post(
    "/sync",
    response_model=SOSSyncBatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch Sync Offline-Queued Packets",
    description=(
        "Flushes multiple offline-buffered SOS packets from browser IndexedDB. "
        "Validates and commits each packet individually. Returns de-duplication tallies "
        "and explicit server confirmation per packet."
    ),
    dependencies=[Depends(check_sos_rate_limit)],
)
def sync_offline_packets(
    payload: SOSSyncBatchRequest, db: Session = Depends(get_db)
):
    """Batch synchronizer for IndexedDB offline queue."""
    results: List[SOSResponse] = []
    new_count = 0
    duplicate_count = 0

    for packet in payload.packets:
        res = _process_single_sos(packet, db)
        results.append(res)
        if res.is_duplicate:
            duplicate_count += 1
        else:
            new_count += 1

    return SOSSyncBatchResponse(
        delivery_status="BATCH_PROCESSED",
        total_received=len(payload.packets),
        new_tickets_created=new_count,
        duplicates_acknowledged=duplicate_count,
        results=results,
        server_timestamp=datetime.utcnow(),
        is_simulated_data=True,
    )
