# Audit Expert Panel — GererSCI SaaS

**Date** : 13 mars 2026
**Comité** : Product Manager · Lead UX/UI · Expert Juridique & Comptable SCI
**Périmètre** : Frontend (SvelteKit) · Backend (FastAPI) · Base de données (Supabase/PostgreSQL)
**Méthodologie** : Revue de code statique + navigation fonctionnelle sur données de seed

---

## Résumé exécutif

| Catégorie | Nombre | Répartition |
|-----------|--------|-------------|
| 🔴 **VALEUR CRITIQUE** | 18 | Sécurité, intégrité données, conformité légale |
| 🟠 **FORTE VALEUR AJOUTÉE** | 24 | Business logic, UX structurelle, complétude fonctionnelle |
| 🟢 **GAINS RAPIDES & CONFORT** | 16 | Polish UX, performance, dette technique |
| **Total** | **58** | |

**Verdict** : L'application couvre les cas d'usage courants (loyers, charges, baux, quittances) avec une architecture solide. Cependant, **5 failles de sécurité**, **4 bugs de calcul financier**, et **6 lacunes légales SCI** empêchent toute mise en production auprès de gérants professionnels. Les corrections critiques sont estimées à 2-3 sprints.

---

## 🔴 CATÉGORIE 1 — VALEUR CRITIQUE

> Bloquants pour la mise en production. Risque juridique, financier ou de sécurité.

---

### C01 — Service role key bypass RLS sur toutes les tables

**Constat critique** : `backend/app/core/supabase_client.py:13-15` — Le client Supabase backend utilise globalement la `SUPABASE_SERVICE_ROLE_KEY` (cache `@lru_cache`), qui bypass toutes les policies RLS. Chaque requête DB s'exécute avec des privilèges superadmin.

**Impact utilisateur** : Une seule faille d'autorisation côté API expose l'intégralité des données multi-tenant. Si un endpoint oublie de vérifier `user_id`, il accède aux données de tous les utilisateurs sans que la DB ne fournisse de filet de sécurité.

**Recommandation d'action** : Migrer vers un client per-request initialisé avec le JWT utilisateur pour toutes les opérations de données. Réserver le service client uniquement aux webhooks Stripe et aux opérations admin. Documenter explicitement chaque usage restant du service_role.

**Edge case test** : Appeler `GET /api/v1/scis/{sci_id_autre_user}/biens` avec un JWT valide d'un user A et un `sci_id` appartenant à un user B — vérifier que la réponse est 403, pas les données de B.

---

### C02 — Quittances générées pour les loyers d'un autre utilisateur

**Constat critique** : `backend/app/api/v1/quitus.py:37-59` — `QuitusRequest` accepte `id_loyer` et `id_bien` en clair. L'endpoint authentifie l'utilisateur mais ne vérifie jamais que ces IDs appartiennent à une SCI dont il est membre.

**Impact utilisateur** : N'importe quel utilisateur authentifié peut générer une quittance PDF pour le loyer d'un autre utilisateur en fournissant un `id_loyer` arbitraire. Le PDF contient le nom du locataire, l'adresse du bien, et le montant — données personnelles sensibles.

**Recommandation d'action** : Ajouter une vérification `id_loyer → id_bien → id_sci → associes.user_id = current_user` avant toute génération. Appliquer le même contrôle sur `download_quitus` (L86-110) qui ne vérifie pas non plus l'ownership du fichier.

**Edge case test** : User A génère une quittance avec `id_loyer` de User B → doit retourner 403. Tester aussi le download avec un filename deviné.

---

### C03 — Suppression du dernier gérant d'une SCI autorisée

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/associes/+page.svelte:64-76` — `handleDeleteAssocie` n'a aucun garde-fou contre la suppression du seul gérant. Le backend (`scis_biens.py`) ne vérifie pas non plus.

**Impact utilisateur** : Une SCI sans gérant est juridiquement ingouvernable. Plus personne ne peut modifier, supprimer ou administrer la SCI dans l'application. L'utilisateur perd l'accès à toutes les fonctions de gestion.

**Recommandation d'action** : Backend : avant `DELETE FROM associes`, vérifier `SELECT COUNT(*) FROM associes WHERE id_sci = ? AND role = 'gerant' AND id != ?`. Si count = 0, retourner 400. Frontend : désactiver le bouton trash si l'associé est le seul gérant.

**Edge case test** : SCI avec 1 gérant + 2 associés → supprimer le gérant → doit être refusé. SCI avec 2 gérants → supprimer l'un → doit être autorisé.

---

### C04 — CERFA 2044 généré pour les SCI à l'IS

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/fiscalite/+page.svelte:54-72` — `handleGenerateCerfa()` génère un CERFA 2044 quel que soit le `regime_fiscal` de la SCI. Le CERFA 2044 est le formulaire des revenus fonciers (régime IR). Les SCI à l'IS utilisent la liasse fiscale 2065.

**Impact utilisateur** : Un gérant de SCI à l'IS qui génère et dépose un CERFA 2044 commet une erreur déclarative auprès de l'administration fiscale. Risque de redressement.

**Recommandation d'action** : Conditionner l'affichage du bouton "Générer CERFA 2044" à `sci.regime_fiscal === 'ir'`. Pour les SCI IS, afficher un message explicatif renvoyant vers la liasse 2065 (hors périmètre actuel).

**Edge case test** : SCI avec `regime_fiscal = 'is'` → le bouton CERFA 2044 ne doit pas apparaître. SCI avec `regime_fiscal = null` → afficher un avertissement.

---

### C05 — Quittance utilise le premier loyer payé au lieu du plus récent

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/biens/[bienId]/+page.svelte:82` — `bien.loyers_recents?.find((l: any) => l.statut === 'paye')` retourne le **premier** élément correspondant. Si le tableau est en ordre chronologique, c'est le loyer le plus ancien, pas le plus récent.

**Impact utilisateur** : Le gérant génère une quittance pour janvier 2024 alors qu'il veut celle de février 2026. Le locataire reçoit un document incorrect. Risque de litige.

**Recommandation d'action** : Utiliser `.findLast()` ou inverser le tableau avant `.find()`. Vérifier côté backend que `loyers_recents` est bien trié par `date_loyer DESC`.

**Edge case test** : Bien avec 12 loyers payés → vérifier que la quittance générée correspond au mois le plus récent, pas au plus ancien.

---

### C06 — Noms de colonnes `bail_locataires` incohérents — corruption données colocation

**Constat critique** : `backend/app/api/v1/scis_biens.py` — `create_bien_bail` (L527) insère `{"id_bail": bail_id, "id_locataire": loc_id}` tandis que `attach_locataire_to_bail` (L654) insère `{"bail_id": bail_id, "locataire_id": locataire_id}`. `delete_bail` (L617) utilise `bail_id`. Un des deux chemins d'insertion utilise les mauvais noms de colonnes.

**Impact utilisateur** : Les colocataires ajoutés via `attach` ne sont jamais réellement liés au bail (insert silencieux avec colonnes inexistantes). La suppression d'un bail ne nettoie pas la table de jointure, créant des orphelins.

**Recommandation d'action** : Vérifier les noms de colonnes réels de `bail_locataires` dans la migration 008. Uniformiser tous les endpoints. Ajouter un test d'intégration vérifiant le round-trip insert/select/delete.

**Edge case test** : Créer un bail avec 2 locataires → détacher un locataire → supprimer le bail → vérifier que `bail_locataires` est vide.

---

### C07 — Paywall non appliqué sur création de biens, baux et loyers

**Constat critique** : `backend/app/api/v1/scis_biens.py:132` (create_bien), L481 (create_bail), L401 (create_loyer) — Aucun de ces endpoints n'appelle `SubscriptionService.enforce_limit()`. Seule la création de SCI dans `scis.py` vérifie le quota. `entitlements.py` définit FREE = 2 biens max, mais cette limite n'est jamais vérifiée.

**Impact utilisateur** : Un utilisateur en plan gratuit peut créer un nombre illimité de biens, baux et loyers. Le modèle économique freemium est contourné.

**Recommandation d'action** : Ajouter `enforce_limit(user_id, "biens")` dans `create_sci_bien`. Ajouter les mêmes gardes sur les baux. La policy RLS `sci_member_insert` (migration 001, `WITH CHECK (true)`) autorise aussi la création directe via Supabase JS SDK — envisager un trigger SQL de quota.

**Edge case test** : User free plan → créer 3 biens → le 3e doit être refusé (limite = 2).

---

### C08 — Rentabilité fausse quand frais d'agence en pourcentage

**Constat critique** : `backend/app/api/v1/scis_biens.py:273` — `frais_annuel = sum(f.get("montant_ou_pourcentage", 0) for f in frais_agence)`. Quand `type_frais == "pourcentage"`, la valeur stockée est ex. `7.5` (signifiant 7.5% du loyer). Le calcul traite cette valeur comme 7,50 €.

**Impact utilisateur** : Pour une agence à 7.5% sur un loyer de 1 200 €/mois, le coût réel est 1 080 €/an. Le calcul affiche 7,50 €/an. La rentabilité nette et le cashflow sont **matériellement faux** pour tous les utilisateurs avec frais en pourcentage.

**Recommandation d'action** : Brancher sur `type_frais` : si `"pourcentage"`, calculer `loyer_hc * montant / 100 * 12` ; si `"fixe"`, prendre `montant * 12`. Ajouter une contrainte `Literal["pourcentage", "fixe"]` sur le schéma `FraisAgenceCreate`.

**Edge case test** : Bien avec loyer 1 000 € + frais agence 8% → rentabilité nette doit déduire 960 €/an, pas 8 €/an.

---

### C09 — `DocumentBienEmbed.file_url` ≠ colonne DB `url` — crash fiche bien

**Constat critique** : `backend/app/schemas/fiche_bien.py:42` déclare `file_url: str` mais la table `documents_bien` et `DocumentBienResponse` utilisent `url`. L'endpoint `get_fiche_bien` retourne les documents en dicts bruts → Pydantic tente de construire `DocumentBienEmbed` avec la clé `url` mais attend `file_url` → `ValidationError`.

**Impact utilisateur** : **Toute fiche bien avec au moins un document uploaded crashe** avec une erreur 500. L'onglet Documents de la fiche bien est inaccessible.

**Recommandation d'action** : Renommer `file_url` en `url` dans `DocumentBienEmbed`, ou ajouter un alias Pydantic `Field(alias="url")`.

**Edge case test** : Uploader un document sur un bien → charger la fiche bien → doit retourner 200 avec le document dans la réponse.

---

### C10 — Parts sociales en pourcentage flottant — impossible de constituer un registre légal

**Constat critique** : `supabase/migrations/001_init.sql:37` — `associes.part NUMERIC(5,2)` stocke un pourcentage (ex. 33.33%). Une SCI française enregistre des parts en **nombre entier** (ex. 333 parts sur 1 000). Le modèle actuel ne permet pas d'exprimer 1/3 sans delta (33.33% × 3 = 99.99%, pas 100%).

**Impact utilisateur** : Impossible de générer un registre des associés conforme. Impossible de calculer la valeur exacte d'une part pour une cession. Blocant pour toute fonctionnalité future de cession de parts.

**Recommandation d'action** : Ajouter `sci.nb_parts_total INTEGER`, `sci.valeur_nominale_part NUMERIC(10,2)`, `associes.nb_parts INTEGER`. Conserver `part` comme champ calculé dérivé. Ajouter un trigger ou contrôle applicatif vérifiant `SUM(nb_parts) = nb_parts_total`.

**Edge case test** : 3 associés avec 333+333+334 parts (total 1 000) → la somme doit être exacte. En pourcentage : 33.33+33.33+33.34 = 100.00 sans delta.

---

### C11 — Contrainte UNIQUE loyers inefficace sur NULL `id_locataire`

**Constat critique** : `supabase/migrations/001_init.sql:80` — `UNIQUE (id_bien, id_locataire, date_loyer)`. En SQL, `NULL ≠ NULL`, donc si `id_locataire IS NULL`, plusieurs loyers identiques (même bien, même mois) coexistent sans violation de contrainte.

**Impact utilisateur** : Un gérant peut enregistrer deux fois le même loyer (double-clic, refresh). Les KPIs dashboard, taux de recouvrement et exports CSV comptent les doublons, gonflant artificiellement les revenus déclarés.

**Recommandation d'action** : Remplacer par deux index uniques partiels : `(id_bien, date_loyer) WHERE id_locataire IS NULL` et `(id_bien, id_locataire, date_loyer) WHERE id_locataire IS NOT NULL`. Côté backend, ajouter un check avant insert.

**Edge case test** : Enregistrer le même loyer deux fois pour le même bien/mois sans locataire → le 2e doit être refusé.

---

### C12 — Registre des mouvements de parts absent

**Constat critique** : Aucune table en base. L'article 1865 du Code civil impose l'enregistrement de toute cession de parts sociales. Aucun historique de modification des `associes.part` n'est tracé.

**Impact utilisateur** : Impossible de reconstituer l'historique de propriété d'une SCI. En cas de contrôle fiscal ou de litige entre associés, le gérant ne peut pas prouver la chaîne de cessions.

**Recommandation d'action** : Créer une table `mouvements_parts` (id_sci, date, type [cession/apport/rachat/succession], cédant, cessionnaire, nb_parts, prix, document_url). Lier les modifications d'`associes.nb_parts` à un enregistrement obligatoire dans cette table.

**Edge case test** : Modifier les parts d'un associé → un enregistrement doit être créé dans `mouvements_parts`. Lister l'historique → doit être chronologique et cohérent.

---

### C13 — Registre des AG absent

**Constat critique** : Aucune table en base. Le calendrier fiscal de la page SCI affiche "AG annuelle — 6 mois post-clôture" mais il n'y a nulle part où enregistrer le PV d'AG, les résolutions, ou les votes.

**Impact utilisateur** : Le gérant voit un rappel pour tenir son AG mais l'application ne lui fournit aucun outil pour le faire. Il doit gérer les AG hors application, réduisant la proposition de valeur du SaaS.

**Recommandation d'action** : Créer une table `assemblees_generales` (id_sci, date, type [ordinaire/extraordinaire], ordre_du_jour, pv_url, quorum). Ajouter un onglet "AG" dans la vue SCI.

**Edge case test** : Créer une AG ordinaire pour l'exercice 2025 → vérifier qu'on ne peut pas créer deux AG ordinaires pour le même exercice.

---

### C14 — Bouton "Modifier" de la fiche bien est un dead button

**Constat critique** : `frontend/src/lib/components/fiche-bien/FicheBienHeader.svelte:37-40` — `handleEdit()` affiche un toast "La modification sera disponible prochainement" au lieu d'ouvrir un formulaire. Pourtant `FicheBienIdentite.svelte` implémente déjà un formulaire d'édition inline fonctionnel.

**Impact utilisateur** : Le gérant clique "Modifier" dans le header → reçoit un message d'attente → perd confiance dans l'application. Il doit découvrir par lui-même que l'édition est possible dans l'onglet "Identité" plus bas.

**Recommandation d'action** : Soit le bouton header scrolle vers l'onglet Identité et active le mode édition, soit il ouvre un modal/slide-over reprenant le formulaire de `FicheBienIdentite`. Supprimer le toast "prochainement".

**Edge case test** : Cliquer "Modifier" dans le header → le formulaire d'édition doit être visible et interactif. Vérifier que le save fonctionne.

---

### C15 — JWKS cache race condition + I/O bloquante en async

**Constat critique** : `backend/app/core/security.py:15,38-41` — `_jwks_cache` est un dict mutable partagé, muté dans une fonction appelée depuis des handlers async concurrents. `urlopen` (L38) est un appel bloquant qui gèle l'event loop pendant 10s max.

**Impact utilisateur** : Sous charge concurrente, corruption potentielle du cache JWKS → échecs d'authentification intermittents. L'appel bloquant dégrade les performances pour tous les utilisateurs simultanés.

**Recommandation d'action** : Protéger avec `asyncio.Lock`. Remplacer `urlopen` par `httpx.AsyncClient`. Ajouter un TTL explicite sur le cache.

**Edge case test** : 50 requêtes concurrentes au moment où le cache expire → toutes doivent s'authentifier correctement sans erreur 401 spurieuse.

---

### C16 — Calendrier fiscal hardcode année civile jan-déc

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/+page.svelte:48-66` — Les échéances fiscales (déclaration 2072 le 20 mai, AG le 30 juin) supposent un exercice janvier-décembre. Une SCI peut clôturer à n'importe quelle date.

**Impact utilisateur** : Une SCI clôturant au 30 septembre voit l'échéance AG au 30 juin au lieu du 31 mars (6 mois post-clôture). Le gérant rate potentiellement son échéance légale.

**Recommandation d'action** : Calculer les échéances à partir de `sci.date_cloture_exercice` (champ à ajouter si absent). AG = date_cloture + 6 mois. Déclaration 2072 = variable selon régime.

**Edge case test** : SCI avec clôture au 30/09 → AG doit être affichée au 31/03. SCI avec clôture au 31/12 → AG au 30/06.

---

### C17 — RLS `associes` post-migration 006 : un associé ne voit plus ses co-associés

**Constat critique** : `supabase/migrations/006_fix_associes_rls_recursion.sql` — La correction de la récursion RLS réduit la policy SELECT à `user_id = auth.uid()`. Un associé ne peut plus voir les autres membres de sa propre SCI.

**Impact utilisateur** : Les appels directs au frontend Supabase JS SDK ne retournent que la propre ligne de l'utilisateur. Le backend compense avec le service_role (C01), mais cela crée une dépendance totale au backend pour toute lecture d'associés.

**Recommandation d'action** : Créer une fonction `SECURITY DEFINER` : `get_user_sci_ids()` qui retourne les `id_sci` de l'utilisateur. Utiliser dans la policy : `id_sci IN (SELECT get_user_sci_ids())`.

**Edge case test** : Depuis le frontend JS (sans backend), un associé doit voir tous les co-associés de ses SCI, mais pas ceux des SCI auxquelles il n'appartient pas.

---

### C18 — Dashboard `cashflow_net` mélange toutes les périodes

**Constat critique** : `backend/app/services/dashboard_service.py:169-184` — `cashflow_net = loyers_payes_all_time - charges_total_all_time`. Aucun filtre temporel. Pour une SCI de 3 ans, ce KPI est un cumul sans signification économique.

**Impact utilisateur** : Le gérant voit un cashflow qui augmente chaque mois mécaniquement (accumulation de loyers). Aucune visibilité sur la performance mensuelle ou annuelle réelle.

**Recommandation d'action** : Ajouter un filtre par période (trailing 12 mois par défaut). Afficher les KPIs pour la période sélectionnée. Le dashboard alerts (`L83`) charge aussi tous les loyers sans filtre de date — ajouter `.gte("date_loyer", 90_days_ago)`.

**Edge case test** : SCI avec 3 ans d'historique → le cashflow dashboard doit refléter les 12 derniers mois, pas le cumul total.

---

## 🟠 CATÉGORIE 2 — FORTE VALEUR AJOUTÉE

> Améliorations structurantes pour la crédibilité produit et la confiance utilisateur.

---

### V01 — Statut "Vacant" affiché même quand un bail actif existe

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/biens/+page.svelte:145` — `bien.statut ?? 'vacant'`. Si le backend retourne `statut: null` mais que le bien a un bail actif, l'UI affiche "Vacant".

**Impact utilisateur** : Tous les biens apparaissent comme vacants dans la liste, même ceux avec des locataires et des loyers. Perte de confiance dans les données affichées.

**Recommandation** : Dériver le statut côté backend : `"loue"` si bail actif avec `date_fin > now()`, `"vacant"` sinon. Ou côté frontend : vérifier `bien.bail_actif` avant le fallback.

**Edge case test** : Bien avec bail actif et `statut = null` → doit afficher "Loué", pas "Vacant".

---

### V02 — Undo-toast sur suppression charge/PNO/frais : callback no-op

**Constat critique** : `frontend/src/lib/components/fiche-bien/FicheBienCharges.svelte:39-93` — `onUndo: () => {}` sur les toasts de suppression. L'utilisateur voit "Annuler" mais le clic ne fait rien.

**Impact utilisateur** : Fausse promesse d'annulation. La charge est supprimée même si l'utilisateur clique "Annuler".

**Recommandation** : Implémenter le pattern deferred-delete : stocker l'ID dans un `pendingDelete` state, ne supprimer réellement que sur `onExpire`. `onUndo` retire l'ID du pending.

**Edge case test** : Supprimer une charge → cliquer "Annuler" dans les 5s → la charge doit réapparaître.

---

### V03 — Pas de total des parts sociales sur la page Associés

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/associes/+page.svelte:112-165` — Chaque associé affiche sa part individuelle mais aucune ligne de total.

**Impact utilisateur** : Deux associés à 60% et 20% ne montrent aucune indication que 20% est non attribué. Impossible de vérifier la cohérence juridique du capital.

**Recommandation** : Ajouter une barre de total en bas : `Total : XX% / 100%` avec un indicateur visuel (rouge si ≠ 100%, vert si = 100%).

**Edge case test** : 3 associés : 40% + 30% + 30% = 100% → vert. 2 associés : 60% + 20% = 80% → rouge avec alerte.

---

### V04 — "Inviter un associé" crée un enregistrement local sans envoyer d'email

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/associes/+page.svelte:87-94` — Le bouton "Inviter un associé" crée un associé en base, mais aucun email d'invitation n'est envoyé.

**Impact utilisateur** : L'utilisateur pense avoir invité quelqu'un. La personne invitée ne reçoit rien. L'associé créé n'a aucun `user_id` lié.

**Recommandation** : Renommer en "Ajouter un associé" (honnêteté) ou implémenter le flow d'invitation réel (email via Resend → lien d'activation → liaison du `user_id`).

**Edge case test** : Créer un associé → vérifier qu'aucun email n'est envoyé → vérifier que le label est cohérent avec le comportement.

---

### V05 — Documents quick-link compte `fiscalite.length` au lieu des documents

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/+page.svelte:180` — `value: sci.fiscalite?.length ?? 0` est utilisé pour le compteur Documents.

**Impact utilisateur** : Le compteur affiche "3" (3 exercices fiscaux) au lieu de "10" (10 documents uploadés).

**Recommandation** : Remplacer par `sci.documents?.length ?? 0` ou ajouter un champ `documents_count` dans la réponse API SCI.

**Edge case test** : SCI avec 0 exercices fiscaux et 5 documents → le compteur doit afficher 5.

---

### V06 — Export CSV portfolio-wide placé dans la page SCI-scoped

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/+page.svelte:89-127` — Les boutons "Exporter les biens (CSV)" et "Exporter les loyers (CSV)" appellent des endpoints qui exportent **toutes les SCI**, pas seulement la SCI courante.

**Impact utilisateur** : Le gérant multi-SCI qui exporte depuis la SCI "Les Tilleuls" reçoit aussi les données de sa SCI "Résidence du Parc". Confusion et risque de diffusion de données à un comptable qui ne gère qu'une SCI.

**Recommandation** : Ajouter un paramètre `?sci_id=` aux endpoints d'export backend. Passer le `sciId` courant dans les appels frontend.

**Edge case test** : User avec 3 SCI → exporter depuis SCI #2 → le CSV ne doit contenir que les biens/loyers de SCI #2.

---

### V07 — Pas de création de nouveau bail quand un bail expiré existe

**Constat critique** : `frontend/src/lib/components/fiche-bien/FicheBienBail.svelte:57-65` — Le bouton "Créer un bail" n'apparaît que si `!bail`. Quand un bail expiré ou résilié existe, seul "Modifier" est disponible.

**Impact utilisateur** : Le gérant qui veut relouer un bien après départ du locataire ne peut pas créer un nouveau bail. Il est forcé de modifier l'ancien bail (ce qui efface l'historique).

**Recommandation** : Afficher "Créer un bail" quand `bail.statut !== 'en_cours'`. Archiver l'ancien bail au lieu de le modifier.

**Edge case test** : Bien avec bail expiré → le bouton "Créer un bail" doit être visible. Créer un nouveau bail → l'ancien doit être archivé.

---

### V08 — Duplication de loyers non détectée

**Constat critique** : `backend/app/api/v1/scis_biens.py:401-428` — `create_bien_loyer` insère sans vérifier l'existence d'un loyer pour le même `(id_bien, date_loyer)`. Combiné avec C11 (contrainte UNIQUE inefficace sur NULL), les doublons sont possibles.

**Impact utilisateur** : Double-clic ou retry réseau → deux loyers identiques. Les KPIs et taux de recouvrement sont gonflés.

**Recommandation** : Backend : `SELECT EXISTS` avant insert. Si doublon, retourner 409 Conflict. Frontend : désactiver le bouton submit pendant l'appel.

**Edge case test** : Envoyer deux requêtes POST identiques simultanément → une seule doit réussir.

---

### V09 — Résultat fiscal naïf (revenus - charges) — non conforme CERFA

**Constat critique** : `backend/app/api/v1/fiscalite.py:89-90` — `resultat_fiscal = total_revenus - total_charges`. Pour une SCI IR, le CERFA 2044 exige : déductions forfaitaires (micro-foncier 30%), amortissements (LMNP), quote-parts par associé, et report déficitaire.

**Impact utilisateur** : Le résultat fiscal affiché est faux pour les SCI en micro-foncier et pour toute SCI avec des reports. Le gérant qui se fie à ce chiffre risque une erreur déclarative.

**Recommandation** : Phase 1 : ajouter un disclaimer "Résultat simplifié — consultez votre comptable". Phase 2 : implémenter les régimes IR micro-foncier et réel.

**Edge case test** : SCI IR avec revenus < 15 000 € → le micro-foncier (abattement 30%) doit être applicable. Vérifier que le résultat != revenus - charges.

---

### V10 — Suppression SCI sans information sur les cascades

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/+page.svelte:218-225` — Le modal de suppression ne liste pas le nombre de biens, baux, loyers et documents qui seront supprimés en cascade.

**Impact utilisateur** : Un gérant supprimant une SCI avec 20 biens et 200 loyers reçoit le même avertissement qu'une SCI vide. Risque de perte de données massive sans prise de conscience.

**Recommandation** : Avant confirmation, afficher : "Cette action supprimera X biens, Y baux, Z loyers et W documents." Requêter les compteurs via un endpoint dédié.

**Edge case test** : SCI avec 5 biens → le modal doit afficher "5 biens seront supprimés". SCI vide → afficher "Aucune donnée liée".

---

### V11 — Suppression SCI ne nettoie pas locataires et bail_locataires

**Constat critique** : `backend/app/api/v1/scis.py:368-386` — Le cascade delete supprime charges, loyers, baux, documents, PNO, frais. Mais `locataires` et `bail_locataires` ne sont pas supprimés.

**Impact utilisateur** : Données orphelines en base. Pas d'impact visible immédiat, mais accumulation de données inaccessibles.

**Recommandation** : Ajouter `locataires` et `bail_locataires` dans le cascade delete. Idéalement, configurer `ON DELETE CASCADE` au niveau SQL.

**Edge case test** : Supprimer une SCI → vérifier que `SELECT * FROM locataires WHERE id_bien IN (biens de la SCI)` retourne 0 ligne.

---

### V12 — Timezone bug sur le label de période de quittance

**Constat critique** : `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte:64-71` — `new Date(dateLoyer)` est timezone-sensitive. "2025-01-01" parsé en UTC-1 → 31 décembre 2024.

**Impact utilisateur** : La quittance affiche "Décembre 2024" au lieu de "Janvier 2025". Document juridique incorrect.

**Recommandation** : Utiliser `new Date(dateLoyer + 'T12:00:00')` ou parser manuellement les composantes `YYYY-MM-DD`.

**Edge case test** : Loyer avec `date_loyer = "2025-01-01"` → en timezone UTC-X → la période doit afficher "Janvier 2025".

---

### V13 — Pas de validation durée minimale de bail selon type locatif

**Constat critique** : Le `BailModal` accepte toute durée sans vérifier : bail nu = 3 ans min (loi 6 juillet 1989), meublé = 1 an min, commercial = 9 ans. Le `type_locatif` du bien n'est pas croisé lors de la création du bail.

**Impact utilisateur** : Un gérant peut créer un bail nu de 6 mois, ce qui est illégal. Le locataire pourrait contester le bail.

**Recommandation** : Frontend : validation croisée `type_locatif` × durée. Backend : validator Pydantic dans `BailCreate`.

**Edge case test** : Bien type "nu" → bail de 2 ans → doit être refusé. Bail de 3 ans → doit être accepté.

---

### V14 — CFE affiché pour toutes les SCI

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/+page.svelte:58` — L'échéance CFE est inconditionnellement affichée. Les SCI avec uniquement des biens résidentiels non meublés gérés directement sont généralement exonérées de CFE.

**Impact utilisateur** : Le gérant d'une SCI familiale classique voit une échéance CFE qui ne le concerne pas. Confusion et potentiellement paiement inutile d'un impôt non dû.

**Recommandation** : Conditionner l'affichage CFE au `type_locatif` des biens (meublé/commercial → CFE applicable ; nu résidentiel → exonéré possible).

**Edge case test** : SCI avec uniquement des biens nus résidentiels → pas de CFE affiché. SCI avec au moins un meublé → CFE affiché.

---

### V15 — Quittance PDF sans accents français

**Constat critique** : `backend/app/services/quitus_service.py:55-72` — Les chaînes comme "Montant acquitte", "Nous attestons avoir recu", "situe" sont sans accents. ReportLab Helvetica ne supporte pas les caractères accentués UTF-8.

**Impact utilisateur** : Document juridique avec des fautes d'orthographe. Perception d'amateurisme.

**Recommandation** : Enregistrer une police avec support Latin-1 complet (ex: DejaVu Sans) dans ReportLab. Corriger toutes les chaînes.

**Edge case test** : Générer une quittance → vérifier que "acquitté", "reçu", "situé" sont correctement accentués dans le PDF.

---

### V16 — Onboarding : création séquentielle de lots bloque l'UI

**Constat critique** : `frontend/src/routes/(app)/onboarding/+page.svelte:144-163` — La boucle `for (let i = 0; i < lotsToCreate; i++) { await createBien() }` exécute N appels API séquentiellement.

**Impact utilisateur** : Créer 20 lots d'un immeuble → 20 appels séquentiels → 20-40 secondes de blocage. L'utilisateur pense que l'app a planté.

**Recommandation** : Utiliser `Promise.all()` avec un batch de 5 maximum pour respecter les rate limits.

**Edge case test** : Créer 10 lots → mesurer le temps total → doit être < 5s (vs ~20s en séquentiel).

---

### V17 — `confirm()` / `alert()` natifs pour les suppressions — incohérent

**Constat critique** : `biens/+page.svelte:40-48`, `associes/+page.svelte:65` — Les dialogues de suppression utilisent `window.confirm()` et `window.alert()` natifs (non stylisés). Le reste de l'app utilise des modals/toasts stylisés.

**Impact utilisateur** : Rupture visuelle. Le dialogue natif n'est pas traduit en français sur tous les navigateurs. Pas de dark mode.

**Recommandation** : Remplacer par un composant `ConfirmDialog.svelte` réutilisable (existe peut-être déjà dans `ui/`).

**Edge case test** : Supprimer un bien en dark mode → le dialogue doit respecter le thème. Vérifier que le texte est en français.

---

### V18 — Plan key résolu par substring matching sur `stripe_price_id`

**Constat critique** : `backend/app/core/entitlements.py:167-171` — `if "pro" in price_lower: return PlanKey.PRO`. Un `stripe_price_id` contenant "promo" ou "prototype" match en PRO.

**Impact utilisateur** : Si une campagne Stripe crée un price_id contenant "pro" (ex: "price_promo_2026"), les utilisateurs de ce plan obtiennent les features PRO.

**Recommandation** : Supprimer le fallback substring. Ne résoudre que via la map explicite `STRIPE_PRICE_TO_PLAN`.

**Edge case test** : Price ID "price_promo_spring_2026" → ne doit PAS être résolu en PRO.

---

### V19 — Onboarding race condition : `free` row écrase `active` subscription

**Constat critique** : `backend/app/api/v1/onboarding.py:148-150` — `complete_onboarding` insère `status: "free"`. Si le webhook Stripe n'a pas encore créé la row, et l'utilisateur finit l'onboarding, la row `free` est insérée. Le webhook tentera ensuite un upsert conflictuel.

**Impact utilisateur** : Un utilisateur qui paie puis complète l'onboarding rapidement peut se retrouver en plan free malgré son paiement.

**Recommandation** : Vérifier si une subscription existe avant insert. Si oui, ne pas écraser. Utiliser `ON CONFLICT (user_id) DO UPDATE SET onboarding_completed = true`.

**Edge case test** : Payer → compléter l'onboarding avant le webhook → vérifier que le plan reste `active`, pas `free`.

---

### V20 — SIREN non validé en onboarding (vs settings qui valide)

**Constat critique** : `frontend/src/routes/(app)/onboarding/+page.svelte:318-327` — Input SIREN sans `pattern`, `maxlength` ni masque. La page Settings utilise `pattern="\d{9}" maxlength="9"`.

**Impact utilisateur** : Un utilisateur peut saisir "ABC" comme SIREN en onboarding. Incohérence entre les deux formulaires.

**Recommandation** : Appliquer les mêmes contraintes dans les deux formulaires. Idéalement, un composant `SirenInput.svelte` réutilisable.

**Edge case test** : Saisir "ABC" en SIREN → doit être refusé. Saisir "12345678" (8 chiffres) → doit être refusé.

---

### V21 — Résultat fiscal `null` affiché comme `0,00 €`

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/fiscalite/+page.svelte:383` — `formatEur(ex.resultat_fiscal ?? 0)`. Un résultat non calculé (null) apparaît comme 0,00 €.

**Impact utilisateur** : Le gérant croit que le résultat fiscal est nul au lieu de non renseigné. Risque de décision fiscale incorrecte.

**Recommandation** : Afficher `—` ou "Non calculé" quand la valeur est null.

**Edge case test** : Exercice sans données → afficher "—". Exercice avec `resultat_fiscal = 0` → afficher "0,00 €".

---

### V22 — Policy UPDATE manquante sur `documents_bien`

**Constat critique** : `supabase/migrations/008_ux_redesign_v2.sql:344-374` — La table a des policies SELECT, INSERT, DELETE mais pas UPDATE.

**Impact utilisateur** : Impossible de renommer un document ou changer sa catégorie via le frontend avec JWT utilisateur.

**Recommandation** : Ajouter une policy UPDATE avec vérification du rôle gérant.

**Edge case test** : Renommer un document en tant que gérant → doit réussir. En tant qu'associé → doit échouer.

---

### V23 — `BailCreate.locataire_ids` typé `list[int]` mais DB utilise UUID

**Constat critique** : `backend/app/schemas/baux.py:16` — `locataire_ids: list[int] = []`. Les IDs Supabase sont des UUID (strings).

**Impact utilisateur** : L'ajout de locataires lors de la création d'un bail échoue si les IDs sont des UUID (validation Pydantic rejette les strings).

**Recommandation** : Changer en `list[str]` ou `list[UUID]`.

**Edge case test** : Créer un bail avec un `locataire_id` UUID → doit être accepté.

---

### V24 — N+1 API calls sur la page Documents SCI

**Constat critique** : `frontend/src/routes/(app)/scis/[sciId]/documents/+page.svelte:58` — Fetch tous les biens, puis pour chaque bien, fetch ses documents séquentiellement.

**Impact utilisateur** : SCI avec 20 biens → 21 appels API séquentiels → page lente (5-10s de chargement).

**Recommandation** : Créer un endpoint `/api/v1/scis/{sciId}/documents` qui retourne tous les documents d'une SCI en une requête.

**Edge case test** : SCI avec 15 biens → la page documents doit charger en < 2s.

---

## 🟢 CATÉGORIE 3 — GAINS RAPIDES & CONFORT

> Améliorations rapides qui polissent l'expérience sans risque.

---

### G01 — Accents manquants dans l'UI (Dashboard, Finances, toasts)

**Constat** : "Activite recente", "Creer une SCI", "Export termine" — dizaines de chaînes sans accents.

**Recommandation** : Grep global `"Activite\|recente\|Creer\|termine\|telecharge\|Reessayer"` → corriger. Batch de 30 min.

---

### G02 — `window.location.reload()` après save Settings

**Constat** : `settings/+page.svelte:44` — Hard reload au lieu de `invalidateAll()`.

**Recommandation** : Remplacer par `invalidateAll()` + toast de confirmation. 5 min.

---

### G03 — SCI switcher dropdown ne se ferme pas au clic extérieur

**Constat** : `AppSidebarV2.svelte:175-200` — Pas de click-outside handler.

**Recommandation** : Ajouter un `use:clickOutside` action Svelte. 15 min.

---

### G04 — Navigation par onglets fiche bien ne suit pas le scroll

**Constat** : `biens/[bienId]/+page.svelte:67-75` — L'onglet actif ne se met à jour qu'au clic, pas au scroll.

**Recommandation** : Ajouter un `IntersectionObserver` sur chaque section. 30 min.

---

### G05 — `#loyers` anchor sur la quittance action ne scrolle pas

**Constat** : `biens/+page.svelte:229-234` — Le lien `/biens/{id}#loyers` ne trigger pas de scroll sur la page cible.

**Recommandation** : Ajouter `onMount(() => { if (window.location.hash) scrollToSection(hash) })` dans la fiche bien.

---

### G06 — Sidebar SCI list non rafraîchie après création d'une SCI

**Constat** : `AppSidebarV2.svelte:39-51` — Refresh uniquement sur navigation vers `/scis` ou `/dashboard`.

**Recommandation** : Écouter un event store `sciCreated` pour trigger le refresh. 15 min.

---

### G07 — Mobile sidebar sans `role="dialog"` ni `aria-hidden`

**Constat** : `AppSidebarV2.svelte:124-128` — Manque d'attributs ARIA pour l'accessibilité mobile.

**Recommandation** : Ajouter `role="dialog"`, `aria-modal="true"`, `aria-hidden` conditionnel. 10 min.

---

### G08 — Boutons icônes associés sans `aria-label`

**Constat** : `associes/+page.svelte:141-158` — Pencil/Trash ont `title` mais pas `aria-label`.

**Recommandation** : Ajouter `aria-label="Modifier l'associé"` / `aria-label="Supprimer l'associé"`. 5 min.

---

### G09 — Finances : noms SCI non cliquables dans la table répartition

**Constat** : `finances/+page.svelte:313-328` — Les noms SCI sont en texte brut, pas en liens.

**Recommandation** : Wrapper dans `<a href="/scis/{sci.id}">`. 5 min.

---

### G10 — Finances : export ignore le filtre période

**Constat** : `finances/+page.svelte:25-43` — Le bouton export exporte toujours tout, même quand le sélecteur montre "6 mois".

**Recommandation** : Passer le paramètre `period` à l'endpoint d'export. 20 min.

---

### G11 — Pas de vérification de doublon exercice fiscal par année

**Constat** : `fiscalite/+page.svelte:81-99` — Aucune vérification client-side que l'année n'existe pas déjà.

**Recommandation** : Vérifier dans la liste existante avant submit. Idéalement, unique constraint `(id_sci, annee)` en DB.

---

### G12 — `FicheBienRentabilite` false positive sur `isAllZero`

**Constat** : `FicheBienRentabilite.svelte:12-17` — Un bien avec `prix_acquisition = 0` et `cashflow = 0` (charges = loyer) affiche le warning "Renseignez le prix d'acquisition" même quand tout est saisi.

**Recommandation** : Distinguer "pas de données" de "données = 0". Vérifier si les champs source sont null vs 0.

---

### G13 — `BailCreate` : pas de validation `date_fin > date_debut`

**Constat** : `backend/app/schemas/baux.py:9-16` — Aucun cross-field validator.

**Recommandation** : Ajouter `@model_validator` dans `BailCreate`. 10 min.

---

### G14 — Dashboard KPI : icône recouvrement ambrée quand `noLoyers = true`

**Constat** : `DashboardKpis.svelte:56-64` — L'icône couleur est calculée même sans données.

**Recommandation** : Si `noLoyers`, forcer la couleur neutre (slate). 5 min.

---

### G15 — `selectSci()` dans sidebar : paramètre `sciId` jamais utilisé

**Constat** : `AppSidebarV2.svelte:92-95` — Dead code.

**Recommandation** : Supprimer le paramètre inutile ou implémenter la navigation programmée. 5 min.

---

### G16 — `biens` typé `Array<any>` — perte de type safety

**Constat** : `biens/+page.svelte:18` — `let biens: Array<any> = $state([])`.

**Recommandation** : Typer avec l'interface `Bien` existante ou créer un type `BienListItem`. 15 min.

---

## Annexe — Tableau récapitulatif par priorité de fix

| # | ID | Catégorie | Temps estimé | Risque si non corrigé |
|---|----|-----------|--------------|-----------------------|
| 1 | C09 | 🔴 | 5 min | Crash 500 sur toute fiche bien avec documents |
| 2 | C06 | 🔴 | 30 min | Corruption données colocations |
| 3 | C02 | 🔴 | 1h | Fuite de données sensibles (quittances) |
| 4 | C05 | 🔴 | 5 min | Quittances avec mauvaise période |
| 5 | C07 | 🔴 | 2h | Paywall contourné — perte de revenus |
| 6 | C08 | 🔴 | 30 min | Rentabilité fausse pour tous les users avec % frais |
| 7 | C03 | 🔴 | 30 min | SCI ingouvernable après suppression gérant |
| 8 | C04 | 🔴 | 10 min | CERFA incorrect → redressement fiscal |
| 9 | C14 | 🔴 | 15 min | Dead button → perte de confiance utilisateur |
| 10 | C11 | 🔴 | 1h | Doublons loyers → KPIs faux |
| 11 | C01 | 🔴 | 3-5j | Architecture sécurité fondamentale |
| 12 | C15 | 🔴 | 2h | Auth intermittente sous charge |
| 13 | C18 | 🔴 | 1h | KPI cashflow sans signification |
| 14 | C10 | 🔴 | 2h | Registre associés non conforme |
| 15 | C12 | 🔴 | 3h | Obligation légale non couverte |
| 16 | C13 | 🔴 | 4h | Obligation légale non couverte |
| 17 | C16 | 🔴 | 1h | Échéances légales incorrectes |
| 18 | C17 | 🔴 | 2h | RLS contournée pour requêtes directes |

---

*Rapport généré automatiquement par le comité d'audit expert — GererSCI v1.0*
*Prochain audit recommandé : après correction des items 🔴 (sprint 1-2)*
