"""
TyphoonLink SOS API Automated Test Suite
Verifies:
  A. Valid SOS submission.
  B. SOS without GPS coordinates (mandatory landmark only).
  C. Invalid category rejection (422 Unprocessable Entity).
  D. Idempotent de-duplication on duplicate client_packet_id.
  E. Batch synchronization of multiple offline-queued packets.
  F. Database verification showing zero duplicate tickets in SQLite.
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add server directory to sys.path so app imports resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))

from app.main import app
from app.database import Base, get_db
from app.models.ticket import DistressTicket

# Use an isolated in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Create a fresh database for each test session."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# TEST A: Valid SOS Submission
# =========================================================================
def test_valid_sos_submission(client):
    packet_id = f"test-{uuid.uuid4()}"
    payload = {
        "client_packet_id": packet_id,
        "packet_tag": "PKT-1001",
        "category": "medical",
        "title": "Severe Trauma from Wall Collapse",
        "telugu_title": "గోడ కూలి తీవ్ర గాయాలు",
        "description": "Victim sustained head injury from collapsed compound wall.",
        "landmark": "MVP Colony, Sector 4, House 12-4",
        "latitude": 17.7231,
        "longitude": 83.3218,
        "gps_accuracy_meters": 5.0,
        "contact_phone": "+919848011223",
        "urgency_tier": "red"
    }

    response = client.post("/api/sos", json=payload)
    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert data["delivery_status"] == "DELIVERED_SERVER"
    assert data["client_packet_id"] == packet_id
    assert data["packet_tag"] == "PKT-1001"
    assert data["category"] == "medical"
    assert data["is_duplicate"] is False
    assert data["is_simulated_data"] is False
    assert data["ticket_id"] > 0
    assert data["status"] == "pending"


# =========================================================================
# TEST B: SOS Without GPS Coordinates (Landmark-only)
# =========================================================================
def test_sos_without_gps_coordinates(client):
    packet_id = f"test-{uuid.uuid4()}"
    payload = {
        "client_packet_id": packet_id,
        "category": "flood",
        "title": "High Tide Inundation on Ground Floor",
        "landmark": "Jalaripeta Fishermen Village, Behind Community Hall, Ward 18",
        # latitude and longitude deliberately omitted
        "contact_phone": "+919848099887",
        "urgency_tier": "red"
    }

    response = client.post("/api/sos", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["delivery_status"] == "DELIVERED_SERVER"
    assert data["client_packet_id"] == packet_id
    assert data["is_duplicate"] is False

    # Verify in database that GPS coordinates are stored as NULL
    db = TestingSessionLocal()
    ticket = db.query(DistressTicket).filter(DistressTicket.client_packet_id == packet_id).first()
    assert ticket is not None
    assert ticket.landmark == "Jalaripeta Fishermen Village, Behind Community Hall, Ward 18"
    assert ticket.latitude is None
    assert ticket.longitude is None
    db.close()


# =========================================================================
# TEST C: Invalid Category Rejection (Validation Guard)
# =========================================================================
def test_invalid_category_rejection(client):
    payload = {
        "category": "unsupported_category_name",
        "landmark": "Beach Road, Visakhapatnam",
        "description": "Test distress message"
    }

    response = client.post("/api/sos", json=payload)
    # Pydantic v2 must reject invalid category with 422 Unprocessable Entity
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


# =========================================================================
# TEST D: Duplicate client_packet_id Handling (Idempotency)
# =========================================================================
def test_duplicate_client_packet_id_handling(client):
    idempotent_id = f"idempotent-uuid-{uuid.uuid4()}"
    payload = {
        "client_packet_id": idempotent_id,
        "packet_tag": "PKT-IDEM",
        "category": "supplies",
        "landmark": "AU Campus South Gate, Siripuram",
        "description": "Infant formula milk needed urgently"
    }

    # First submission: Must create new ticket
    res1 = client.post("/api/sos", json=payload)
    assert res1.status_code == 201
    data1 = res1.json()
    assert data1["delivery_status"] == "DELIVERED_SERVER"
    assert data1["is_duplicate"] is False
    original_ticket_id = data1["ticket_id"]

    # Second submission with the exact same client_packet_id: Must NOT create another ticket
    res2 = client.post("/api/sos", json=payload)
    assert res2.status_code == 201
    data2 = res2.json()
    assert data2["delivery_status"] == "ACKNOWLEDGED_EXISTING"
    assert data2["is_duplicate"] is True
    # Returned ticket_id must match original
    assert data2["ticket_id"] == original_ticket_id


# =========================================================================
# TEST E: Batch Sync With Multiple Packets (Offline Queue Flush)
# =========================================================================
def test_batch_sync_with_multiple_packets(client):
    id_dup = f"batch-dup-{uuid.uuid4()}"
    id_new1 = f"batch-new1-{uuid.uuid4()}"
    id_new2 = f"batch-new2-{uuid.uuid4()}"

    # Pre-seed one ticket so it's recognized as duplicate in the sync batch
    client.post("/api/sos", json={
        "client_packet_id": id_dup,
        "packet_tag": "PKT-PRE1",
        "category": "hazard",
        "landmark": "Waltair Main Road, Near Siripuram",
        "description": "Tree fallen on road"
    })

    batch_payload = {
        "packets": [
            {
                "client_packet_id": id_dup,  # Duplicate
                "category": "hazard",
                "landmark": "Waltair Main Road, Near Siripuram",
                "description": "Tree fallen on road"
            },
            {
                "client_packet_id": id_new1, # New packet 1
                "category": "medical",
                "landmark": "MVP Sector 2, Water Tank",
                "description": "Diabetic patient insulin emergency"
            },
            {
                "client_packet_id": id_new2, # New packet 2
                "category": "supplies",
                "landmark": "RK Beach Road, Submerged Fishing Shacks",
                "description": "Fresh water cans needed"
            }
        ]
    }

    response = client.post("/api/sos/sync", json=batch_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["delivery_status"] == "BATCH_PROCESSED"
    assert data["total_received"] == 3
    assert data["new_tickets_created"] == 2
    assert data["duplicates_acknowledged"] == 1
    assert len(data["results"]) == 3


# =========================================================================
# TEST F: Database Verification Showing No Duplicate Tickets
# =========================================================================
def test_database_verification_no_duplicates(client):
    target_id = f"strict-no-dup-{uuid.uuid4()}"
    payload = {
        "client_packet_id": target_id,
        "category": "hazard",
        "landmark": "Lawsons Bay Colony, Beach Junction",
        "description": "Live electric pole sparking"
    }

    # Submit 3 times consecutively
    client.post("/api/sos", json=payload)
    client.post("/api/sos", json=payload)
    client.post("/api/sos", json=payload)

    # Inspect database directly
    db = TestingSessionLocal()
    records = db.query(DistressTicket).filter(DistressTicket.client_packet_id == target_id).all()
    assert len(records) == 1, f"Expected exactly 1 record in database, found {len(records)}!"
    assert records[0].client_packet_id == target_id
    db.close()


if __name__ == "__main__":
    pytest.main(["-v", __file__])
