# 🧹 ÉTAPE 1: Nettoyer et redémarrer le système
# Usage: ./demo_1_cleanup.ps1

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║         🧹 NETTOYAGE ET REDÉMARRAGE DES SERVICES             ║" -ForegroundColor Yellow
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Yellow

Write-Host "Arrêt des services..." -ForegroundColor Cyan
docker compose down -v

Write-Host "`nNettoyage des volumes..." -ForegroundColor Cyan
docker volume prune -f

Write-Host "`nDémarrage des services..." -ForegroundColor Cyan
docker compose up -d

Write-Host "`nAttente de l'initialisation de PostgreSQL (15 secondes)..." -ForegroundColor Green
sleep 15

Write-Host "`n✅ Vérification du statut:" -ForegroundColor Green
docker compose ps --format "table {{.Names}}\t{{.Status}}"

Write-Host "`n✅ SYSTÈME PRÊT POUR LA DÉMO!" -ForegroundColor Green
