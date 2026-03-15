# Import CSV — Biens + Loyers

**Date** : 15 mars 2026
**Priorité** : P0 (frein #1 à l'adoption, unanime panel Big4)
**Scope** : Import CSV avec template téléchargeable pour biens et loyers

---

## Contexte

Le gérant SCI type a déjà ses données dans un fichier Excel. Sans import, il doit tout ressaisir manuellement — 30-60 minutes pour 5+ biens avec historique. Le panel a mesuré que le taux d'activation double quand l'import CSV existe.

## Architecture

### Backend

**Module** : `backend/app/api/v1/import_csv.py`
**Router prefix** : `/api/v1/import`

#### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/templates/{type}` | Aucune | Télécharge le template CSV (biens ou loyers) |
| POST | `/csv` | Gérant | Upload et importe un CSV dans une SCI |

#### POST /csv — Paramètres

| Param | Type | Description |
|-------|------|-------------|
| `file` | UploadFile | Fichier CSV (max 5 MB) |
| `sci_id` | str (form) | ID de la SCI cible |
| `type` | str (form) | `biens` ou `loyers` |

#### Réponse

```json
{
  "success": true,
  "imported": 12,
  "skipped": 2,
  "errors": ["ligne 5: adresse manquante", "ligne 8: montant invalide"],
  "type": "biens"
}
```

#### Validation

- Taille max : 5 MB
- Lignes max : 500
- Colonnes obligatoires vérifiées contre le template
- Sanitization : strip HTML/scripts, escape SQL
- Auth : gérant de la SCI cible (require_gerant_role)
- Doublons : skip si bien avec même adresse+ville existe déjà

### Templates CSV

**Biens** (`import-biens-template.csv`) :
```csv
adresse,ville,code_postal,type_locatif,surface_m2,nb_pieces,loyer_cc,charges,dpe_classe
12 rue de la Paix,Paris,75001,nu,65,3,1250,180,C
8 rue des Lilas,Lyon,69001,meuble,28,1,750,90,D
```

**Loyers** (`import-loyers-template.csv`) :
```csv
adresse_bien,date_loyer,montant,statut
12 rue de la Paix,2026-01-01,1250,paye
12 rue de la Paix,2026-02-01,1250,en_attente
```

Le matching loyer→bien se fait par `adresse_bien` (recherche dans les biens de la SCI).

### Frontend

**Accès** : bouton "Importer (CSV)" sur la page biens (`/scis/[sciId]/biens`)

**Flow** :
1. Modale s'ouvre avec 2 onglets : "Biens" / "Loyers"
2. Lien "Télécharger le template" → GET /templates/{type}
3. Zone de drop / sélection fichier
4. Upload → aperçu tableau des données parsées
5. Bouton "Importer X lignes" → POST /csv
6. Résultat : succès/erreurs affichés, puis refresh de la liste

### Sécurité

- Rate limit : 5 imports/heure par utilisateur
- Validation MIME type (text/csv uniquement)
- Pas d'exécution de formules (pas de =CMD() Excel)
- Encoding UTF-8 vérifié
- Service client pour les INSERTs (pattern _get_write_client)

### Tests

- Backend : ~15 tests (upload valide, colonnes manquantes, fichier trop gros, doublons, mauvais format, auth)
- Frontend : 0 errors svelte-check
- E2E : 1 test billing-audit (import avec compte pro)
