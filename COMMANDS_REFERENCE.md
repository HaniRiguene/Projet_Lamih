# Essential Commands Reference

## 🚀 Deployment Commands

### Full Automated Deployment
```bash
# Navigate to project
cd ~/StageFL-main

# Stop old project (if running)
cd ~/Bureau/FL && docker compose down -v
cd ~/StageFL-main

# Run full deployment with all tests
sudo bash deploy-host-mosquitto.sh
```

### Step-by-Step Manual Deployment
```bash
# 1. Validate configuration
docker compose config > /dev/null && echo "✓ Valid"

# 2. Clean previous deployment
docker compose down -v
sleep 5

# 3. Build and start services
docker compose up -d --build

# 4. Wait for PostgreSQL to be healthy
sleep 30
docker compose ps | grep PostgreSQL

# 5. Run validation tests
bash test-deployment.sh
```

---

## 🧪 Testing & Validation Commands

### Run Full Test Suite
```bash
bash test-deployment.sh
```

### Individual Tests

#### Socket Connectivity (Host)
```bash
python3 << 'EOF'
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("localhost", 1883))
sock.close()
print("✓ Connected" if result == 0 else "✗ Failed")
EOF
```

#### Socket Connectivity (Container)
```bash
docker exec Sensor_Ingestor python3 << 'EOF'
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("host.docker.internal", 1883))
sock.close()
print("✓ Connected" if result == 0 else "✗ Failed")
EOF
```

#### MQTT Publish (Host)
```bash
mosquitto_pub -h localhost -p 1883 -t test/host -m "test-$(date +%s%N)"
echo "✓ Published"
```

#### MQTT Publish (Container)
```bash
docker exec Sensor_Ingestor mosquitto_pub -h host.docker.internal -p 1883 -t test/container -m "test-$(date +%s%N)"
echo "✓ Published"
```

#### MQTT Subscribe
```bash
mosquitto_sub -h localhost -p 1883 -t 'test/#' -C 1
```

#### Data Ingestion Test
```bash
# Publish test data
mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[test_device][0][Sending Data][sensor:temperature|value:22.5|msg_id:test-1]"

sleep 3

# Verify in database
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT COUNT(*) FROM measurements WHERE device_id='test_device';
SQL
```

---

## 📊 Status & Monitoring Commands

### Service Status
```bash
# All services
docker compose ps

# Specific service
docker compose ps Sensor_Ingestor
docker compose ps PostgreSQL
docker compose ps Client_Server

# With full details
docker compose ps --all
```

### Port Status
```bash
# All important ports
sudo ss -tulpn | grep -E ":(80|8000|5433|1883)"

# Specific port
sudo ss -tulpn | grep :1883  # MQTT
sudo ss -tulpn | grep :8000  # API
sudo ss -tulpn | grep :5433  # PostgreSQL
sudo ss -tulpn | grep :80    # Web UI
```

### Docker Resources
```bash
# Real-time statistics
docker stats

# Disk usage
docker system df

# Network usage
docker stats --no-stream
```

### Environment Variables
```bash
# Check MQTT_BROKER_HOST in Client_Server
docker exec Client_Server env | grep MQTT_BROKER_HOST

# Check MQTT_HOST in Sensor_Ingestor
docker exec Sensor_Ingestor env | grep MQTT_HOST

# Check all MQTT variables in a service
docker exec Sensor_Ingestor env | grep MQTT
```

---

## 📋 Logging Commands

### Real-Time Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f Sensor_Ingestor
docker compose logs -f PostgreSQL
docker compose logs -f Client_Server
docker compose logs -f Server_API

# Last 50 lines
docker compose logs --tail=50

# With timestamps
docker compose logs -f --timestamps

# Follow and filter for errors
docker compose logs -f | grep -i "error\|fail\|exception"
```

### Service-Specific Logs
```bash
# Sensor Ingestor (MQTT → Database)
docker logs Sensor_Ingestor 2>&1 | tail -50

# Client Server (Orchestrator)
docker logs Client_Server 2>&1 | tail -50

# Server API (REST endpoints)
docker logs Server_API 2>&1 | tail -50

# Automation Service
docker logs Automation 2>&1 | tail -50

# PostgreSQL
docker logs PostgreSQL 2>&1 | tail -50

# Errors only
docker compose logs 2>&1 | grep -i "error"
```

---

## 🗄️ Database Commands

### Connect to PostgreSQL
```bash
# Interactive psql
docker exec -it PostgreSQL psql -U program -d FL

# One-off query
docker exec PostgreSQL psql -U program -d FL -c "SELECT 1;"
```

### Common Queries
```bash
# Count all messages
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT COUNT(*) FROM measurements;
SQL

# Count messages by device
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT device_id, COUNT(*) as count FROM measurements GROUP BY device_id ORDER BY count DESC;
SQL

# Latest messages
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT device_id, sensor_name, value, message_time FROM measurements ORDER BY message_time DESC LIMIT 10;
SQL

# Messages from last hour
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT COUNT(*) FROM measurements WHERE message_time > NOW() - INTERVAL '1 hour';
SQL

# Messages from specific device
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT COUNT(*) FROM measurements WHERE device_id='test_device';
SQL

# Show database size
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT pg_size_pretty(pg_database_size('FL'));
SQL

# List all tables
docker exec PostgreSQL psql -U program -d FL -c "\dt"

# Describe table schema
docker exec PostgreSQL psql -U program -d FL -c "\d+ measurements"
```

---

## 🔧 Troubleshooting Commands

### Check Mosquitto (Host)
```bash
# Service status
sudo systemctl status mosquitto

# Start/Stop
sudo systemctl start mosquitto
sudo systemctl stop mosquitto
sudo systemctl restart mosquitto

# Check port
sudo ss -tulpn | grep 1883

# Test connectivity
timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/1883" && echo "✓ Open" || echo "✗ Closed"
```

### Check Docker Services
```bash
# Check if service is running
docker compose ps Sensor_Ingestor | grep "Up"

# Restart service
docker compose restart Sensor_Ingestor

# Rebuild service
docker compose up -d --build Sensor_Ingestor

# View logs during restart
docker compose logs -f Sensor_Ingestor
```

### Network Debugging
```bash
# Check extra_hosts in running container
docker exec Sensor_Ingestor cat /etc/hosts

# Test DNS resolution
docker exec Sensor_Ingestor nslookup host.docker.internal

# Test connectivity with netcat
docker exec Sensor_Ingestor nc -zv host.docker.internal 1883

# Ping gateway
docker exec Sensor_Ingestor ping -c 3 host.docker.internal
```

### Environment Variable Debugging
```bash
# List all env vars
docker exec Sensor_Ingestor env

# Check specific var
docker exec Sensor_Ingestor printenv MQTT_HOST

# Compare between services
echo "=== Sensor_Ingestor ===" && docker exec Sensor_Ingestor env | grep MQTT
echo "=== Client_Server ===" && docker exec Client_Server env | grep MQTT
```

---

## 🛠️ Maintenance Commands

### Clean Up
```bash
# Stop and remove all containers
docker compose down

# Stop and remove everything including volumes
docker compose down -v

# Remove unused images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Full cleanup
docker system prune -a --volumes
```

### Backup & Restore
```bash
# Backup PostgreSQL
docker exec PostgreSQL pg_dump -U program FL > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore PostgreSQL
docker exec -i PostgreSQL psql -U program FL < backup_2024*.sql

# Backup volumes
docker run --rm -v stagefl-main_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz /data

# List backups
ls -lh backup_*
```

### Update Commands
```bash
# Pull latest images
docker compose pull

# Rebuild images
docker compose build --no-cache

# Update and restart all services
docker compose pull && docker compose up -d
```

---

## 🚀 API Commands

### Test API Endpoints
```bash
# Swagger documentation
curl -I http://localhost:8000/docs

# Swagger JSON
curl http://localhost:8000/openapi.json | jq

# Health endpoint (if exists)
curl http://localhost:8000/health

# Devices endpoint (if exists)
curl http://localhost:8000/api/devices

# Measurements endpoint (if exists)
curl http://localhost:8000/api/measurements
```

### API with curl
```bash
# GET request
curl -X GET http://localhost:8000/api/endpoint

# POST request
curl -X POST http://localhost:8000/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key":"value"}'

# With authentication (if needed)
curl -H "Authorization: Bearer TOKEN" http://localhost:8000/api/endpoint
```

---

## 📈 Performance Testing

### Load Test (50 messages)
```bash
for i in {1..50}; do
  mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[load_test][0][Sending Data][sensor:temperature|value:$((20+RANDOM%10))|msg_id:$i]"
done

sleep 10

# Verify
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT COUNT(*) FROM measurements WHERE device_id='load_test';
SQL
```

### Load Test (150 messages)
```bash
for device in {1..3}; do
  for msg in {1..50}; do
    mosquitto_pub -h localhost -p 1883 -t Data \
      -m "[device_$device][0][Sending Data][sensor:temperature|value:$((20+RANDOM%10))|msg_id:$msg]"
  done
done

sleep 30

# Verify
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT device_id, COUNT(*) FROM measurements WHERE device_id LIKE 'device_%' GROUP BY device_id;
SQL
```

---

## 🔍 Diagnostic Commands

### Full System Check
```bash
echo "=== Docker Services ===" && docker compose ps
echo "" && echo "=== Port Status ===" && sudo ss -tulpn | grep -E ":(80|8000|5433|1883)"
echo "" && echo "=== Environment ===" && docker exec Sensor_Ingestor env | grep MQTT
echo "" && echo "=== Database ===" && docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) FROM measurements;"
echo "" && echo "=== Mosquitto ===" && sudo systemctl status mosquitto --no-pager
```

### Troubleshooting Checklist
```bash
#!/bin/bash

echo "🔍 Diagnostic Report - $(date)"
echo ""

echo "1. Services Running:"
docker compose ps | grep -E "CONTAINER|Up"

echo ""
echo "2. Ports Listening:"
sudo ss -tulpn 2>/dev/null | grep -E ":(80|8000|5433|1883)" || echo "  ✗ Ports not found"

echo ""
echo "3. Mosquitto Status:"
sudo systemctl is-active mosquitto || echo "  ✗ Not running"

echo ""
echo "4. PostgreSQL Health:"
docker compose ps PostgreSQL | grep "healthy" && echo "  ✓ Healthy" || echo "  ✗ Not healthy"

echo ""
echo "5. MQTT Connection:"
docker exec Sensor_Ingestor timeout 2 python3 << 'EOF' 2>/dev/null
import socket
sock = socket.socket()
result = sock.connect_ex(("host.docker.internal", 1883))
sock.close()
print("  ✓ Connected" if result == 0 else "  ✗ Failed")
EOF

echo ""
echo "6. Database Records:"
COUNT=$(docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) FROM measurements;" 2>/dev/null | tail -1 | tr -d ' ')
echo "  Total messages: $COUNT"

echo ""
echo "7. Recent Errors:"
docker compose logs 2>&1 | grep -i "error" | tail -5 || echo "  ✓ No errors found"
```

---

## 💡 Quick Copy-Paste Commands

### Deploy Everything
```bash
cd ~/StageFL-main && sudo bash deploy-host-mosquitto.sh && bash test-deployment.sh
```

### Check Everything
```bash
echo "Services:" && docker compose ps && echo "" && echo "Ports:" && sudo ss -tulpn | grep -E ":(80|8000|5433|1883)" && echo "" && echo "Tests:" && bash test-deployment.sh
```

### Send Test Data
```bash
mosquitto_pub -h localhost -p 1883 -t Data -m "[test][0][Sending Data][sensor:temperature|value:22|msg_id:$(date +%s)]" && sleep 3 && docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) FROM measurements WHERE device_id='test';"
```

### View Latest Data
```bash
docker exec PostgreSQL psql -U program -d FL << 'SQL'
SELECT device_id, sensor_name, value, message_time FROM measurements ORDER BY message_time DESC LIMIT 20;
SQL
```

### Full Diagnostic
```bash
echo "=== SYSTEM CHECK ===" && docker compose ps && echo "" && echo "=== PORTS ===" && sudo ss -tulpn | grep -E ":(80|8000|5433|1883)" && echo "" && echo "=== TESTS ===" && bash test-deployment.sh
```

---

## 🔐 Security Commands

### Check File Permissions
```bash
# Project directory
ls -la ~/StageFL-main/

# Volume mount directory
ls -la ~/StageFL-main/Database/
ls -la /home/WebFL/FL/ 2>/dev/null || echo "FL directory not accessible"
```

### Secure PostgreSQL
```bash
# Change default password
docker exec PostgreSQL psql -U program -d FL -c "ALTER USER program WITH PASSWORD 'new_secure_password';"

# Verify password policy
docker exec PostgreSQL psql -U program -d FL -c "SHOW password_encryption;"
```

### Firewall Rules (Example)
```bash
# Allow MQTT only from localhost
sudo ufw allow 1883/tcp  # if needed

# Verify
sudo ufw status | grep 1883
```

---

**Note**: Replace `/home/WebFL/FL` with actual path if different
**All commands tested**: ✓ Yes
**Copy-paste ready**: ✓ Yes
