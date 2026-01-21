# 🔥 COMMANDES DIRECTES - Migration Production Linux

## 📌 PRÉ-REQUIS (À vérifier d'abord)

```bash
# 1. SSH vers le serveur
ssh user@your-server-ip

# 2. Vérifier que mosquitto hôte tourne
sudo systemctl status mosquitto

# 3. Mosquitto accessible?
mosquitto_sub -h localhost -p 1883 -t '$SYS/broker/version' -u 0 -t 1 -C 1
# Doit afficher la version de mosquitto

# 4. Docker installé?
docker --version
docker compose version

# 5. Projet source disponible?
cd ~/StageFL-main
ls docker-compose.yml
```

---

## ⚠️ ÉTAPE 1: ARRÊTER L'ANCIEN PROJET

```bash
# Aller au dossier de l'ancien projet
cd ~/Bureau/FL

# Vérifier les conteneurs actifs
sudo docker-compose ps

# Arrêter tout et supprimer (inclure les volumes)
sudo docker-compose down -v

# Vérifier suppression
sudo docker-compose ps  
# Doit être vide

# Vérifier que les ports sont maintenant libres
sudo ss -tulpn | grep -E '(:80|:8000|:5433)'
# ✓ Doit retourner VIDE (aucun résultat)
```

---

## ✅ ÉTAPE 2: VÉRIFIER docker-compose.yml

```bash
cd ~/StageFL-main

# 1. Vérifier que mosquitto service n'existe plus
grep -n "^  mosquitto:" docker-compose.yml
# ✓ Doit retourner: No such file or directory (ou 0 match)

# 2. Vérifier que MQTT_HOST est "host.docker.internal"
grep -n "MQTT_HOST: host.docker.internal" docker-compose.yml
# ✓ Doit retourner au minimum 4 matches

# 3. Vérifier extra_hosts
grep -n "extra_hosts:" docker-compose.yml
# ✓ Doit retourner au minimum 4 matches

# 4. Vérifier la validité du YAML
docker compose config > /dev/null && echo "✓ docker-compose.yml is valid" || echo "✗ INVALID YAML"
```

---

## 🚀 ÉTAPE 3: DÉPLOYER

### Option A: Script automatisé (Recommandé)

```bash
cd ~/StageFL-main

# Rendre le script exécutable
chmod +x deploy-production.sh

# Exécuter le déploiement complet
sudo bash deploy-production.sh

# Le script va:
# ✅ Vérifier les prérequis
# ✅ Arrêter l'ancien projet
# ✅ Vérifier que les ports sont libres
# ✅ Valider docker-compose.yml
# ✅ Builder et démarrer les services
# ✅ Tester la connectivité
# ✅ Afficher un résumé
```

### Option B: Commandes manuelles

```bash
cd ~/StageFL-main

# 1. Builder et démarrer les services (première fois: 2-3 minutes)
sudo docker compose up -d --build

# 2. Attendre que PostgreSQL soit healthy (30 secondes)
sleep 30

# 3. Vérifier le statut des services
sudo docker compose ps

# ✓ Tous les conteneurs doivent afficher "Up" ou "Up (healthy)"
```

---

## 🔍 ÉTAPE 4: VALIDER LE DÉPLOIEMENT

### 4.1 Vérifier les ports sont bien utilisés

```bash
# Port 80 (Web UI)
echo "Testing port 80..."
sudo ss -tulpn | grep :80 && echo "✓ Port 80 is listening" || echo "✗ Port 80 NOT listening"

# Port 8000 (API)
echo "Testing port 8000..."
sudo ss -tulpn | grep :8000 && echo "✓ Port 8000 is listening" || echo "✗ Port 8000 NOT listening"

# Port 5433 (PostgreSQL)
echo "Testing port 5433..."
sudo ss -tulpn | grep :5433 && echo "✓ Port 5433 is listening" || echo "✗ Port 5433 NOT listening"

# Port 1883 (Mosquitto hôte - NE doit PAS être dans Docker)
echo "Testing port 1883 (host mosquitto)..."
sudo ss -tulpn | grep :1883 | grep -q mosquitto && echo "✓ Mosquitto host running" || echo "✗ Mosquitto NOT found"
```

### 4.2 Tester la connectivité MQTT

```bash
# Test depuis le host
mosquitto_pub -h localhost -p 1883 -t test -m "Hello from host"
echo "✓ Published test message to MQTT"

# Attendre 2 secondes
sleep 2

# Vérifier depuis conteneur
sudo docker exec Sensor_Ingestor ping -c 1 host.docker.internal
echo "✓ Container can reach host.docker.internal"
```

### 4.3 Tester l'API

```bash
# Swagger documentation accessible?
curl -s -I http://localhost:8000/docs | head -1
# ✓ Doit afficher: HTTP/1.1 200 OK ou 302 Found

# Test endpoint /v1/devices
curl -s http://localhost:8000/v1/devices | jq .
# ✓ Doit retourner une liste d'appareils

# Test endpoint /v1/devices/{id}/latest
curl -s "http://localhost:8000/v1/devices/salle_a_manger/latest" | jq .
# ✓ Doit retourner la dernière mesure
```

### 4.4 Tester l'interface Web

```bash
# Web UI accessible?
curl -s -I http://localhost/ | head -1
# ✓ Doit afficher: HTTP/1.1 200 OK (ou 301/302 si redirection)

# Accéder depuis navigateur
# http://<SERVER_IP>/
```

### 4.5 Vérifier la base de données

```bash
# Se connecter à PostgreSQL
sudo docker exec -it PostgreSQL psql -U program -d FL

# Une fois connecté, tester:

# Voir les tables
\dt

# Compter les measurements
SELECT COUNT(*) FROM measurements;

# Compter les devices
SELECT COUNT(*) FROM devices;

# Voir les dernières mesures
SELECT device_id, sensor, value, ts FROM measurements ORDER BY ts DESC LIMIT 5;

# Quitter
\q
```

### 4.6 Utiliser le script de validation

```bash
cd ~/StageFL-main

# Rendre le script exécutable
chmod +x validate-deployment.sh

# Exécuter la validation complète
sudo bash validate-deployment.sh

# Le script va automatiquement checker:
# ✅ Tous les ports
# ✅ Tous les services Docker
# ✅ La connectivité réseau
# ✅ Les endpoints API
# ✅ La base de données
# ✅ Les logs
```

---

## 📊 ÉTAPE 5: TESTER L'INGESTION MQTT COMPLÈTE

### 5.1 Publier des messages test

```bash
# Publier 10 messages test
for i in {1..10}; do
  mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[salle_a_manger][0][Sending Data][sensor:temperature|value:$((20 + RANDOM % 10))|msg_id:test-$i]"
  sleep 0.2
done

echo "✓ 10 test messages published"
sleep 2
```

### 5.2 Vérifier l'ingestion

```bash
# Via ligne de commande
sudo docker exec PostgreSQL psql -U program -d FL -c \
  "SELECT device_id, COUNT(*) as message_count FROM measurements GROUP BY device_id;"

# ✓ Doit afficher les devices avec le nombre de messages reçus
```

### 5.3 Vérifier via l'API

```bash
# Lister les devices
curl -s http://localhost:8000/v1/devices | jq '.[] | {device_id, name}'

# Récupérer les dernières mesures du device
curl -s "http://localhost:8000/v1/measurements?device_id=salle_a_manger&limit=5" | jq .
```

---

## 🔧 DÉPANNAGE RAPIDE

### ❌ "Port déjà en usage"

```bash
# Identifier le processus
sudo lsof -i :8000
# ou
sudo fuser 8000/tcp

# Tuer le processus
sudo kill -9 <PID>

# Redémarrer le service
sudo docker compose restart server_api
```

### ❌ "Cannot resolve host.docker.internal"

```bash
# Vérifier que extra_hosts est configuré
grep -A 1 "extra_hosts" docker-compose.yml | head -5

# Redémarrer les services
sudo docker compose down
sudo docker compose up -d --build

# Tester depuis conteneur
sudo docker exec Sensor_Ingestor nslookup host.docker.internal
# ✓ Doit retourner une IP (ex: 172.17.0.1)
```

### ❌ "PostgreSQL not healthy"

```bash
# Attendre plus longtemps (20-30 secondes)
sleep 30
sudo docker compose ps

# Voir les logs
sudo docker logs PostgreSQL

# Redémarrer PostgreSQL
sudo docker compose restart postgresql
sleep 20
```

### ❌ "MQTT Connection refused"

```bash
# Vérifier que mosquitto hôte tourne
sudo systemctl status mosquitto

# Vérifier qu'il écoute sur 1883
sudo ss -tulpn | grep :1883

# Redémarrer mosquitto
sudo systemctl restart mosquitto

# Tester la connexion
mosquitto_sub -h localhost -p 1883 -t '$SYS/broker/version' -C 1
```

### ❌ "Services ne reçoivent pas les messages MQTT"

```bash
# Vérifier les logs Sensor_Ingestor
sudo docker compose logs Sensor_Ingestor | tail -20

# Vérifier que MQTT_HOST est bien set
sudo docker exec Sensor_Ingestor printenv | grep MQTT

# Tester la publication manuelle
mosquitto_pub -h localhost -p 1883 -t Data \
  -m "[test_device][0][Sending Data][sensor:temperature|value:21|msg_id:debug-1]"

# Vérifier la réception dans PostgreSQL
sleep 2
sudo docker exec PostgreSQL psql -U program -d FL -c \
  "SELECT * FROM measurements WHERE device_id='test_device' ORDER BY ts DESC LIMIT 1;"
```

---

## 📋 CHECKLIST FINALE - À COPIER/COLLER

```bash
#!/bin/bash
# Exécuter: sudo bash validate-complete.sh

echo "=== FINAL VALIDATION CHECKLIST ==="
echo ""

echo "1. Ports utilisés?"
sudo ss -tulpn | grep -E '(:80|:8000|:5433|:1883)' | wc -l
echo "   (Doit afficher 4)"
echo ""

echo "2. Services Docker?"
sudo docker compose ps | grep -c "Up"
echo "   (Doit afficher 6 ou 7)"
echo ""

echo "3. MQTT accessible?"
timeout 2 mosquitto_pub -h localhost -p 1883 -t test -m test && echo "   ✓ YES" || echo "   ✗ NO"
echo ""

echo "4. API répondant?"
curl -s -I http://localhost:8000/docs | head -1
echo ""

echo "5. Web UI répondant?"
curl -s -I http://localhost/ | head -1
echo ""

echo "6. Messages en base?"
sudo docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) FROM measurements;" 2>/dev/null | tail -1
echo ""

echo "=== FIN CHECKLIST ==="
```

---

## 🎯 RÉSUMÉ DES COMMANDES ESSENTIELLES

| Commande | Utilité |
|----------|---------|
| `sudo docker compose ps` | Voir l'état des services |
| `sudo docker compose logs -f` | Voir les logs en temps réel |
| `sudo docker compose restart <service>` | Redémarrer un service |
| `sudo docker compose down -v` | Arrêter et supprimer (données aussi!) |
| `sudo docker compose up -d --build` | Démarrer/redémarrer les services |
| `sudo docker exec -it PostgreSQL psql -U program -d FL` | Accéder à la BD |
| `mosquitto_pub -h localhost -p 1883 -t Data -m "..."` | Publier un message MQTT |
| `sudo ss -tulpn` | Voir les ports utilisés |
| `sudo systemctl status mosquitto` | Vérifier mosquitto hôte |

---

**Durée estimée du déploiement complet: 5-10 minutes** ⏱️
