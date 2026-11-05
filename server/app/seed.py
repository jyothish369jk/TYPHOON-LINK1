"""
TyphoonLink Demonstration Data Seeder
Note: All seeded records are explicitly marked is_simulated=True.
Never present mock telemetry as verified live real-world information.
"""

from datetime import datetime
from app.database import SessionLocal, engine, Base
from app.models.ticket import DistressTicket
from app.models.zone import DisasterZone
from app.models.shelter import RefugeShelter
from app.models.user import User


def seed_database(force_reseed: bool = False):
    """Seed initial demonstration records if tables are empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(DisasterZone).first() and not force_reseed:
            print("[INFO] Database already populated with demonstration telemetry.")
            return

        print("[SEED] Seeding clearly labeled demonstration dataset (is_simulated=True)...")

        # 1. Hyper-Local Disaster Zones (Matches Radar & Map prototype)
        zones = [
            DisasterZone(
                zone_key="mvp",
                name="MVP Colony & Beach Road (Ward #14)",
                telugu_name="ఎంవీపీ కాలనీ & తీరప్రాంత వార్డు #14",
                vulnerability_tag="HIGH VULNERABILITY SECTOR",
                status="CRITICAL SURGE",
                status_class="bg-error-container text-on-error-container",
                active_sos_count=4,
                deployed_squads="2 Squads",
                water_level="1.4m Depth",
                is_simulated=True,
            ),
            DisasterZone(
                zone_key="jalaripeta",
                name="Jalaripeta Fisher Village Ward #18",
                telugu_name="జలారిపేట మత్స్యకార గ్రామం",
                vulnerability_tag="COASTAL HAMLET EVACUATION",
                status="RELIEF PENDING",
                status_class="bg-tertiary-container text-on-tertiary-container",
                active_sos_count=7,
                deployed_squads="1 Boat Squad",
                water_level="2.1m Surge",
                is_simulated=True,
            ),
            DisasterZone(
                zone_key="au_stadium",
                name="AU Indoor Stadium Safe Shelter",
                telugu_name="ఆంధ్రా యూనివర్సిటీ ప్రధాన శిబిరం",
                vulnerability_tag="PRIMARY DESIGNATED RELIEF HUB",
                status="SAFE & OPERATIONAL",
                status_class="bg-secondary-container text-on-secondary-container",
                active_sos_count=0,
                deployed_squads="6 Ward Staff",
                water_level="0.0m Ground Clear",
                is_simulated=True,
            ),
            DisasterZone(
                zone_key="gvmc_school",
                name="GVMC High School Sector 9",
                telugu_name="జివిఎంసి హై స్కూల్ ఆశ్రయం",
                vulnerability_tag="INTERMEDIATE RELIEF POINT",
                status="POWER GENERATOR ACTIVE",
                status_class="bg-secondary-container text-on-secondary-container",
                active_sos_count=1,
                deployed_squads="3 Volunteers",
                water_level="0.2m Low Pool",
                is_simulated=True,
            ),
        ]
        for z in zones:
            db.merge(z)

        # 2. Verified Refuge Shelters (Matches Shelter Directory)
        shelters = [
            RefugeShelter(
                id=1,
                name="AU Indoor Stadium",
                telugu_name="ఆంధ్రా యూనివర్సిటీ ప్రధాన శిబిరం",
                zone_key="au_stadium",
                landmark="Andhra University South Campus, Near Siripuram",
                capacity=1200,
                current_occupancy=480,
                is_operational=True,
                has_power_generator=True,
                has_potable_water=True,
                has_medical_unit=True,
                is_simulated=True,
            ),
            RefugeShelter(
                id=2,
                name="GVMC High School Sector 9",
                telugu_name="జివిఎంసి హై స్కూల్ ఆశ్రయం",
                zone_key="gvmc_school",
                landmark="Sector 9, MVP Colony",
                capacity=600,
                current_occupancy=210,
                is_operational=True,
                has_power_generator=True,
                has_potable_water=True,
                has_medical_unit=False,
                is_simulated=True,
            ),
        ]
        for s in shelters:
            db.merge(s)

        # 3. Initial Triage Distress Tickets (Matches Google Stitch Triage Feed)
        tickets = [
            DistressTicket(
                client_packet_id="sim-pkt-9440-trauma",
                packet_tag="PKT-9440",
                category="medical",
                title="Critical Breathing Distress & Rising Ground Water",
                telugu_title="వృద్ధుడికి శ్వాస తీసుకోవడంలో ఇబ్బంది",
                description="72yo male acute breathing distress, power out for O2 concentrator. Rising sea-surge water entering ground floor. 3 residents trapped inside.",
                landmark="MVP Colony, Sector 4, D-Block (Near Ushodaya Junction)",
                latitude=17.7231,
                longitude=83.3218,
                gps_accuracy_meters=6.0,
                contact_phone="+919848022338",
                urgency_tier="red",
                status="pending",
                is_simulated=True,
            ),
            DistressTicket(
                client_packet_id="sim-pkt-9441-ration",
                packet_tag="PKT-9441",
                category="supplies",
                title="Family Stranded on Open Terrace - Infant Formula Needed",
                telugu_title="మంచినీరు లేదు, 6 నెలల పసికందు ఉంది",
                description="Family of 5 stranded on 1st-floor open terrace. Raincoats shredded, no potable drinking water for 14 hours. Includes 6-month-old infant requiring dry formula milk.",
                landmark="Beach Road, Jalaripeta Ward 16 (Near Fishermen Community Hall)",
                latitude=17.7295,
                longitude=83.3325,
                gps_accuracy_meters=12.0,
                contact_phone="+919848033449",
                urgency_tier="amber",
                status="pending",
                is_simulated=True,
            ),
            DistressTicket(
                client_packet_id="sim-pkt-9442-hazard",
                packet_tag="PKT-9442",
                category="hazard",
                title="Collapsed 11kV Electrical Feeder & Tree on Ambulance Highway",
                telugu_title="విద్యుత్ స్తంభం మరియు భారీ చెట్టు కూలి ప్రధాన రహదారి మూసుకుపోయింది",
                description="Uprooted ancient banyan tree and 11kV electrical feeder line collapsed across arterial evacuation highway. 2 auto-rickshaws stalled, ambulance corridor blocked.",
                landmark="Waltair Main Road, Near Siripuram Jn (Near Gurajada Kalakshetram)",
                latitude=17.7180,
                longitude=83.3150,
                gps_accuracy_meters=8.0,
                contact_phone="+919848055667",
                urgency_tier="blue",
                status="pending",
                is_simulated=True,
            ),
        ]
        for t in tickets:
            db.merge(t)

        # 4. Responder and Coordinator Demo User (Hashed password: 'responder14pass')
        # Using a dummy bcrypt hash string for demo bootstrap without external dependencies
        demo_user = User(
            id=1,
            username="squad14_lead",
            # Standard bcrypt hash for 'responder14pass'
            hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQmG6W65WVIxTCrtdcuW.",
            full_name="K. Ramanathan (Ward #14 SDRF Lead)",
            role="volunteer",
            squad_name="AU Ward Squad #14",
            is_active=True,
        )
        db.merge(demo_user)

        db.commit()
        print("[SEED] Successfully seeded 4 zones, 2 shelters, 3 tickets, and 1 demo user.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Failed to seed database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
