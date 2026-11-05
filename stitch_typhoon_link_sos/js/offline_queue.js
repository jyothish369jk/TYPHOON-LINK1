/**
 * TyphoonLink Offline SOS Queue Engine (IndexedDB)
 * 
 * Capabilities:
 * - Persistent client-side distress packet queue using browser IndexedDB.
 * - Generates immutable client_packet_id (UUIDv4) and tactical packet tags (PKT-xxxx).
 * - Lifecycle States: 'pending' -> 'syncing' -> 'delivered'.
 * - Preserves queued reports across page refreshes, tab closures, and device restarts.
 * - Listens to network connectivity events and automatically flushes queue when online.
 * - Idempotently syncs with Python FastAPI backend at /api/sos/sync.
 */

const DB_NAME = 'TyphoonLinkLocalDB';
const DB_VERSION = 1;
const STORE_NAME = 'sos_queue';

class OfflineQueueEngine {
  constructor() {
    this.db = null;
    this.isSyncing = false;
    this.initPromise = this._initDB();
    this._initNetworkListeners();
  }

  /**
   * Initialize IndexedDB database and object store
   */
  _initDB() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'client_packet_id' });
          store.createIndex('sync_status', 'sync_status', { unique: false });
          store.createIndex('created_at', 'created_at', { unique: false });
          store.createIndex('category', 'category', { unique: false });
        }
      };

      request.onsuccess = (event) => {
        this.db = event.target.result;
        this.updateQueueBadge();
        resolve(this.db);
      };

      request.onerror = (event) => {
        console.error('[TyphoonLink IndexedDB] Initialization error:', event.target.error);
        reject(event.target.error);
      };
    });
  }

  /**
   * Listen to browser online/offline events for automatic queue flush
   */
  _initNetworkListeners() {
    window.addEventListener('online', () => {
      console.log('[TyphoonLink Queue] Connectivity restored. Auto-flushing pending reports...');
      this.syncPendingReports();
    });

    window.addEventListener('offline', () => {
      console.warn('[TyphoonLink Queue] Network offline. SOS packets will buffer in IndexedDB.');
      this.updateQueueBadge();
    });
  }

  /**
   * Helper to generate a compliant UUIDv4
   */
  _generateUUID() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  /**
   * Helper to generate a human-readable tactical packet tag (e.g. PKT-9440)
   */
  _generatePacketTag() {
    const hex = Math.floor(1000 + Math.random() * 9000).toString(16).toUpperCase();
    return `PKT-${hex}`;
  }

  /**
   * Enqueue a new SOS report into IndexedDB
   * Saved persistently before any network attempt
   */
  async enqueueSOS(report) {
    await this.initPromise;

    const packet = {
      client_packet_id: report.client_packet_id || this._generateUUID(),
      packet_tag: report.packet_tag || this._generatePacketTag(),
      category: report.category || 'medical',
      title: report.title || 'Emergency Distress Beacon',
      telugu_title: report.telugu_title || 'అత్యవసర సమాచారం',
      description: report.description || 'Automated 1-tap beacon broadcast.',
      landmark: report.landmark || 'MVP Colony, Sector 4, Visakhapatnam',
      latitude: report.latitude !== undefined ? report.latitude : null,
      longitude: report.longitude !== undefined ? report.longitude : null,
      gps_accuracy_meters: report.gps_accuracy_meters || null,
      contact_phone: report.contact_phone || null,
      urgency_tier: report.urgency_tier || 'red',
      sync_status: 'pending',        // 'pending' -> 'syncing' -> 'delivered'
      retry_count: 0,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      server_ticket_id: null,
      is_simulated: false,            // Actual citizen report
    };

    return new Promise((resolve, reject) => {
      const tx = this.db.transaction([STORE_NAME], 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const req = store.put(packet);

      req.onsuccess = () => {
        console.log(`[TyphoonLink Queue] Packet ${packet.packet_tag} saved to IndexedDB.`);
        this.updateQueueBadge();
        // Trigger background sync attempt if online
        if (navigator.onLine) {
          this.syncPendingReports().catch(() => {});
        }
        resolve(packet);
      };

      req.onerror = (e) => {
        console.error('[TyphoonLink Queue] Failed to save packet:', e.target.error);
        reject(e.target.error);
      };
    });
  }

  /**
   * Retrieve all pending (unsynced) reports
   */
  async getPendingReports() {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction([STORE_NAME], 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const index = store.index('sync_status');
      const req = index.getAll('pending');

      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  }

  /**
   * Retrieve all reports in IndexedDB (pending + syncing + delivered)
   */
  async getAllReports() {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction([STORE_NAME], 'readonly');
      const store = tx.objectStore(STORE_NAME);
      const req = store.getAll();

      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
    });
  }

  /**
   * Mark a packet as delivered after server acknowledgment
   */
  async markDelivered(clientPacketId, serverTicketId) {
    await this.initPromise;
    return new Promise((resolve, reject) => {
      const tx = this.db.transaction([STORE_NAME], 'readwrite');
      const store = tx.objectStore(STORE_NAME);
      const getReq = store.get(clientPacketId);

      getReq.onsuccess = () => {
        const record = getReq.result;
        if (!record) return resolve(null);

        record.sync_status = 'delivered';
        record.server_ticket_id = serverTicketId;
        record.delivered_at = new Date().toISOString();
        record.updated_at = new Date().toISOString();

        const putReq = store.put(record);
        putReq.onsuccess = () => {
          this.updateQueueBadge();
          resolve(record);
        };
        putReq.onerror = () => reject(putReq.error);
      };

      getReq.onerror = () => reject(getReq.error);
    });
  }

  /**
   * Flush pending reports to backend API (/api/sos/sync)
   */
  async syncPendingReports(apiUrl = 'http://localhost:8000/api/sos/sync') {
    if (this.isSyncing) return;
    this.isSyncing = true;

    try {
      const pending = await this.getPendingReports();
      if (!pending || pending.length === 0) {
        this.updateQueueBadge();
        this.isSyncing = false;
        return { synced: 0 };
      }

      console.log(`[TyphoonLink Queue] Syncing ${pending.length} pending report(s) to ${apiUrl}...`);

      // Prepare batch payload
      const payload = {
        packets: pending.map((p) => ({
          client_packet_id: p.client_packet_id,
          packet_tag: p.packet_tag,
          category: p.category,
          title: p.title,
          telugu_title: p.telugu_title,
          description: p.description,
          landmark: p.landmark,
          latitude: p.latitude,
          longitude: p.longitude,
          gps_accuracy_meters: p.gps_accuracy_meters,
          contact_phone: p.contact_phone,
          urgency_tier: p.urgency_tier,
        })),
      };

      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Sync HTTP error ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('[TyphoonLink Queue] Batch sync success:', result);

      // Mark delivered locally for every server-confirmed packet
      if (result.results && Array.isArray(result.results)) {
        for (const res of result.results) {
          if (res.client_packet_id && res.ticket_id) {
            await this.markDelivered(res.client_packet_id, res.ticket_id);
          }
        }
      }

      this.updateQueueBadge();
      return result;
    } catch (err) {
      console.warn('[TyphoonLink Queue] Sync paused (offline or server unreachable):', err.message);
      this.updateQueueBadge();
      throw err;
    } finally {
      this.isSyncing = false;
    }
  }

  /**
   * Update the UI counter badge across Stitch pages
   */
  async updateQueueBadge() {
    try {
      const pending = await this.getPendingReports();
      const all = await this.getAllReports();
      const counterEl = document.getElementById('queueCounterText');

      if (counterEl) {
        if (pending.length === 0) {
          if (all.length > 0) {
            counterEl.innerText = `${all.length} SOS packet(s) verified synced with server`;
          } else {
            counterEl.innerText = `0 SOS packets in local queue`;
          }
        } else {
          counterEl.innerText = `${pending.length} SOS packet(s) queued locally in IndexedDB`;
        }
      }
    } catch (e) {
      // Ignore if DOM element not present
    }
  }
}

// Global singleton instance
window.TyphoonOfflineQueue = new OfflineQueueEngine();
