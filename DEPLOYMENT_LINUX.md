# 🚀 Déploiement Production Linux - Réutilisation Mosquitto Hôte

## 📋 Architecture

```
┌─────────────────────────────────────────────────────┐
│         LINUX SERVER (hôte physique)                │
│                                                      │
│  ┌─────────────────────────────────────┐            │
│  │  Mosquitto Hôte (port 1883)         │            │
│  │  ss -tulpn | grep :1883             │            │
│  │  users:(("mosquitto"...))           │            │
│  └─────────────────────────────────────┘            │
│           ▲                                          │
│           │ (host.docker.internal:1883)             │
│           │                                          │
│  ┌─────────────────────────────────────┐            │
│  │     Docker Network (bridge)         │            │
│  │                                     │            │
│  │  ┌──────────────┐  ┌──────────────┐ │            │
│  │  │  Sensor      │  │  Automation  │ │            │
│  │  │  Ingestor    │  │  Service     │ │            │
│  │  └──────────────┘  └──────────────┘ │            │
│  │         │                  │         │            │
│  │         └──────────────────┘         │            │
│  │                  │                   │            │
│  │         ┌────────▼────────┐         │            │
│  │         │   PostgreSQL    │         │            │
│  │         │   (5433)        │         │            │
│  │         └─────────────────┘         │            │
│  │                                     │            │
│  │  ┌──────────────┐  ┌──────────────┐ │            │
│  │  │  Server API  │  │  Vue Frontend│ │            │
│  │  │  (8000)      │  │  (80)        │ │            │
│  │  └──────────────┘  └──────────────┘ │            │
│  └─────────────────────────────────────┘            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## ✅ PRÉ-REQUIS AVANT DÉPLOIEMENT

Vérifier sur le serveur Linux:

```bash
# 1. Mosquitto hôte actif
sudo systemctl status mosquitto
mosquitto_sub -h localhost -p 1883 -t '$SYS/#' -u test | head -1

# 2. Anciens ports libérés
sudo ss -tulpn | grep -E '(:80|:8000|:5433)'
# Doit retourner: aucun résultat

# 3. Docker/Docker Compose installés
docker --version
docker compose version

# 4. Accès à la source du projet
cd ~/StageFL-main
git pull  # ou rsync depuis Windows
ls docker-compose.yml
```

---

## 🔴 ÉTAPE 1: ARRÊTER L'ANCIEN PROJET

```bash
# Naviguer au dossier de l'ancien projet
cd ~/Bureau/FL

# Vérifier les conteneurs
sudo docker-compose ps

# Arrêter et supprimer
sudo docker-compose down

# Vérifier suppression
sudo docker-compose ps  # doit être vide

# Vérifier que les ports sont libres
sudo ss -tulpn | grep -E '(:80|:8000|:5433)'
# ✓ Doit retourner: (aucun résultat)

# Vérifier la vraie liste des ports utilisés
sudo ss -tulpn | grep -E '(:1883|:8086)'
# ✓ mosquitto hôte 1883 doit être visible
# ✓ influxdb 8086 peut rester actif
```

**Temps estimé**: 2-3 minutes

---

## 🟢 ÉTAPE 2: MODIFIER DOCKER-COMPOSE (DÉJÀ FAIT)

**✅ Modifications appliquées** au fichier `docker-compose.yml`:

### Mosquitto - SUPPRIMÉ ❌
```diff
- services:
-   mosquitto:
-     image: eclipse-mosquitto:2
-     container_name: Mosquitto
-     ports:
-       - "1883:1883"
-     volumes:
-       - ./Mosquitto_Config/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
```

### Services - MODIFIÉS ✅

**Ajout à TOUS les services consommant MQTT** (sensor_ingestor, automation, server_api, client_server):

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"

environment:
  MQTT_HOST: host.docker.internal  # (au lieu de "mosquitto")
  MQTT_PORT: "1883"
```

**Suppression des dépendances** sur mosquitto:
```diff
depends_on:
- mosquitto:
-   condition: service_started
  postgresql:
    condition: service_healthy
```

### Résumé des changements:
| Service | Avant | Après |
|---------|-------|-------|
| Mosquitto | ✅ Lancé dans Docker | ❌ Désactivé (utilise hôte) |
| Sensor_Ingestor | MQTT_HOST: mosquitto | MQTT_HOST: host.docker.internal |
| Automation | MQTT_HOST: mosquitto | MQTT_HOST: host.docker.internal |
| Server_API | MQTT_HOST: mosquitto | MQTT_HOST: host.docker.internal |
| Client_Server | MQTT_HOST: mosquitto | MQTT_HOST: host.docker.internal |
| **extra_hosts** | ❌ Non présent | ✅ host.docker.internal:host-gateway |

---

## 🟡 ÉTAPE 3: DÉPLOYER LE NOUVEAU PROJET

```bash
# 1. Naviguer au nouveau projet
cd ~/StageFL-main
# OU (si depuis Windows/Git)
cd /home/user/projects/StageFL-main

# 2. Vérifier le docker-compose.yml modifié
cat docker-compose.yml | grep -A 5 "extra_hosts"
# Doit afficher extra_hosts pour chaque service

# 3. Builder et démarrer les services
sudo docker compose up -d --build

# ⏳ Attendre 20-30 secondes pour PostgreSQL (healthcheck)

# 4. Vérifier que tous les services sont UP
sudo docker compose ps
# ✓ All containers should show "Up" or "Up (healthy)"
```

**Output attendu** (après ~15-20 sec):
```
NAME                 IMAGE                          STATUS
PostgreSQL           postgres:14-alpine             Up (healthy)
Sensor_Ingestor      stagefl-main-sensor_ingestor   Up
Automation_Service   stagefl-main-automation        Up
Server_API           stagefl-main-server_api        Up
vue_app              stagefl-main-vue_frontend      Up
Client_Server        stagefl-main-client_server     Up
```

**Temps estimé**: 3-5 minutes (first build)

---

## 🔵 ÉTAPE 4: VÉRIFICATIONS POST-DÉPLOIEMENT

### 4.1 Vérifier les ports

```bash
# PostgreSQL sur 5433
sudo ss -tulpn | grep :5433
# Doit afficher: tcp  0  0 0.0.0.0:5433  0.0.0.0:*  LISTEN

# FastAPI sur 8000
sudo ss -tulpn | grep :8000
# Doit afficher: tcp  0  0 0.0.0.0:8000  0.0.0.0:*  LISTEN

# Nginx/Vue sur 80
sudo ss -tulpn | grep :80
# Doit afficher: tcp  0  0 0.0.0.0:80  0.0.0.0:*  LISTEN

# Mosquitto hôte sur 1883 (PAS dans Docker)
sudo ss -tulpn | grep :1883
# Doit afficher: tcp  0  0 0.0.0.0:1883  0.0.0.0:*  LISTEN  users:(("mosquitto"...))
```

### 4.2 Test MQTT - Publisher depuis hôte

```bash
# Publier un message test sur le broker hôte
mosquitto_pub -h localhost -p 1883 -t Data \
  -m "[salle_a_manger][0][Sending Data][sensor:temperature|value:21.5|msg_id:test-1]"

# ✓ Aucune erreur = succès
```

### 4.3 Test API - HTTP

```bash
# Health check Swagger docs (FastAPI alive?)
curl -I http://localhost:8000/docs
# ✓ HTTP 200 ou 302 = OK

# List devices (vérifier MQTT ingestion)
curl -s http://localhost:8000/v1/devices | jq .
# ✓ Doit retourner au minimum: [{"device_id": "salle_a_manger", ...}]

# Get latest measurement
curl -s http://localhost:8000/v1/devices/salle_a_manger/latest | jq .
# ✓ Doit retourner température ~21.5
```

### 4.4 Test Web UI

```bash
# Accéder à http://SERVER_IP/
curl -I http://localhost/
# ✓ HTTP 200 = OK

# Vérifier depuis navigateur
# Browser: http://SERVER_IP/
# Doit charger l'interface Vue.js
```

### 4.5 Vérifier Ingestion DB

```bash
# Vérifier que le message a été inséré
sudo docker exec -it PostgreSQL psql -U program -d FL -c \
  "SELECT device_id, COUNT(*) as cnt FROM measurements GROUP BY device_id;"

# ✓ Attendu: salle_a_manger | 1
#            (et autres devices si présents)
```

### 4.6 Logs des services

```bash
# Vérifier les logs (pas d'erreur de connexion MQTT?)
sudo docker logs Sensor_Ingestor --tail 20
sudo docker logs Automation_Service --tail 20
sudo docker logs Server_API --tail 20

# ✓ Doit afficher des messages normaux, pas d'erreurs de connexion
# ✗ À éviter: "Connection refused", "Cannot resolve host", "Failed to connect"
```

---

## 🟢 ÉTAPE 5: CHECKLIST FINALE

```bash
# Copier-coller cette checklist après déploiement

echo "=== CHECKLIST DÉPLOIEMENT PRODUCTION ==="
echo ""

echo "1. PORTS LIBÉRÉS (anciens ports libres?)"
sudo ss -tulpn | grep -E '(:1888|:8086|:5432)' && echo "  ⚠️  ATTENTION: Anciens ports encore actifs!" || echo "  ✓ OK"

echo ""
echo "2. NOUVEAUX PORTS ACTIFS"
echo -n "  Port 80 (Web)? "
sudo ss -tulpn | grep :80 > /dev/null && echo "✓ OK" || echo "✗ ERREUR"

echo -n "  Port 8000 (API)? "
sudo ss -tulpn | grep :8000 > /dev/null && echo "✓ OK" || echo "✗ ERREUR"

echo -n "  Port 5433 (DB)? "
sudo ss -tulpn | grep :5433 > /dev/null && echo "✓ OK" || echo "✗ ERREUR"

echo ""
echo "3. MOSQUITTO HÔTE"
echo -n "  Mosquitto 1883? "
sudo ss -tulpn | grep :1883 | grep -q mosquitto && echo "✓ OK (hôte)" || echo "✗ ERREUR"

echo ""
echo "4. CONTENEURS DOCKER"
echo -n "  PostgreSQL healthy? "
sudo docker compose ps | grep -q "Up (healthy)" && echo "✓ OK" || echo "✗ NOT healthy"

echo -n "  Sensor_Ingestor running? "
sudo docker compose ps | grep -q "Sensor_Ingestor.*Up" && echo "✓ OK" || echo "✗ NOT running"

echo -n "  Automation_Service running? "
sudo docker compose ps | grep -q "Automation_Service.*Up" && echo "✓ OK" || echo "✗ NOT running"

echo ""
echo "5. CONNECTIVITÉ MQTT (depuis hôte)"
mosquitto_pub -h localhost -p 1883 -t test -m "test" 2>/dev/null && echo "  ✓ OK (test message sent)" || echo "  ✗ ERREUR (cannot reach MQTT)"

echo ""
echo "6. API FASTAPI"
curl -s -I http://localhost:8000/docs | grep -q "200\|302" && echo "  ✓ OK (Swagger accessible)" || echo "  ✗ ERREUR (API not responding)"

echo ""
echo "=== FIN CHECKLIST ==="
```

---

## 🆘 TROUBLESHOOTING

### ❌ Error: "Cannot resolve host 'host.docker.internal'"
**Cause**: extra_hosts non configuré ou pas de `host-gateway`

**Solution**:
```bash
# Vérifier dans docker-compose.yml
grep -A 2 "extra_hosts" docker-compose.yml

# Redémarrer avec rebuild
sudo docker compose down
sudo docker compose up -d --build

# Vérifier depuis conteneur
sudo docker exec Sensor_Ingestor ping -c 1 host.docker.internal
# ✓ Doit répondre (ex: 172.17.0.1 ou host IP)
```

### ❌ Error: "Connection refused on 1883"
**Cause**: Mosquitto hôte arrêté ou firewall

**Solution**:
```bash
# Vérifier mosquitto hôte
sudo systemctl status mosquitto
sudo systemctl restart mosquitto

# Vérifier firewall (si ufw)
sudo ufw allow 1883/tcp
sudo ufw status

# Test depuis le host
mosquitto_sub -h localhost -p 1883 -t test & sleep 1 && \
mosquitto_pub -h localhost -p 1883 -t test -m "ok"
```

### ❌ Error: "PostgreSQL not healthy"
**Cause**: Démarrage lent ou credentials incorrectes

**Solution**:
```bash
# Attendre 30 secondes et vérifier
sleep 30
sudo docker compose ps

# Voir les logs
sudo docker logs PostgreSQL

# Redémarrer
sudo docker compose restart postgresql
```

### ❌ Error: "No measurements in database"
**Cause**: Sensor_Ingestor ne reçoit pas les messages MQTT

**Solution**:
```bash
# Vérifier logs Sensor_Ingestor
sudo docker logs Sensor_Ingestor -n 50

# Vérifier MQTT connectivity depuis conteneur
sudo docker exec Sensor_Ingestor ping host.docker.internal

# Tester publication manuelle
mosquitto_pub -h localhost -p 1883 -t Data \
  -m "[test_device][0][Sending Data][sensor:temperature|value:20|msg_id:test-1]"

# Vérifier dans BD
sudo docker exec -it PostgreSQL psql -U program -d FL -c \
  "SELECT * FROM measurements ORDER BY ts DESC LIMIT 1;"
```

### ❌ Error: "Ports already in use"
**Cause**: Ancien project toujours actif

**Solution**:
```bash
# Trouver process sur port
sudo lsof -i :8000
sudo lsof -i :80
sudo lsof -i :5433

# Tuer le process (sauf si important!)
# sudo kill -9 <PID>

# OU arrêter ancien docker
cd ~/Bureau/FL
sudo docker-compose down -v
```

---

## 📊 INFORMATIONS UTILES

### Fichiers importants
```
StageFL-main/
├── docker-compose.yml              (MODIFIÉ - avec host.docker.internal)
├── Sensor_Ingestor/
│   ├── Dockerfile
│   ├── sensor_ingestor.py
│   └── requirements.txt
├── Automation/
│   ├── Dockerfile
│   ├── automation.py
│   └── requirements.txt
├── Serveur_API/
│   ├── Dockerfile
│   ├── server_api.py
│   └── requirements.txt
├── Serveur_Client/
│   ├── Dockerfile
│   └── ...
└── Database/
    └── init.sql
```

### Variables d'environnement clés
```
MQTT_HOST: host.docker.internal  # Résout vers 172.17.0.1 (Linux) ou 192.168.x.x (Docker Desktop)
MQTT_PORT: "1883"
DB_HOST: postgresql              # Service Docker interne
POSTGRES_USER: program
POSTGRES_PASSWORD: program
```

### Commandes útiles
```bash
# Voir tous les logs (suivi en temps réel)
sudo docker compose logs -f

# Redémarrer un service spécifique
sudo docker compose restart sensor_ingestor

# Accéder au shell d'un conteneur
sudo docker exec -it PostgreSQL bash

# Supprimer tout et recommencer (WARNING: perte de données!)
sudo docker compose down -v
```

---

## 📞 SUPPORT

En cas de problème:
1. Vérifier les **logs** (`sudo docker compose logs`)
2. Vérifier les **ports** (`sudo ss -tulpn`)
3. Vérifier la **connectivité MQTT** (`mosquitto_pub -h localhost -p 1883 ...`)
4. Vérifier les **healthchecks** (`sudo docker compose ps`)

---

**Déploiement préparé pour production** ✅

Date: 2026-01-21  
Version: 1.0
