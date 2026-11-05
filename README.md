# TyphoonLink — Tactical Emergency Cyclone Dispatch & Volunteer Triage System

TyphoonLink is a mission-critical disaster dispatch engine engineered for coastal cyclone corridors (e.g. Visakhapatnam / Andhra Pradesh coast). It pairs a high-contrast dark-mode PWA frontend with a Python FastAPI + SQLite backend, featuring persistent client-side IndexedDB offline queuing, idempotent batch synchronization, and atomic volunteer ticket claiming.

---

## 📁 Project Structure

```
typhoon-link/
│
├── stitch_typhoon_link_sos/                       # Frontend PWA Prototype
│   ├── citizen_offline_sos_dispatcher_simplified/ # Citizen 1-tap/hold SOS beacon
│   │   └── code.html
│   ├── volunteer_triage_deduplication_feed/       # Responder triage & claim feed
│   │   └── code.html
│   ├── hyper_local_cyclone_grid_resource_map/     # Multi-sector map & shelters
│   │   └── code.html
│   ├── satellite_intelligence_disaster_mapping_mobile/ # Satellite & telemetry bento
│   │   └── code.html
│   ├── js/
│   │   └── offline_queue.js                       # IndexedDB client queue engine
│   └── sw.js                                      # Service Worker offline shell cache
│
├── stitch_typhoon_link_sos_backup/                # Untouched original backup
│
├── server/                                        # FastAPI + SQLite Backend
│   ├── app/
│   │   ├── api/                                   # REST API Endpoints
│   │   │   ├── sos.py                             # SOS submit & batch sync
│   │   │   └── tickets.py                         # Volunteer ticket retrieval & claim
│   │   ├── core/                                  # Security & rate limiting
│   │   ├── database/                              # SQLAlchemy engine & session
│   │   ├── models/                                # Database models (Ticket, Zone, etc.)
│   │   ├── schemas/                               # Pydantic v2 validation schemas
│   │   ├── config.py                              # Environment settings
│   │   ├── main.py                                # FastAPI application entrypoint
│   │   └── seed.py                                # Demonstration data seeder
│   ├── database/
│   │   └── schema.sql                             # Initial SQLite DDL
│   ├── requirements.txt                           # Python dependencies
│   ├── .env.example                               # Environment template
│   └── .gitignore
│
└── tests/                                         # Verification & Test Suites
    ├── verify_phase_2_3.ps1                       # Phase 2.3 Ticket & API tests
    ├── verify_phase_2_4.ps1                       # Phase 2.4 Offline Queue tests
    ├── test_sos_api.py                            # Python SOS test suite
    └── test_tickets_api.py                        # Python Ticket test suite
```

---

## 🚀 Step-by-Step Local Testing Guide

### 1. Prerequisites
- **Python 3.10+** installed on your system.
- Modern web browser (Chrome, Edge, Firefox, or Brave).

---

### 2. Start the Backend Server

Open a terminal (PowerShell or Command Prompt) and navigate to `typhoon-link/server`:

```powershell
cd "typhoon-link\server"
```

#### Step A: Create and activate a Python virtual environment (recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Step B: Install dependencies
```powershell
pip install -r requirements.txt
```

#### Step C: Start FastAPI with Uvicorn
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

When started, you will see:
```
[STARTUP] Initializing TyphoonLink Disaster Response Engine v1.0.0...
[SEED] Seeding clearly labeled demonstration dataset (is_simulated=True)...
INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

- **Interactive API Docs (Swagger UI)**: Open `http://localhost:8000/docs` in your browser.
- **System Status Check**: Open `http://localhost:8000/` to verify health.

---

### 3. Open the Frontend Application

You can open the frontend in either of two ways:

#### Option A: Using VS Code Live Server / Python HTTP Server (Recommended for PWA/Service Worker)
From the `typhoon-link/stitch_typhoon_link_sos` directory:
```powershell
cd "typhoon-link\stitch_typhoon_link_sos"
python -m http.server 5500
```
Then navigate to:
- **Citizen SOS**: `http://localhost:5500/citizen_offline_sos_dispatcher_simplified/code.html`
- **Volunteer Triage**: `http://localhost:5500/volunteer_triage_deduplication_feed/code.html`
- **Radar & Resource Map**: `http://localhost:5500/hyper_local_cyclone_grid_resource_map/code.html`
- **Satellite Mapping**: `http://localhost:5500/satellite_intelligence_disaster_mapping_mobile/code.html`

#### Option B: Direct Double-Click (File Protocol)
You can directly double-click any `code.html` file in Windows Explorer. (IndexedDB functions fully on `file://`; Service Workers require HTTP/HTTPS per browser security standards).

---

### 4. Interactive End-to-End Testing Scenarios

#### Scenario 1: Citizen Offline SOS Beacon Submission
1. Open the **Citizen SOS Dispatcher** page.
2. Select an emergency category (e.g. *Medical Emergency* or *Flooding / Trapped*).
3. Tap **CONFIRM GPS** to lock simulated DGPS coordinates.
4. **Press and hold the red SOS button for 3 seconds**:
   - The circular radar animation charges up and chimes.
   - Upon release, the screen displays `SENT! ✓` and generates a tactical packet tag (e.g. `PACKET #PKT-9440 STORED IN INDEXEDDB`).
   - The bottom Local Queue card updates to show: `1 SOS packet(s) queued locally in IndexedDB`.
5. **Verify Persistent Storage**:
   - Refresh the page or close the tab and re-open.
   - Notice the card still displays the stored packet count.
   - In Chrome DevTools (`F12`), go to **Application** $\rightarrow$ **Storage** $\rightarrow$ **IndexedDB** $\rightarrow$ `TyphoonLinkLocalDB` $\rightarrow$ `sos_queue` to view the stored packet JSON with `sync_status: 'pending'`.

#### Scenario 2: Automatic Network Restoration & Sync
1. With the backend running at `http://localhost:8000`, open DevTools and toggle **Offline Mode** in the **Network** tab (or disconnect WiFi).
2. Submit another SOS packet. Notice it buffers in IndexedDB.
3. Toggle the network back to **Online**:
   - The browser detects connection restoration.
   - `offline_queue.js` automatically flushes all pending packets in a single batch to `POST /api/sos/sync`.
   - The server acknowledges the batch and assigns database ticket IDs.
   - Each local record's status transitions from `'pending'` to `'delivered'`.
   - The queue badge displays: `X SOS packet(s) verified synced with server`.

#### Scenario 3: Volunteer Ticket Management & Atomic Claiming
1. Open the **Volunteer Triage Feed** page (`volunteer_triage_deduplication_feed/code.html`).
2. Notice the live triage stream with seeded Red, Amber, and Blue priority tickets.
3. On Ticket 1 (*Critical Breathing Distress*), click **CLAIM RESCUE TASK**:
   - An atomic request is sent to `POST /api/tickets/1/claim` with volunteer identity headers (`X-Volunteer-Squad: AU Ward Squad #14`).
   - The button transitions to `CLAIMED BY YOUR SQUAD` and a confirmation toast appears.
4. **Test Atomic Conflict Guard (409 Conflict)**:
   - In Swagger docs (`http://localhost:8000/docs`) or another browser tab, attempt to claim Ticket 1 with another squad name (`AU NCC Squad #2`).
   - The backend responds with `HTTP 409 Conflict`: `"Ticket 1 has already been claimed by squad 'AU Ward Squad #14'"`.
5. On the claimed ticket, click **Mark En Route**:
   - Status updates via `PATCH /api/tickets/1/status` to `in_progress`.

#### Scenario 4: Manual Field Ticket Logging
1. In the Volunteer Triage Feed, tap **+ Log Field Ticket** (top right floating button).
2. Choose urgency, enter a landmark (e.g., `MVP Colony Sector 2, Water Tank`) and situation description.
3. Click **Save & Broadcast**:
   - The ticket is immediately committed to client IndexedDB and queued for mesh/server sync.

---

### 5. Running Automated Verification Scripts

Open PowerShell in the `typhoon-link` directory:

```powershell
cd "typhoon-link"

# Run Phase 2.3 Verification (Tickets API, Atomic Claims, Filter, State Machine)
powershell -ExecutionPolicy Bypass -File tests\verify_phase_2_3.ps1

# Run Phase 2.4 Verification (IndexedDB Queue, Service Worker, Prototypes Integration)
powershell -ExecutionPolicy Bypass -File tests\verify_phase_2_4.ps1
```

Both suites should exit with all assertions passing (100% green).
