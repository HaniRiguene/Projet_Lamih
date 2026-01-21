# 📝 INSTRUCTIONS POUR EXÉCUTER LES SCRIPTS DE DÉMO

## 📂 Fichiers disponibles

Tous les scripts sont dans: `c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main\`

### Option 1: DÉMO COMPLÈTE EN UNE FOIS (RECOMMANDÉ)
```powershell
cd c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main
.\demo_complete.ps1
```

**Durée:** ~5 minutes  
**Résultat:** Demo complète avec 150 mesures et tests APIs

---

### Option 2: DÉMO PAR ÉTAPES (POUR CONTRÔLE TOTAL)

**Étape 1: Nettoyer et redémarrer (2 min)**
```powershell
.\demo_1_cleanup.ps1
```

**Étape 2: Envoyer les données (2 min)**
```powershell
.\demo_2_send_data.ps1
```

**Étape 3: Vérifier la base de données (30 sec)**
```powershell
.\demo_3_verify_db.ps1
```

**Étape 4: Tester les APIs (1 min)**
```powershell
.\demo_4_test_apis.ps1
```

**Étape 5: Tester l'Automation (optionnel, 2 min)**
```powershell
.\demo_5_test_automation.ps1
```

---

## 🚀 DÉMARRAGE RAPIDE

### Première exécution
```powershell
cd c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main
.\demo_complete.ps1
```

### Réutilisation rapide (sans nettoyage)
Si les services sont déjà en ligne, vous pouvez directement:
```powershell
.\demo_2_send_data.ps1
.\demo_3_verify_db.ps1
.\demo_4_test_apis.ps1
```

---

## ⚙️ PRÉALABLES

Avant de lancer les scripts, assurez-vous:

1. **Docker est lancé**
   ```powershell
   docker --version
   ```

2. **Vous êtes dans le bon dossier**
   ```powershell
   cd c:\Users\hanir\Desktop\smarthomeproject\StageFL-main\StageFL-main
   dir demo_*.ps1  # Devrait afficher les 5 scripts
   ```

3. **PowerShell peut exécuter les scripts**
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

---

## 📊 CE QUE CHAQUE SCRIPT FAIT

| Script | Durée | Description |
|--------|-------|-------------|
| `demo_complete.ps1` | 5 min | ✅ Démo COMPLÈTE end-to-end |
| `demo_1_cleanup.ps1` | 2 min | 🧹 Nettoie DB et redémarre |
| `demo_2_send_data.ps1` | 2 min | 📤 Envoie 150 messages |
| `demo_3_verify_db.ps1` | 30 sec | 📊 Vérifie données en DB |
| `demo_4_test_apis.ps1` | 1 min | 🔌 Teste les 4 APIs |
| `demo_5_test_automation.ps1` | 2 min | 🤖 Teste l'automation |

---

## 🎯 SCÉNARIOS D'UTILISATION

### Scénario A: Vous avez 5 minutes (salle de classe/meeting)
```powershell
.\demo_complete.ps1
```
→ Affiche la démo complète avec tous les résultats

---

### Scénario B: Vous avez 10 minutes (présentation détaillée)
```powershell
.\demo_1_cleanup.ps1
# Montrez l'écran pendant que les services démarrent

.\demo_2_send_data.ps1
# Montrez les messages qui s'envoient

.\demo_3_verify_db.ps1
# Montrez les données dans la DB

.\demo_4_test_apis.ps1
# Montrez les APIs en action

.\demo_5_test_automation.ps1
# Montrez l'automation optionnellement
```

---

### Scénario C: Vous réutilisez (services déjà en ligne)
```powershell
.\demo_2_send_data.ps1
# Envoyer nouvelles données
# (Ajouter à l'ancienne)

.\demo_3_verify_db.ps1
# Voir les nouvelles données
```

---

## ✅ VALIDATION

Après `demo_complete.ps1`, vous devriez voir:

**Base de données:**
```
             device_id            | nb_mesures
--------------------------------+------------
 capteur_de_laser_salle_de_bain |         50
 capteur_de_temperature_cuisine |         50
 salle_a_manger                 |         50
```

**API:**
```
✓ Devices: 3 devices listés
✓ Latest: Dernière température affichée
✓ Measurements: Requêtes filtrées fonctionnelles
```

---

## 🆘 PROBLÈMES?

### Erreur "containers not found"
```powershell
docker compose ps
# Si vide, lancer:
docker compose up -d
sleep 15
```

### Erreur PowerShell exécution
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# Puis relancer le script
```

### PostgreSQL pas "healthy"
```powershell
docker logs PostgreSQL
# Attendre 20 secondes après docker compose up -d
```

### API non accessible
```powershell
# Vérifier que Server_API est Up
docker compose ps

# Si pas Up, vérifier les logs
docker logs Server_API
```

---

## 📞 SUPPORT

Tous les scripts incluent:
- ✅ Messages de progression clairs
- ✅ Couleurs pour la lisibilité
- ✅ Vérification des résultats
- ✅ Gestion des erreurs

Pour plus d'infos, consultez: `DEMO_GUIDE.md`

---

**Bon courage pour votre démo! 🚀**
