# Étude de marché & fonctionnalités — Tarification GererSCI

> Date : 2026-06-23. Objet : valider/ajuster la tarification de GererSCI à partir d'une étude de
> marché (concurrents français) et d'une étude des fonctionnalités, puis aligner les prix (app +
> Stripe + CGV/CGU). Décisions appliquées en bas de document.

## 1. Étude de marché — concurrents français

GererSCI adresse trois besoins que le marché traite habituellement séparément : **gestion
locative**, **fiscalité SCI** et **juridique SCI**. Panorama des prix (2026, HT sauf mention) :

### a) Logiciels compta / fiscalité SCI (concurrents directs)
| Acteur | Prix | Positionnement |
|--------|------|----------------|
| **Ownily** | Basic **14€**/mois (143€/an) · Premium **29€**/mois (~296€/an) | Compta SCI (liasse 2072) + locatif allégé — le plus proche de GererSCI |
| **Indy** | **32€**/mois SCI à l'IS (24€/mois en annuel) · gratuit SCI à l'IR 1 bien | Compta + liasse + télétransmission EDI |
| **Macompta.fr** | ~**24€**/mois (compta + immobilisations + déclarations) | Compta complète, modulaire |
| **Qlower** | **269€ TTC/an** autonome (+130€/bien) · 590€ TTC/an avec expert (OGA) | Compta LMNP/SCI + déclarations |
| **Pennylane** | 14-29€/mois | Compta indépendant/PME (non spécialisé SCI) |
| **InfoSCI** | **5,90€**/mois entrée · 12€/mois premium (144€/an) | SCI à l'IR familiales, IS limité |
| **Dougs** | **79-99€**/mois | Vrai expert-comptable inscrit à l'Ordre |
| ComptaSCI (Solinfo) | licence 99,90€ (IR) / 139,90€ (IS) + abo MAJ | Logiciel desktop Windows |

### b) Logiciels de gestion locative (concurrents indirects)
| Acteur | Prix |
|--------|------|
| **Rentila** | gratuit 1 bien, puis ~8€/mois (Silver 49€/an, Gold 99€/an) |
| **Smartloc** | **9,90€**/mois |
| **GererSeul** | **11,90€**/mois |
| BailFacile / FairePlace | 7-35€/mois |

**Fourchette marché** : gestion locative **7-12€**, compta SCI self-service **14-32€**, expert-
comptable **79-99€**.

## 2. Étude des fonctionnalités — le moat de GererSCI

Matrice fonctionnelle comparée (self-service) :

| Capacité | GererSCI | Compta SCI (Ownily/Indy/Qlower) | Gestion locative (Rentila/Smartloc) |
|----------|:--------:|:-------------------------------:|:-----------------------------------:|
| Gestion locative (quittances, loyers, relances) | ✅ | partiel | ✅ |
| Fiscalité SCI (CERFA 2044, résumé fiscal, calendrier) | ✅ | ✅ | ❌ |
| **Juridique SCI (AG, registre, convocations, PV)** | ✅ | ❌ | ❌ |
| **Mouvements de parts (cession/transmission + droits)** | ✅ | ❌ | ❌ |
| Multi-SCI illimité | ✅ (Pilotage) | partiel | partiel |
| Expert-comptable inclus | ❌ | ❌ (sauf Dougs / Qlower OGA) | ❌ |

➡️ **Le moat = le juridique SCI** (AG, registre, mouvements de parts) combiné à la gestion +
fiscalité. **Aucun concurrent self-service ne couvre le juridique SCI.** C'est ce qui justifie le
positionnement premium de Pilotage, sous le seuil de l'expert-comptable (79€+).

Paliers GererSCI :
- **Gestion** (19€/mois, 190€/an) — 1 SCI, 5 biens : quittances, loyers + relances, CERFA 2044,
  charges/PNO/agence, export CSV, support 48h.
- **Pilotage** (39€/mois, 390€/an) — illimité : tout Gestion + AG/convocations, mouvements de
  parts, moteur 44+ échéances, calendrier fiscal, vue comptable, révision IRL auto, support 24h.
- **Fondateur** (paiement unique) — accès à vie au Pilotage, 25 places.

## 3. Positionnement & analyse
- **Gestion 19€** : entre la gestion locative low-cost (8-12€) et la compta SCI d'entrée
  (Ownily 14€, InfoSCI 6-12€). Légère prime justifiée par la fiscalité incluse. **Bien positionné.**
- **Pilotage 39€** : au-dessus des compta SCI self-service (Indy 32€, Ownily 29€, Macompta 24€),
  mais **différencié** (juridique + illimité) et bien **sous l'expert-comptable** (Dougs 79€+).
  **Sweet spot premium.**
- **Fondateur** : un « lifetime » vaut usuellement 2-4x l'abonnement annuel. À 500€ il valait
  ≈1,3 an de Pilotage annuel — sous-évalué. **990€ ≈ 2,5x l'annuel**, cohérent, tout en gardant
  l'effet rareté (25 places).
- **Cabinet** : le segment cabinet comptable est mieux servi par des outils multi-clients à la
  carte (Ownily/Qlower) ou un expert-comptable (Dougs). Un palier « 69€ illimité multi-clients »
  peu différencié ajoutait de la complexité sans avantage net. **Abandon** pour concentrer
  l'offre sur le gérant de SCI direct (Gestion/Pilotage) + Fondateur.

## 4. Décisions appliquées
| Plan | Avant | Après | Action |
|------|-------|-------|--------|
| Gestion | 19€/190€ | **19€/190€** | Inchangé (validé marché) |
| Pilotage | 39€/390€ | **39€/390€** | Inchangé (validé marché) |
| Fondateur | 500€ | **990€ HT** (1 188€ TTC) | Nouveau prix Stripe live `price_1TlazQApRgYAyPDH449eJzEk` ; ancien archivé ; app + CGV/CGU mis à jour |
| Cabinet | 69€/588€ (caché) | **Abandonné** | Produit + prix archivés dans Stripe ; vars d'env retirées |

## Sources
- [Comparatif logiciels compta SCI 2026 — fiscalite-sci.com](https://fiscalite-sci.com/logiciel-comptabilite-sci/)
- [Comparatif compta SCI gratuit — Indy](https://www.indy.fr/guide/comptabilite-en-ligne/logiciel/comparatif/sci/gratuit/)
- [Compta SCI à l'IS — Indy](https://www.indy.fr/guide/comptabilite-en-ligne/logiciel/comparatif/sci/sci-is/)
- [Ownily — Tarifs](https://www.ownily.fr/tarifs)
- [Qlower — déclaration SCI](https://www.qlower.com/en/sci-statement) · [avis/prix Qlower](https://fiscalite-sci.com/logiciel-comptabilite-sci/qlower/)
- [macompta.fr — SCI](https://www.macompta.fr/societes-civiles-immobilieres)
- [Comparatif gestion locative 2026 — FairePlace](https://faireplace.com/comparatif-logiciel-gestion-locative/)
- [Rentila — avis/prix](https://investissement-locatif-avis.fr/rentila-avis/)
