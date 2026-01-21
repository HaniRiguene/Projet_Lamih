# Linux Production Deployment - Quick Start

## 🚀 TL;DR - Commands to Run

```bash
# 1. Stop old project
cd ~/Bureau/FL && docker compose down -v

# 2. Prepare new project
cd ~/StageFL-main
docker compose config > /dev/null && echo "✓ Config valid"

# 3. Deploy with validation
sudo bash deploy-host-mosquitto.sh

# 4. Test connectivity
bash test-deployment.sh

# 5. Verify success
docker compose ps
curl http://localhost:8000/docs
```

---

## 📋 Prerequisites Checklist

Before deployment, verify these are ready:

```bash
# ✓ Host mosquitto running on port 1883
sudo systemctl status mosquitto
# Expected: active (running)

# ✓ Ports 80, 8000, 5433 are free
sudo ss -tulpn | grep -E ":(80|8000|5433)"
# Expected: No output (ports are free)

# ✓ Docker & docker compose installed
docker --version    # 20.10+
docker compose version  # 2.0+

# ✓ Project files present
ls -la ~/StageFL-main/docker-compose.yml
ls -la ~/StageFL-main/{Sensor_Ingestor,Automation,Serveur_Client,Serveur_API,Site_Vue}/Dockerfile
```

---

## 🏗️ What Changed in docker-compose.yml

### Removed
```yaml
# ❌ NO LONGER USED
# mosquitto:
#   image: eclipse-mosquitto:latest
```

### Added to All MQTT Services
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"  # ← Allows containers to reach host
```

### Environment Variables

| Service | Variables | Value |
|---------|-----------|-------|
| **Sensor_Ingestor** | MQTT_HOST, MQTT_PORT | host.docker.internal, 1883 |
| **Automation** | MQTT_HOST, MQTT_PORT | host.docker.internal, 1883 |
| **Server_API** | MQTT_HOST, MQTT_PORT | host.docker.internal, 1883 |
| **Client_Server** | **MQTT_BROKER_HOST**, MQTT_HOST, MQTT_PORT | host.docker.internal, host.docker.internal, 1883 |

**KEY**: Client_Server uses `MQTT_BROKER_HOST` (not `MQTT_HOST`)

---

## 📝 Step-by-Step Deployment

### Step 1: Verify Mosquitto

```bash
# Check service is running
sudo systemctl status mosquitto

# Check port is listening
sudo ss -tulpn | grep 1883
# Output: tcp  LISTEN 0 128 127.0.0.1:1883
```

### Step 2: Prepare Environment

```bash
cd ~/StageFL-main

# Verify structure
test -f docker-compose.yml && echo "✓ Found"
test -f Database/init.sql && echo "✓ Found"
ls -d Sensor_Ingestor Automation Serveur_Client Serveur_API Site_Vue
```

### Step 3: Deploy

```bash
# Validate config first
docker compose config > /dev/null

# Remove old containers
docker compose down -v

# Wait
sleep 5

# Build and start
docker compose up -d --build

# Wait for health checks
sleep 30

# Verify all running
docker compose ps
```

### Step 4: Test Connectivity

```bash
# Run full test suite
bash test-deployment.sh

# Or manual tests:

# Test 1: Socket connectivity
docker exec Sensor_Ingestor python3 << 'EOF'
import socket
sock = socket.socket()
if sock.connect_ex(("host.docker.internal", 1883)) == 0:
    print("✓ Container → host mosquitto OK")
else:
    print("✗ FAILED")
EOF

# Test 2: MQTT publish
mosquitto_pub -h localhost -p 1883 -t test/quick -m "test"

# Test 3: Data ingestion
mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[test_device][0][Sending Data][sensor:temp|value:20|msg_id:1]"
sleep 3
docker exec PostgreSQL psql -U program -d FL \
    -c "SELECT COUNT(*) FROM measurements WHERE device_id='test_device';"
```

---

## 🧪 Testing Guide

### Socket Test (Python)

```python
import socket

def test_socket(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

# From host
print("Host →", "✓" if test_socket("localhost", 1883) else "✗")

# From container (via Docker exec)
# Run: docker exec Sensor_Ingestor python3 << script.py
```

### MQTT Test

```bash
# Subscribe to all topics (real-time)
mosquitto_sub -h localhost -p 1883 -t '#' -v

# Publish from host
mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[device_id][0][Sending Data][sensor:temperature|value:22|msg_id:1]"

# Subscribe for 5 seconds
timeout 5 mosquitto_sub -h localhost -p 1883 -t test/#
```

### Database Test

```bash
# Connect to database
docker exec -it PostgreSQL psql -U program -d FL

# View schema
\dt

# Count messages
SELECT COUNT(*) FROM measurements;

# View latest messages
SELECT device_id, sensor_name, value, message_time 
FROM measurements ORDER BY message_time DESC LIMIT 10;
```

### API Test

```bash
# Swagger UI
curl -I http://localhost:8000/docs

# Get info endpoint (if available)
curl http://localhost:8000/info

# List devices (if available)
curl http://localhost:8000/devices
```

---

## 🔧 Troubleshooting

### Problem: Container can't reach host.docker.internal

**Check 1**: Verify extra_hosts in docker-compose
```bash
grep -A2 "extra_hosts" docker-compose.yml
# Should show: host.docker.internal:host-gateway
```

**Check 2**: Verify from container
```bash
docker exec Sensor_Ingestor cat /etc/hosts | grep host.docker.internal
# Should show an entry
```

**Check 3**: Rebuild
```bash
docker compose down -v
docker compose up -d --build
```

### Problem: Mosquitto connection refused

**Check 1**: Mosquitto running
```bash
sudo systemctl status mosquitto
# Should be: active (running)
```

**Check 2**: Port listening
```bash
sudo ss -tulpn | grep 1883
# Should show: LISTEN state
```

**Check 3**: Start if needed
```bash
sudo systemctl start mosquitto
```

### Problem: Client_Server logs show "Using default broker 172.18.0.1"

**Issue**: MQTT_BROKER_HOST not set properly

**Fix**: Verify in docker-compose.yml
```bash
grep -B3 -A8 "client_server:" docker-compose.yml | grep MQTT_BROKER_HOST
# Should show: MQTT_BROKER_HOST: host.docker.internal
```

**Rebuild**:
```bash
docker compose down -v
docker compose up -d --build
```

### Problem: PostgreSQL not becoming healthy

**Wait longer** (first time takes 30-60 seconds):
```bash
sleep 60
docker compose ps | grep PostgreSQL
```

**Check logs**:
```bash
docker logs PostgreSQL | tail -20
```

**Reset if needed**:
```bash
docker compose down -v
docker volume rm stagefl-main_postgres_data 2>/dev/null || true
docker compose up -d --build
```

---

## ✅ Validation Checklist

After deployment, verify these:

- [ ] `docker compose ps` shows all services as "Up"
- [ ] PostgreSQL is "healthy"
- [ ] Port 80 responds: `curl -I http://localhost`
- [ ] Port 8000 responds: `curl -I http://localhost:8000/docs`
- [ ] Port 5433 responds: `docker exec PostgreSQL psql -U program -d FL -c "SELECT 1;"`
- [ ] Port 1883 responds: `timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/1883"`
- [ ] Socket test passes: `docker exec Sensor_Ingestor python3 ...socket test...`
- [ ] MQTT pub works: `mosquitto_pub -h localhost -p 1883 -t test -m test`
- [ ] Data in DB: `docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) FROM measurements;"`
- [ ] No error logs: `docker compose logs | grep -i error`

---

## 📊 Test Results Format

When running `test-deployment.sh`, expect:

```
[PASS] PostgreSQL container running
[PASS] Sensor_Ingestor container running
[PASS] Port 80 listening
[PASS] Port 8000 listening
[PASS] Port 5433 listening
[PASS] Port 1883 listening
[PASS] Host → localhost:1883 (socket)
[PASS] Container → host.docker.internal:1883 (socket)
[PASS] Publish from host
[PASS] Publish from container
[PASS] Subscribe test
[PASS] PostgreSQL connection
[PASS] Database tables exist
[PASS] API responding
[PASS] Data ingestion (1 message(s))

Success Rate: 100%
✓ DEPLOYMENT VALIDATED - Ready for production
```

---

## 🚨 Common Mistakes

### ❌ Don't forget to:

1. Stop the old project before deploying
   ```bash
   cd ~/Bureau/FL && docker compose down -v
   ```

2. Use host.docker.internal (not localhost or 127.0.0.1)
   ```bash
   # ✓ Correct
   MQTT_HOST: host.docker.internal
   
   # ✗ Wrong
   MQTT_HOST: localhost  # Won't work in container
   ```

3. Ensure mosquitto is running on host
   ```bash
   sudo systemctl start mosquitto
   ```

4. Rebuild after docker-compose changes
   ```bash
   docker compose down -v
   docker compose up -d --build
   ```

5. Use MQTT_BROKER_HOST for Client_Server
   ```bash
   # ✓ Correct
   MQTT_BROKER_HOST: host.docker.internal
   
   # ✗ Won't work (Client_Server specifically requires this var name)
   MQTT_HOST: host.docker.internal
   ```

---

## 📞 Support & Logs

### View Real-Time Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f Sensor_Ingestor

# Last 50 lines
docker compose logs --tail=50

# With timestamps
docker compose logs -f --timestamps
```

### Check Specific Issues

```bash
# MQTT connection issues
docker logs Sensor_Ingestor 2>&1 | grep -i "mqtt\|connection\|error"

# Database connection
docker logs Sensor_Ingestor 2>&1 | grep -i "database\|postgres\|sql"

# Environment variables
docker exec Sensor_Ingestor env | grep MQTT
```

### Performance Check

```bash
# CPU/Memory usage
docker stats

# Container health
docker compose ps

# Disk space
df -h
```

---

## 📦 Deployment Scripts Provided

| Script | Purpose |
|--------|---------|
| `deploy-host-mosquitto.sh` | Full automated deployment with tests |
| `test-deployment.sh` | Validation test suite (can run anytime) |
| `docker-compose.yml` | Production configuration with host mosquitto |

### Usage

```bash
# Full deployment with all checks
sudo bash deploy-host-mosquitto.sh

# Just run tests (no deployment)
bash test-deployment.sh

# Manual deployment (step-by-step)
docker compose up -d --build
sleep 30
bash test-deployment.sh
```

---

## 🔍 Verification Commands

Quick commands to verify at any time:

```bash
# Service status
docker compose ps

# Port status
sudo ss -tulpn | grep -E ":(80|8000|5433|1883)"

# Database connectivity
docker exec PostgreSQL psql -U program -d FL -c "SELECT NOW();"

# Message count
docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) FROM measurements;"

# Recent messages
docker exec PostgreSQL psql -U program -d FL -c \
  "SELECT device_id, value, message_time FROM measurements ORDER BY message_time DESC LIMIT 5;"

# MQTT connectivity
mosquitto_sub -h localhost -p 1883 -t test -C 1 -W 2 > /dev/null 2>&1 && echo "✓ MQTT OK"

# API health
curl -s http://localhost:8000/docs | grep -q "Swagger UI" && echo "✓ API OK"
```

---

## 🎯 Next Steps After Deployment

1. **Monitor Logs**: Keep an eye on `docker compose logs -f`
2. **Test with Real Data**: Send actual sensor data via MQTT
3. **Load Test**: Send 100+ messages and verify all persist
4. **Schedule Backups**: PostgreSQL data should be backed up regularly
5. **Set Up Monitoring**: Monitor disk space, CPU, memory usage
6. **Document Setup**: Note any customizations made

---

**Status**: ✅ Production Ready
**Last Updated**: 2024
**Deployment Method**: Docker Compose + Host Mosquitto
**Tested Configurations**: ✓ All services running, ✓ MQTT connectivity, ✓ Data ingestion
