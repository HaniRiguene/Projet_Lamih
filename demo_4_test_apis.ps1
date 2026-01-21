# 🔌 ÉTAPE 4: Tester les APIs FastAPI
# Usage: ./demo_4_test_apis.ps1

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           🔌 TEST DES APIs - FASTAPI SERVER                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# TEST 1: GET /v1/devices
# ============================================================================
Write-Host "`n1️⃣ GET /v1/devices - Liste de tous les devices" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

try {
  $devices = Invoke-RestMethod "http://localhost:8000/v1/devices"
  Write-Host "✓ Réponse reçue:" -ForegroundColor Green
  $devices | Format-Table device_id, name, type, location
  $count = $devices.Count
  Write-Host "  Total devices: $count" -ForegroundColor Green
} catch {
  Write-Host "❌ Erreur: $_" -ForegroundColor Red
}

# ============================================================================
# TEST 2: GET /v1/devices/{id}/latest
# ============================================================================
Write-Host "`n2️⃣ GET /v1/devices/{{id}}/latest - Dernière mesure par device" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

# Device 1
Write-Host "`n  📍 salle_a_manger:" -ForegroundColor Green
try {
  $latest = Invoke-RestMethod "http://localhost:8000/v1/devices/salle_a_manger/latest"
  $latest | Select-Object sensor, value, @{Name="timestamp";Expression={([datetime]$_.ts).ToString("yyyy-MM-dd HH:mm:ss")}} | Format-Table
} catch {
  Write-Host "  ❌ Erreur: $_" -ForegroundColor Red
}

# Device 2
Write-Host "`n  🍳 capteur_de_temperature_cuisine:" -ForegroundColor Green
try {
  $latest = Invoke-RestMethod "http://localhost:8000/v1/devices/capteur_de_temperature_cuisine/latest"
  $latest | Select-Object sensor, value, @{Name="timestamp";Expression={([datetime]$_.ts).ToString("yyyy-MM-dd HH:mm:ss")}} | Format-Table
} catch {
  Write-Host "  ❌ Erreur: $_" -ForegroundColor Red
}

# Device 3
Write-Host "`n  🚿 capteur_de_laser_salle_de_bain:" -ForegroundColor Green
try {
  $latest = Invoke-RestMethod "http://localhost:8000/v1/devices/capteur_de_laser_salle_de_bain/latest"
  $latest | Select-Object sensor, value, @{Name="timestamp";Expression={([datetime]$_.ts).ToString("yyyy-MM-dd HH:mm:ss")}} | Format-Table
} catch {
  Write-Host "  ❌ Erreur: $_" -ForegroundColor Red
}

# ============================================================================
# TEST 3: GET /v1/measurements (avec filtres)
# ============================================================================
Write-Host "`n3️⃣ GET /v1/measurements - Requête avec filtres" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

# Dernières 5 mesures cuisine
Write-Host "`n  Dernières 5 mesures de la cuisine:" -ForegroundColor Green
try {
  $meas = Invoke-RestMethod "http://localhost:8000/v1/measurements?device_id=capteur_de_temperature_cuisine&limit=5&order=desc"
  $meas | Select-Object device_id, sensor, value, @{Name="timestamp";Expression={([datetime]$_.ts).ToString("HH:mm:ss")}} | Format-Table -AutoSize
} catch {
  Write-Host "  ❌ Erreur: $_" -ForegroundColor Red
}

# Dernières 3 mesures laser
Write-Host "`n  Dernières 3 mesures du laser (salle de bain):" -ForegroundColor Green
try {
  $meas = Invoke-RestMethod "http://localhost:8000/v1/measurements?device_id=capteur_de_laser_salle_de_bain&limit=3&order=desc"
  $meas | Select-Object device_id, sensor, value, @{Name="timestamp";Expression={([datetime]$_.ts).ToString("HH:mm:ss")}} | Format-Table -AutoSize
} catch {
  Write-Host "  ❌ Erreur: $_" -ForegroundColor Red
}

# ============================================================================
# TEST 4: GET /v1/measurements/aggregate
# ============================================================================
Write-Host "`n4️⃣ GET /v1/measurements/aggregate - Agrégation par bucket" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

try {
  $agg = Invoke-RestMethod "http://localhost:8000/v1/measurements/aggregate?device_id=salle_a_manger&bucket=1h&agg=avg"
  if ($agg) {
    Write-Host "✓ Agrégation par heure (moyenne):" -ForegroundColor Green
    $agg | Select-Object bucket, avg_value, count | Format-Table -AutoSize
  } else {
    Write-Host "ℹ Pas de résultats pour agrégation" -ForegroundColor Yellow
  }
} catch {
  Write-Host "❌ Erreur (optionnel): $_" -ForegroundColor Yellow
}

# ============================================================================
# INFO SUPPLÉMENTAIRE
# ============================================================================
Write-Host "`n════════════════════════════════════" -ForegroundColor Gray
Write-Host "`n📍 ACCÈS SUPPLÉMENTAIRE:" -ForegroundColor Yellow
Write-Host "  • API Docs (Swagger): http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  • API ReDoc: http://localhost:8000/redoc" -ForegroundColor Cyan
Write-Host "  • Web UI: http://localhost" -ForegroundColor Cyan
Write-Host "  • PostgreSQL: localhost:5433" -ForegroundColor Cyan

Write-Host "`n✅ TESTS DES APIs COMPLÉTÉS!" -ForegroundColor Green
