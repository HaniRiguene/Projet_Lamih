# Demo Complete
Write-Host "STEP 1: Cleaning up..." -ForegroundColor Yellow
docker compose down -v
docker compose up -d
Write-Host "Waiting 15 seconds..." -ForegroundColor Gray
sleep 15
Write-Host "OK" -ForegroundColor Green

Write-Host ""
Write-Host "STEP 2a: Device 1 - salle_a_manger (50 msgs)" -ForegroundColor Yellow
for ($i = 1; $i -le 50; $i++) {
  $val = Get-Random -Minimum 18 -Maximum 24
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[salle_a_manger][0][Sending Data][sensor:temperature|value:$val|msg_id:d1_$i]"
  if ($i % 10 -eq 0) { Write-Host "  OK $i/50" -ForegroundColor Gray }
  Start-Sleep -Milliseconds 8
}
sleep 5

Write-Host ""
Write-Host "STEP 2b: Device 2 - temperature_cuisine (50 msgs)" -ForegroundColor Yellow
for ($i = 1; $i -le 50; $i++) {
  $val = Get-Random -Minimum 20 -Maximum 26
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[capteur_de_temperature_cuisine][0][Sending Data][sensor:temperature|value:$val|msg_id:d2_$i]"
  if ($i % 10 -eq 0) { Write-Host "  OK $i/50" -ForegroundColor Gray }
  Start-Sleep -Milliseconds 8
}
sleep 5

Write-Host ""
Write-Host "STEP 2c: Device 3 - laser (50 msgs)" -ForegroundColor Yellow
for ($i = 1; $i -le 50; $i++) {
  $val = Get-Random -Minimum 0 -Maximum 1
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[capteur_de_laser_salle_de_bain][0][Sending Data][sensor:laser|value:$val|msg_id:d3_$i]"
  if ($i % 10 -eq 0) { Write-Host "  OK $i/50" -ForegroundColor Gray }
  Start-Sleep -Milliseconds 8
}
Write-Host "OK - All 150 msgs sent" -ForegroundColor Green
sleep 5

Write-Host ""
Write-Host "STEP 3: Verify Database" -ForegroundColor Yellow
docker exec PostgreSQL psql -U program -d FL -c "SELECT device_id, COUNT(*) as cnt FROM measurements GROUP BY device_id ORDER BY device_id;"
sleep 2

Write-Host ""
Write-Host "STEP 4: Test APIs" -ForegroundColor Yellow
Write-Host "API 1: Devices" -ForegroundColor Cyan
$devices = Invoke-RestMethod "http://localhost:8000/v1/devices"
$devices | Format-Table device_id, name

Write-Host ""
Write-Host "API 2: Latest values" -ForegroundColor Cyan
$latest = Invoke-RestMethod "http://localhost:8000/v1/devices/salle_a_manger/latest"
$latest | Format-Table sensor, value

Write-Host ""
Write-Host "API 3: Recent measurements" -ForegroundColor Cyan
$measurements = Invoke-RestMethod "http://localhost:8000/v1/measurements?limit=5"
$measurements | Format-Table device_id, sensor, value

Write-Host ""
Write-Host "API 4: Aggregates" -ForegroundColor Cyan
$aggregate = Invoke-RestMethod "http://localhost:8000/v1/measurements/aggregate?time_bucket=10m"
$aggregate | Format-Table device_id, time_bucket, avg_value

Write-Host ""
Write-Host "SUCCESS! Demo complete." -ForegroundColor Green
