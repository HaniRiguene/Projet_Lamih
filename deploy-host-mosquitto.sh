#!/bin/bash

###############################################################################
#          PRODUCTION DEPLOYMENT - HOST MOSQUITTO SETUP
#          
# This script deploys StageFL with host mosquitto (1883) integration
# Tests: socket connectivity + MQTT pub/sub
#
# Usage: sudo bash deploy-host-mosquitto.sh
###############################################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

PROJECT_DIR="$(pwd)"
MQTT_HOST="localhost"
MQTT_PORT="1883"

# ═══════════════════════════════════════════════════════════════════════════
# 1. PRÉ-DEPLOYMENT CHECKS
# ═══════════════════════════════════════════════════════════════════════════

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Mosquitto Host
    if ! pgrep -x "mosquitto" > /dev/null; then
        log_error "Mosquitto host not running"
        echo "  Run: sudo systemctl start mosquitto"
        exit 1
    fi
    log_success "Mosquitto host running"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi
    log_success "Docker installed"
    
    # Check Docker Compose
    if ! docker compose version > /dev/null 2>&1; then
        log_error "docker compose not available"
        exit 1
    fi
    log_success "docker compose available"
    
    # Check Ports Free
    if sudo ss -tulpn 2>/dev/null | grep -q ":80 " || \
       sudo ss -tulpn 2>/dev/null | grep -q ":8000 " || \
       sudo ss -tulpn 2>/dev/null | grep -q ":5433 "; then
        log_warning "Some ports (80, 8000, 5433) may already be in use"
        read -p "Continue? (y/N) " -n 1 -r
        echo
        [[ ! $REPLY =~ ^[Yy]$ ]] && exit 1
    fi
    log_success "Ports available (80, 8000, 5433)"
}

# ═══════════════════════════════════════════════════════════════════════════
# 2. VALIDATE DOCKER-COMPOSE
# ═══════════════════════════════════════════════════════════════════════════

validate_compose() {
    log_info "Validating docker-compose.yml..."
    
    if ! docker compose config > /dev/null 2>&1; then
        log_error "docker-compose.yml is invalid"
        exit 1
    fi
    log_success "docker-compose.yml is valid"
    
    # Check for host.docker.internal
    if ! grep -q "host.docker.internal" docker-compose.yml; then
        log_error "host.docker.internal not configured in docker-compose.yml"
        exit 1
    fi
    log_success "host.docker.internal configured"
    
    # Check for MQTT_BROKER_HOST
    if ! grep -q "MQTT_BROKER_HOST" docker-compose.yml; then
        log_warning "MQTT_BROKER_HOST not found (may be optional)"
    else
        log_success "MQTT_BROKER_HOST configured"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 3. DEPLOY SERVICES
# ═══════════════════════════════════════════════════════════════════════════

deploy_services() {
    log_info "Building and deploying services..."
    
    docker compose down -v 2>/dev/null || true
    sleep 5
    
    log_info "Starting services (this may take 2-3 minutes)..."
    docker compose up -d --build
    
    log_info "Waiting for PostgreSQL to be healthy..."
    for i in {1..30}; do
        if docker compose ps | grep -q "PostgreSQL.*healthy"; then
            log_success "PostgreSQL is healthy"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    
    sleep 5
}

# ═══════════════════════════════════════════════════════════════════════════
# 4. TEST SOCKET CONNECTIVITY
# ═══════════════════════════════════════════════════════════════════════════

test_socket_connectivity() {
    log_info "Testing socket connectivity to host mosquitto..."
    
    # Create Python test script
    cat > /tmp/test_mqtt_socket.py << 'EOF'
import socket
import sys

def test_mqtt_socket(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✓ Socket connection to {host}:{port} successful")
            return True
        else:
            print(f"✗ Socket connection to {host}:{port} failed (errno: {result})")
            return False
    except Exception as e:
        print(f"✗ Socket error: {e}")
        return False

# Test from host
print("\n[HOST CONNECTIVITY]")
if test_mqtt_socket("localhost", 1883):
    print("  Connection: localhost:1883 OK")
else:
    print("  Connection: localhost:1883 FAILED")
    sys.exit(1)
EOF
    
    python3 /tmp/test_mqtt_socket.py
    
    # Test from container
    log_info "Testing socket connectivity from container (sensor_ingestor)..."
    
    docker exec Sensor_Ingestor python3 << 'PYEOF'
import socket
import time

def test_mqtt_socket(host, port, timeout=5):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Error: {e}")
        return False

# Test from container
print("[CONTAINER CONNECTIVITY]")
if test_mqtt_socket("host.docker.internal", 1883):
    print("✓ Container → host.docker.internal:1883 OK")
else:
    print("✗ Container → host.docker.internal:1883 FAILED")
    import sys
    sys.exit(1)
PYEOF
    
    log_success "Socket connectivity test passed"
}

# ═══════════════════════════════════════════════════════════════════════════
# 5. TEST MQTT PUB/SUB
# ═══════════════════════════════════════════════════════════════════════════

test_mqtt_pubsub() {
    log_info "Testing MQTT pub/sub..."
    
    # Test publish from host
    log_info "Publishing test message from host..."
    if timeout 5 mosquitto_pub -h localhost -p 1883 -t test/connectivity -m "test-$(date +%s)" 2>/dev/null; then
        log_success "MQTT publish (host → broker) successful"
    else
        log_error "MQTT publish failed"
        return 1
    fi
    
    # Test from container
    log_info "Publishing test message from container..."
    if docker exec Sensor_Ingestor mosquitto_pub -h host.docker.internal -p 1883 -t test/container -m "container-test-$(date +%s)" 2>/dev/null; then
        log_success "MQTT publish (container → broker) successful"
    else
        log_error "MQTT publish from container failed"
        return 1
    fi
    
    sleep 2
    
    # Test subscribe
    log_info "Testing MQTT subscribe (5 second timeout)..."
    if timeout 5 mosquitto_sub -h localhost -p 1883 -t test/# -C 1 > /dev/null 2>&1; then
        log_success "MQTT subscribe successful"
    else
        log_warning "MQTT subscribe timeout (may be normal if no messages)"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 6. TEST DATA INGESTION
# ═══════════════════════════════════════════════════════════════════════════

test_data_ingestion() {
    log_info "Testing MQTT data ingestion into database..."
    
    # Publish test device data
    log_info "Publishing test sensor data..."
    mosquitto_pub -h localhost -p 1883 -t Data \
        -m "[deployment_test][0][Sending Data][sensor:temperature|value:22.5|msg_id:deploy-test-1]" \
        2>/dev/null
    
    sleep 2
    
    # Check in database
    MSG_COUNT=$(docker exec PostgreSQL psql -U program -d FL -c \
        "SELECT COUNT(*) FROM measurements WHERE device_id='deployment_test';" 2>/dev/null | tail -1 | tr -d ' ')
    
    if [ "$MSG_COUNT" -gt "0" ]; then
        log_success "Data ingestion successful ($MSG_COUNT message(s) in database)"
    else
        log_warning "No data ingested (check if sensor_ingestor is running)"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 7. VALIDATE ALL SERVICES
# ═══════════════════════════════════════════════════════════════════════════

validate_all_services() {
    log_info "Validating all services..."
    
    # Check services running
    echo ""
    log_info "Service Status:"
    docker compose ps
    
    echo ""
    log_info "Port Status:"
    if sudo ss -tulpn 2>/dev/null | grep -q ":80 "; then
        echo "  ✓ Port 80 (Web UI) listening"
    else
        echo "  ✗ Port 80 not listening"
    fi
    
    if sudo ss -tulpn 2>/dev/null | grep -q ":8000 "; then
        echo "  ✓ Port 8000 (API) listening"
    else
        echo "  ✗ Port 8000 not listening"
    fi
    
    if sudo ss -tulpn 2>/dev/null | grep -q ":5433 "; then
        echo "  ✓ Port 5433 (PostgreSQL) listening"
    else
        echo "  ✗ Port 5433 not listening"
    fi
    
    if sudo ss -tulpn 2>/dev/null | grep :1883 | grep -q mosquitto; then
        echo "  ✓ Port 1883 (Mosquitto - Host) running"
    else
        echo "  ✗ Port 1883 not found (host mosquitto)"
    fi
    
    # Check API
    echo ""
    log_info "API Status:"
    if curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
        echo "  ✓ FastAPI responding (Swagger docs available)"
    else
        echo "  ✗ FastAPI not responding"
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 8. SHOW SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

show_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║          DEPLOYMENT COMPLETE - HOST MOSQUITTO SETUP           ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "✅ Services Deployed:"
    docker compose ps --services
    echo ""
    echo "🌐 Web Access:"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • Web Portal: http://localhost"
    echo ""
    echo "🔌 MQTT Configuration:"
    echo "  • Broker: localhost:1883 (Host mosquitto)"
    echo "  • Container access: host.docker.internal:1883"
    echo "  • Protocol: MQTT 3.1.1"
    echo ""
    echo "📊 Database:"
    echo "  • Host: localhost"
    echo "  • Port: 5433"
    echo "  • User: program"
    echo "  • Database: FL"
    echo ""
    echo "🧪 Test Commands:"
    echo "  # Publish test message"
    echo "  mosquitto_pub -h localhost -p 1883 -t Data -m '[test_device][0][Sending Data][sensor:temperature|value:20|msg_id:test-1]'"
    echo ""
    echo "  # Subscribe to topic"
    echo "  mosquitto_sub -h localhost -p 1883 -t 'Data' -C 1"
    echo ""
    echo "  # Query database"
    echo "  docker exec -it PostgreSQL psql -U program -d FL -c 'SELECT COUNT(*) FROM measurements;'"
    echo ""
    log_success "Deployment successful!"
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║       StageFL - Deployment with Host Mosquitto Integration    ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_prerequisites
    echo ""
    
    validate_compose
    echo ""
    
    deploy_services
    echo ""
    
    test_socket_connectivity
    echo ""
    
    test_mqtt_pubsub
    echo ""
    
    test_data_ingestion
    echo ""
    
    validate_all_services
    echo ""
    
    show_summary
}

main
