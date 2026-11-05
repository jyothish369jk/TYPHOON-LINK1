"""
TyphoonLink Volunteer Ticket Management API
Provides:
  - GET /api/tickets                 -> List triage stream with filters & pagination (masked phone)
  - POST /api/tickets/{id}/claim     -> Atomic conditional claim (HTTP 409 Conflict if claimed)
  - PATCH /api/tickets/{id}/status   -> Validated status transition & authorization check
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ticket import DistressTicket
from app.schemas.ticket import (
    TicketResponse,
    TicketListResponse,
    TicketClaimRequest,
    TicketClaimResponse,
    TicketStatusUpdateRequest,
    TicketStatusUpdateResponse,
    mask_phone_number,
)

router = APIRouter(prefix="/tickets", tags=["Volunteer Triage"])

# Allowed lifecycle state transitions
VALID_TRANSITIONS = {
    "pending": ["claimed"],
    "claimed": ["in_progress", "pending"],
    "in_progress": ["resolved", "claimed"],
    "resolved": [],  # Terminal state (requires admin override)
}


@router.get(
    "",
    response_model=TicketListResponse,
    summary="Retrieve Triage Distress Tickets",
    description=(
        "Retrieves active distress tickets ordered newest first. "
        "Supports filtering by status, emergency category, urgency tier, and zone. "
        "Citizen telephone numbers are masked by default to protect privacy."
    ),
)
def get_tickets(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: pending, claimed, in_progress, resolved"),
    category: Optional[str] = Query(None, description="Filter by category: medical, flood, supplies, hazard"),
    urgency: Optional[str] = Query(None, description="Filter by urgency: red, amber, blue"),
    zone: Optional[str] = Query(None, description="Search/filter by landmark or zone text"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Page limit (max 100)"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role", description="[DEMO-ONLY: Testing header. Not secure production auth] 'admin' or 'volunteer'"),
    x_volunteer_squad: Optional[str] = Header(None, alias="X-Volunteer-Squad", description="[DEMO-ONLY: Testing header. Not secure production auth] Squad name"),
    db: Session = Depends(get_db),
):
    query = db.query(DistressTicket)

    # 1. Apply Filters
    if status_filter:
        query = query.filter(DistressTicket.status == status_filter)

    if category:
        query = query.filter(DistressTicket.category == category)

    if urgency:
        query = query.filter(DistressTicket.urgency_tier == urgency)

    if zone:
        query = query.filter(DistressTicket.landmark.ilike(f"%{zone}%"))

    total_count = query.count()

    # 2. Sort newest reports first
    tickets = (
        query.order_by(DistressTicket.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # 3. Privacy Masking: Unmask phone only if authorized responder/admin
    is_authorized_responder = x_user_role in ("admin", "volunteer") and bool(x_volunteer_squad)

    items = []
    for t in tickets:
        item = TicketResponse.model_validate(t)
        if not is_authorized_responder:
            item.contact_phone = mask_phone_number(t.contact_phone)
        items.append(item)

    return TicketListResponse(
        total=total_count,
        skip=skip,
        limit=limit,
        items=items,
        is_simulated_data=True,
    )


@router.post(
    "/{ticket_id}/claim",
    response_model=TicketClaimResponse,
    status_code=status.HTTP_200_OK,
    summary="Claim Rescue Ticket Atomically",
    description=(
        "Claims a pending distress ticket for a response squad. "
        "Enforces an atomic conditional database update. "
        "If another responder claims it first, returns HTTP 409 Conflict."
    ),
)
def claim_ticket(
    ticket_id: int,
    payload: TicketClaimRequest,
    x_volunteer_squad: Optional[str] = Header(None, alias="X-Volunteer-Squad"),
    db: Session = Depends(get_db),
):
    # Check ticket existence
    ticket = db.query(DistressTicket).filter(DistressTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Distress ticket #{ticket_id} does not exist.",
        )

    # Resolve claiming squad name
    squad = payload.squad_name or x_volunteer_squad or "AU Ward Squad #14"
    now = datetime.utcnow()

    # ATOMIC CONDITIONAL UPDATE:
    # Only updates if status is currently 'pending'
    rows_updated = (
        db.query(DistressTicket)
        .filter(DistressTicket.id == ticket_id, DistressTicket.status == "pending")
        .update(
            {
                DistressTicket.status: "claimed",
                DistressTicket.assigned_squad: squad,
                DistressTicket.claimed_by_user_id: payload.volunteer_id,
                DistressTicket.claimed_at: now,
                DistressTicket.updated_at: now,
            },
            synchronize_session="fetch",
        )
    )
    db.commit()

    if rows_updated == 0:
        # Atomic update failed: Re-read ticket to detail the exact conflict
        db.refresh(ticket)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Conflict: Ticket #{ticket_id} could not be claimed. "
                f"It is currently '{ticket.status}' and already claimed by squad '{ticket.assigned_squad}'."
            ),
        )

    db.refresh(ticket)
    return TicketClaimResponse(
        success=True,
        message=f"Ticket #{ticket_id} successfully claimed by {squad}.",
        ticket_id=ticket.id,
        status=ticket.status,
        assigned_squad=ticket.assigned_squad,
        claimed_at=ticket.claimed_at or now,
        is_simulated_data=True,
    )


@router.patch(
    "/{ticket_id}/status",
    response_model=TicketStatusUpdateResponse,
    summary="Update Ticket Status (Enforce State Machine & Auth)",
    description=(
        "Updates the lifecycle status of an emergency ticket. "
        "Supported: pending, claimed, in_progress, resolved. "
        "Enforces valid state transitions and authorization checks."
    ),
)
def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdateRequest,
    x_user_role: Optional[str] = Header(None, alias="X-User-Role", description="[DEMO-ONLY: Testing header. Not secure production auth] 'admin' or 'volunteer'"),
    x_volunteer_squad: Optional[str] = Header(None, alias="X-Volunteer-Squad", description="[DEMO-ONLY: Testing header. Not secure production auth] Squad name"),
    db: Session = Depends(get_db),
):
    ticket = db.query(DistressTicket).filter(DistressTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Distress ticket #{ticket_id} does not exist.",
        )

    # 1. Target status (strictly: pending, claimed, in_progress, resolved)
    target_status = payload.status
    prev_status = ticket.status

    # 2. Check Allowed State Transitions
    allowed = VALID_TRANSITIONS.get(prev_status, [])
    # Special admin override allowed
    is_admin = x_user_role == "admin"
    if not is_admin and target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid status transition from '{prev_status}' to '{target_status}'. "
                f"Allowed transitions from '{prev_status}' are: {allowed}."
            ),
        )

    # 3. Authorization Check:
    # If ticket is already claimed or in_progress, only assigned squad or admin can update it
    if prev_status in ("claimed", "in_progress") and not is_admin:
        request_squad = payload.squad_name or x_volunteer_squad
        if not request_squad or request_squad != ticket.assigned_squad:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Forbidden: You are not authorized to update ticket #{ticket_id}. "
                    f"It is currently assigned to squad '{ticket.assigned_squad}', but request specified '{request_squad}'."
                ),
            )

    # 4. Commit State Transition
    now = datetime.utcnow()
    ticket.status = target_status
    ticket.updated_at = now

    if target_status == "resolved":
        ticket.resolved_at = now
    elif target_status == "pending":
        # Released back to queue
        ticket.assigned_squad = None
        ticket.claimed_by_user_id = None
        ticket.claimed_at = None

    db.commit()
    db.refresh(ticket)

    return TicketStatusUpdateResponse(
        success=True,
        message=f"Ticket #{ticket_id} status transitioned from '{prev_status}' to '{target_status}'.",
        ticket_id=ticket.id,
        previous_status=prev_status,
        new_status=ticket.status,
        assigned_squad=ticket.assigned_squad,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
        is_simulated_data=True,
    )
