#!/bin/bash

###############################################################################
#                    VALIDATION CHECKLIST - Post-Deployment
#                    
# Usage: sudo bash validate-deployment.sh
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED=0
PASSED=0

check() {
    local name=$1
    local cmd=$2
    local expected=$3
    
    echo -n "  Checking: $name... "
    
    if eval "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAILED++))
        if [ ! -z "$expected" ]; then
            echo "    Expected: $expected"
        fi
    fi
}

section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

header() {
    clear
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║   StageFL Production Deployment - Validation Checklist         ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
}

# Main checks

header

section "1. PORTS & NETWORK"

check "Port 80 is free/listening" "sudo ss -tulpn | grep -q ':80 '"
check "Port 8000 is free/listening" "sudo ss -tulpn | grep -q ':8000 '"
check "Port 5433 is free/listening" "sudo ss -tulpn | grep -q ':5433 '"
check "Mosquitto on 1883 (host)" "sudo ss -tulpn | grep ':1883' | grep -q mosquitto"

section "2. DOCKER SERVICES"

check "PostgreSQL is running" "sudo docker compose ps | grep -q 'PostgreSQL.*Up'"
check "PostgreSQL is healthy" "sudo docker compose ps | grep -q 'PostgreSQL.*healthy'"
check "Sensor_Ingestor is running" "sudo docker compose ps | grep -q 'Sensor_Ingestor.*Up'"
check "Automation_Service is running" "sudo docker compose ps | grep -q 'Automation_Service.*Up'"
check "Server_API is running" "sudo docker compose ps | grep -q 'Server_API.*Up'"
check "vue_app is running" "sudo docker compose ps | grep -q 'vue_app.*Up'"
check "Client_Server is running" "sudo docker compose ps | grep -q 'Client_Server.*Up'"

section "3. NETWORK CONNECTIVITY"

check "MQTT broker is reachable" "timeout 2 mosquitto_pub -h localhost -p 1883 -t test -m 'test' 2>/dev/null"
check "host.docker.internal resolves (Sensor_Ingestor)" "sudo docker exec Sensor_Ingestor ping -c 1 host.docker.internal &>/dev/null"
check "host.docker.internal resolves (Automation)" "sudo docker exec Automation_Service ping -c 1 host.docker.internal &>/dev/null"

section "4. API ENDPOINTS"

check "FastAPI is responding (/docs)" "curl -s -f http://localhost:8000/docs > /dev/null"
check "API devices endpoint" "curl -s -f http://localhost:8000/v1/devices > /dev/null"
check "Web UI is accessible" "curl -s -I http://localhost/ | grep -q '200\\|301\\|302'"

section "5. DATABASE CONNECTIVITY"

check "PostgreSQL database FL exists" "sudo docker exec PostgreSQL psql -U program -d FL -c 'SELECT 1' &>/dev/null"
check "Measurements table exists" "sudo docker exec PostgreSQL psql -U program -d FL -c 'SELECT 1 FROM measurements LIMIT 1' &>/dev/null"
check "Devices table exists" "sudo docker exec PostgreSQL psql -U program -d FL -c 'SELECT 1 FROM devices LIMIT 1' &>/dev/null"

section "6. DOCKER-COMPOSE CONFIGURATION"

check "mosquitto service is removed" "! grep -q '^  mosquitto:' docker-compose.yml"
check "host.docker.internal is configured" "grep -q 'host.docker.internal' docker-compose.yml"
check "extra_hosts is present" "grep -q 'extra_hosts:' docker-compose.yml"
check "MQTT_HOST references host.docker.internal" "grep -q 'MQTT_HOST: host.docker.internal' docker-compose.yml"

section "7. ENVIRONMENT VARIABLES (Containers)"

ENV_MQTT_HOST=$(sudo docker exec Sensor_Ingestor printenv MQTT_HOST 2>/dev/null)
ENV_MQTT_PORT=$(sudo docker exec Sensor_Ingestor printenv MQTT_PORT 2>/dev/null)

if [ "$ENV_MQTT_HOST" = "host.docker.internal" ]; then
    echo -e "  Sensor_Ingestor MQTT_HOST: ${GREEN}✓$NC ($ENV_MQTT_HOST)"
    ((PASSED++))
else
    echo -e "  Sensor_Ingestor MQTT_HOST: ${RED}✗$NC (got: $ENV_MQTT_HOST, expected: host.docker.internal)"
    ((FAILED++))
fi

if [ "$ENV_MQTT_PORT" = "1883" ]; then
    echo -e "  Sensor_Ingestor MQTT_PORT: ${GREEN}✓$NC ($ENV_MQTT_PORT)"
    ((PASSED++))
else
    echo -e "  Sensor_Ingestor MQTT_PORT: ${RED}✗$NC (got: $ENV_MQTT_PORT, expected: 1883)"
    ((FAILED++))
fi

section "8. DATA INGESTION TEST"

echo -n "  Publishing test message... "
mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[validation_test][0][Sending Data][sensor:temperature|value:20.5|msg_id:test-$(date +%s)]" \
    2>/dev/null && echo -e "${GREEN}✓$NC" || echo -e "${RED}✗$NC"

sleep 2

echo -n "  Checking database for ingested message... "
MSG_COUNT=$(sudo docker exec PostgreSQL psql -U program -d FL -c \
    "SELECT COUNT(*) FROM measurements WHERE device_id='validation_test';" 2>/dev/null | tail -1 | tr -d ' ')

if [ "$MSG_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✓$NC ($MSG_COUNT messages)"
    ((PASSED++))
else
    echo -e "${RED}✗$NC (0 messages - check logs)"
    ((FAILED++))
fi

section "9. SERVICE LOGS (Last 5 lines per service)"

for service in sensor_ingestor automation server_api; do
    echo ""
    echo -e "  ${BLUE}$service:${NC}"
    sudo docker compose logs --tail 3 $service 2>/dev/null | sed 's/^/    /'
done

section "SUMMARY"

TOTAL=$((PASSED + FAILED))
PERCENTAGE=$((PASSED * 100 / TOTAL))

echo ""
echo "  Tests Passed:  ${GREEN}$PASSED/$TOTAL${NC}"
echo "  Tests Failed:  ${RED}$FAILED/$TOTAL${NC}"
echo "  Success Rate:  $PERCENTAGE%"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ ALL CHECKS PASSED - DEPLOYMENT IS SUCCESSFUL!               ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Web Access:"
    echo "  • http://$(hostname -I | awk '{print $1}')        (Web UI)"
    echo "  • http://$(hostname -I | awk '{print $1}'):8000/docs  (API Docs)"
    echo ""
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ✗ SOME CHECKS FAILED - SEE ABOVE FOR DETAILS                 ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "  1. Check service logs:     sudo docker compose logs -f <service>"
    echo "  2. Restart a service:      sudo docker compose restart <service>"
    echo "  3. Check MQTT connection:  mosquitto_sub -h localhost -p 1883 -t '$SYS/#'"
    echo "  4. Check database:         sudo docker exec -it PostgreSQL psql -U program -d FL"
    echo ""
    exit 1
fi
