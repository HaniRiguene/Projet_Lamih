# 🤖 ÉTAPE 5 (OPTIONNEL): Tester l'Automation Service
# Usage: ./demo_5_test_automation.ps1

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        🤖 TEST AUTOMATION SERVICE - HYSTERESIS LAMP           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "ℹ Configuration du service Automation:" -ForegroundColor Yellow
Write-Host "  • Capteur écouté: 'light'" -ForegroundColor Gray
Write-Host "  • Threshold LOW: 200 lux → Allume lampe après 5s" -ForegroundColor Gray
Write-Host "  • Threshold HIGH: 300 lux → Éteint lampe après 5s" -ForegroundColor Gray
Write-Host "  • Topic actuator: actuators/lamp1/set" -ForegroundColor Gray

Write-Host "`n═══════════════════════════════════════════════════════════════" -ForegroundColor Gray

# ============================================================================
# Envoyer des mesures de faible luminosité (< 200 = allume)
# ============================================================================
Write-Host "`n📤 Envoi de 20 mesures avec faible luminosité (50-150 lux)..." -ForegroundColor Green
Write-Host "   (Cela devrait déclencher l'allumage de la lampe après 5s)" -ForegroundColor Gray

$light_count = 0
for ($i = 1; $i -le 20; $i++) {
  $val = Get-Random -Minimum 50 -Maximum 150
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[light_sensor][0][Sending Data][sensor:light|value:$val|msg_id:light_$i]"
  Start-Sleep -Milliseconds 100
  $light_count++
  if ($i % 5 -eq 0) { Write-Host "  ✓ $i/20 messages envoyés" -ForegroundColor Gray }
}

Write-Host "✅ $light_count messages envoyés" -ForegroundColor Green

# ============================================================================
# Attendre l'hysteresis (5s de seuil)
# ============================================================================
Write-Host "`n⏳ Attente 8s pour hysteresis..." -ForegroundColor Yellow
for ($i = 0; $i -le 8; $i++) {
  Write-Host "   $i/8s" -ForegroundColor Gray -NoNewline
  Start-Sleep 1
  Write-Host "`r" -NoNewline
}
Write-Host "   ✓ Hysteresis complète" -ForegroundColor Green

# ============================================================================
# Vérifier les logs du service Automation
# ============================================================================
Write-Host "`n📋 Logs du service Automation:" -ForegroundColor Yellow
Write-Host "════════════════════════════════════" -ForegroundColor Gray

$logs = docker logs Automation_Service --tail 10
if ($logs -match "Publish.*ON.*lamp1") {
  Write-Host "✅ SUCCÈS - Lampe allumée!" -ForegroundColor Green
  $logs | Select-String "Publish"
} elseif ($logs -match "Connected") {
  Write-Host "ℹ Service connecté mais pas d'action encore" -ForegroundColor Yellow
  $logs | Select-String "Connected|Subscribed"
} else {
  Write-Host "ℹ Logs du service:" -ForegroundColor Gray
  $logs | Select-Object -Last 5
}

# ============================================================================
# TEST OPTIONNEL: Envoyer haute luminosité (> 300 = éteint)
# ============================================================================
Write-Host "`n📤 (OPTIONNEL) Envoi de 20 mesures haute luminosité (350-450 lux)..." -ForegroundColor Cyan
Write-Host "   (Cela devrait éteindre la lampe après 5s)" -ForegroundColor Gray

$response = Read-Host "Continuer? (O/N)"
if ($response -eq "O") {
  for ($i = 1; $i -le 20; $i++) {
    $val = Get-Random -Minimum 350 -Maximum 450
    docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[light_sensor][0][Sending Data][sensor:light|value:$val|msg_id:light_off_$i]"
    Start-Sleep -Milliseconds 100
    if ($i % 5 -eq 0) { Write-Host "  ✓ $i/20 messages envoyés" -ForegroundColor Gray }
  }
  
  Write-Host "`n⏳ Attente 8s..." -ForegroundColor Yellow
  sleep 8
  
  Write-Host "`nVérification logs:" -ForegroundColor Yellow
  docker logs Automation_Service --tail 5 | Select-String "Publish|OFF"
}

Write-Host "`n✅ TEST AUTOMATION COMPLÉTÉ!" -ForegroundColor Green
