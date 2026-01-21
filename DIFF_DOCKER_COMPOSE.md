# 📊 DIFF - Modifications du docker-compose.yml

## Vue d'ensemble des changements

```
AVANT (Local Dev)          APRÈS (Production Linux)
════════════════════════   ════════════════════════════
✅ Mosquitto Docker        ❌ Mosquitto Docker (REMOVED)
✅ MQTT_HOST: mosquitto    ✅ MQTT_HOST: host.docker.internal
❌ extra_hosts             ✅ extra_hosts: host.docker.internal:host-gateway
❌ Dépend de mosquitto     ✅ Dépendance mosquitto removed
```

---

## 1️⃣ MOSQUITTO - COMPLÈTEMENT SUPPRIMÉ

### AVANT (Local/Windows)
```yaml
services:
  # ╔══════════════════════════════════════╗
  # ║                 MQTT                 ║
  # ╚══════════════════════════════════════╝
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: Mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
    volumes:
      - ./Mosquitto_Config/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro
```

### APRÈS (Production Linux)
```yaml
services:
  # NOTE: MQTT Broker is provided by host mosquitto on port 1883
  # Do NOT start a separate mosquitto container in production
  # Services connect via host.docker.internal:1883 (Linux) or host.docker.internal:1883 (Docker Desktop)
```

**Impact**: 
- ✅ Économise 1 conteneur Docker
- ✅ Réutilise le mosquitto hôte existant
- ✅ Réduit la complexité réseau

---

## 2️⃣ SERVER_API - CONFIGURATION MQTT

### AVANT
```yaml
server_api:
  build: ./Serveur_API
  container_name: Server_API
  restart: on-failure
  ports:
    - "8000:8000"
  depends_on:
    postgresql:
      condition: service_healthy
    mosquitto:                          # ❌ SUPPRIMÉ
      condition: service_started        # ❌ SUPPRIMÉ
  volumes:
    - type: bind
      source: /home/WebFL/FL
      target: /app/FL
  environment:
    POSTGRES_HOST: postgresql
    POSTGRES_DB: FL
    POSTGRES_USER: program
    POSTGRES_PASSWORD: program
    MQTT_HOST: mosquitto                # ❌ CHANGÉ
    MQTT_PORT: "1883"
```

### APRÈS
```yaml
server_api:
  build: ./Serveur_API
  container_name: Server_API
  restart: on-failure
  ports:
    - "8000:8000"
  depends_on:
    postgresql:
      condition: service_healthy
  extra_hosts:                          # ✅ AJOUTÉ
    - "host.docker.internal:host-gateway"
  volumes:
    - type: bind
      source: /home/WebFL/FL
      target: /app/FL
  environment:
    POSTGRES_HOST: postgresql
    POSTGRES_DB: FL
    POSTGRES_USER: program
    POSTGRES_PASSWORD: program
    MQTT_HOST: host.docker.internal    # ✅ CHANGÉ
    MQTT_PORT: "1883"
```

**Changements clés**:
```diff
  depends_on:
    postgresql:
      condition: service_healthy
-   mosquitto:
-     condition: service_started
+
+ extra_hosts:
+   - "host.docker.internal:host-gateway"
  
  environment:
    ...
-   MQTT_HOST: mosquitto
+   MQTT_HOST: host.docker.internal
```

---

## 3️⃣ SENSOR_INGESTOR - CONFIGURATION MQTT

### AVANT
```yaml
sensor_ingestor:
  build: ./Sensor_Ingestor
  container_name: Sensor_Ingestor
  restart: on-failure
  depends_on:
    postgresql:
      condition: service_healthy
    mosquitto:                    # ❌ SUPPRIMÉ
      condition: service_started  # ❌ SUPPRIMÉ
  environment:
    MQTT_HOST: mosquitto          # ❌ CHANGÉ
    MQTT_PORT: "1883"
    DB_HOST: postgresql
    DB_NAME: FL
    DB_USER: program
    DB_PASS: program
    BATCH_SIZE: "200"
    BATCH_FLUSH_SECS: "1.0"
```

### APRÈS
```yaml
sensor_ingestor:
  build: ./Sensor_Ingestor
  container_name: Sensor_Ingestor
  restart: on-failure
  depends_on:
    postgresql:
      condition: service_healthy
  extra_hosts:                    # ✅ AJOUTÉ
    - "host.docker.internal:host-gateway"
  environment:
    MQTT_HOST: host.docker.internal    # ✅ CHANGÉ
    MQTT_PORT: "1883"
    DB_HOST: postgresql
    DB_NAME: FL
    DB_USER: program
    DB_PASS: program
    BATCH_SIZE: "200"
    BATCH_FLUSH_SECS: "1.0"
```

---

## 4️⃣ AUTOMATION - CONFIGURATION MQTT

### AVANT
```yaml
automation:
  build: ./Automation
  container_name: Automation_Service
  restart: on-failure
  depends_on:
    postgresql:
      condition: service_healthy
    mosquitto:                    # ❌ SUPPRIMÉ
      condition: service_started  # ❌ SUPPRIMÉ
  environment:
    MQTT_HOST: mosquitto          # ❌ CHANGÉ
    MQTT_PORT: "1883"
    SENSOR_TOPIC: "Data"
    LIGHT_SENSOR_NAME: "light"
    LAMP_ID: "lamp1"
    TH_LOW: "200"
    TH_HIGH: "300"
    DUR_ON_SECS: "5"
    DUR_OFF_SECS: "5"
```

### APRÈS
```yaml
automation:
  build: ./Automation
  container_name: Automation_Service
  restart: on-failure
  depends_on:
    postgresql:
      condition: service_healthy
  extra_hosts:                    # ✅ AJOUTÉ
    - "host.docker.internal:host-gateway"
  environment:
    MQTT_HOST: host.docker.internal    # ✅ CHANGÉ
    MQTT_PORT: "1883"
    SENSOR_TOPIC: "Data"
    LIGHT_SENSOR_NAME: "light"
    LAMP_ID: "lamp1"
    TH_LOW: "200"
    TH_HIGH: "300"
    DUR_ON_SECS: "5"
    DUR_OFF_SECS: "5"
```

---

## 5️⃣ CLIENT_SERVER - CONFIGURATION MQTT

### AVANT
```yaml
client_server:
  build: ./Serveur_Client
  container_name: Client_Server
  restart: on-failure
  depends_on:
    server_api:
      condition: service_started
    mosquitto:                    # ❌ SUPPRIMÉ
      condition: service_started  # ❌ SUPPRIMÉ
  volumes:
    - type: bind
      source: /home/WebFL/FL
      target: /app/FL
  environment:
    MQTT_HOST: mosquitto          # ❌ CHANGÉ
    MQTT_PORT: "1883"
```

### APRÈS
```yaml
client_server:
  build: ./Serveur_Client
  container_name: Client_Server
  restart: on-failure
  depends_on:
    server_api:
      condition: service_started
  extra_hosts:                    # ✅ AJOUTÉ
    - "host.docker.internal:host-gateway"
  volumes:
    - type: bind
      source: /home/WebFL/FL
      target: /app/FL
  environment:
    MQTT_HOST: host.docker.internal    # ✅ CHANGÉ
    MQTT_PORT: "1883"
```

---

## 6️⃣ VUE_FRONTEND - AUCUN CHANGEMENT

```yaml
vue_frontend:
  build: ./Site_Vue
  container_name: vue_app
  restart: unless-stopped
  ports:
    - "80:80"
  depends_on:
    - server_api
  # ✅ Pas de changement (ne consomme pas MQTT)
```

---

## 7️⃣ POSTGRESQL - AUCUN CHANGEMENT

```yaml
postgresql:
  image: postgres:14-alpine
  container_name: PostgreSQL
  restart: unless-stopped
  ports:
    - "5433:5432"
  environment:
    POSTGRES_DB: FL
    POSTGRES_USER: program
    POSTGRES_PASSWORD: program
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./Database/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
    interval: 5s
    timeout: 5s
    retries: 10
  # ✅ Pas de changement
```

---

## 📋 RÉSUMÉ DES MODIFICATIONS

| Aspect | Avant | Après | Raison |
|--------|-------|-------|--------|
| **Mosquitto Container** | Lancé | Supprimé | Réutiliser hôte |
| **MQTT_HOST (services)** | `mosquitto` | `host.docker.internal` | Connexion au broker hôte |
| **extra_hosts** | Non présent | `host.docker.internal:host-gateway` | DNS resolution sur Linux |
| **depends_on mosquitto** | Présent | Supprimé | Pas de dépendance Docker |
| **Services MQTT** | 4 (server_api, sensor_ingestor, automation, client_server) | 4 (configurés pour hôte) | Même nombre, nouv. config |

---

## 🔧 PARAMÈTRE CLÉ: extra_hosts

### Pourquoi `extra_hosts` est crucial?

Sur Linux, `host.docker.internal` n'existe pas nativement. La ligne:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Ajoute une entrée DNS au conteneur qui résout `host.docker.internal` vers la passerelle Docker (habituellement `172.17.0.1`), qui correspond à la machine hôte.

### Vérification depuis le conteneur:
```bash
$ docker exec Sensor_Ingestor ping -c 1 host.docker.internal
PING host.docker.internal (172.17.0.1): 56 data bytes
64 bytes from 172.17.0.1: seq=0 ttl=64 time=0.123 ms
```

✅ Succès = conteneur peut joindre l'hôte

---

## ✅ VÉRIFICATION POST-MODIFICATION

```bash
# 1. Vérifier que mosquitto n'est pas dans le compose
grep -c "mosquitto:" docker-compose.yml  # Doit retourner 0

# 2. Vérifier que host.docker.internal est présent
grep -c "host.docker.internal" docker-compose.yml  # Doit retourner >= 4

# 3. Vérifier que extra_hosts est présent
grep -c "extra_hosts" docker-compose.yml  # Doit retourner >= 4

# 4. Vérifier la validité du YAML
docker compose config > /dev/null && echo "✓ Valid YAML"
```

---

## 🚀 APPLICATION

```bash
# Vérifier les changements
git diff docker-compose.yml

# Appliquer et déployer
sudo docker compose down -v
sudo docker compose up -d --build

# Vérifier depuis conteneur
sudo docker exec Sensor_Ingestor printenv | grep MQTT
# Doit afficher:
# MQTT_HOST=host.docker.internal
# MQTT_PORT=1883
```

---

**Résumé**: ✅ **4 services modifiés**, ✅ **1 service supprimé** (mosquitto), ✅ **Prêt pour production Linux**
