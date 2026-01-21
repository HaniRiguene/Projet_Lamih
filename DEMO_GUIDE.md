# 🎬 GUIDE DÉMO COMPLÈTE - SYSTÈME IOT MULTI-CAPTEURS

## 🎯 OBJECTIF
Démontrer un **système IoT production-ready** avec:
- ✅ Pipeline temps réel MQTT → PostgreSQL → FastAPI
- ✅ 3 devices différents (salle_a_manger, cuisine, salle de bain)
- ✅ 150 mesures stockées et requêtables
- ✅ APIs REST fonctionnelles
- ✅ Automation avec hysteresis

---

## ✅ PRÉREQUIS

### Avant de commencer:
- ✓ Docker & Docker Compose installés
- ✓ Terminal PowerShell
- ✓ Dossier: `c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main`
- ✓ 5-10 minutes disponibles

---

## 🚀 DÉMARRAGE RAPIDE (RECOMMANDÉ)

### Option 1: Démo complète en une seule commande
```powershell
cd c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main
.\demo_complete.ps1
```
**Durée:** 5 minutes | **Résultat:** Démo complète end-to-end

### Option 2: Démo par étapes (pour contrôle total)
```powershell
cd c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main
.\demo_1_cleanup.ps1        # Nettoyage (2 min)
.\demo_2_send_data.ps1      # Envoi données (2 min)
.\demo_3_verify_db.ps1      # Vérifier DB (30 sec)
.\demo_4_test_apis.ps1      # Tester APIs (1 min)
.\demo_5_test_automation.ps1  # Automation (2 min, optionnel)
```
**Durée:** 7-10 minutes | **Résultat:** Démo progressive avec explications

---

## 📋 ÉTAPE 1: Vérifier le statut des services

```powershell
cd c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main
docker compose ps
```

**Résultat attendu:** 7 containers tous "Up"
```
NAME                   STATUS
Automation_Service     Up (20 hours)
Client_Server          Up (20 hours)
Mosquitto              Up (20 hours)
PostgreSQL             Up (20 hours) (healthy)
Sensor_Ingestor        Up (20 hours)
Server_API             Up (20 hours)
vue_app                Up (20 hours)
```

---

## 🧹 ÉTAPE 2: Nettoyer la base de données (OPTIONNEL - si démarrage zéro)

```powershell
.\demo_1_cleanup.ps1
```

**Ou manuellement:**
```powershell
docker compose down -v
docker volume prune -f
docker compose up -d
sleep 15
```

⏳ Attendez que PostgreSQL soit "healthy" (vérifiez avec `docker compose ps`)

---

## 📤 ÉTAPE 3: Envoyer les données depuis 3 devices

```powershell
.\demo_2_send_data.ps1
```

**Ou manuellement (voir détails ci-dessous):**

### Device 1: salle_a_manger (50 mesures température 18-24°C)
```powershell
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 18 -Maximum 24
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[salle_a_manger][0][Sending Data][sensor:temperature|value:$val|msg_id:d1_$i]"
  Start-Sleep -Milliseconds 8
}
```

### Device 2: capteur_de_température_cuisine (50 mesures température 20-26°C)
```powershell
sleep 5
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 20 -Maximum 26
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[capteur_de_temperature_cuisine][0][Sending Data][sensor:temperature|value:$val|msg_id:d2_$i]"
  Start-Sleep -Milliseconds 8
}
```

### Device 3: capteur_de_laser_salle_de_bain (50 mesures laser 0 ou 1)
```powershell
sleep 5
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 0 -Maximum 1
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[capteur_de_laser_salle_de_bain][0][Sending Data][sensor:laser|value:$val|msg_id:d3_$i]"
  Start-Sleep -Milliseconds 8
}
sleep 5
```

✅ **Total: 150 messages envoyés** (3 devices × 50 mesures)

---

## 📊 ÉTAPE 4: Vérifier les données en base de données

```powershell
.\demo_3_verify_db.ps1
```

**Ou manuellement:**

### Total des mesures
```powershell
docker exec PostgreSQL psql -U program -d FL -c "SELECT COUNT(*) as total_mesures FROM measurements;"
```

**Résultat attendu:**
```
 total_mesures
---------------
           150
(1 row)
```

### Mesures par device
```powershell
docker exec PostgreSQL psql -U program -d FL -c "SELECT device_id, COUNT(*) as nb_mesures FROM measurements GROUP BY device_id ORDER BY device_id;"
```

**Résultat attendu:**
```
              device_id            | nb_mesures
--------------------------------+------------
 capteur_de_laser_salle_de_bain |         50
 capteur_de_temperature_cuisine |         50
 salle_a_manger                 |         50
(3 rows)
```

### Statistiques complètes
```powershell
docker exec PostgreSQL psql -U program -d FL -c "
SELECT 
  device_id,
  COUNT(*) as nb_mesures,
  MIN(value) as min_val,
  MAX(value) as max_val,
  ROUND(AVG(value)::numeric, 2) as avg_val
FROM measurements
GROUP BY device_id
ORDER BY device_id;
"
```

---

## 🔌 ÉTAPE 5: Tester les APIs FastAPI

```powershell
.\demo_4_test_apis.ps1
```

**Ou manuellement:**

### 5.1 - GET /v1/devices (Liste tous les devices)
```powershell
$devices = Invoke-RestMethod "http://localhost:8000/v1/devices"
$devices | Format-Table device_id, name, type, location
```

**Résultat attendu:**
```
device_id                      name type location
---------                      ---- ---- --------
capteur_de_laser_salle_de_bain      
capteur_de_temperature_cuisine      
salle_a_manger
```

### 5.2 - GET /v1/devices/{id}/latest (Dernière mesure par device)

#### salle_a_manger:
```powershell
$latest = Invoke-RestMethod "http://localhost:8000/v1/devices/salle_a_manger/latest"
$latest | Format-Table sensor, value, ts
```

#### capteur_de_temperature_cuisine:
```powershell
$latest = Invoke-RestMethod "http://localhost:8000/v1/devices/capteur_de_temperature_cuisine/latest"
$latest | Format-Table sensor, value, ts
```

#### capteur_de_laser_salle_de_bain:
```powershell
$latest = Invoke-RestMethod "http://localhost:8000/v1/devices/capteur_de_laser_salle_de_bain/latest"
$latest | Format-Table sensor, value, ts
```

**Résultat attendu:**
```
sensor      value ts
------      ----- --
temperature  21.5 2026-01-21T15:49:44.123456+00:00
```

### 5.3 - GET /v1/measurements (Requête filtrée avec limit & order)

#### Dernières 5 mesures de la cuisine:
```powershell
$meas = Invoke-RestMethod "http://localhost:8000/v1/measurements?device_id=capteur_de_temperature_cuisine&limit=5&order=desc"
$meas | Select-Object device_id, sensor, value, ts | Format-Table
```

#### Dernières 3 mesures du laser:
```powershell
$meas = Invoke-RestMethod "http://localhost:8000/v1/measurements?device_id=capteur_de_laser_salle_de_bain&limit=3&order=desc"
$meas | Select-Object device_id, sensor, value, ts | Format-Table
```

**Résultat attendu:** 5 et 3 lignes respectivement

### 5.4 - GET /v1/measurements/aggregate (Agrégation par bucket)
```powershell
$agg = Invoke-RestMethod "http://localhost:8000/v1/measurements/aggregate?device_id=salle_a_manger&bucket=1h&agg=avg"
$agg | Format-Table
```

**Résultat attendu:** Agrégation par heure avec moyenne

---

## 🤖 ÉTAPE 6: Tester l'Automation Service (OPTIONNEL)

```powershell
.\demo_5_test_automation.ps1
```

**Ou manuellement:**

Le service écoute les capteurs de lumière et allume/éteint une lampe selon les seuils:
- **TH_LOW = 200 lux** → Allume lampe après 5s
- **TH_HIGH = 300 lux** → Éteint lampe après 5s

### Envoyer des mesures de faible luminosité (< 200 = allume)
```powershell
for ($i = 1; $i -le 20; $i++) {
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[light_sensor][0][Sending Data][sensor:light|value:$([int](Get-Random -Minimum 50 -Maximum 150))|msg_id:light_$i]"
  Start-Sleep -Milliseconds 100
}
```

### Attendre l'hysteresis (5 secondes)
```powershell
sleep 8
```

### Vérifier les logs du service automation
```powershell
docker logs Automation_Service --tail 10
```

**Vous devriez voir:**
```
[AUTOMATION] Publish {"state": "ON"} to actuators/lamp1/set
```

---

## 🌐 ÉTAPE 7: Accéder à l'interface Web

Ouvrir dans un navigateur:
- **API Docs (Swagger):** http://localhost:8000/docs
- **API ReDoc:** http://localhost:8000/redoc
- **Web UI:** http://localhost
- **PostgreSQL:** localhost:5433 (user: program, pass: program)

---

## 🔧 ÉTAPE 8: Vérifier les logs des services

### Logs Sensor_Ingestor
```powershell
docker logs Sensor_Ingestor --tail 20
```

### Logs Mosquitto
```powershell
docker logs Mosquitto --tail 20
```

### Logs Server_API
```powershell
docker logs Server_API --tail 20
```

### Logs Automation
```powershell
docker logs Automation_Service --tail 20
```

---

## 📁 SCRIPTS DISPONIBLES

| Script | Fonction | Durée |
|--------|----------|-------|
| `demo_complete.ps1` | 🚀 Démo COMPLÈTE en une fois | 5 min |
| `demo_1_cleanup.ps1` | 🧹 Nettoie et redémarre | 2 min |
| `demo_2_send_data.ps1` | 📤 Envoie 150 messages | 2 min |
| `demo_3_verify_db.ps1` | 📊 Vérifie données | 30 sec |
| `demo_4_test_apis.ps1` | 🔌 Teste les 4 APIs | 1 min |
| `demo_5_test_automation.ps1` | 🤖 Teste automation | 2 min |

---

## 📝 COMMANDE RAPIDE: DÉMO COMPLÈTE EN UNE FOIS

```powershell
cd c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main

# Option 1: Utiliser le script (RECOMMANDÉ)
.\demo_complete.ps1

# Option 2: Manuellement
docker compose down -v
docker compose up -d
sleep 15

# Device 1
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 18 -Maximum 24
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[salle_a_manger][0][Sending Data][sensor:temperature|value:$val|msg_id:d1_$i]"
  Start-Sleep -Milliseconds 8
}
sleep 5

# Device 2
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 20 -Maximum 26
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[capteur_de_temperature_cuisine][0][Sending Data][sensor:temperature|value:$val|msg_id:d2_$i]"
  Start-Sleep -Milliseconds 8
}
sleep 5

# Device 3
for ($i = 1; $i -le 50; $i++) { 
  $val = Get-Random -Minimum 0 -Maximum 1
  docker exec Mosquitto mosquitto_pub -h localhost -p 1883 -t Data -m "[capteur_de_laser_salle_de_bain][0][Sending Data][sensor:laser|value:$val|msg_id:d3_$i]"
  Start-Sleep -Milliseconds 8
}
sleep 5

# Vérifier database
docker exec PostgreSQL psql -U program -d FL -c "SELECT device_id, COUNT(*) as cnt FROM measurements GROUP BY device_id;"

# Vérifier API
Write-Host "=== DEVICES ===" -ForegroundColor Green
(Invoke-RestMethod "http://localhost:8000/v1/devices") | Format-Table device_id

Write-Host "`n=== LATEST VALUES ===" -ForegroundColor Green
(Invoke-RestMethod "http://localhost:8000/v1/devices/salle_a_manger/latest") | Format-Table sensor, value

Write-Host "`n✅ DÉMO COMPLÈTE!" -ForegroundColor Green
```

---

## 🆘 TROUBLESHOOTING

### Si les services ne démarrent pas
```powershell
docker compose logs
docker compose down
docker compose up -d
sleep 20
```

### Si PostgreSQL n'est pas "healthy"
```powershell
docker logs PostgreSQL
# Attendre 15-20 secondes après docker compose up -d
```

### Si MQTT ne reçoit pas les messages
```powershell
docker logs Mosquitto | Select-String "listening"
```

### Si la base de données est vide après l'envoi
```powershell
# Vérifier les logs Sensor_Ingestor
docker logs Sensor_Ingestor

# Vérifier que la table existe
docker exec PostgreSQL psql -U program -d FL -c "\dt"
```

### Erreur PowerShell exécution
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📊 CE QUE CELA DÉMONTRE

✅ **Pipeline temps réel:**
- Capteurs → MQTT → Sensor_Ingestor → PostgreSQL → FastAPI → Client

✅ **Multi-devices:**
- 3 devices distincts avec identités uniques
- Types de capteurs variés (température, laser/motion)

✅ **Stockage persistent:**
- 150 mesures avec timestamps réalistes
- Requêtes filtrées et agrégations

✅ **REST API production:**
- 4 endpoints fonctionnels
- Documentation Swagger auto-générée

✅ **Automation:**
- Logique hysteresis pour contrôle de lampe
- Basée sur seuils de capteurs

✅ **Infrastructure:**
- Docker orchestration complète
- Connection pooling PostgreSQL
- Retry logic avec exponential backoff
- Batch processing avec déduplication

---

## 🎯 RÉSUMÉ RAPIDEMENT

| Étape | Commande | Résultat |
|-------|----------|----------|
| **Démarrer** | `docker compose ps` | Voir tous les services Up |
| **Envoi données** | `.\demo_2_send_data.ps1` | 150 messages publiés |
| **Vérifier DB** | `.\demo_3_verify_db.ps1` | Voir 150 mesures stockées |
| **Tester API** | `.\demo_4_test_apis.ps1` | 4 endpoints fonctionnels |
| **Documentation** | `http://localhost:8000/docs` | Swagger UI interactive |

---

## 📞 POINTS CLÉS À RETENIR

🎯 **Pour la démo:**
1. Exécutez `demo_complete.ps1` pour une démo rapide (5 min)
2. Ou exécutez étape par étape pour un contrôle total
3. Vérifiez toujours que PostgreSQL est "healthy"
4. Les données persistent même après redémarrage

💡 **Points techniques:**
- MQTT topic: `Data`
- Format: `[device][0][Sending Data][sensor:X|value:Y|msg_id:Z]`
- API base: `http://localhost:8000`
- DB credentials: user=program, pass=program
- All devices auto-created on first message

🚀 **Production-ready:**
- Connection pooling (1-5 connexions)
- Batch processing (max 200 messages)
- Retry logic (30 tentatives avec backoff)
- Deduplication (PRIMARY KEY sur device_id, ts, sensor)

---

**Bon courage pour votre démo! 🚀**
