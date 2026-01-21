# Service Access & Ports Reference

## 🌐 Web Access After Deployment

### Immediate Access (After Deployment)

| Service | URL | Port | Description |
|---------|-----|------|-------------|
| **Web Portal** | http://localhost | 80 | Vue.js frontend for StageFL |
| **API Docs** | http://localhost:8000/docs | 8000 | Swagger UI documentation |
| **API JSON** | http://localhost:8000/openapi.json | 8000 | OpenAPI specification |
| **Database** | localhost:5433 | 5433 | PostgreSQL (psql/DBeaver) |
| **MQTT Broker** | localhost:1883 | 1883 | Mosquitto (mosquitto_pub/sub) |

---

## 📡 Port Mapping

### All Ports Used

```
┌─────────────────────────────────────────────────────┐
│                   HOST MACHINE                       │
│                                                     │
│  Port 80    ──→ Vue Frontend (HTTP)                │
│  Port 8000  ──→ FastAPI Server (API)               │
│  Port 5433  ──→ PostgreSQL Database                │
│  Port 1883  ──→ Mosquitto MQTT Broker (HOST)       │
│                                                     │
└─────────────────────────────────────────────────────┘

Internal Docker Network (172.17.0.0/16):
  • Sensor_Ingestor    → 172.17.0.x
  • Automation         → 172.17.0.x
  • Server_API         → 172.17.0.x (port 8000)
  • Client_Server      → 172.17.0.x
  • PostgreSQL         → 172.17.0.x (port 5432)
  • Vue_Frontend       → 172.17.0.x (port 3000)
```

### Port Usage Summary

```bash
# Port 80 (HTTP Web)
Host → Port 80 → Docker → Vue Frontend :3000

# Port 8000 (API)
Host → Port 8000 → Docker → FastAPI :8000

# Port 5433 (Database)
Host → Port 5433 → Docker → PostgreSQL :5432

# Port 1883 (MQTT)
Host Mosquitto → Port 1883 (NO DOCKER, uses HOST system mosquitto)

# Internal MQTT
Containers → host.docker.internal:1883 → Host Mosquitto :1883
```

---

## 🔌 Connection Strings

### PostgreSQL

**From Host Machine**:
```
Host: localhost
Port: 5433
User: program
Password: passwordFL
Database: FL
```

**Connection String**:
```
postgresql://program:passwordFL@localhost:5433/FL
```

**psql Command**:
```bash
psql -h localhost -p 5433 -U program -d FL
```

**DBeaver/GUI Tools**:
```
Server: localhost
Port: 5433
User: program
Password: passwordFL
Database: FL
```

### MQTT Broker

**From Host Machine**:
```
Broker: localhost
Port: 1883
Protocol: MQTT 3.1.1
```

**mosquitto_pub**:
```bash
mosquitto_pub -h localhost -p 1883 -t topic -m message
```

**mosquitto_sub**:
```bash
mosquitto_sub -h localhost -p 1883 -t 'topic/#'
```

**From Docker Container**:
```
Broker: host.docker.internal
Port: 1883
Protocol: MQTT 3.1.1
```

### FastAPI

**Swagger UI**:
```
http://localhost:8000/docs
```

**ReDoc**:
```
http://localhost:8000/redoc
```

**OpenAPI JSON**:
```
http://localhost:8000/openapi.json
```

### Web Frontend

```
http://localhost
http://localhost:80
```

---

## 🔍 Service Discovery

### From Browser

```
Web Portal:        http://localhost
                   → http://localhost:80 (explicit)

API Documentation: http://localhost:8000/docs
                   → Swagger UI with all endpoints
```

### From Command Line

```
# Check if port is listening
netstat -tulpn | grep -E ":(80|8000|5433|1883)"

# Using ss command (modern)
sudo ss -tulpn | grep -E ":(80|8000|5433|1883)"

# Check specific port
lsof -i :8000     # API
lsof -i :5433     # Database
lsof -i :1883     # MQTT
lsof -i :80       # Web
```

### From Docker

```bash
# List all port mappings
docker compose ps

# Expected output columns:
# CONTAINER  STATUS  PORTS
# PostgreSQL  Up  ...→5433/tcp
# server_api  Up  ...→8000/tcp
# vue_frontend Up  ...→80/tcp
# (MQTT has no Docker port - uses host)
```

---

## 🧪 Service Connection Tests

### Web Portal
```bash
# Quick test
curl -I http://localhost

# Expected: 200 OK or 301 redirect

# Get page
curl http://localhost | grep -i "<!DOCTYPE\|<html"
```

### API
```bash
# Swagger docs
curl -I http://localhost:8000/docs

# Expected: 200 OK

# OpenAPI spec
curl http://localhost:8000/openapi.json | jq '.' | head -20
```

### Database
```bash
# psql connection
docker exec PostgreSQL psql -U program -d FL -c "SELECT 1;"

# Expected: 
# ?column?
# ----------
#        1

# Connection test
psql -h localhost -p 5433 -U program -d FL -c "SELECT NOW();"

# Expected: current timestamp
```

### MQTT
```bash
# Subscribe test
timeout 5 mosquitto_sub -h localhost -p 1883 -t 'test' -W 2

# Expected: waits for message or timeout

# Publish test
mosquitto_pub -h localhost -p 1883 -t test -m "hello"

# Expected: message sent
```

---

## 🚀 Access Scenarios

### Scenario 1: Web Portal User

1. Open browser
2. Navigate to: **http://localhost**
3. See Vue.js frontend
4. Interact with IoT dashboard

**Requirements**: Port 80 listening

### Scenario 2: API Developer

1. Open browser
2. Navigate to: **http://localhost:8000/docs**
3. See Swagger UI
4. Test endpoints interactively
5. View request/response examples

**Requirements**: Port 8000 listening

### Scenario 3: Database Administrator

1. Install PostgreSQL client: `sudo apt install postgresql-client`
2. Connect: `psql -h localhost -p 5433 -U program -d FL`
3. Query data: `SELECT * FROM measurements LIMIT 10;`
4. Manage tables and indexes

**Requirements**: Port 5433 listening

### Scenario 4: MQTT Publisher/Subscriber

1. Install mosquitto clients: `sudo apt install mosquitto-clients`
2. Publish: `mosquitto_pub -h localhost -p 1883 -t Data -m "..."`
3. Subscribe: `mosquitto_sub -h localhost -p 1883 -t '#'`
4. Monitor data flow

**Requirements**: Port 1883 listening (host mosquitto)

### Scenario 5: Docker Container Developer

1. In container: access MQTT via `host.docker.internal:1883`
2. Example Python code:
```python
import paho.mqtt.client as mqtt

client = mqtt.Client()
client.connect("host.docker.internal", 1883, 60)
client.publish("topic/test", "message")
```

**Requirements**: extra_hosts configured in docker-compose

---

## 🔐 Security Considerations

### Port Access

```
RESTRICTED (Firewall Rules Recommended):
├── Port 1883 (MQTT): Only from localhost/trusted hosts
├── Port 5433 (Database): Only from Docker network or trusted IPs
└── Port 8000 (API): Consider API key authentication

OPEN (Generally OK):
└── Port 80 (Web): Public internet (if desired)
```

### Access Control Commands

```bash
# Check current port listening
sudo ss -tulpn | grep LISTEN

# Allow port 1883 only from localhost (ufw)
sudo ufw allow from 127.0.0.1 to 127.0.0.1 port 1883

# View firewall rules
sudo ufw status numbered
```

### Network Isolation

```bash
# Check Docker network
docker network ls
docker network inspect stagefl-main_default

# Verify PostgreSQL is only in Docker network
docker port PostgreSQL
# Expected: No port mappings (internal only)

# But exposed via 5433 mapping
docker compose ps | grep PostgreSQL
# Shows: 0.0.0.0:5433->5432/tcp
```

---

## 📊 Monitoring Port Activity

### Real-Time Port Monitoring

```bash
# Watch ports continuously
watch -n 1 'sudo ss -tulpn | grep -E ":(80|8000|5433|1883)"'

# Watch Docker ports
watch -n 2 'docker compose ps'

# Watch network connections
watch -n 2 'netstat -an | grep ESTABLISHED | wc -l'
```

### Port Activity Analysis

```bash
# Count connections per port
netstat -an | grep -E ":(80|8000|5433|1883)" | wc -l

# See which ports have connections
netstat -an | grep ESTABLISHED | awk '{print $4}' | cut -d: -f2 | sort | uniq -c

# Monitor MQTT connections
netstat -an | grep :1883

# Monitor API connections
netstat -an | grep :8000
```

---

## 🛠️ Troubleshooting Port Issues

### Port Already in Use

**Problem**: Port 80 is already in use
```bash
# Find what's using it
sudo lsof -i :80

# or
sudo ss -tulpn | grep :80

# Solution: Stop conflicting service or use different port
```

**Problem**: Cannot connect to database
```bash
# Verify PostgreSQL is running
docker compose ps PostgreSQL | grep "Up"

# Check if port is listening
sudo ss -tulpn | grep 5433

# Connect directly in container
docker exec PostgreSQL psql -U program -d FL -c "SELECT 1;"
```

**Problem**: MQTT not responding
```bash
# Check mosquitto service
sudo systemctl status mosquitto

# Check if port is listening
sudo ss -tulpn | grep 1883

# Test with socket
timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/1883" && echo "Open" || echo "Closed"
```

**Problem**: API not responding
```bash
# Check if container is running
docker compose ps Server_API

# Check if port is listening
sudo ss -tulpn | grep 8000

# Check logs
docker logs Server_API | tail -20

# Restart service
docker compose restart server_api
```

### Port Configuration Changes

If you need to change ports, edit `docker-compose.yml`:

```yaml
# Current configuration
postgres:
  ports:
    - "5433:5432"  # HOST:CONTAINER

server_api:
  ports:
    - "8000:8000"

vue_frontend:
  ports:
    - "80:3000"

# To change, modify the HOST port (first number)
# For example, use port 5434 for PostgreSQL:
postgres:
  ports:
    - "5434:5432"  # Changed from 5433 to 5434
```

Then restart:
```bash
docker compose down -v
docker compose up -d --build
```

---

## 📱 Remote Access

### Access from Another Machine

**Setup SSH Port Forwarding**:
```bash
# Local machine
ssh -L 5433:localhost:5433 \
    -L 8000:localhost:8000 \
    -L 80:localhost:80 \
    user@remote-server

# Then access as if local:
# Database: localhost:5433
# API: http://localhost:8000
# Web: http://localhost
```

**Direct Access (if firewall allows)**:
```bash
# Replace 'server-ip' with actual IP/hostname
psql -h server-ip -p 5433 -U program -d FL
curl http://server-ip:8000/docs
mosquitto_pub -h server-ip -p 1883 -t test -m hello
```

**Docker Expose All Ports**:
```bash
# In docker-compose.yml
services:
  server_api:
    ports:
      - "0.0.0.0:8000:8000"  # Listen on all interfaces
```

---

## ✅ Port Validation Checklist

After deployment, verify:

```bash
# 1. Port 80 (Web)
curl -I http://localhost
# Expected: HTTP/1.1 200 OK or 301

# 2. Port 8000 (API)
curl -I http://localhost:8000/docs
# Expected: HTTP/1.1 200 OK

# 3. Port 5433 (Database)
psql -h localhost -p 5433 -U program -d FL -c "SELECT 1;"
# Expected: Shows 1 row

# 4. Port 1883 (MQTT)
timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/1883"
# Expected: Exit status 0

# 5. All ports in single command
for port in 80 8000 5433 1883; do
  timeout 1 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/$port" && \
    echo "✓ Port $port: OPEN" || \
    echo "✗ Port $port: CLOSED"
done
```

---

## 🎯 Quick Port Reference Card

```
┌────────────────────────────────────────────────────────┐
│              SERVICE ACCESS REFERENCE                  │
├────────────────────────────────────────────────────────┤
│                                                        │
│  WEB INTERFACE                                         │
│  └─ http://localhost (Port 80)                        │
│                                                        │
│  API DOCUMENTATION                                     │
│  └─ http://localhost:8000/docs (Port 8000)            │
│  └─ http://localhost:8000/openapi.json                │
│                                                        │
│  DATABASE                                              │
│  └─ localhost:5433                                     │
│  └─ User: program                                      │
│  └─ DB: FL                                             │
│                                                        │
│  MQTT BROKER                                           │
│  └─ localhost:1883                                     │
│  └─ Protocol: MQTT 3.1.1                              │
│                                                        │
│  HEALTH CHECKS                                         │
│  └─ curl http://localhost       (Web)                │
│  └─ curl http://localhost:8000  (API)                │
│  └─ psql -h localhost -p 5433   (DB)                 │
│  └─ mosquitto_sub -h localhost  (MQTT)               │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

**Port Configuration**: ✅ Complete
**Access Documentation**: ✅ Complete
**Testing Commands**: ✅ Complete
**Remote Access**: ✅ Documented
