# ✅ Configuration Stripe Complète

## 🎯 Produits Créés

| Plan | Product ID | Price ID | Prix | Billing |
|------|-----------|----------|------|---------|
| **Starter** | prod_U5Xbfs8216Pvo4 | price_1T7MW5BCxd3SKdGJP2xjawrj | €19.00 | /mois |
| **Pro** | prod_U5Xbintqwgo6DU | price_1T7MW6BCxd3SKdGJKzcNqdkJ | €49.00 | /mois |
| **Lifetime** | prod_U5XbG8qEUxCiHM | price_1T7MW7BCxd3SKdGJVrHWprJ8 | €299.00 | une fois |

## 📝 Variables d'Environnement

### Backend (`.env`)
```
# ⚠️ Remplacer avec vos vraies clés Stripe (depuis dashboard.stripe.com)
STRIPE_SECRET_KEY=sk_test_YOUR_ACTUAL_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_ACTUAL_KEY_HERE
STRIPE_STARTER_PRICE_ID=price_1T7MW5BCxd3SKdGJP2xjawrj
STRIPE_PRO_PRICE_ID=price_1T7MW6BCxd3SKdGJKzcNqdkJ
STRIPE_LIFETIME_PRICE_ID=price_1T7MW7BCxd3SKdGJVrHWprJ8
```

### Frontend (`.env`)
```
# ⚠️ Clés publiques Stripe (remplacer avec les vôtres)
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_ACTUAL_KEY_HERE
```

## 🔧 Fichiers Configurés

✅ `backend/app/core/config.py` - Ajout des 3 price IDs
✅ `frontend/src/routes/pricing/+page.svelte` - Envoie `plan_key` au backend
✅ `.env` - Test keys + tous les Price IDs
✅ `.env.example` - Template avec placeholders

## 🧪 Prochaines Étapes

### 1. Tester le flux de checkout local
```bash
# Terminal 1: Backend sur port 8000
cd backend && python -m uvicorn app.main:app --reload

# Terminal 2: Frontend sur port 5173
cd frontend && npm run dev

# Accéder à: http://localhost:5173/pricing
```

### 2. Vérifier la page de paiement
- Cliquer sur "Choisir" pour un plan
- Vérifier que la session Stripe est créée
- Le backend doit résoudre le `price_id` correspondant au `plan_key` choisi

### 3. Configurer Webhook Stripe (avant prod)
```bash
# Dans le dashboard Stripe, ajouter endpoint webhook:
# https://votre-api.domaine.fr/api/v1/stripe/webhook
```

### 4. Phase 6 - Déploiement
- Docker containerization
- Nginx reverse proxy config
- Deployment documentation (README)

---

**Status:** ✅ Stripe products prêts pour test local  
**Date:** $(date)  
**Environment:** Test keys activées (sk_test_*, pk_test_*)
