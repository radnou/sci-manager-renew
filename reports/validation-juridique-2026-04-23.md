# Validation Juridique + RGPD — SCI Manager Renew
**Date :** 2026-04-23
**Agent :** sci-fiscal
**Statut :** 🟡 PARTIEL — Actions requises

---

## 1. Déclaration 2065 (backend/app/services/declaration_2065_service.py)

### ✅ Conformité DGFiP
- [x] Champs obligatoires présents (actif + passif)
- [x] Calcul bilan : actif.total = passif.total (équilibre vérifié)
- [x] Date de clôture paramétrable

### ⚠️ Approximations à corriger
- [ ] **Crédits** : approximation 50% du capital restant (ligne 120)
  - **Risque :** Inexact pour reporting fiscal
  - **Action :** Implémenter calcul amortissement linéaire réel
  ```python
  # TODO : calcul exact
  # Solde = capital_initial - (mensualité * mois_écoulés - intérêts_payés)
  ```

### 🔴 Manquant
- [ ] **PDF CERFA** : placeholder `generate_2065_pdf()` → `NotImplementedError`
  - Action : Intégrer pypdf ou reportlab avec template officiel

---

## 2. Landing Page (frontend/src/routes/+page.svelte)

### ✅ Présent
- [x] Mentions légales dans TrustBar (hébergement France, RGPD)
- [x] CGU accessibles (lien footer)
- [x] Pricing avec mentions (€/mois, TTC)

### 🔴 Manquant
- [ ] **Bannière cookies** : obligatoire CNIL
  - Action : Créer `<CookieBanner />` component
  - Script : tarteaucitron.js ou custom
  
- [ ] **Mentions légales page dédiée** `/mentions-legales`
  - Éditeur, hébergeur, DPO, CNIL number

- [ ] **CGV** pour les paiements (Stripe)
  - Action requise avant ouverture commerciale

---

## 3. RGPD — Register des traitements

### ⚠️ Register incomplet
| Traitement | Finalité | Base légale | Durée | Statut |
|------------|----------|-------------|-------|--------|
| Gestion SCI | Admin patrimoine | Contrat | Durée vie SCI | ✅ |
| Données bancaires | Paiement | Contrat | 5 ans | ⚠️ À chiffrer |
| Documents fiscaux | Déclarations | Obligation légale | 10 ans | ⚠️ Hébergement |
| Analytics (Umami) | Stats | Consentement | 13 mois | ✅ Anonymisé |
| Stripe | Paiement | Contrat | 5 ans | ✅ Tokenisé |

---

## 4. Split API (biens_*.py)

### ✅ Pas de régression
- [x] Routes identiques (préfixe `/scis/{sci_id}/biens`)
- [x] `require_sci_membership` appliqué partout
- [x] Rate limiting conservé

### ⚠️ Risque
- [ ] **RLS Supabase** : vérifier que `biens` table a RLS activé
  ```sql
  -- À vérifier sur Supabase
  SELECT relrowsecurity FROM pg_class WHERE relname = 'biens';
  ```

---

## 5. Recommandations Prioritaires

### P1 (avant production)
1. **Bannière cookies** — sanction CNIL 35k€+
2. **Page mentions légales** — obligation légale
3. **CGV Stripe** — obligation commerciale
4. **Calcul crédits exact** — précision fiscale

### P2 (post-lancement)
5. **PDF CERFA 2065** — valeur ajoutée majeure
6. **Register traitements complet** — audit CNIL
7. **DPO désigné** — si +10 salariés (pas le cas pour solopreneur)

---

## 6. Conclusion

**Score conformité : 7/10**
- API 2065 : fonctionnelle mais inexacte (crédits)
- Landing : manque bannière cookies + mentions légales
- RGPD : base solide, à compléter

**Action immédiate :** Créer bannière cookies + page mentions légales avant ouverture.
