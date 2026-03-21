# Spécification Module Fiscalité — Panel Big4
**Date** : 21 mars 2026
**Auteurs** : Panel Big4 (Expert Fiscal, Juridique, Comptable, Produit)
**Statut** : Validé — Référence pour roadmap

## Roadmap

### MVP Fiscal (4-6 semaines) — Score 13/15
- [x] Résumé fiscal IR réel per-bien (CERFA 2044 L211-L240)
- [x] Micro-foncier comparison (art. 32 CGI)
- [x] Déficit foncier decomposition (art. 156-I-3° CGI)
- [x] Quittance PDF conforme (art. 21 loi 1989, R.123-237)
- [ ] CERFA 2044 pré-rempli PDF (mapping officiel complet)
- [ ] Report 2042 individuel par associé (cases 4BA/4BB/4BC/4BD)
- [ ] Déficit foncier tracker 10 ans (table deficit_reportable)
- [ ] Simulateur plus-value immobilière (lead magnet public)

### V1 Fiscal (+6-8 semaines) — Rétention
- [ ] Grand livre auto-généré (écritures silencieuses)
- [ ] Bilan simplifié + compte de résultat
- [ ] Export FEC réglementaire (18 champs, pipe-separated)
- [ ] Déclaration 2072 pré-remplie
- [ ] PV AG modèles avec pré-remplissage
- [ ] Registre mouvements de parts avec formalités

### V2 Fiscal (+8-12 semaines) — Différenciation
- [ ] Amortissement IS par composant
- [ ] Liasse 2065 + 2033 (régime simplifié)
- [ ] Rapprochement bancaire (import CSV/OFX)
- [ ] Dispositifs spéciaux (Pinel, Denormandie, Malraux)

### V3 Fiscal (+6 mois) — Référence marché
- [ ] Open Banking (DSP2)
- [ ] Télétransmission EDI-TDFC
- [ ] IA catégorisation écritures
- [ ] Portail comptable (lecture seule)

## Packaging

| Feature | Essentiel (0€) | Gestion (19€) | Fiscal (39€) |
|---|:-:|:-:|:-:|
| Dashboard + KPIs | ✅ | ✅ | ✅ |
| Biens (max 2 / 10 / illimité) | ✅ | ✅ | ✅ |
| Loyers + quittances | ✅ | ✅ | ✅ |
| Calendrier fiscal | — | ✅ | ✅ |
| CERFA 2044 pré-rempli | — | Aperçu flouté | ✅ |
| Déficit foncier tracker | — | — | ✅ |
| Grand livre + balance | — | — | ✅ |
| Export FEC | — | — | ✅ |
| 2072 pré-remplie | — | — | ✅ |
| PV AG + registre parts | — | ✅ | ✅ |
| Simulateur PV | ✅ (lead magnet) | ✅ | ✅ |

## Positionnement

"Votre comptable facture 1 500€/an pour votre SCI. GérerSCI fait 80% du travail pour 468€/an."

GérerSCI ne remplace pas le comptable. GérerSCI prépare 80% de son travail.

## Références légales

- CGI art. 28-31 (charges déductibles revenus fonciers)
- CGI art. 32 (micro-foncier)
- CGI art. 156-I-3° (déficit foncier)
- CGI art. 206-2 / 239 (option IS)
- Code civil art. 1856 (registre AG)
- Code civil art. 1861 (cession parts)
- Code commerce R.123-237 (mentions obligatoires)
- Loi 89-462 art. 21 (quittance)
- LPF art. L.47 A-I (FEC)
