-- TyphoonLink Central Server Database Schema (SQLite)
-- Note: Clearly segregated from on-device client IndexedDB.
-- All demonstration records are marked is_simulated = 1.

PRAGMA foreign_keys = ON;

-- 1. Users Table (Responders, Admins, Dispatchers)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(64) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(128),
    role VARCHAR(32) NOT NULL DEFAULT 'volunteer', -- 'volunteer', 'admin', 'dispatcher'
    squad_name VARCHAR(64),                        -- e.g. 'AU Ward Squad #14'
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 2. Disaster Zones Table (Hyper-local grid telemetry)
CREATE TABLE IF NOT EXISTS disaster_zones (
    zone_key VARCHAR(32) PRIMARY KEY,              -- 'mvp', 'jalaripeta', 'au_stadium', 'gvmc_school'
    name VARCHAR(128) NOT NULL,
    telugu_name VARCHAR(128) NOT NULL,
    vulnerability_tag VARCHAR(64) NOT NULL,
    status VARCHAR(64) NOT NULL,                   -- 'CRITICAL SURGE', 'RELIEF PENDING', 'SAFE & OPERATIONAL'
    status_class VARCHAR(64) NOT NULL,             -- Tailwind styling class
    active_sos_count INTEGER NOT NULL DEFAULT 0,
    deployed_squads VARCHAR(64) NOT NULL,
    water_level VARCHAR(32) NOT NULL,
    is_simulated BOOLEAN NOT NULL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 3. Refuge Shelters Table (Verified safe shelters)
CREATE TABLE IF NOT EXISTS refuge_shelters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(128) NOT NULL,
    telugu_name VARCHAR(128) NOT NULL,
    zone_key VARCHAR(32) NOT NULL,
    landmark VARCHAR(255) NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 500,
    current_occupancy INTEGER NOT NULL DEFAULT 0,
    is_operational BOOLEAN NOT NULL DEFAULT 1,
    has_power_generator BOOLEAN NOT NULL DEFAULT 1,
    has_potable_water BOOLEAN NOT NULL DEFAULT 1,
    has_medical_unit BOOLEAN NOT NULL DEFAULT 0,
    is_simulated BOOLEAN NOT NULL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_shelters_zone_key ON refuge_shelters(zone_key);

-- 4. Distress Tickets Table (SOS Beacons & Field Distress)
CREATE TABLE IF NOT EXISTS distress_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_packet_id VARCHAR(64) UNIQUE NOT NULL,  -- Unique client UUID for idempotent de-duplication
    packet_tag VARCHAR(32),                        -- 'PKT-9440'
    category VARCHAR(32) NOT NULL DEFAULT 'medical', -- 'medical', 'flood', 'supplies', 'hazard'
    title VARCHAR(128) NOT NULL,
    telugu_title VARCHAR(128),
    description TEXT,
    landmark VARCHAR(255) NOT NULL,                -- Mandatory for landmark/locality-based reporting
    latitude REAL,                                 -- Strictly optional (null when GPS unavailable)
    longitude REAL,                                -- Strictly optional (null when GPS unavailable)
    gps_accuracy_meters REAL,
    contact_phone VARCHAR(32),                     -- Masked on public triage feed for privacy
    urgency_tier VARCHAR(16) NOT NULL DEFAULT 'red', -- 'red', 'amber', 'blue'
    status VARCHAR(32) NOT NULL DEFAULT 'pending', -- 'pending', 'claimed', 'en_route', 'resolved'
    assigned_squad VARCHAR(64),
    claimed_by_user_id INTEGER REFERENCES users(id),
    claimed_at TIMESTAMP,
    resolved_at TIMESTAMP,
    is_simulated BOOLEAN NOT NULL DEFAULT 1,       -- Data integrity flag
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tickets_client_packet_id ON distress_tickets(client_packet_id);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON distress_tickets(category);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON distress_tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_urgency ON distress_tickets(urgency_tier);

-- =========================================================================
-- SEEDED DEMONSTRATION DATA (is_simulated = 1)
-- =========================================================================

-- Seed Disaster Zones
INSERT OR REPLACE INTO disaster_zones (zone_key, name, telugu_name, vulnerability_tag, status, status_class, active_sos_count, deployed_squads, water_level, is_simulated)
VALUES
('mvp', 'MVP Colony & Beach Road (Ward #14)', 'ఎంవీపీ కాలనీ & తీరప్రాంత వార్డు #14', 'HIGH VULNERABILITY SECTOR', 'CRITICAL SURGE', 'bg-error-container text-on-error-container', 4, '2 Squads', '1.4m Depth', 1),
('jalaripeta', 'Jalaripeta Fisher Village Ward #18', 'జలారిపేట మత్స్యకార గ్రామం', 'COASTAL HAMLET EVACUATION', 'RELIEF PENDING', 'bg-tertiary-container text-on-tertiary-container', 7, '1 Boat Squad', '2.1m Surge', 1),
('au_stadium', 'AU Indoor Stadium Safe Shelter', 'ఆంధ్రా యూనివర్సిటీ ప్రధాన శిబిరం', 'PRIMARY DESIGNATED RELIEF HUB', 'SAFE & OPERATIONAL', 'bg-secondary-container text-on-secondary-container', 0, '6 Ward Staff', '0.0m Ground Clear', 1),
('gvmc_school', 'GVMC High School Sector 9', 'జివిఎంసి హై స్కూల్ ఆశ్రయం', 'INTERMEDIATE RELIEF POINT', 'POWER GENERATOR ACTIVE', 'bg-secondary-container text-on-secondary-container', 1, '3 Volunteers', '0.2m Low Pool', 1);

-- Seed Refuge Shelters
INSERT OR REPLACE INTO refuge_shelters (id, name, telugu_name, zone_key, landmark, capacity, current_occupancy, is_operational, has_power_generator, has_potable_water, has_medical_unit, is_simulated)
VALUES
(1, 'AU Indoor Stadium', 'ఆంధ్రా యూనివర్సిటీ ప్రధాన శిబిరం', 'au_stadium', 'Andhra University South Campus, Near Siripuram', 1200, 480, 1, 1, 1, 1, 1),
(2, 'GVMC High School Sector 9', 'జివిఎంసి హై స్కూల్ ఆశ్రయం', 'gvmc_school', 'Sector 9, MVP Colony', 600, 210, 1, 1, 1, 0, 1);

-- Seed Initial Distress Tickets
INSERT OR REPLACE INTO distress_tickets (client_packet_id, packet_tag, category, title, telugu_title, description, landmark, latitude, longitude, gps_accuracy_meters, contact_phone, urgency_tier, status, is_simulated)
VALUES
('sim-pkt-9440-trauma', 'PKT-9440', 'medical', 'Critical Breathing Distress & Rising Ground Water', 'వృద్ధుడికి శ్వాస తీసుకోవడంలో ఇబ్బంది', '72yo male acute breathing distress, power out for O2 concentrator. Rising sea-surge water entering ground floor. 3 residents trapped inside.', 'MVP Colony, Sector 4, D-Block (Near Ushodaya Junction)', 17.7231, 83.3218, 6.0, '+919848022338', 'red', 'pending', 1),
('sim-pkt-9441-ration', 'PKT-9441', 'supplies', 'Family Stranded on Open Terrace - Infant Formula Needed', 'మంచినీరు లేదు, 6 నెలల పసికందు ఉంది', 'Family of 5 stranded on 1st-floor open terrace. Raincoats shredded, no potable drinking water for 14 hours. Includes 6-month-old infant requiring dry formula milk.', 'Beach Road, Jalaripeta Ward 16 (Near Fishermen Community Hall)', 17.7295, 83.3325, 12.0, '+919848033449', 'amber', 'pending', 1),
('sim-pkt-9442-hazard', 'PKT-9442', 'hazard', 'Collapsed 11kV Electrical Feeder & Tree on Ambulance Highway', 'విద్యుత్ స్తంభం మరియు భారీ చెట్టు కూలి ప్రధాన రహదారి మూసుకుపోయింది', 'Uprooted ancient banyan tree and 11kV electrical feeder line collapsed across arterial evacuation highway. 2 auto-rickshaws stalled, ambulance corridor blocked.', 'Waltair Main Road, Near Siripuram Jn (Near Gurajada Kalakshetram)', 17.7180, 83.3150, 8.0, '+919848055667', 'blue', 'pending', 1);

-- Seed Demo Volunteer User (username: squad14_lead, password: responder14pass)
INSERT OR REPLACE INTO users (id, username, hashed_password, full_name, role, squad_name, is_active)
VALUES
(1, 'squad14_lead', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQmG6W65WVIxTCrtdcuW.', 'K. Ramanathan (Ward #14 SDRF Lead)', 'volunteer', 'AU Ward Squad #14', 1);
