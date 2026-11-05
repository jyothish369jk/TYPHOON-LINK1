"""
TyphoonLink Phase 2.3 Volunteer Ticket Management Test Suite
Verifies:
  A. Listing pending tickets.
  B. Filtering tickets by status, category, urgency, and zone.
  C. Successfully claiming a ticket.
  D. Rejecting a second volunteer's attempt to claim the same ticket (HTTP 409 Conflict).
  E. Updating a ticket status (claimed -> in_progress -> resolved).
  F. Rejecting invalid status values.
  G. Rejecting unauthorized status changes (forbidden).
  H. Confirming Phase 2.2 SOS submission and duplicate handling still work.
"""

import os
import sys
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add server directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))

from app.main import app
from app.database import Base, get_db
from app.models.ticket import DistressTicket

# In-memory SQLite for test isolation
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


# Helper function to seed test tickets
def seed_test_ticket(category="medical", landmark="MVP Colony Sector 4", urgency="red", status="pending", phone="+919848011223"):
    db = TestingSessionLocal()
    ticket = DistressTicket(
        client_packet_id=f"test-pkt-{uuid.uuid4()}",
        packet_tag=f"PKT-{uuid.uuid4().hex[:4].upper()}",
        category=category,
        title=f"Emergency distress {category}",
        telugu_title="అత్యవసర సమాచారం",
        description="Trapped civilian needing assistance",
        landmark=landmark,
        contact_phone=phone,
        urgency_tier=urgency,
        status=status,
        is_simulated=True,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    ticket_id = ticket.id
    db.close()
    return ticket_id


# =========================================================================
# TEST A: Listing Pending Tickets
# =========================================================================
def test_A_list_pending_tickets(client):
    id1 = seed_test_ticket(status="pending", category="medical")
    id2 = seed_test_ticket(status="pending", category="flood")

    res = client.get("/api/tickets?status=pending")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 2
    assert len(data["items"]) >= 2
    # Verify phone privacy masking in public feed
    for item in data["items"]:
        assert item["status"] == "pending"
        if item["contact_phone"]:
            assert "•••••" in item["contact_phone"]


# =========================================================================
# TEST B: Filtering Tickets by Category, Urgency, and Zone
# =========================================================================
def test_B_filter_tickets(client):
    seed_test_ticket(category="medical", urgency="red", landmark="MVP Colony Sector 4")
    seed_test_ticket(category="flood", urgency="amber", landmark="Jalaripeta Beach Road")
    seed_test_ticket(category="hazard", urgency="blue", landmark="Waltair Main Road")

    # Filter by category
    res_cat = client.get("/api/tickets?category=medical")
    assert res_cat.status_code == 200
    items_cat = res_cat.json()["items"]
    assert all(i["category"] == "medical" for i in items_cat)

    # Filter by urgency
    res_urg = client.get("/api/tickets?urgency=amber")
    assert res_urg.status_code == 200
    items_urg = res_urg.json()["items"]
    assert all(i["urgency_tier"] == "amber" for i in items_urg)

    # Filter by zone / landmark text
    res_zone = client.get("/api/tickets?zone=Jalaripeta")
    assert res_zone.status_code == 200
    items_zone = res_zone.json()["items"]
    assert all("Jalaripeta" in i["landmark"] for i in items_zone)


# =========================================================================
# TEST C: Successfully Claiming a Ticket
# =========================================================================
def test_C_claim_ticket_success(client):
    ticket_id = seed_test_ticket(status="pending")

    claim_payload = {
        "squad_name": "AU Ward Squad #14",
        "volunteer_id": 1,
        "volunteer_name": "K. Ramanathan"
    }

    res = client.post(f"/api/tickets/{ticket_id}/claim", json=claim_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["ticket_id"] == ticket_id
    assert data["status"] == "claimed"
    assert data["assigned_squad"] == "AU Ward Squad #14"


# =========================================================================
# TEST D: Rejecting a Second Volunteer's Attempt to Claim the Same Ticket
# =========================================================================
def test_D_reject_duplicate_claim(client):
    ticket_id = seed_test_ticket(status="pending")

    # Volunteer 1 claims
    res1 = client.post(f"/api/tickets/{ticket_id}/claim", json={"squad_name": "AU Ward Squad #14"})
    assert res1.status_code == 200

    # Volunteer 2 attempts to claim the same ticket
    res2 = client.post(f"/api/tickets/{ticket_id}/claim", json={"squad_name": "SDRF Rescue Team 02"})
    # Must reject with HTTP 409 Conflict
    assert res2.status_code == 409
    data2 = res2.json()
    assert "already claimed" in data2["detail"].lower()


# =========================================================================
# TEST E: Updating Ticket Status (State Machine)
# =========================================================================
def test_E_update_ticket_status(client):
    ticket_id = seed_test_ticket(status="pending")

    # Step 1: Claim
    client.post(f"/api/tickets/{ticket_id}/claim", json={"squad_name": "AU Ward Squad #14"})

    # Step 2: Transition claimed -> in_progress
    res_prog = client.patch(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "in_progress", "squad_name": "AU Ward Squad #14"},
        headers={"X-Volunteer-Squad": "AU Ward Squad #14", "X-User-Role": "volunteer"}
    )
    assert res_prog.status_code == 200
    assert res_prog.json()["new_status"] == "in_progress"

    # Step 3: Transition in_progress -> resolved
    res_res = client.patch(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "resolved", "squad_name": "AU Ward Squad #14"},
        headers={"X-Volunteer-Squad": "AU Ward Squad #14", "X-User-Role": "volunteer"}
    )
    assert res_res.status_code == 200
    assert res_res.json()["new_status"] == "resolved"
    assert res_res.json()["resolved_at"] is not None


# =========================================================================
# TEST F: Rejecting Invalid Status Values
# =========================================================================
def test_F_reject_invalid_status(client):
    ticket_id = seed_test_ticket(status="pending")

    # Attempt to transition with invalid status string
    res = client.patch(f"/api/tickets/{ticket_id}/status", json={"status": "non_existent_status"})
    assert res.status_code == 422  # Pydantic schema validation rejects invalid status


# =========================================================================
# TEST G: Rejecting Unauthorized Status Changes
# =========================================================================
def test_G_reject_unauthorized_status_change(client):
    ticket_id = seed_test_ticket(status="pending")

    # Claimed by Squad #14
    client.post(f"/api/tickets/{ticket_id}/claim", json={"squad_name": "AU Ward Squad #14"})

    # Unauthorized squad (e.g. Rogue Squad #99) attempts to update status
    res = client.patch(
        f"/api/tickets/{ticket_id}/status",
        json={"status": "in_progress", "squad_name": "Rogue Squad #99"},
        headers={"X-Volunteer-Squad": "Rogue Squad #99", "X-User-Role": "volunteer"}
    )
    assert res.status_code == 403
    assert "not authorized" in res.json()["detail"].lower()


# =========================================================================
# TEST H: Confirming Existing Phase 2.2 SOS Submission Still Works
# =========================================================================
def test_H_sos_submission_and_duplicate_handling_preserved(client):
    idem_id = f"test-preserve-{uuid.uuid4()}"
    payload = {
        "client_packet_id": idem_id,
        "packet_tag": "PKT-PRESERVE",
        "category": "medical",
        "landmark": "MVP Colony, Shivaji Park Sector 4",
        "urgency_tier": "red"
    }

    # 1. Normal submission (Actual citizen submission has is_simulated_data = False)
    res1 = client.post("/api/sos", json=payload)
    assert res1.status_code == 201
    assert res1.json()["delivery_status"] == "DELIVERED_SERVER"
    assert res1.json()["is_duplicate"] is False
    assert res1.json()["is_simulated_data"] is False
    orig_id = res1.json()["ticket_id"]

    # 2. Duplicate submission
    res2 = client.post("/api/sos", json=payload)
    assert res2.status_code == 201
    assert res2.json()["delivery_status"] == "ACKNOWLEDGED_EXISTING"
    assert res2.json()["is_duplicate"] is True
    assert res2.json()["ticket_id"] == orig_id
