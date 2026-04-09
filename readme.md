# 🏠 ProjetLamih - Système IoT Temps Réel pour Smart Home

**Système complet de gestion IoT et orchestration en temps réel**

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)]()
[![Documentation](https://img.shields.io/badge/Documentation-Complete-blue)]()
[![Version](https://img.shields.io/badge/Version-1.0-orange)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

---

## 🎯 Aperçu

**ProjetLamih** est une plateforme IoT moderne et extensible pour la gestion de systèmes domotiques, avec support pour:
- ✅ Collecte temps réel de données de capteurs
- ✅ Orchestration automatisée via règles MQTT
- ✅ Base de données PostgreSQL pour l'historique
- ✅ API REST complète pour intégration
- ✅ Interface Web Vue.js intuitive
- ✅ Support du mosquitto MQTT hébergé ou Docker

**Use Case**: Gestion complète d'un système domotique avec 3+ appareils, stockage des mesures, et orchestration d'actions automatisées.

---

## ✨ Fonctionnalités

### 🔴 Core Features

| Fonctionnalité | Description | Status |
|---|---|---|
| **Collecte MQTT** | Réception en temps réel des données des capteurs | ✅ |
| **Ingestion DB** | Stockage automatique dans PostgreSQL | ✅ |
| **Orchestration** | Automatisation des actions basée sur les règles | ✅ |
| **API REST** | Endpoints pour requêtes et gestion | ✅ |
| **Web UI** | Dashboard Vue.js pour visualisation | ✅ |
| **Déploiement** | Scripts automatisés pour Linux/Docker | ✅ |

### 🟡 Services

- **Sensor_Ingestor**: Écoute MQTT → Stocke en base
- **Automation**: Règles MQTT pour orchestration
- **Server_API**: FastAPI avec endpoints REST
- **Client_Server**: Orchestrateur MQTT
- **Vue_Frontend**: Interface Web responsive

---


**Flux de Données**:
```
IoT Devices → MQTT (1883) → Sensor_Ingestor → PostgreSQL
              ↓
           Automation → Actions
              ↓
           Server_API → REST Endpoints
              ↓
           React Frontend → Web UI
```

---

## 🚀 Démarrage Rapide

### Prérequis

```bash
# Vérifier les prérequis
✓ Docker & docker compose (20.10+, 2.0+)
✓ Mosquitto en cours d'exécution (port 1883)
✓ Ports 80, 8000, 5433 libres
```

### Installation (5 minutes)

```bash
# 1. Clone et navigate
git clone https://github.com/HaniRiguene/Projet_Lamih.git
cd Projet_Lamih

# 2. Déploiement automatique
sudo bash deploy-host-mosquitto.sh

# 3. Vérification
bash test-deployment.sh
```

### Accès aux Services

| Service | URL |
|---------|-----|
| **Web Portal** | http://localhost |
| **API Docs** | http://localhost:8000/docs |
| **Database** | localhost:5433 (user: program) |
| **MQTT Broker** | localhost:1883 |

---

## 🎬 Demo Complète

### Lancer la démo avec 150 messages (10 minutes)

```bash
# Lancer la démo complète
./demo_complete.ps1

# Étapes automatiques:
# 1️⃣ Nettoyage des services
# 2️⃣ Envoi de 150 messages MQTT (3 appareils × 50 chacun)
#    - Device 1: 50 mesures température
#    - Device 2: 50 mesures humidité
#    - Device 3: 50 mesures pression
# 3️⃣ Vérification en base de données (150 messages attendus)
# 4️⃣ Test des 4 endpoints API
# 5️⃣ Rapport final avec statut ✅
```

---

## 🛠️ Technologie

### Stack Principal

| Composant | Technologie | Version |
|-----------|-------------|---------|
| **Backend APIs** | FastAPI + Uvicorn | 0.100+ |
| **MQTT Broker** | Eclipse Mosquitto | 2.0+ |
| **Database** | PostgreSQL | 14-alpine |
| **Frontend** | React.js | 19.0+ |
| **Conteneurisation** | Docker | 20.10+ |
| **Orchestration** | docker compose | 2.0+ |

### Languages

- 🐍 **Python** 3.10+ (Services backend)
- 🟩 **React.js** (Frontend interactif)
- 📝 **SQL** (PostgreSQL time-series)
- 🔵 **MQTT 3.1.1** (Communication temps réel)

---

## ✅ Configuration Production

### Prérequis Système

```bash
# Mosquitto doit être en cours d'exécution
sudo systemctl status mosquitto

# Si besoin de démarrer
sudo systemctl start mosquitto

# Vérifier port 1883
sudo ss -tulpn | grep 1883
```

### Variables d'Environnement Critiques

```yaml
# Tous les services MQTT
MQTT_HOST: host.docker.internal
MQTT_PORT: 1883
EXTRA_HOSTS: host.docker.internal:host-gateway

# Client_Server IMPORTANT
MQTT_BROKER_HOST: host.docker.internal


---

## 📊 Performance Mesurée

| Métrique | Résultat |
|----------|----------|
| Temps déploiement | 3-4 minutes |
| Temps démarrage services | 30-60 secondes |
| Messages testés (demo) | 150+ messages |
| Taux persistence | 100% (150/150) |
| CPU par service | <5% |
| Mémoire totale | ~500MB |
| Latence MQTT→DB | <100ms |

---

## 🧪 Tests Inclus (8 catégories)

```bash
bash test-deployment.sh
```

Couverture de test:
- ✅ Services Docker en cours d'exécution (5/5)
- ✅ Ports accessibles (80, 8000, 5433, 1883)
- ✅ Connectivité socket (host + container)
- ✅ MQTT pub/sub opérationnel
- ✅ Connectivité base de données
- ✅ Endpoints API REST (4 endpoints)
- ✅ Variables d'environnement correctes
- ✅ Ingestion de données (E2E)

---

## 🔧 Commandes de Gestion

### Déploiement

```bash
# Déploiement complet (recommandé)
sudo bash deploy-host-mosquitto.sh

# Démarrage manuel
docker compose up -d --build

# Arrêt
docker compose down -v

# Rebuild complet
docker compose down -v && docker compose up -d --build
```

### Monitoring

```bash
# Logs temps réel
docker compose logs -f

# Suivi spécifique
docker compose logs -f sensor_ingestor

# Statut services
docker compose ps

# Ressources utilisés
docker stats
```

### Base de Données

```bash
# Connexion interactive
docker exec -it PostgreSQL psql -U program -d FL

# Compte de mesures
docker exec PostgreSQL psql -U program -d FL \
    -c "SELECT COUNT(*) FROM measurements;"

# Dernières mesures
docker exec PostgreSQL psql -U program -d FL \
    -c "SELECT * FROM measurements ORDER BY message_time DESC LIMIT 10;"
```

### MQTT

```bash
# Publier un message
mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[device_1][0][Sending Data][sensor:temperature|value:22.5|msg_id:1]"

# S'abonner aux messages
mosquitto_sub -h localhost -p 1883 -t 'Data' -v

# Afficher topiques disponibles
mosquitto_sub -h localhost -p 1883 -t '$SYS/#' -v
```

---

## 🐛 Troubleshooting Rapide

### Erreur: Conteneur ne peut pas atteindre mosquitto

```bash
# Solution 1: Vérifier mosquitto
sudo systemctl status mosquitto
sudo systemctl start mosquitto

# Solution 2: Rebuild
docker compose down -v && docker compose up -d --build

# Vérifier connexion
docker exec Sensor_Ingestor python3 -c \
  "import socket; s=socket.socket(); \
   print('✅ MQTT OK' if s.connect_ex(('host.docker.internal',1883))==0 else '❌ MQTT FAIL')"
```

### PostgreSQL lent à démarrer

```bash
# Attendre 60-90 secondes
sleep 60
docker compose ps PostgreSQL

# Vérifier logs
docker compose logs PostgreSQL | tail -20
```

### API ne répond pas

```bash
# Vérifier port
curl http://localhost:8000/docs

# Vérifier service
docker compose logs server_api | tail -20
```

## 🚀 Démarrage Rapide

```bash
# 🟢 Option 1: Déploiement automatique complet (Recommandé)
sudo bash deploy-host-mosquitto.sh

# 🟡 Option 2: Lancer la démo
./demo_complete.ps1

# 🔵 Option 3: Lire la doc d'abord
cat START_HERE.md

# 🟣 Option 4: Démarrage manuel
docker compose up -d && bash test-deployment.sh
```

## 📈 Prochaines Étapes

1. ✅ Cloner le dépôt
2. ✅ Lancer le déploiement
3. ✅ Exécuter les tests
4. ✅ Accéder aux services
5. ✅ Lire la documentation
6. ✅ Personnaliser la configuration

---

**Status**: ✅ Production Ready | **Version**: 1.0 | **Last Updated**: 2026-01-21

**Accès services**: 
- 🌐 Frontend: http://localhost
- 📚 API Docs: http://localhost:8000/docs
- 🗄️ Database: localhost:5433
- 📨 MQTT: localhost:1883

---
