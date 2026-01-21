#!/bin/bash

###############################################################################
#          TEST CONNECTIVITY & DATA INGESTION
#          
# Validates deployment before full launch
# Tests: socket connectivity, MQTT pub/sub, data ingestion
#
# Usage: bash test-deployment.sh
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_pass() { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)); }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; ((FAIL++)); }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARN++)); }

# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: DOCKER SERVICES
# ═══════════════════════════════════════════════════════════════════════════

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              DEPLOYMENT VALIDATION TESTS                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

test_docker_services() {
    log_info "Testing Docker services..."
    echo ""
    
    # Check if docker-compose is up
    if ! docker compose ps > /dev/null 2>&1; then
        log_fail "docker compose is not running"
        return 1
    fi
    
    # Check PostgreSQL
    if docker compose ps | grep -q "PostgreSQL"; then
        if docker compose ps PostgreSQL 2>/dev/null | grep -q "Up"; then
            log_pass "PostgreSQL container running"
        else
            log_fail "PostgreSQL container not running"
        fi
    else
        log_fail "PostgreSQL container not found"
    fi
    
    # Check Sensor_Ingestor
    if docker compose ps | grep -q "Sensor_Ingestor"; then
        if docker compose ps Sensor_Ingestor 2>/dev/null | grep -q "Up"; then
            log_pass "Sensor_Ingestor container running"
        else
            log_fail "Sensor_Ingestor container not running"
        fi
    else
        log_fail "Sensor_Ingestor container not found"
    fi
    
    # Check Automation
    if docker compose ps | grep -q "Automation"; then
        if docker compose ps Automation 2>/dev/null | grep -q "Up"; then
            log_pass "Automation container running"
        else
            log_fail "Automation container not running"
        fi
    else
        log_fail "Automation container not found"
    fi
    
    # Check Server_API
    if docker compose ps | grep -q "Server_API"; then
        if docker compose ps Server_API 2>/dev/null | grep -q "Up"; then
            log_pass "Server_API container running"
        else
            log_fail "Server_API container not running"
        fi
    else
        log_fail "Server_API container not found"
    fi
    
    # Check Client_Server
    if docker compose ps | grep -q "Client_Server"; then
        if docker compose ps Client_Server 2>/dev/null | grep -q "Up"; then
            log_pass "Client_Server container running"
        else
            log_fail "Client_Server container not running"
        fi
    else
        log_fail "Client_Server container not found"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: PORTS
# ═══════════════════════════════════════════════════════════════════════════

test_ports() {
    log_info "Testing port accessibility..."
    echo ""
    
    # Port 80 (Web)
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/80" 2>/dev/null; then
        log_pass "Port 80 (Web) listening"
    else
        log_fail "Port 80 (Web) not listening"
    fi
    
    # Port 8000 (API)
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/8000" 2>/dev/null; then
        log_pass "Port 8000 (API) listening"
    else
        log_fail "Port 8000 (API) not listening"
    fi
    
    # Port 5433 (PostgreSQL)
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/5433" 2>/dev/null; then
        log_pass "Port 5433 (PostgreSQL) listening"
    else
        log_fail "Port 5433 (PostgreSQL) not listening"
    fi
    
    # Port 1883 (MQTT - Host)
    if timeout 2 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/1883" 2>/dev/null; then
        log_pass "Port 1883 (MQTT Host) listening"
    else
        log_fail "Port 1883 (MQTT Host) not listening"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: SOCKET CONNECTIVITY
# ═══════════════════════════════════════════════════════════════════════════

test_socket_connectivity() {
    log_info "Testing socket connectivity..."
    echo ""
    
    # Host → Mosquitto
    if docker run --rm -q --network host python:3.10-slim python3 << 'EOF' 2>/dev/null
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("localhost", 1883))
sock.close()
exit(0 if result == 0 else 1)
EOF
    then
        log_pass "Host → localhost:1883 (socket)"
    else
        log_fail "Host → localhost:1883 (socket)"
    fi
    
    # Container → host.docker.internal
    if docker exec Sensor_Ingestor python3 << 'EOF' 2>/dev/null
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(("host.docker.internal", 1883))
sock.close()
exit(0 if result == 0 else 1)
EOF
    then
        log_pass "Container → host.docker.internal:1883 (socket)"
    else
        log_fail "Container → host.docker.internal:1883 (socket)"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: MQTT PUBLISH/SUBSCRIBE
# ═══════════════════════════════════════════════════════════════════════════

test_mqtt_pubsub() {
    log_info "Testing MQTT pub/sub..."
    echo ""
    
    # Publish from host
    if timeout 5 mosquitto_pub -h localhost -p 1883 -t "test/host" -m "test-$(date +%s)" 2>/dev/null; then
        log_pass "Publish from host"
    else
        log_fail "Publish from host"
    fi
    
    # Publish from container
    if docker exec Sensor_Ingestor timeout 5 mosquitto_pub -h host.docker.internal -p 1883 -t "test/container" -m "test-$(date +%s)" 2>/dev/null; then
        log_pass "Publish from container"
    else
        log_fail "Publish from container"
    fi
    
    # Subscribe test
    if timeout 5 mosquitto_sub -h localhost -p 1883 -t "test/#" -C 1 > /dev/null 2>&1; then
        log_pass "Subscribe test"
    else
        log_warn "Subscribe test (may timeout if no messages)"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: DATABASE CONNECTIVITY
# ═══════════════════════════════════════════════════════════════════════════

test_database() {
    log_info "Testing database connectivity..."
    echo ""
    
    # Check PostgreSQL connection
    if docker exec PostgreSQL psql -U program -d FL -c "SELECT 1;" > /dev/null 2>&1; then
        log_pass "PostgreSQL connection"
    else
        log_fail "PostgreSQL connection"
    fi
    
    # Check tables exist
    if docker exec PostgreSQL psql -U program -d FL -c "\dt" 2>/dev/null | grep -q "measurements"; then
        log_pass "Database tables exist"
    else
        log_fail "Database tables missing"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

test_api() {
    log_info "Testing API endpoints..."
    echo ""
    
    # Health check
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1 || \
       curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
        log_pass "API responding"
    else
        log_fail "API not responding"
    fi
    
    # Swagger docs
    if curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
        log_pass "Swagger documentation available"
    else
        log_fail "Swagger documentation not available"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: DATA INGESTION
# ═══════════════════════════════════════════════════════════════════════════

test_data_ingestion() {
    log_info "Testing data ingestion..."
    echo ""
    
    # Clear test device data
    docker exec PostgreSQL psql -U program -d FL -c "DELETE FROM measurements WHERE device_id='test_ingest';" 2>/dev/null || true
    
    sleep 1
    
    # Publish test data
    TIMESTAMP=$(date +%s)
    mosquitto_pub -h localhost -p 1883 -t "Data" \
        -m "[test_ingest][0][Sending Data][sensor:temperature|value:22.5|msg_id:$TIMESTAMP]" 2>/dev/null
    
    sleep 3
    
    # Check if data was persisted
    COUNT=$(docker exec PostgreSQL psql -U program -d FL -c \
        "SELECT COUNT(*) FROM measurements WHERE device_id='test_ingest';" 2>/dev/null | tail -1 | tr -d ' ')
    
    if [ "$COUNT" -gt "0" ]; then
        log_pass "Data ingestion ($COUNT message(s))"
    else
        log_fail "Data ingestion (0 messages persisted)"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# TEST 8: ENVIRONMENT VARIABLES
# ═══════════════════════════════════════════════════════════════════════════

test_environment() {
    log_info "Testing environment variables..."
    echo ""
    
    # Check MQTT_BROKER_HOST in client_server
    if docker exec Client_Server env 2>/dev/null | grep -q "MQTT_BROKER_HOST=host.docker.internal"; then
        log_pass "Client_Server MQTT_BROKER_HOST set"
    else
        log_warn "Client_Server MQTT_BROKER_HOST not properly set"
    fi
    
    # Check MQTT_HOST in sensor_ingestor
    if docker exec Sensor_Ingestor env 2>/dev/null | grep -q "MQTT_HOST=host.docker.internal"; then
        log_pass "Sensor_Ingestor MQTT_HOST set"
    else
        log_fail "Sensor_Ingestor MQTT_HOST not set"
    fi
    
    echo ""
}

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

show_summary() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                      TEST SUMMARY                             ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    TOTAL=$((PASS + FAIL + WARN))
    PERCENT=$(( (PASS * 100) / TOTAL ))
    
    echo "Results:"
    echo "  ✓ Passed:  $PASS"
    echo "  ✗ Failed:  $FAIL"
    echo "  ⚠ Warned:  $WARN"
    echo "  ─────────────"
    echo "  Total:   $TOTAL"
    echo ""
    echo "Success Rate: $PERCENT%"
    echo ""
    
    if [ $FAIL -eq 0 ]; then
        echo -e "${GREEN}✓ DEPLOYMENT VALIDATED - Ready for production${NC}"
        return 0
    else
        echo -e "${RED}✗ DEPLOYMENT HAS ISSUES - Please review failures above${NC}"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

main() {
    test_docker_services
    test_ports
    test_socket_connectivity
    test_mqtt_pubsub
    test_database
    test_api
    test_environment
    test_data_ingestion
    show_summary
}

main
exit $FAIL
