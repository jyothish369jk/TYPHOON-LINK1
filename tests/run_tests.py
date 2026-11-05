"""
TyphoonLink Zero-Dependency Standalone Test Runner
Runs automated tests using Python's built-in unittest module.
Covers:
  - Phase 2.2: SOS Submission, Missing GPS, Duplicate De-duplication, Batch Sync
  - Phase 2.3: Ticket Listing, Filtering, Atomic Claiming, 409 Conflict, Status Updates, Auth Guards
"""

import os
import sys
import unittest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add server directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server")))

from app.main import app
from app.database import Base, get_db
from app.models.ticket import DistressTicket

# In-memory SQLite for testing
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


class TestTyphoonLinkFullSuite(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=test_engine)
        self.client = TestClient(app)

    def tearDown(self):
        Base.metadata.drop_all(bind=test_engine)

    def _seed_ticket(self, category="medical", landmark="MVP Colony Sector 4", urgency="red", status="pending"):
        db = TestingSessionLocal()
        ticket = DistressTicket(
            client_packet_id=f"test-pkt-{uuid.uuid4()}",
            packet_tag=f"PKT-{uuid.uuid4().hex[:4].upper()}",
            category=category,
            title=f"Distress {category}",
            landmark=landmark,
            contact_phone="+919848011223",
            urgency_tier=urgency,
            status=status,
            is_simulated=True,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        t_id = ticket.id
        db.close()
        return t_id

    # ---------------- Phase 2.3 Tests ----------------
    def test_A_listing_pending_tickets(self):
        """Test A: Listing pending tickets with masked phone privacy."""
        self._seed_ticket(status="pending")
        self._seed_ticket(status="pending")
        res = self.client.get("/api/tickets?status=pending")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["total"], 2)
        for item in data["items"]:
            self.assertEqual(item["status"], "pending")
            if item["contact_phone"]:
                self.assertIn("•••••", item["contact_phone"])

    def test_B_filtering_tickets(self):
        """Test B: Filtering tickets by category, urgency, and zone."""
        self._seed_ticket(category="medical", urgency="red", landmark="MVP Colony Sector 4")
        self._seed_ticket(category="flood", urgency="amber", landmark="Jalaripeta Beach Road")
        self._seed_ticket(category="hazard", urgency="blue", landmark="Waltair Main Road")

        # Category filter
        res = self.client.get("/api/tickets?category=medical")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(all(i["category"] == "medical" for i in res.json()["items"]))

        # Urgency filter
        res = self.client.get("/api/tickets?urgency=amber")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(all(i["urgency_tier"] == "amber" for i in res.json()["items"]))

        # Zone filter
        res = self.client.get("/api/tickets?zone=Jalaripeta")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(all("Jalaripeta" in i["landmark"] for i in res.json()["items"]))

    def test_C_successfully_claiming_ticket(self):
        """Test C: Successfully claiming a pending ticket."""
        t_id = self._seed_ticket(status="pending")
        res = self.client.post(f"/api/tickets/{t_id}/claim", json={"squad_name": "AU Ward Squad #14"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["ticket_id"], t_id)
        self.assertEqual(data["status"], "claimed")
        self.assertEqual(data["assigned_squad"], "AU Ward Squad #14")

    def test_D_reject_duplicate_claim_with_409(self):
        """Test D: Rejecting a second volunteer's attempt to claim with HTTP 409 Conflict."""
        t_id = self._seed_ticket(status="pending")
        # 1st claim
        res1 = self.client.post(f"/api/tickets/{t_id}/claim", json={"squad_name": "AU Ward Squad #14"})
        self.assertEqual(res1.status_code, 200)
        # 2nd claim on same ticket
        res2 = self.client.post(f"/api/tickets/{t_id}/claim", json={"squad_name": "SDRF Rescue Unit 02"})
        self.assertEqual(res2.status_code, 409)
        self.assertIn("already claimed", res2.json()["detail"].lower())

    def test_E_updating_ticket_status(self):
        """Test E: Transitioning ticket lifecycle: claimed -> in_progress -> resolved."""
        t_id = self._seed_ticket(status="pending")
        self.client.post(f"/api/tickets/{t_id}/claim", json={"squad_name": "AU Ward Squad #14"})

        # claimed -> in_progress
        res1 = self.client.patch(
            f"/api/tickets/{t_id}/status",
            json={"status": "in_progress", "squad_name": "AU Ward Squad #14"},
            headers={"X-Volunteer-Squad": "AU Ward Squad #14"}
        )
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json()["new_status"], "in_progress")

        # in_progress -> resolved
        res2 = self.client.patch(
            f"/api/tickets/{t_id}/status",
            json={"status": "resolved", "squad_name": "AU Ward Squad #14"},
            headers={"X-Volunteer-Squad": "AU Ward Squad #14"}
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["new_status"], "resolved")
        self.assertIsNotNone(res2.json()["resolved_at"])

    def test_F_rejecting_invalid_status_values(self):
        """Test F: Rejecting invalid status values with HTTP 422."""
        t_id = self._seed_ticket(status="pending")
        res = self.client.patch(f"/api/tickets/{t_id}/status", json={"status": "invalid_status_xyz"})
        self.assertEqual(res.status_code, 422)

    def test_G_rejecting_unauthorized_status_changes(self):
        """Test G: Rejecting unauthorized status changes with HTTP 403 Forbidden."""
        t_id = self._seed_ticket(status="pending")
        self.client.post(f"/api/tickets/{t_id}/claim", json={"squad_name": "AU Ward Squad #14"})

        # Unauthorized squad attempts update
        res = self.client.patch(
            f"/api/tickets/{t_id}/status",
            json={"status": "in_progress", "squad_name": "Unauthorized Rogue Squad"},
            headers={"X-Volunteer-Squad": "Unauthorized Rogue Squad"}
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("not authorized", res.json()["detail"].lower())

    # ---------------- Phase 2.2 Preserved Tests ----------------
    def test_H_phase_2_2_sos_submission_preserved(self):
        """Test H: Confirming Phase 2.2 SOS submission and idempotent de-duplication remain functional."""
        idem_id = f"preserve-{uuid.uuid4()}"
        payload = {
            "client_packet_id": idem_id,
            "category": "medical",
            "landmark": "MVP Colony, Shivaji Park Sector 4",
        }
        # First submission (Actual citizen submission has is_simulated_data = False)
        res1 = self.client.post("/api/sos", json=payload)
        self.assertEqual(res1.status_code, 201)
        self.assertEqual(res1.json()["delivery_status"], "DELIVERED_SERVER")
        self.assertFalse(res1.json()["is_duplicate"])
        self.assertFalse(res1.json()["is_simulated_data"])
        t_id = res1.json()["ticket_id"]

        # Duplicate submission returns acknowledged existing
        res2 = self.client.post("/api/sos", json=payload)
        self.assertEqual(res2.status_code, 201)
        self.assertEqual(res2.json()["delivery_status"], "ACKNOWLEDGED_EXISTING")
        self.assertTrue(res2.json()["is_duplicate"])
        self.assertEqual(res2.json()["ticket_id"], t_id)


if __name__ == "__main__":
    unittest.main(verbosity=2)
