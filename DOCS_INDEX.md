# Production Deployment Documentation Index

## 📑 Quick Navigation

### 🚀 Start Here (First-Time Users)

1. **[QUICK_START.md](QUICK_START.md)** ⭐ START HERE
   - 5-step quick deployment
   - TL;DR commands
   - Common mistakes to avoid
   - **Time**: 5-10 minutes to read

2. **[PROD_DEPLOYMENT_SUMMARY.md](PROD_DEPLOYMENT_SUMMARY.md)** - Overview
   - What was done
   - Key discoveries
   - Files modified/created
   - **Time**: 10 minutes to read

### 📚 Detailed Guides

3. **[DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md)** - Full Documentation
   - Complete architecture overview
   - Configuration details
   - Step-by-step deployment
   - Troubleshooting guide
   - Monitoring procedures
   - **Time**: 20-30 minutes to read

### 🛠️ Automation Scripts

4. **[deploy-host-mosquitto.sh](deploy-host-mosquitto.sh)** - Automated Deployment
   - Full deployment automation
   - All checks included
   - Socket & MQTT testing
   - **Usage**: `sudo bash deploy-host-mosquitto.sh`
   - **Time**: 3-4 minutes to run

5. **[test-deployment.sh](test-deployment.sh)** - Validation Suite
   - 8 test categories
   - Service verification
   - Connectivity testing
   - **Usage**: `bash test-deployment.sh`
   - **Time**: 1-2 minutes to run

### 🔧 Configuration

6. **[docker-compose.yml](docker-compose.yml)** - Production Configuration
   - Host mosquitto integration
   - Environment variables
   - Health checks
   - Volume management

---

## 🎯 Deployment Scenarios

### Scenario 1: First Time Deployment

**Time**: 15-20 minutes total

```
1. Read: QUICK_START.md (5 min)
        ↓
2. Run: deploy-host-mosquitto.sh (5 min)
        ↓
3. Verify: test-deployment.sh (2 min)
        ↓
4. Access: http://localhost:8000/docs (instant)
```

**Command**:
```bash
cd ~/StageFL-main
sudo bash deploy-host-mosquitto.sh
bash test-deployment.sh
```

### Scenario 2: Troubleshooting Existing Deployment

**Time**: 10-15 minutes

```
1. Check: docker compose ps
        ↓
2. Run: test-deployment.sh (identify issue)
        ↓
3. Read: DEPLOYMENT_HOST_MOSQUITTO.md → Troubleshooting
        ↓
4. Fix: Apply suggested solution
        ↓
5. Verify: test-deployment.sh (confirm fix)
```

### Scenario 3: Understanding Architecture

**Time**: 30-45 minutes

```
1. Read: PROD_DEPLOYMENT_SUMMARY.md (key discoveries)
        ↓
2. Read: DEPLOYMENT_HOST_MOSQUITTO.md (architecture section)
        ↓
3. Study: docker-compose.yml (configuration details)
        ↓
4. Review: deploy-host-mosquitto.sh (deployment steps)
```

### Scenario 4: Production Monitoring Setup

**Time**: 20-30 minutes

```
1. Read: DEPLOYMENT_HOST_MOSQUITTO.md → Monitoring
        ↓
2. Setup: Docker stats monitoring
        ↓
3. Setup: Log aggregation
        ↓
4. Setup: Database backup schedule
```

---

## 📋 Documentation Index by Topic

### Architecture & Design
- [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#architecture) - Network diagram
- [PROD_DEPLOYMENT_SUMMARY.md](PROD_DEPLOYMENT_SUMMARY.md#key-technical-discoveries) - Key discoveries

### Prerequisites & Setup
- [QUICK_START.md](QUICK_START.md#-prerequisites-checklist) - Quick checklist
- [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#pre-deployment-checklist) - Detailed checklist

### Configuration Details
- [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#configuration-details) - Full config guide
- [QUICK_START.md](QUICK_START.md#-what-changed-in-docker-composeyml) - What changed

### Deployment Steps
- [QUICK_START.md](QUICK_START.md#-tl-dr---commands-to-run) - TL;DR version
- [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#step-by-step-deployment) - Detailed steps

### Testing & Validation
- [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#connectivity-testing) - Socket/MQTT/DB tests
- [QUICK_START.md](QUICK_START.md#-testing-guide) - Quick test commands

### Troubleshooting
- [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#troubleshooting) - 5 common issues
- [QUICK_START.md](QUICK_START.md#-troubleshooting) - 4 common issues

### Monitoring
- [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#monitoring) - Detailed monitoring guide
- [QUICK_START.md](QUICK_START.md#-support--logs) - Quick monitoring commands

### Rollback & Recovery
- [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#rollback-procedure) - Step-by-step rollback

---

## 🔑 Key Concepts

### MQTT_BROKER_HOST Variable
- **Purpose**: Specify mosquitto broker address for Client_Server service
- **Value**: `host.docker.internal` (resolves to 172.17.0.1)
- **Unique**: Other services use `MQTT_HOST` instead
- **Reference**: [Serveur_Client/server_main_program.py](Serveur_Client/server_main_program.py#L51)

### extra_hosts: host.docker.internal:host-gateway
- **Purpose**: Map container requests to host IP
- **Location**: All MQTT-consuming services in docker-compose
- **Linux Only**: Works with `host-gateway` syntax on Linux
- **Effect**: Containers can reach host mosquitto on 127.0.0.1:1883

### Host Mosquitto Integration
- **Broker**: Runs on Linux host (not Docker)
- **Port**: 1883
- **Access**: From containers via `host.docker.internal:1883`
- **Advantage**: Reuse existing broker, reduce complexity

---

## ✅ Deployment Checklist

### Before Deployment
- [ ] Read QUICK_START.md
- [ ] Verify Mosquitto running: `sudo systemctl status mosquitto`
- [ ] Check ports free: `sudo ss -tulpn | grep -E ":(80|8000|5433)"`
- [ ] Docker/docker compose installed: `docker --version`
- [ ] Project files present: `ls docker-compose.yml Database/init.sql`

### During Deployment
- [ ] Run: `sudo bash deploy-host-mosquitto.sh`
- [ ] Wait for services to start (3-4 minutes)
- [ ] Monitor: `docker compose logs -f`
- [ ] Run: `bash test-deployment.sh`

### After Deployment
- [ ] All services running: `docker compose ps`
- [ ] All ports listening: `sudo ss -tulpn | grep -E ":(80|8000|5433|1883)"`
- [ ] PostgreSQL healthy: `docker compose ps | grep PostgreSQL`
- [ ] API accessible: `curl http://localhost:8000/docs`
- [ ] MQTT working: `mosquitto_pub -h localhost -p 1883 -t test -m test`
- [ ] Data ingesting: `docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) FROM measurements;"`

---

## 🚨 Common Issues Quick Reference

| Problem | Solution | Reference |
|---------|----------|-----------|
| Container can't reach host mosquitto | Rebuild with correct extra_hosts | [Link](DEPLOYMENT_HOST_MOSQUITTO.md#issue-1-container-cannot-connect-to-hostdockerinternal) |
| Mosquitto connection refused | Start mosquitto: `sudo systemctl start mosquitto` | [Link](DEPLOYMENT_HOST_MOSQUITTO.md#issue-2-services-failing-to-connect-to-mosquitto) |
| Client_Server using wrong broker IP | Verify MQTT_BROKER_HOST set in docker-compose | [Link](DEPLOYMENT_HOST_MOSQUITTO.md#issue-3-client_server-using-wrong-environment-variable) |
| PostgreSQL not healthy | Wait 60 seconds, then check | [Link](DEPLOYMENT_HOST_MOSQUITTO.md#issue-4-postgresql-not-healthy) |
| Web UI not accessible | Check port 80: `docker compose ps vue_frontend` | [Link](DEPLOYMENT_HOST_MOSQUITTO.md#issue-5-web-ui-not-accessible) |

---

## 📞 Support Resources

### Need Help?

1. **Quick Answer**: Check [QUICK_START.md](QUICK_START.md#-troubleshooting)
2. **Detailed Help**: See [DEPLOYMENT_HOST_MOSQUITTO.md](DEPLOYMENT_HOST_MOSQUITTO.md#troubleshooting)
3. **Test Suite**: Run [test-deployment.sh](test-deployment.sh)
4. **Logs**: Check `docker compose logs -f <service>`

### Verify Deployment Status

```bash
# Quick status check
docker compose ps
docker compose logs --tail=50

# Detailed validation
bash test-deployment.sh

# Full diagnostics
docker compose logs | grep -i "error\|warning"
```

---

## 📊 File Quick Reference

| File | Type | Size | Purpose |
|------|------|------|---------|
| QUICK_START.md | Markdown | 400 lines | Quick reference & common commands |
| PROD_DEPLOYMENT_SUMMARY.md | Markdown | 600 lines | Overview & key discoveries |
| DEPLOYMENT_HOST_MOSQUITTO.md | Markdown | 650 lines | Complete guide & troubleshooting |
| deploy-host-mosquitto.sh | Bash | 544 lines | Automated deployment |
| test-deployment.sh | Bash | 492 lines | Validation test suite |
| docker-compose.yml | YAML | 200+ lines | Production configuration |

---

## 🎓 Learning Path

### For Beginners
1. QUICK_START.md (understand basics)
2. Run deploy-host-mosquitto.sh (hands-on experience)
3. Run test-deployment.sh (verify success)
4. DEPLOYMENT_HOST_MOSQUITTO.md (deepen understanding)

### For Advanced Users
1. PROD_DEPLOYMENT_SUMMARY.md (key discoveries)
2. docker-compose.yml (review configuration)
3. deploy-host-mosquitto.sh (understand automation)
4. DEPLOYMENT_HOST_MOSQUITTO.md → Troubleshooting (edge cases)

### For DevOps/SRE
1. DEPLOYMENT_HOST_MOSQUITTO.md → Monitoring
2. Set up log aggregation
3. Configure alerting
4. Schedule backups
5. Load testing

---

## 🔄 Workflow Examples

### Example 1: Deploy to Production Server
```bash
# 1. SSH to server
ssh user@server

# 2. Navigate to project
cd ~/StageFL-main

# 3. Run automated deployment
sudo bash deploy-host-mosquitto.sh

# 4. Verify
bash test-deployment.sh

# 5. Done! Services are running
```

### Example 2: Debug Connection Issue
```bash
# 1. Check service status
docker compose ps

# 2. Run tests to identify issue
bash test-deployment.sh

# 3. Check logs for error
docker logs Sensor_Ingestor | grep -i "mqtt\|error"

# 4. Review relevant troubleshooting section
# → See DEPLOYMENT_HOST_MOSQUITTO.md

# 5. Fix and rebuild if needed
docker compose down -v
docker compose up -d --build
```

### Example 3: Monitor System
```bash
# 1. Real-time logs
docker compose logs -f

# 2. Service metrics
docker stats

# 3. Database queries
docker exec PostgreSQL psql -U program -d FL \
    -c "SELECT device_id, COUNT(*) FROM measurements GROUP BY device_id;"

# 4. MQTT monitoring
mosquitto_sub -h localhost -p 1883 -t '#' -v
```

---

## ✨ Success Indicators

When deployment is complete, you should see:

✅ All services running and healthy
```bash
docker compose ps
# All containers: "Up (healthy)" or "Up"
```

✅ All ports responding
```bash
sudo ss -tulpn | grep -E ":(80|8000|5433|1883)"
# All ports showing LISTEN state
```

✅ Connectivity working
```bash
bash test-deployment.sh
# Success Rate: 100%
# ✓ DEPLOYMENT VALIDATED - Ready for production
```

✅ API accessible
```bash
curl http://localhost:8000/docs
# Returns Swagger UI HTML
```

✅ Data flowing
```bash
# After publishing a message:
mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[device][0][Data][sensor:temp|value:20|msg_id:1]"
# Message appears in PostgreSQL
```

---

## 📅 Maintenance Schedule

- **Daily**: Check `docker compose ps` and logs
- **Weekly**: Run `test-deployment.sh` for validation
- **Monthly**: Full backup of PostgreSQL data
- **Quarterly**: Review and update documentation
- **As-needed**: Apply patches and updates

---

**Last Updated**: 2024
**Version**: 1.0 - Production Ready
**Status**: ✅ Complete & Tested
