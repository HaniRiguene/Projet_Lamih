# 📤 ÉTAPE 2: Envoyer les données depuis les 3 devices
# Usage: ./demo_2_send_data.ps1

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         📤 ENVOI DES DONNÉES - 3 DEVICES × 50 MESURES      ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# ============================================================================
# DEVICE 1: salle_a_manger (50 mesures température)
# ============================================================================
Write-Host "`n📍 DEVICE 1: salle_a_manger" -ForegroundColor Green
Write-Host "Type: Température | Mesures: 50 | Plage: 18-24°C" -ForegroundColor Gray

$device1_count = 0
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 18 -Maximum 24
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[salle_a_manger][0][Sending Data][sensor:temperature|value:$val|msg_id:d1_$i]"
  Start-Sleep -Milliseconds 8
  $device1_count++
  if ($i % 10 -eq 0) { Write-Host "  ✓ $i/50 messages envoyés" -ForegroundColor Gray }
}
Write-Host "  ✅ Device 1: $device1_count/50 messages envoyés" -ForegroundColor Green

# ============================================================================
# DEVICE 2: capteur_de_température_cuisine (50 mesures température)
# ============================================================================
Write-Host "`n⏳ Attente 5s avant Device 2..." -ForegroundColor Yellow
sleep 5

Write-Host "`n🍳 DEVICE 2: capteur_de_temperature_cuisine" -ForegroundColor Green
Write-Host "Type: Température | Mesures: 50 | Plage: 20-26°C" -ForegroundColor Gray

$device2_count = 0
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 20 -Maximum 26
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[capteur_de_temperature_cuisine][0][Sending Data][sensor:temperature|value:$val|msg_id:d2_$i]"
  Start-Sleep -Milliseconds 8
  $device2_count++
  if ($i % 10 -eq 0) { Write-Host "  ✓ $i/50 messages envoyés" -ForegroundColor Gray }
}
Write-Host "  ✅ Device 2: $device2_count/50 messages envoyés" -ForegroundColor Green

# ============================================================================
# DEVICE 3: capteur_de_laser_salle_de_bain (50 mesures laser/motion)
# ============================================================================
Write-Host "`n⏳ Attente 5s avant Device 3..." -ForegroundColor Yellow
sleep 5

Write-Host "`n🚿 DEVICE 3: capteur_de_laser_salle_de_bain" -ForegroundColor Green
Write-Host "Type: Laser/Motion | Mesures: 50 | Valeur: 0 ou 1" -ForegroundColor Gray

$device3_count = 0
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 0 -Maximum 1
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[capteur_de_laser_salle_de_bain][0][Sending Data][sensor:laser|value:$val|msg_id:d3_$i]"
  Start-Sleep -Milliseconds 8
  $device3_count++
  if ($i % 10 -eq 0) { Write-Host "  ✓ $i/50 messages envoyés" -ForegroundColor Gray }
}
Write-Host "  ✅ Device 3: $device3_count/50 messages envoyés" -ForegroundColor Green

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║              ✅ TOTAL: 150 MESSAGES ENVOYÉS                  ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "⏳ Attente 5s pour le traitement..." -ForegroundColor Yellow
sleep 5

Write-Host "`n✅ ENVOI COMPLÉTÉ! Passez à l'étape 3 (vérification DB)" -ForegroundColor Green
