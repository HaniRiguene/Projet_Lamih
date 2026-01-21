# 📊 ÉTAPE 3: Vérifier les données en base de données
# Usage: ./demo_3_verify_db.ps1

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║      📊 VÉRIFICATION DES DONNÉES EN BASE DE DONNÉES           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# Vérification 1: Total des mesures
# ============================================================================
Write-Host "1️⃣ TOTAL DES MESURES:" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

$result = docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) as total_mesures FROM measurements;"
$result | Select-Object -Last 3

# ============================================================================
# Vérification 2: Mesures par device
# ============================================================================
Write-Host "`n2️⃣ MESURES PAR DEVICE:" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

docker exec PostgreSQL psql -U program -d FL -c "SELECT device_id, COUNT(*) as nb_mesures FROM measurements GROUP BY device_id ORDER BY device_id;"

# ============================================================================
# Vérification 3: Dernière mesure par device
# ============================================================================
Write-Host "`n3️⃣ DERNIÈRE MESURE PAR DEVICE:" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

docker exec PostgreSQL psql -U program -d FL -c "SELECT DISTINCT ON (device_id) device_id, sensor, value, ts FROM measurements ORDER BY device_id, ts DESC;"

# ============================================================================
# Vérification 4: Statistiques complètes
# ============================================================================
Write-Host "`n4️⃣ STATISTIQUES COMPLÈTES:" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

docker exec PostgreSQL psql -U program -d FL -c "
SELECT 
  device_id,
  COUNT(*) as nb_mesures,
  MIN(value) as min_val,
  MAX(value) as max_val,
  ROUND(AVG(value)::numeric, 2) as avg_val
FROM measurements
GROUP BY device_id
ORDER BY device_id;
"

Write-Host "`n✅ VÉRIFICATION COMPLÉTÉE! Passez à l'étape 4 (test APIs)" -ForegroundColor Green
