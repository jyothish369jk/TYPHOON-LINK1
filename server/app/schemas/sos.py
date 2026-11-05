import re
import uuid
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# Allowed category whitelist
SOSCategory = Literal["medical", "flood", "supplies", "hazard"]
SOSUrgency = Literal["red", "amber", "blue"]


class SOSCreate(BaseModel):
    """
    Client SOS Distress Beacon Submission Payload.
    Enforces required landmark and optional GPS coordinates.
    """
    # Unique client packet ID: If provided by IndexedDB, validated; if omitted, generated
    client_packet_id: Optional[str] = Field(
        None,
        max_length=64,
        description="Client-assigned unique packet UUID for idempotent synchronization"
    )
    packet_tag: Optional[str] = Field(
        None,
        max_length=32,
        description="Human-readable broadcast label (e.g., PKT-9440)"
    )

    # Category validation (medical, flood, supplies, hazard)
    category: SOSCategory = Field(
        ...,
        description="Emergency classification: medical, flood, supplies, hazard"
    )

    title: Optional[str] = Field(
        None,
        max_length=128,
        description="Short summary headline"
    )
    telugu_title: Optional[str] = Field(
        None,
        max_length=128,
        description="Vernacular Telugu emergency summary"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Distress situation details (capped at 1000 chars to prevent payload abuse)"
    )

    # Mandatory Landmark/Locality: Enables distress reporting without active GPS lock
    landmark: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Mandatory landmark or street description (e.g., MVP Colony Sector 4 near Ushodaya Jn)"
    )

    # Optional GPS Coordinates: Strictly nullable when satellite lock is absent
    latitude: Optional[float] = Field(
        None,
        ge=-90.0,
        le=90.0,
        description="Optional GPS latitude (WGS84)"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180.0,
        le=180.0,
        description="Optional GPS longitude (WGS84)"
    )
    gps_accuracy_meters: Optional[float] = Field(
        None,
        ge=0.0,
        le=5000.0,
        description="GPS estimated horizontal accuracy in meters"
    )

    # Caller Privacy: Contact phone is masked for public triage feeds
    contact_phone: Optional[str] = Field(
        None,
        max_length=32,
        description="Caller contact number for rescue dispatch (masked in public feeds)"
    )

    # Urgency tier
    urgency_tier: Optional[SOSUrgency] = Field(
        "red",
        description="Triage urgency: red (critical life threat), amber (rations), blue (infrastructure)"
    )

    @field_validator("landmark")
    @classmethod
    def sanitize_landmark(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 3:
            raise ValueError("Landmark must contain at least 3 characters.")
        # Prevent HTML injection
        cleaned = re.sub(r"[<>]", "", cleaned)
        return cleaned

    @field_validator("client_packet_id", mode="before")
    @classmethod
    def default_packet_id(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            return f"pkt-{uuid.uuid4()}"
        return v.strip()

    @field_validator("packet_tag", mode="before")
    @classmethod
    def default_packet_tag(cls, v: Optional[str]) -> str:
        if not v or not v.strip():
            hex_part = uuid.uuid4().hex[:4].upper()
            return f"PKT-{hex_part}"
        return v.strip().upper()


class SOSResponse(BaseModel):
    """
    Authoritative server delivery confirmation.
    Clearly indicates whether a new ticket was created or an existing packet was acknowledged.
    """
    delivery_status: Literal["DELIVERED_SERVER", "ACKNOWLEDGED_EXISTING"] = Field(
        ...,
        description="Explicit delivery status confirming database transaction commitment"
    )
    ticket_id: int
    client_packet_id: str
    packet_tag: str
    category: str
    landmark: str
    status: str
    urgency_tier: str
    server_timestamp: datetime
    is_duplicate: bool = False
    is_simulated_data: bool = True
    message: str


class SOSSyncBatchRequest(BaseModel):
    """
    Batch payload for flushing offline-queued SOS packets from IndexedDB.
    """
    packets: List[SOSCreate] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of queued client packets to synchronize (max 50 per batch)"
    )


class SOSSyncBatchResponse(BaseModel):
    """
    Batch synchronization summary report.
    """
    delivery_status: str = "BATCH_PROCESSED"
    total_received: int
    new_tickets_created: int
    duplicates_acknowledged: int
    results: List[SOSResponse]
    server_timestamp: datetime
    is_simulated_data: bool = True
