# Linux Deployment Guide - Host Mosquitto Integration

## Overview

This guide deploys **StageFL** on Linux with:
- ✅ **Host Mosquitto** (existing installation on port 1883)
- ✅ **Docker Compose** with 5 Python services + PostgreSQL
- ✅ **host.docker.internal** networking for service-to-host MQTT connectivity
- ✅ **Socket tests** + **MQTT pub/sub validation** before full deployment

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Architecture](#architecture)
3. [Configuration Details](#configuration-details)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Connectivity Testing](#connectivity-testing)
6. [Troubleshooting](#troubleshooting)
7. [Post-Deployment Validation](#post-deployment-validation)

---

## Pre-Deployment Checklist

Before starting deployment, verify:

```bash
# ✓ Mosquitto host is running
sudo systemctl status mosquitto
# Expected: active (running)

# ✓ No conflicting services on ports 80, 8000, 5433
sudo ss -tulpn | grep -E ":(80|8000|5433)"
# Expected: No output

# ✓ Docker and docker compose installed
docker --version
docker compose version

# ✓ Project directory structure
ls -la ~/StageFL-main/docker-compose.yml
ls -la ~/StageFL-main/Serveur_Client/
ls -la ~/StageFL-main/Sensor_Ingestor/
```

---

## Architecture

### Network Flow

```
┌─────────────────────────────────────────────────────┐
│              Linux Host (192.168.x.x)               │
│                                                     │
│  ┌─────────────────┐    ┌────────────────────┐     │
│  │  Mosquitto      │    │  PostgreSQL        │     │
│  │  :1883 (host)   │    │  (Docker :5433)    │     │
│  └────────┬────────┘    └────────┬───────────┘     │
│           │                      │                  │
│           │                      │                  │
│  ┌────────▼──────────────────────▼──────────────┐  │
│  │     Docker Bridge Network (172.17.0.0/16)    │  │
│  │                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │Sensor        │  │Automation    │          │  │
│  │  │Ingestor      │  │Service       │          │  │
│  │  │:172.17.0.x   │  │:172.17.0.x   │          │  │
│  │  └──────────────┘  └──────────────┘          │  │
│  │                                               │  │
│  │  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │Server API    │  │Client Server │          │  │
│  │  │:172.17.0.x   │  │:172.17.0.x   │          │  │
│  │  └──────────────┘  └──────────────┘          │  │
│  │                                               │  │
│  │  ┌────────────────────────────────┐           │  │
│  │  │ Vue Frontend :80               │           │  │
│  │  │ :172.17.0.x                    │           │  │
│  │  └────────────────────────────────┘           │  │
│  │                                               │  │
│  │  All services connect to:                    │  │
│  │  • MQTT: host.docker.internal:1883 ════════════ │
│  │    (resolves to 172.17.0.1 via gateway)     │  │
│  └───────────────────────────────────────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Environment Variables

| Service | MQTT Variable | Value | Port |
|---------|---------------|-------|------|
| Sensor_Ingestor | MQTT_HOST | host.docker.internal | 1883 |
| Automation | MQTT_HOST | host.docker.internal | 1883 |
| Server_API | MQTT_HOST | host.docker.internal | 1883 |
| Client_Server | **MQTT_BROKER_HOST** | host.docker.internal | 1883 |
| Vue_Frontend | (None) | - | - |

**Key Point**: `Client_Server` uses `MQTT_BROKER_HOST` (not `MQTT_HOST`)

---

## Configuration Details

### docker-compose.yml Changes

The production `docker-compose.yml` includes:

#### 1. All MQTT Services Have `extra_hosts`
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

**Why**: Allows containers to reach the host's mosquitto on port 1883

#### 2. Environment Variables for Each Service

**sensor_ingestor**:
```yaml
environment:
  MQTT_HOST: host.docker.internal
  MQTT_PORT: "1883"
```

**automation**:
```yaml
environment:
  MQTT_HOST: host.docker.internal
  MQTT_PORT: "1883"
```

**server_api**:
```yaml
environment:
  MQTT_HOST: host.docker.internal
  MQTT_PORT: "1883"
```

**client_server** (CRITICAL - Different env var name):
```yaml
environment:
  MQTT_BROKER_HOST: host.docker.internal  # ← NOT "MQTT_HOST"
  MQTT_HOST: host.docker.internal          # ← Also set for compatibility
  MQTT_PORT: "1883"
```

#### 3. Mosquitto Service - REMOVED
```yaml
# ❌ NO MOSQUITTO SERVICE
# Uses host mosquitto instead
```

#### 4. PostgreSQL Service
```yaml
postgresql:
  image: postgres:14-alpine
  container_name: PostgreSQL
  environment:
    POSTGRES_USER: program
    POSTGRES_PASSWORD: passwordFL
    POSTGRES_DB: FL
  ports:
    - "5433:5432"
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./Database/init.sql:/docker-entrypoint-initdb.d/init.sql
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U program -d FL"]
    interval: 10s
    timeout: 5s
    retries: 5
```

---

## Step-by-Step Deployment

### Step 1: Stop Old Project (If Running)

```bash
# Stop and remove old project containers/images
cd ~/Bureau/FL  # Old project directory

docker compose down -v
docker rmi fl_*

echo "✓ Old project stopped"
```

### Step 2: Prepare New Project

```bash
cd ~/StageFL-main

# Verify docker-compose.yml exists
test -f docker-compose.yml && echo "✓ docker-compose.yml found" || exit 1

# Verify all services have Dockerfiles
for service in Sensor_Ingestor Automation Serveur_API Serveur_Client Site_Vue; do
    test -f "$service/Dockerfile" && echo "✓ $service/Dockerfile found" || exit 1
done

# Verify Database/init.sql exists
test -f Database/init.sql && echo "✓ Database/init.sql found" || exit 1
```

### Step 3: Validate Configuration

```bash
# Check docker-compose.yml syntax
docker compose config > /dev/null && echo "✓ docker-compose.yml valid" || exit 1

# Verify host.docker.internal is configured
grep -q "host.docker.internal" docker-compose.yml && \
    echo "✓ host.docker.internal configured" || exit 1

# Verify MQTT_BROKER_HOST is set
grep -q "MQTT_BROKER_HOST" docker-compose.yml && \
    echo "✓ MQTT_BROKER_HOST configured" || exit 1
```

### Step 4: Build and Start Services

```bash
# Clean previous deployment
docker compose down -v

# Wait for cleanup
sleep 5

# Build and start services
docker compose up -d --build

# Verify all services started
sleep 10
docker compose ps
```

### Step 5: Verify Mosquitto Host Connectivity

```bash
# Test socket connectivity from host
python3 << 'EOF'
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("localhost", 1883))
sock.close()

if result == 0:
    print("✓ Host mosquitto (:1883) reachable")
else:
    print("✗ Host mosquitto (:1883) NOT reachable")
    exit(1)
EOF
```

### Step 6: Verify Container Connectivity

```bash
# Test socket connectivity from inside container
docker exec Sensor_Ingestor python3 << 'EOF'
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("host.docker.internal", 1883))
sock.close()

if result == 0:
    print("✓ Container → host.docker.internal:1883 OK")
else:
    print("✗ Container → host.docker.internal:1883 FAILED")
    exit(1)
EOF
```

---

## Connectivity Testing

### Test 1: Socket Connectivity (Python)

```python
import socket

def test_mqtt_socket(host, port, timeout=5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✓ Connection to {host}:{port} successful")
            return True
        else:
            print(f"✗ Connection to {host}:{port} failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

# From host
print("[HOST]")
test_mqtt_socket("localhost", 1883)

# From container
import subprocess
print("\n[CONTAINER]")
result = subprocess.run([
    "docker", "exec", "Sensor_Ingestor", "python3", "-c",
    "import socket; sock = socket.socket(); result = sock.connect_ex(('host.docker.internal', 1883)); sock.close(); print('✓' if result == 0 else '✗')"
], capture_output=True, text=True)
print(result.stdout)
```

### Test 2: MQTT Publish/Subscribe

```bash
# Test 1: Publish from host
mosquitto_pub -h localhost -p 1883 -t test/connectivity -m "test-$(date +%s)"
echo "✓ Published from host"

# Test 2: Publish from container
docker exec Sensor_Ingestor mosquitto_pub -h host.docker.internal -p 1883 -t test/container -m "container-test-$(date +%s)"
echo "✓ Published from container"

# Test 3: Subscribe (timeout 5 seconds)
mosquitto_sub -h localhost -p 1883 -t test/# -C 1
echo "✓ Subscribe successful"
```

### Test 3: Data Ingestion

```bash
# Publish sensor data
mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[test_device][0][Sending Data][sensor:temperature|value:22.5|msg_id:test-1]"

sleep 2

# Query database
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT COUNT(*) as message_count FROM measurements WHERE device_id='test_device';
SQL
```

---

## Troubleshooting

### Issue 1: Container Cannot Connect to host.docker.internal

**Symptom**: 
```
Connection refused to host.docker.internal:1883
```

**Solution**:
```bash
# Verify extra_hosts in docker-compose.yml
grep -A2 "extra_hosts" docker-compose.yml

# Verify from container
docker exec Sensor_Ingestor cat /etc/hosts | grep host.docker.internal

# Rebuild with correct config
docker compose down -v
docker compose up -d --build
```

### Issue 2: Services Failing to Connect to Mosquitto

**Symptom**:
```
docker logs Sensor_Ingestor | grep -i "mqtt\|connection"
# Shows: "Connection failed" or "Cannot connect"
```

**Solution**:
```bash
# Verify mosquitto is running on host
sudo systemctl status mosquitto

# Check port 1883 is listening
sudo ss -tulpn | grep 1883

# Restart if needed
sudo systemctl restart mosquitto
```

### Issue 3: Client_Server Using Wrong Environment Variable

**Symptom**:
```
docker logs Client_Server | grep -i "MQTT_HOST"
# Shows: "Using default broker 172.18.0.1" (old Docker IP)
```

**Solution**:
```bash
# Verify MQTT_BROKER_HOST is set in docker-compose.yml
grep -B5 -A5 "client_server:" docker-compose.yml | grep MQTT_BROKER_HOST

# Verify in running container
docker exec Client_Server env | grep MQTT_BROKER_HOST

# Rebuild if missing
docker compose down -v
docker compose up -d --build
```

### Issue 4: PostgreSQL Not Healthy

**Symptom**:
```
docker compose ps
# postgres: unhealthy
```

**Solution**:
```bash
# Check logs
docker logs PostgreSQL

# Wait longer for PostgreSQL to initialize
sleep 30
docker exec PostgreSQL psql -U program -d FL -c "SELECT 1;"

# If still failing, reset
docker compose down -v
docker compose up -d --build
sleep 60
```

### Issue 5: Web UI Not Accessible

**Symptom**:
```
curl http://localhost:80/
# Connection refused
```

**Solution**:
```bash
# Check if container is running
docker compose ps vue_frontend

# Check logs
docker logs vue_frontend

# Verify port binding
sudo ss -tulpn | grep ":80 "

# Restart service
docker compose restart vue_frontend
```

---

## Post-Deployment Validation

### 1. Check All Services Status

```bash
# Service status
docker compose ps

# All should show: "Up (healthy)" or "Up"
```

### 2. Verify Ports

```bash
# Port 80 (Web)
curl -I http://localhost/

# Port 8000 (API)
curl -I http://localhost:8000/docs

# Port 5433 (PostgreSQL)
docker exec PostgreSQL psql -U program -d FL -c "SELECT NOW();"
```

### 3. Test MQTT End-to-End

```bash
# Publish
mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[deploy_test][0][Sending Data][sensor:temperature|value:23|msg_id:deploy-test]"

sleep 5

# Verify in database
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT device_id, COUNT(*) FROM measurements GROUP BY device_id;
SQL
```

### 4. Check Logs for Errors

```bash
# Sensor Ingestor
docker logs Sensor_Ingestor | tail -20

# Client Server
docker logs Client_Server | tail -20

# Server API
docker logs Server_API | tail -20

# No "Error" or "Connection failed" should appear
```

### 5. Performance Test

```bash
# Publish 50 messages
for i in {1..50}; do
    mosquitto_pub -h localhost -p 1883 -t Data \
        -m "[perf_test][0][Sending Data][sensor:temperature|value:$((20+RANDOM%10))|msg_id:perf-$i]"
done

sleep 10

# Verify all received
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT COUNT(*) FROM measurements WHERE device_id='perf_test';
SQL

# Expected: 50 (or close to it)
```

---

## Deployment Automation

A complete deployment script is provided: [deploy-host-mosquitto.sh](deploy-host-mosquitto.sh)

```bash
sudo bash deploy-host-mosquitto.sh
```

This script automatically:
1. ✓ Checks prerequisites
2. ✓ Validates docker-compose.yml
3. ✓ Builds and deploys services
4. ✓ Tests socket connectivity (host + container)
5. ✓ Tests MQTT pub/sub
6. ✓ Verifies data ingestion
7. ✓ Validates all services
8. ✓ Shows deployment summary

---

## Monitoring

### Real-Time Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f Sensor_Ingestor
docker compose logs -f Client_Server

# Filter by pattern
docker compose logs -f | grep -i "mqtt\|error"
```

### Database Monitoring

```bash
# Message count by device
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT device_id, COUNT(*) as count, 
       MAX(message_time) as latest 
FROM measurements 
GROUP BY device_id 
ORDER BY latest DESC;
SQL

# Recent messages
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT device_id, sensor_name, value, message_time 
FROM measurements 
ORDER BY message_time DESC 
LIMIT 20;
SQL
```

### MQTT Monitoring

```bash
# Subscribe to all topics (real-time)
mosquitto_sub -h localhost -p 1883 -t '#' -v

# Count messages per topic
mosquitto_sub -h localhost -p 1883 -t '#' -C 100 | awk -F' ' '{print $1}' | sort | uniq -c
```

---

## Rollback Procedure

If deployment fails or needs to be rolled back:

```bash
# Stop all services
docker compose down -v

# Verify stopped
docker ps | grep -E "(Sensor|Automation|Client|Server|Frontend)" || echo "All stopped"

# If needed, restart old project
cd ~/Bureau/FL
docker compose up -d

echo "✓ Rolled back to previous version"
```

---

## Success Criteria

After deployment, verify:

- [ ] `docker compose ps` shows all services as "Up"
- [ ] PostgreSQL healthcheck is "healthy"
- [ ] Socket test passes (host → localhost:1883, container → host.docker.internal:1883)
- [ ] MQTT pub/sub test passes
- [ ] Data ingestion test shows messages in PostgreSQL
- [ ] Web UI accessible at http://localhost
- [ ] API docs accessible at http://localhost:8000/docs
- [ ] Logs show no MQTT connection errors
- [ ] 50-message performance test completes with count ≥ 48 (96%)

---

## Key Files Modified

- `docker-compose.yml` - Removed mosquitto service, added extra_hosts, configured MQTT_BROKER_HOST
- All Dockerfiles - No changes (use host mosquitto)
- `.env` or environment variables - None needed (hardcoded in docker-compose)

---

## Support

For issues:

1. Check Mosquitto: `sudo systemctl status mosquitto`
2. Check Docker: `docker compose ps`
3. Check logs: `docker compose logs <service>`
4. Test socket: `docker exec Sensor_Ingestor nc -zv host.docker.internal 1883`
5. Test MQTT: `mosquitto_sub -h localhost -p 1883 -t test/# -C 1`

---

**Last Updated**: $(date)
**Deployment Method**: Linux with host mosquitto
**Docker Compose Version**: 2.0+
**Docker Version**: 20.10+
