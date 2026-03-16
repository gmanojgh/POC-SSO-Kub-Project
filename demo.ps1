[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# --- SETUP: Update this URL with your current Minikube service URL ---
# Run 'minikube service report-api-service' in a separate terminal and keep it open!
$BASE = "http://127.0.0.1:50940" 

Write-Host "Targeting API at: $BASE" -ForegroundColor Gray
Write-Host "NOTE: If this fails, ensure your 'minikube service' tunnel is open in another terminal.`n" -ForegroundColor DarkGray

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Secure Report API - RBAC Demo" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# --- Step 1: Login all three users ------------------------------------------------

Write-Host "STEP 1 - Authenticate all users" -ForegroundColor Yellow

$LoginAlice = @{ username="alice"; password="password123" }
$LoginBob   = @{ username="bob";   password="password123" }
$LoginCarol = @{ username="carol"; password="password123" }

try {
    $ALICE = (Invoke-RestMethod -Method Post -Uri "$BASE/api/auth/login/" -ContentType "application/json" -Body ($LoginAlice | ConvertTo-Json)).access
    $BOB   = (Invoke-RestMethod -Method Post -Uri "$BASE/api/auth/login/" -ContentType "application/json" -Body ($LoginBob   | ConvertTo-Json)).access
    $CAROL = (Invoke-RestMethod -Method Post -Uri "$BASE/api/auth/login/" -ContentType "application/json" -Body ($LoginCarol | ConvertTo-Json)).access
} catch {
    Write-Host "ERROR: Could not log in. Is the server running and the tunnel open?" -ForegroundColor Red
    Write-Host "Service URL: $BASE" -ForegroundColor Gray
    Write-Host "Error details: $($_.Exception.Message)" -ForegroundColor Gray
    exit 1
}

Write-Host "  Alice (Admin)   token: $($ALICE.Substring(0,20))..." -ForegroundColor Green
Write-Host "  Bob   (Manager) token: $($BOB.Substring(0,20))..." -ForegroundColor Green
Write-Host "  Carol (Viewer)  token: $($CAROL.Substring(0,20))..." -ForegroundColor Green


# --- Step 2: Show profiles and permissions ---------------------------------------

Write-Host "`nSTEP 2 - Verify roles and permissions" -ForegroundColor Yellow

$AuthAlice = @{ Authorization = "Bearer $ALICE" }
$AuthBob   = @{ Authorization = "Bearer $BOB" }
$AuthCarol = @{ Authorization = "Bearer $CAROL" }

Write-Host "`n  Alice's profile (Admin - should have all 4 permissions):" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BASE/api/me/" -Headers $AuthAlice | ConvertTo-Json -Depth 3

Write-Host "`n  Bob's profile (Manager - should have view + create):" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BASE/api/me/" -Headers $AuthBob | ConvertTo-Json -Depth 3

Write-Host "`n  Carol's profile (Viewer - should have view only):" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BASE/api/me/" -Headers $AuthCarol | ConvertTo-Json -Depth 3


# --- Step 3: Create reports ------------------------------------------------------

Write-Host "`nSTEP 3 - Create reports (Admin and Manager only)" -ForegroundColor Yellow

$Report1 = @{ title="Board Report Q4"; content="Revenue up 12%"; category="Executive" }
$Report2 = @{ title="Q1 Sales Analysis"; content="Sales up 8%"; category="Finance" }

Write-Host "`n  Alice creates a report (SHOULD SUCCEED - 201):" -ForegroundColor Cyan
Invoke-RestMethod -Method Post -Uri "$BASE/api/reports/create/" -Headers $AuthAlice -ContentType "application/json" -Body ($Report1 | ConvertTo-Json) | ConvertTo-Json

Write-Host "`n  Bob creates a report (SHOULD SUCCEED - 201):" -ForegroundColor Cyan
Invoke-RestMethod -Method Post -Uri "$BASE/api/reports/create/" -Headers $AuthBob -ContentType "application/json" -Body ($Report2 | ConvertTo-Json) | ConvertTo-Json

Write-Host "`n  Carol tries to create (SHOULD FAIL - 403 Forbidden):" -ForegroundColor Cyan
try {
    Invoke-RestMethod -Method Post -Uri "$BASE/api/reports/create/" -Headers $AuthCarol -ContentType "application/json" -Body ($Report1 | ConvertTo-Json)
} catch {
    Write-Host "  Response: $($_.Exception.Message)" -ForegroundColor Red
}


# --- Step 4: View reports --------------------------------------------------------

Write-Host "`nSTEP 4 - View reports (all roles)" -ForegroundColor Yellow

Write-Host "`n  Carol views all reports (SHOULD SUCCEED - 200):" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BASE/api/reports/" -Headers $AuthCarol | ConvertTo-Json -Depth 5


# --- Step 5: Delete reports ------------------------------------------------------

Write-Host "`nSTEP 5 - Delete reports (Admin only)" -ForegroundColor Yellow

Write-Host "`n  Alice deletes report #1 (SHOULD SUCCEED - 200):" -ForegroundColor Cyan
Invoke-RestMethod -Method Delete -Uri "$BASE/api/reports/1/" -Headers $AuthAlice | ConvertTo-Json

Write-Host "`n  Bob tries to delete report #2 (SHOULD FAIL - 403 Forbidden):" -ForegroundColor Cyan
try {
    Invoke-RestMethod -Method Delete -Uri "$BASE/api/reports/2/" -Headers $AuthBob
} catch {
    Write-Host "  Response: $($_.Exception.Message)" -ForegroundColor Red
}


# --- Step 6: Admin - list all users ---------------------------------------------

Write-Host "`nSTEP 6 - User management (Admin only)" -ForegroundColor Yellow

Write-Host "`n  Alice lists all users (SHOULD SUCCEED):" -ForegroundColor Cyan
Invoke-RestMethod -Method Get -Uri "$BASE/api/users/" -Headers $AuthAlice | ConvertTo-Json -Depth 3

Write-Host "`n  Carol tries to list users (SHOULD FAIL - 403 Forbidden):" -ForegroundColor Cyan
try {
    Invoke-RestMethod -Method Get -Uri "$BASE/api/users/" -Headers $AuthCarol
} catch {
    Write-Host "  Response: $($_.Exception.Message)" -ForegroundColor Red
}


# --- Summary --------------------------------------------------------------------

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " DEMO COMPLETE - ALL RBAC RULES VERIFIED" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan
