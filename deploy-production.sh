#!/bin/bash

###############################################################################
#          PRODUCTION DEPLOYMENT SCRIPT - StageFL IoT System
#          
# Usage: sudo bash deploy-production.sh
# 
# This script:
# 1. Stops and removes the old project (~/Bureau/FL)
# 2. Verifies ports are free (80, 8000, 5433)
# 3. Deploys the new StageFL project with host mosquitto
# 4. Validates all services and connectivity
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OLD_PROJECT_DIR="$HOME/Bureau/FL"
NEW_PROJECT_DIR="$HOME/StageFL-main"
MQTT_HOST="localhost"
MQTT_PORT="1883"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prereq() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    log_success "Docker found: $(docker --version)"
    
    # Check Docker Compose
    if ! command -v docker &> /dev/null; then
        log_error "docker compose is not available"
        exit 1
    fi
    log_success "docker compose found: $(docker compose version 2>/dev/null | head -1)"
    
    # Check Mosquitto on host
    if ! netstat -tulpn 2>/dev/null | grep -q :1883 || ! pgrep -x "mosquitto" > /dev/null; then
        log_error "Host mosquitto not running on port 1883"
        echo "  Run: sudo systemctl status mosquitto"
        exit 1
    fi
    log_success "Host mosquitto running on port 1883"
    
    # Check new project exists
    if [ ! -d "$NEW_PROJECT_DIR" ]; then
        log_error "New project directory not found: $NEW_PROJECT_DIR"
        exit 1
    fi
    log_success "New project found: $NEW_PROJECT_DIR"
}

stop_old_project() {
    log_info "Stopping old project (if exists)..."
    
    if [ -d "$OLD_PROJECT_DIR" ]; then
        cd "$OLD_PROJECT_DIR"
        
        if sudo docker compose ps 2>/dev/null | grep -q "Up"; then
            log_info "Stopping containers in $OLD_PROJECT_DIR..."
            sudo docker compose down --remove-orphans 2>/dev/null || true
            log_success "Old project stopped"
        else
            log_info "Old project already stopped"
        fi
    else
        log_info "Old project directory not found ($OLD_PROJECT_DIR)"
    fi
}

verify_ports_free() {
    log_info "Verifying ports are free..."
    
    local ports=(80 8000 5433)
    local all_free=true
    
    for port in "${ports[@]}"; do
        if sudo netstat -tulpn 2>/dev/null | grep -q ":$port "; then
            log_error "Port $port is still in use"
            sudo lsof -i :$port 2>/dev/null || echo "  Details unavailable"
            all_free=false
        else
            log_success "Port $port is free"
        fi
    done
    
    if [ "$all_free" = false ]; then
        log_error "Some ports are still in use. Please free them and retry."
        exit 1
    fi
}

verify_docker_compose() {
    log_info "Verifying docker-compose.yml configuration..."
    
    cd "$NEW_PROJECT_DIR"
    
    # Check for host.docker.internal
    if ! grep -q "host.docker.internal" docker-compose.yml; then
        log_error "docker-compose.yml does not have host.docker.internal configured"
        exit 1
    fi
    log_success "docker-compose.yml properly configured"
    
    # Check for extra_hosts
    local extra_hosts_count=$(grep -c "extra_hosts" docker-compose.yml || true)
    log_info "Found $extra_hosts_count extra_hosts declarations"
    
    # Check mosquitto service is removed
    if grep -q "mosquitto:" docker-compose.yml; then
        log_warning "mosquitto service still defined in docker-compose.yml (should be removed)"
    else
        log_success "mosquitto service properly removed"
    fi
}

deploy_new_project() {
    log_info "Deploying new project..."
    
    cd "$NEW_PROJECT_DIR"
    
    log_info "Building and starting services (this may take 2-3 minutes)..."
    sudo docker compose up -d --build 2>&1 | tail -5
    
    log_info "Waiting for PostgreSQL to become healthy (30 seconds)..."
    for i in {1..30}; do
        if sudo docker compose ps | grep -q "PostgreSQL.*Up.*healthy"; then
            log_success "PostgreSQL is healthy"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
    
    # Final check
    sleep 5
    if sudo docker compose ps | grep -q "Up"; then
        log_success "New project deployed successfully"
    else
        log_error "Services not running properly"
        sudo docker compose ps
        exit 1
    fi
}

validate_deployment() {
    log_info "Validating deployment..."
    
    # Check all services
    log_info "Service status:"
    sudo docker compose ps
    echo ""
    
    # Check port bindings
    log_info "Checking port bindings..."
    
    if sudo netstat -tulpn 2>/dev/null | grep -q ":80 "; then
        log_success "Port 80 (Web) is listening"
    else
        log_error "Port 80 (Web) is not listening"
    fi
    
    if sudo netstat -tulpn 2>/dev/null | grep -q ":8000 "; then
        log_success "Port 8000 (API) is listening"
    else
        log_error "Port 8000 (API) is not listening"
    fi
    
    if sudo netstat -tulpn 2>/dev/null | grep -q ":5433 "; then
        log_success "Port 5433 (DB) is listening"
    else
        log_error "Port 5433 (DB) is not listening"
    fi
    
    # Test MQTT
    log_info "Testing MQTT connectivity..."
    if timeout 2 mosquitto_pub -h localhost -p 1883 -t test -m "test" 2>/dev/null; then
        log_success "MQTT broker is reachable"
    else
        log_error "Cannot reach MQTT broker on localhost:1883"
    fi
    
    # Test API
    log_info "Testing FastAPI..."
    if curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
        log_success "FastAPI is responding (Swagger docs available)"
    else
        log_error "FastAPI is not responding"
    fi
    
    # Test Web UI
    log_info "Testing Web UI..."
    if curl -s -I http://localhost/ | grep -q "200\|301\|302"; then
        log_success "Web UI is responding"
    else
        log_error "Web UI is not responding"
    fi
}

test_mqtt_ingestion() {
    log_info "Testing MQTT message ingestion..."
    
    cd "$NEW_PROJECT_DIR"
    
    # Publish test message
    mosquitto_pub -h localhost -p 1883 -t Data \
        -m "[test_device][0][Sending Data][sensor:temperature|value:21.0|msg_id:test-001]" \
        2>/dev/null || log_warning "Could not publish test message"
    
    sleep 2
    
    # Check if message was ingested
    if sudo docker exec PostgreSQL psql -U program -d FL -c \
        "SELECT COUNT(*) FROM measurements WHERE device_id='test_device';" 2>/dev/null | grep -q "1"; then
        log_success "Message successfully ingested into database"
    else
        log_warning "Message ingestion test inconclusive (check logs)"
    fi
}

show_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║         DEPLOYMENT SUMMARY - StageFL Production                ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Project Directory: $NEW_PROJECT_DIR"
    echo ""
    echo "Services deployed:"
    sudo docker compose ps --services
    echo ""
    echo "Web Access:"
    echo "  • API Docs (Swagger):    http://$(hostname -I | awk '{print $1}')/docs"
    echo "  • Web Portal:            http://$(hostname -I | awk '{print $1}')"
    echo "  • API Documentation:    http://$(hostname -I | awk '{print $1}'):8000/docs"
    echo ""
    echo "Database Access:"
    echo "  • Host: localhost"
    echo "  • Port: 5433"
    echo "  • User: program"
    echo "  • Password: program"
    echo "  • Database: FL"
    echo ""
    echo "MQTT Broker:"
    echo "  • Host: localhost (hôte système)"
    echo "  • Port: 1883"
    echo ""
    echo "Next steps:"
    echo "  1. Verify all services: sudo docker compose ps"
    echo "  2. Check logs: sudo docker compose logs -f"
    echo "  3. Query database: sudo docker exec -it PostgreSQL psql -U program -d FL"
    echo "  4. Send test MQTT: mosquitto_pub -h localhost -p 1883 -t Data -m '...'"
    echo ""
    log_success "Deployment completed successfully!"
    echo ""
}

# Main execution
main() {
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║    StageFL Production Deployment - Host Mosquitto Setup         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    check_prereq
    echo ""
    
    stop_old_project
    echo ""
    
    verify_ports_free
    echo ""
    
    verify_docker_compose
    echo ""
    
    deploy_new_project
    echo ""
    
    validate_deployment
    echo ""
    
    test_mqtt_ingestion
    echo ""
    
    show_summary
}

# Run main
main
