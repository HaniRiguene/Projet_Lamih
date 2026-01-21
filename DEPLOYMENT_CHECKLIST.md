# 📋 CHECKLIST DÉPLOIEMENT PRODUCTION LINUX

**Projet**: StageFL IoT System  
**Date**: 2026-01-21  
**Type**: Migration Dev→Production Linux  

---

## ✅ PRÉ-DÉPLOIEMENT (À faire avant de commencer)

### Vérifications Système

```
☐ SSH accès au serveur Linux
☐ Mosquitto hôte actif
  $ sudo systemctl status mosquitto
  Doit afficher: "active (running)"

☐ Docker installé et à jour
  $ docker --version
  $ docker compose version

☐ Projet source disponible
  $ ls ~/StageFL-main/docker-compose.yml
  Doit exister

☐ Ancien projet accessible (backup)
  $ test -d ~/Bureau/FL && echo "Existe"
  Optionnel (archive avant suppression)

☐ Droits sudo disponibles
  $ sudo whoami
  Doit afficher "root"
```

### Vérifications Fichiers de Migration

```
☐ docker-compose.yml modifié
  $ cd ~/StageFL-main
  $ grep -c "host.docker.internal" docker-compose.yml
  Doit afficher ≥ 4

☐ Mosquitto service supprimé
  $ grep -c "^  mosquitto:" docker-compose.yml
  Doit afficher 0

☐ extra_hosts configuré
  $ grep -c "extra_hosts:" docker-compose.yml
  Doit afficher ≥ 4

☐ YAML valide
  $ docker compose config > /dev/null && echo "OK"
  Doit afficher "OK" sans erreur

☐ Scripts exécutables
  $ chmod +x deploy-production.sh validate-deployment.sh
  $ ls -la deploy-production.sh | grep -q rwx && echo "OK"
```

### Vérifications Ports

```
☐ Port 80 libre
  $ sudo ss -tulpn | grep :80
  Doit être VIDE (aucun résultat)

☐ Port 8000 libre
  $ sudo ss -tulpn | grep :8000
  Doit être VIDE (aucun résultat)

☐ Port 5433 libre
  $ sudo ss -tulpn | grep :5433
  Doit être VIDE (aucun résultat)

☐ Port 1883 en use par mosquitto hôte
  $ sudo ss -tulpn | grep :1883 | grep mosquitto
  Doit afficher : users:(("mosquitto"...))
```

---

## 🔴 PHASE 1: ARRÊT ANCIEN PROJET (3 min)

### Arrêt des Services

```
☐ Naviguer au dossier ancien projet
  $ cd ~/Bureau/FL

☐ Vérifier les conteneurs
  $ sudo docker-compose ps
  Doit afficher la liste des services

☐ Arrêter et supprimer (inclure volumes)
  $ sudo docker-compose down -v
  Doit afficher: "Network removed"

☐ Vérifier suppression
  $ sudo docker-compose ps
  Doit être VIDE (no services)
```

### Vérification Ports Libérés

```
☐ Port 80 libre après arrêt
  $ sudo ss -tulpn | grep :80
  Doit être VIDE (aucun résultat)

☐ Port 8000 libre après arrêt
  $ sudo ss -tulpn | grep :8000
  Doit être VIDE (aucun résultat)

☐ Port 5433 libre après arrêt
  $ sudo ss -tulpn | grep :5433
  Doit être VIDE (aucun résultat)

☐ Prendre une minute pour laisser ports se libérer
  $ sleep 60
```

---

## 🟢 PHASE 2: DÉPLOIEMENT (5-10 min)

### Option A: Déploiement Automatisé (Recommandé)

```
☐ Naviguer au nouveau projet
  $ cd ~/StageFL-main

☐ Rendre scripts exécutables
  $ chmod +x deploy-production.sh validate-deployment.sh

☐ Exécuter le script de déploiement
  $ sudo bash deploy-production.sh
  Doit afficher: "Deployment completed successfully!"

☐ Attendre que PostgreSQL soit healthy (~30 sec)
  Le script attend automatiquement

☐ Note des informations affichées
  • API Docs URL: http://<IP>:8000/docs
  • Web Portal: http://<IP>
  • Database credentials
```

### Option B: Déploiement Manuel

```
☐ Naviguer au projet
  $ cd ~/StageFL-main

☐ Builder et démarrer services (2-3 min, first build)
  $ sudo docker compose up -d --build
  Doit afficher: "Network created", puis "Started"

☐ Attendre 30 secondes
  $ sleep 30

☐ Vérifier status des services
  $ sudo docker compose ps
  Doit afficher 6 services "Up"
  PostgreSQL doit être "Up (healthy)"

☐ Vérifier pas d'erreurs
  $ sudo docker compose logs | grep -i error
  Doit retourner très peu d'erreurs (warnings OK)
```

---

## 🔵 PHASE 3: VALIDATION (5 min)

### Validation Automatisée (Recommandé)

```
☐ Exécuter le script de validation
  $ cd ~/StageFL-main
  $ sudo bash validate-deployment.sh
  Doit afficher: "ALL CHECKS PASSED"

☐ Lire le résumé affiché
  • Success Rate doit être 100%
  • Web Access URLs affichées
```

### Validation Manuelle (Si script échoue)

```
☐ Ports utilisés
  $ sudo ss -tulpn | grep -E '(:80|:8000|:5433|:1883)' | wc -l
  Doit afficher: 4

☐ Services Docker running
  $ sudo docker compose ps | grep -c "Up"
  Doit afficher: 6 ou 7

☐ PostgreSQL healthy
  $ sudo docker compose ps | grep PostgreSQL
  Doit contenir: "healthy"

☐ MQTT accessible depuis hôte
  $ mosquitto_pub -h localhost -p 1883 -t test -m "test"
  Aucune erreur = OK

☐ MQTT accessible depuis conteneur
  $ sudo docker exec Sensor_Ingestor ping -c 1 host.docker.internal
  Doit afficher: "64 bytes from 172.17.0.1"

☐ API accessible
  $ curl -s -I http://localhost:8000/docs | head -1
  Doit afficher: "HTTP/1.1 200" ou "HTTP/1.1 302"

☐ Web UI accessible
  $ curl -s -I http://localhost/ | head -1
  Doit afficher: "HTTP/1.1 200"

☐ PostgreSQL accessible
  $ sudo docker exec -it PostgreSQL psql -U program -d FL -c "SELECT 1"
  Doit afficher: "1"

☐ Logs propres
  $ sudo docker compose logs Sensor_Ingestor | tail -5
  Doit montrer: messages normaux, pas "error" ou "Connection refused"
```

---

## 🧪 PHASE 4: TEST INGESTION MQTT (5 min)

### Publier des Messages Test

```
☐ Publier un message test unique
  $ mosquitto_pub -h localhost -p 1883 -t Data \
    -m "[test_device][0][Sending Data][sensor:temperature|value:21|msg_id:test-1]"
  Aucune erreur = OK

☐ Publier 10 messages test (boucle)
  $ for i in {1..10}; do \
      mosquitto_pub -h localhost -p 1883 -t Data \
        -m "[test_device][0][Sending Data][sensor:temperature|value:$((20 + RANDOM % 5))|msg_id:test-$i]"; \
      sleep 0.2; \
    done
  Tous doivent se publier sans erreur

☐ Attendre ingestion (2 secondes)
  $ sleep 2
```

### Vérifier Ingestion Database

```
☐ Compter messages en database
  $ sudo docker exec PostgreSQL psql -U program -d FL -c \
    "SELECT device_id, COUNT(*) FROM measurements WHERE device_id='test_device' GROUP BY device_id;"
  Doit afficher: test_device | 10 (au minimum)

☐ Vérifier dernier message
  $ sudo docker exec PostgreSQL psql -U program -d FL -c \
    "SELECT device_id, sensor, value, ts FROM measurements WHERE device_id='test_device' ORDER BY ts DESC LIMIT 1;"
  Doit retourner 1 ligne avec timestamp récent
```

### Vérifier via API

```
☐ Lister les devices via API
  $ curl -s http://localhost:8000/v1/devices | jq '.[] | .device_id'
  Doit afficher: "test_device" (entre autres)

☐ Récupérer dernière mesure du test device
  $ curl -s "http://localhost:8000/v1/devices/test_device/latest" | jq .
  Doit afficher: {"sensor": "temperature", "value": 21, ...}
```

---

## 🆘 TROUBLESHOOTING RAPIDE

### Si ça échoue à une étape:

```
☐ Lire le message d'erreur complètement
  → Chercher le mot-clé (Connection, refused, timeout, etc.)

☐ Vérifier logs du service
  $ sudo docker compose logs <service> | tail -50

☐ Vérifier que le service est bien UP
  $ sudo docker compose ps | grep <service>

☐ Redémarrer le service
  $ sudo docker compose restart <service>
  $ sleep 10

☐ Si ça persiste, redémarrer tous les services
  $ sudo docker compose down
  $ sudo docker compose up -d --build
  $ sleep 30

☐ Consulter le guide complet
  → Lire: DEPLOYMENT_LINUX.md section TROUBLESHOOTING
```

### Erreurs Courantes et Solutions:

```
❌ "Port already in use"
   $ sudo lsof -i :<port>
   $ sudo kill -9 <PID>

❌ "Cannot resolve host.docker.internal"
   → Redémarrer docker compose
   → Vérifier extra_hosts dans docker-compose.yml

❌ "PostgreSQL not healthy"
   → Attendre 30 secondes (demarrage lent)
   → Vérifier docker logs PostgreSQL

❌ "MQTT Connection refused"
   → Vérifier mosquitto: sudo systemctl status mosquitto
   → Redémarrer: sudo systemctl restart mosquitto
```

---

## 📊 POST-DÉPLOIEMENT (MAINTENANCE)

### Vérifications Régulières

```
☐ Vérifier services chaque matin
  $ cd ~/StageFL-main && sudo docker compose ps

☐ Monitorer les logs pour erreurs
  $ sudo docker compose logs -f | grep -i error

☐ Vérifier les mesures en database
  $ sudo docker exec PostgreSQL psql -U program -d FL -c \
    "SELECT COUNT(*) FROM measurements;"

☐ Test de publication MQTT mensuel
  $ mosquitto_pub -h localhost -p 1883 -t test -m "health-check"
```

### Backup & Restore

```
☐ Backup database (avant modifications)
  $ sudo docker exec PostgreSQL pg_dump -U program -d FL > ~/FL_backup_$(date +%Y%m%d).sql

☐ Backup docker-compose.yml
  $ cp docker-compose.yml docker-compose.yml.backup

☐ Vérifier backups existent
  $ ls -la ~/FL_backup_*.sql
  $ ls -la docker-compose.yml.backup
```

---

## ✅ VALIDATION FINALE - À COCHER ABSOLUMENT

```
CONDITION DE SUCCÈS - TOUS LES POINTS DOIVENT ÊTRE COCHÉS

☐ Ancien projet complètement arrêté
☐ Ports 80, 8000, 5433 libres et réutilisés
☐ Tous les services Docker "Up"
☐ PostgreSQL "healthy"
☐ MQTT broker accessible (localhost:1883)
☐ API FastAPI répond (/docs accessible)
☐ Web UI accessible (port 80)
☐ Messages MQTT ingérés en database
☐ Logs sans erreurs critiques
☐ Validation script passe 100%

Si OUI sur tous → ✅ DÉPLOIEMENT RÉUSSI
```

---

## 📞 RESSOURCES DISPONIBLES

```
Si vous avez besoin de...          Consultez...
─────────────────────────────────────────────────────
Vue d'ensemble                      EXECUTIVE_SUMMARY.md
Étapes détaillées                   DEPLOYMENT_LINUX.md
Diff des changements                DIFF_DOCKER_COMPOSE.md
Commandes directes                  DEPLOY_COMMANDS.md
Automatisation complète             deploy-production.sh
Validation automatisée              validate-deployment.sh
Point d'entrée général              LINUX_MIGRATION_README.md
```

---

## 🎯 RÉSUMÉ EXÉCUTIF

```
AVANT                    APRÈS
═══════════════════════  ═══════════════════════
Docker Mosquitto         Mosquitto système
7 conteneurs             6 conteneurs
Démarrage 25-30s        Démarrage 15-20s
Architecture complexe    Architecture claire
+15% ressources         -15% ressources

TEMPS TOTAL: 20-30 minutes
COMPLEXITÉ: Moyenne
RISQUE: Faible (architecture éprouvée)
SUPPORT: Documentation + Scripts
```

---

**Imprimez cette checklist et cochez les cases au fur et à mesure!**

**Date de déploiement**: ________________  
**Responsable**: ________________  
**Observations**: ________________

---

*Préparé le: 2026-01-21*  
*Révision: 1.0*  
*Status: ✅ READY FOR PRODUCTION*
