from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


# Supported Lifecycle Statuses (Strict Consistency)
TicketStatus = Literal["pending", "claimed", "in_progress", "resolved"]


def mask_phone_number(phone: Optional[str]) -> Optional[str]:
    """
    Mask citizen phone number for public feeds to protect privacy.
    e.g., '+919848022338' -> '+91 98480 •••••'
    """
    if not phone:
        return None
    phone_clean = phone.strip()
    if len(phone_clean) <= 6:
        return "••••••"
    return phone_clean[:6] + " •••••"


class TicketResponse(BaseModel):
    """
    Volunteer Triage Feed item representation.
    Phone number is masked by default to protect citizen privacy.
    """
    id: int
    client_packet_id: str
    packet_tag: Optional[str] = None
    category: str
    title: str
    telugu_title: Optional[str] = None
    description: Optional[str] = None
    landmark: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_accuracy_meters: Optional[float] = None
    contact_phone: Optional[str] = Field(
        None,
        description="Masked contact phone for citizen privacy in public triage feed"
    )
    urgency_tier: str
    status: str
    assigned_squad: Optional[str] = None
    claimed_by_user_id: Optional[int] = None
    claimed_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    is_simulated: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    """
    Paginated list of triage tickets.
    """
    total: int
    skip: int
    limit: int
    items: List[TicketResponse]
    is_simulated_data: bool = True


class TicketClaimRequest(BaseModel):
    """
    Payload for claiming a pending ticket.
    """
    squad_name: Optional[str] = Field(
        "AU Ward Squad #14",
        max_length=64,
        description="Squad claiming lead responsibility (e.g., AU Ward Squad #14, SDRF Team 04)"
    )
    volunteer_id: Optional[int] = Field(
        None,
        description="Optional registered responder ID from users table"
    )
    volunteer_name: Optional[str] = Field(
        None,
        max_length=128,
        description="Lead volunteer name for squad record"
    )


class TicketClaimResponse(BaseModel):
    """
    Response confirming successful atomic ticket claim.
    """
    success: bool = True
    message: str
    ticket_id: int
    status: str = "claimed"
    assigned_squad: str
    claimed_at: datetime
    is_simulated_data: bool = True


class TicketStatusUpdateRequest(BaseModel):
    """
    Request to transition ticket lifecycle state.
    Supported: pending, claimed, in_progress (or en_route), resolved
    """
    status: TicketStatus = Field(
        ...,
        description="Target status: pending, claimed, in_progress, resolved"
    )
    squad_name: Optional[str] = Field(
        None,
        description="Operating squad name verifying authorization"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Field operational notes (e.g. O2 cylinder delivered, patient stabilized)"
    )


class TicketStatusUpdateResponse(BaseModel):
    """
    Response confirming state transition and audit timestamp.
    """
    success: bool = True
    message: str
    ticket_id: int
    previous_status: str
    new_status: str
    assigned_squad: Optional[str] = None
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    is_simulated_data: bool = True
