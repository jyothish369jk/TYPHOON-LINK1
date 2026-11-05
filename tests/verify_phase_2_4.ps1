# TyphoonLink Phase 2.4 Offline Queue, IndexedDB & Frontend Verification Script

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " TyphoonLink Phase 2.4: Offline Queue & Frontend Integration Verification" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$baseDir = "stitch_typhoon_link_sos"
$backupDir = "stitch_typhoon_link_sos_backup"
$totalTests = 0
$passedTests = 0

function Assert-Test([string]$name, [bool]$condition, [string]$detail) {
    $script:totalTests++
    if ($condition) {
        $script:passedTests++
        Write-Host "  [PASS] $name - $detail" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $name - $detail" -ForegroundColor Red
    }
}

# TEST 1: Backup preservation
Write-Host "`n[CHECK 1] Verifying Backup Folder Integrity..." -ForegroundColor Yellow
$backupFiles = Get-ChildItem -Recurse -File $backupDir
Assert-Test "Backup Untouched" ($backupFiles.Count -ge 9) "Backup directory contains $($backupFiles.Count) untouched original files."

# TEST 2: JavaScript Offline Queue Engine
Write-Host "`n[CHECK 2] Verifying IndexedDB Offline Queue Engine..." -ForegroundColor Yellow
$queuePath = Join-Path $baseDir "js/offline_queue.js"
$queueContent = Get-Content $queuePath -Raw

Assert-Test "IndexedDB Engine File" (Test-Path $queuePath) "Found offline_queue.js"
Assert-Test "Database & Store Names" ($queueContent.Contains("TyphoonLinkLocalDB") -and $queueContent.Contains("sos_queue")) "Contains TyphoonLinkLocalDB and sos_queue"
Assert-Test "UUIDv4 & Packet Tag" ($queueContent.Contains("_generateUUID") -and $queueContent.Contains("_generatePacketTag")) "Implements UUIDv4 and tactical PKT tag generators"
Assert-Test "Lifecycle States" ($queueContent.Contains("pending") -and $queueContent.Contains("delivered")) "Implements pending -> syncing -> delivered state transitions"
Assert-Test "Sync API Endpoint" ($queueContent.Contains("/api/sos/sync")) "Hooks into /api/sos/sync batch endpoint"
Assert-Test "Auto-Sync Listeners" ($queueContent.Contains("online") -and $queueContent.Contains("offline")) "Listens for browser online and offline connectivity restoration"

# TEST 3: Service Worker
Write-Host "`n[CHECK 3] Verifying Service Worker Caching..." -ForegroundColor Yellow
$swPath = Join-Path $baseDir "sw.js"
$swContent = Get-Content $swPath -Raw

Assert-Test "Service Worker File" (Test-Path $swPath) "Found sw.js"
Assert-Test "Offline Shell Cache" ($swContent.Contains("typhoon-link-v1") -and $swContent.Contains("ASSETS_TO_CACHE")) "Pre-caches application HTML, script, and CSS shell assets"
Assert-Test "API Pass-Through" ($swContent.Contains("/api/")) "Bypasses cache for backend REST API calls"
Assert-Test "Honest Disclaimers" ($swContent.Contains("DOES NOT provide wireless radio transmission")) "Includes clear hardware outage limitations disclaimer"

# TEST 4: Frontend Prototype Integrations
Write-Host "`n[CHECK 4] Verifying 4 HTML Prototypes Integration..." -ForegroundColor Yellow
$pages = @(
    "citizen_offline_sos_dispatcher_simplified/code.html",
    "volunteer_triage_deduplication_feed/code.html",
    "hyper_local_cyclone_grid_resource_map/code.html",
    "satellite_intelligence_disaster_mapping_mobile/code.html"
)

foreach ($page in $pages) {
    $fullPath = Join-Path $baseDir $page
    $content = Get-Content $fullPath -Raw
    $hasQueueScript = $content.Contains("offline_queue.js")
    $hasSW = $content.Contains("serviceWorker")
    
    Assert-Test "Queue Script in $page" $hasQueueScript "Loads offline_queue.js"
    Assert-Test "ServiceWorker in $page" $hasSW "Registers Service Worker"
}

# TEST 5: Interactive Event Bindings in Citizen Dispatcher
Write-Host "`n[CHECK 5] Citizen Dispatcher Offline Storage Bindings..." -ForegroundColor Yellow
$citContent = Get-Content (Join-Path $baseDir "citizen_offline_sos_dispatcher_simplified/code.html") -Raw
Assert-Test "Enqueue Call" ($citContent.Contains("TyphoonOfflineQueue.enqueueSOS")) "Enqueues report to IndexedDB on SOS hold completion"
Assert-Test "Manual Sync Call" ($citContent.Contains("TyphoonOfflineQueue.syncPendingReports")) "Manual sync triggers syncPendingReports()"
Assert-Test "Persistent Queue UI Card" ($citContent.Contains("queueCounterText")) "Contains queueCounterText card element"

# TEST 6: Interactive Event Bindings in Volunteer Feed
Write-Host "`n[CHECK 6] Volunteer Triage Feed API & Claim Bindings..." -ForegroundColor Yellow
$volContent = Get-Content (Join-Path $baseDir "volunteer_triage_deduplication_feed/code.html") -Raw
Assert-Test "Claim API Integration" ($volContent.Contains("/api/tickets/") -and $volContent.Contains("/claim")) "claimTask connects to /api/tickets/{id}/claim"
Assert-Test "Conflict 409 Handling" ($volContent.Contains("409")) "Handles HTTP 409 Conflict with feedback"
Assert-Test "Status Update Integration" ($volContent.Contains("/api/tickets/") -and $volContent.Contains("/status")) "toggleEnRoute connects to /api/tickets/{id}/status"
Assert-Test "Manual Field Ticket Enqueue" ($volContent.Contains("enqueueSOS")) "saveManualTicket enqueues to IndexedDB"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host " RESULT: $passedTests / $totalTests Checks Passed" -ForegroundColor $(if ($passedTests -eq $totalTests) { "Green" } else { "Red" })
Write-Host "======================================================================" -ForegroundColor Cyan
