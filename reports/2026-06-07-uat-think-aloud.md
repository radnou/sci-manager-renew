# Rapport de Simulation UAT & d'Audit de Personas — GérerSCI
**Date d'évaluation** : 7 juin 2026  
**Comité d'Évaluation UAT** : Cabinets WEST (UX, Design & Rétention), ALPINE (Conformité, Gestion & Règle Métier) et EAST (Performance, Accessibilité & Anti-erreur)  
**Produit** : GérerSCI SaaS (FastAPI backend / SvelteKit 5 frontend / Supabase PostgreSQL)  

---

## 1. Introduction et Méthodologie d’Évaluation

L'évaluation de la maturité et de l'utilisabilité de la plateforme **GérerSCI** a été menée conjointement par trois cabinets de test fictifs mais hautement spécialisés, simulant les comportements d'utilisateurs réels dans des contextes B2B et B2C :

*   **Cabinet WEST (Focus "Wow & Friction")** : Analyse l'engagement émotionnel, la clarté visuelle, la navigation esthétique, l'effet "Aha!" à la première utilisation, et traque les moindres frustrations d'interface (le "choc visuel", les boutons fantômes, les animations lentes).
*   **Cabinet ALPINE (Focus "Conformité Légale & Métier")** : Examine la justesse des calculs financiers, la conformité légale vis-à-vis du droit français des sociétés (SCI IR/IS, cessions de parts, obligations d'AG, calcul de rentabilité déduisant les frais réels), l'intégrité de la base de données et la rigueur de l'onboarding.
*   **Cabinet EAST (Focus "Speed, Accessibilité & Anti-Erreur / Poka-Yoke")** : Analyse la vitesse d'exécution, la résilience aux pannes (offline), l'accessibilité au clavier (WCAG 2.1 AA), et teste la robustesse du système face aux erreurs humaines involontaires (le "Troll testing") par la mise en place de dispositifs de détrompage (*Poka-Yoke*).

---

## 2. Fiches Personas Détaillées

### Persona 1 : Jean-Pierre (Le Technophobe Impatient)
*   **Profil** : 62 ans, retraité, gérant d'une SCI familiale possédant 2 appartements à Lyon.
*   **Aisance Numérique** : Très faible. Utilise principalement un vieil ordinateur portable. Hésitant face aux applications modernes, craint de faire une bêtise ou de perdre ses données.
*   **Objectif principal** : Abandonner ses fichiers Excel mal formatés pour éditer facilement ses quittances de loyer mensuelles et ne plus oublier ses déclarations fiscales.
*   **Attentes** : Pas de jargon anglais, de gros boutons clairs, des confirmations à chaque étape et un guidage pas à pas.
*   **Facteur critique de succès** : Pouvoir générer une quittance correcte en moins de 3 clics après l'inscription.

### Persona 2 : Sarah (La Travailleuse sous Pression)
*   **Profil** : 38 ans, cadre supérieure dans la finance, investisseuse active possédant 8 biens (appartements et parking) répartis sur 3 SCI.
*   **Aisance Numérique** : Très élevée. Gère sa vie sur son smartphone, souvent en déplacement ou dans le métro.
*   **Objectif principal** : Piloter ses flux financiers à la volée, valider les loyers reçus dès réception de la notification de virement bancaire, et suivre son cashflow mensuel global.
*   **Attentes** : Vitesse de chargement instantanée, design mobile-first sans perte de lisibilité, KPIs denses et concis, pas de modale bloquante nécessitant un grand écran.
*   **Facteur critique de succès** : Renseigner un paiement de loyer et envoyer la quittance par email au locataire en moins de 30 secondes depuis son smartphone dans les transports.

### Persona 3 : Lucas (Le Troll Involontaire)
*   **Profil** : 29 ans, graphiste free-lance, s'occupe de la gestion de la SCI familiale pour soulager ses parents âgés.
*   **Aisance Numérique** : Moyenne-haute. Très chaotique. Navigue en multi-onglets, double-clique de manière compulsive sur les boutons de validation, recharge la page pendant les chargements et ignore les champs d'aide.
*   **Objectif principal** : Saisir rapidement les données de la SCI sans lire les instructions.
*   **Attentes** : Un système qui tolère les erreurs de saisie (SIRET incomplet, dates de bail inversées), empêche les doublons accidentels et ne crashe jamais en cas de mauvaise manipulation.
*   **Facteur critique de succès** : Ne pas corrompre la base de données ou créer des écritures comptables fantômes malgré des clics répétés sur "Enregistrer".

### Persona 4 : Valérie (L'Utilisatrice Métier Principale / Experte B2B)
*   **Profil** : 45 ans, gérante d'un cabinet de gestion comptable avec 15 SCI sous mandat de ses clients.
*   **Aisance Numérique** : Élevée sur les progiciels professionnels, exigeante sur les détails comptables.
*   **Objectif principal** : Centraliser le suivi de ses portefeuilles clients, générer des CERFA 2044 fiables sans retouches manuelles, et exporter les bilans au format comptable propre (FEC/CSV).
*   **Attentes** : Rigueur absolue dans les calculs financiers (gestion des frais d'agence en pourcentage vs forfait, amortissements, proratas de charges), suivi des parts sociales en nombre entier pour le registre juridique.
*   **Facteur critique de succès** : La génération d'un CERFA 2044 dont les totaux de revenus et de charges correspondent exactement, au centime près, aux bilans financiers des biens de la SCI.

### Persona 5 : Thomas (Le Sceptique/Manager B2B)
*   **Profil** : 52 ans, chef d'entreprise d'une PME de Bâtiment, gérant d'une SCI de locaux professionnels (IS).
*   **Aisance Numérique** : Moyenne. Très attentif aux coûts, à la rentabilité et à la conformité juridique.
*   **Objectif principal** : Vérifier la valeur ajoutée de la formule à 39€/mois par rapport à un comptable externe et s'assurer que ses données professionnelles sont sécurisées et exportables.
*   **Attentes** : Transparence sur le pricing, gestion autonome de son abonnement via Stripe, conformité RGPD irréprochable (exportation et suppression en 1 clic), et clarté sur la garantie satisfait ou remboursé.
*   **Facteur critique de succès** : La possibilité de tester l'outil avec des données réalistes (démo) sans barrière de carte bleue, suivie d'une facturation claire avec accès immédiat au portail de résiliation.

### Persona 6 : Karim (L'Edge Case Technique)
*   **Profil** : 34 ans, ingénieur logiciel DevOps, propriétaire de 3 biens en location meublée gérés en SCI.
*   **Aisance Numérique** : Expert. N'utilise pas la souris (uniquement clavier/Vimium), a configuré son système en mode sombre par défaut, navigue avec un bloqueur de scripts et surveille la console réseau.
*   **Objectif principal** : Automatiser sa gestion et utiliser une interface rapide, accessible et propre techniquement.
*   **Attentes** : Pas de dégradation d'API en cas de coupure réseau temporaire, support parfait de l'accessibilité ARIA, gestion stricte des timezones (pas de loyer daté du 31/12 au lieu du 01/01 à cause de décalages UTC), pas d'erreurs 402 ou 500 silencieuses dans la console.
*   **Facteur critique de succès** : Naviguer de l'onboarding au dashboard en 0 clic de souris, avec une console de dev restée vierge de tout warning ou erreur.

---

## 3. Grille d'Évaluation : Features x Cabinets

Cette grille évalue les fonctionnalités clés de la version actuelle de GérerSCI selon les prismes spécifiques des trois cabinets, attribuant une note globale sur 20.

| Fonctionnalité | Cabinet WEST (Wow/Friction) | Cabinet ALPINE (Compliance/Légal) | Cabinet EAST (Vitesse/Anti-Erreur) | Note Globale | Verdict & Actions Correctives |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **Inscription & Welcome (Demo Seed)** | **Wow** : Le passage direct au chargement d'une démo interactive avec barre de progression animée est bluffant.<br>**Friction** : Aucun bouton pour passer la démo immédiatement si on veut saisir ses données. | **Rigueur** : Données fictives bien structurées. Le SIREN de démo doit être unique en DB pour éviter les collisions.<br>**Biais** : Nettoyage de la démo post-achat à tester pour éviter la pollution. | **Vitesse** : L'API `/api/v1/demo/seed` s'exécute en tâche de fond. Si elle échoue, l'interface propose un bouton "Réessayer" au lieu de crasher. | **17/20** | **Validé**. Ajouter une option "Sauter l'animation de démo" pour les utilisateurs pressés. |
| **Wizard Onboarding (5 étapes)** | **Wow** : Questionnaire initial ludique et progressif.<br>**Friction** : La séparation en sous-étapes pour l'adresse d'un bien ajoute des clics inutiles. | **Rigueur** : Saisie des champs légaux optionnelle mais complète (RCS, capital, gérant).<br>**Erreur** : Pas de validation du format du SIRET à l'étape 2. | **Vitesse** : Création de biens multiples (ex: immeuble de lots) gérée en batchs asynchrones (Promise.all) pour éviter le blocage de l'UI. | **15/20** | **Améliorable**. Intégrer un validateur de SIREN (9 chiffres) en temps réel dès l'onboarding. |
| **Multi-SCI Dashboard** | **Wow** : Cartes graphiques élégantes en mode sombre, vue d'ensemble du cashflow.<br>**Friction** : La liste d'activité récente est statique (non cliquable). | **Erreur** : Le KPI `cashflow_net` calcule un cumul historique total sans filtre temporel, ce qui n'a aucun sens pour le pilotage financier annuel. | **Vitesse** : Chargement rapide.<br>**Détrompage** : Les icônes de statut de recouvrement s'affichent en Slate neutre si aucun loyer n'est enregistré (au lieu d'un faux avertissement). | **14/20** | **À corriger**. Ajouter un filtre temporel (ex: 12 derniers mois glissants) sur les calculs de cashflow du dashboard. |
| **Fiche Bien (10 onglets)** | **Wow** : Centralisation complète (Bail, Loyers, Charges, PNO, Rentabilité).<br>**Friction** : Le bouton "Modifier" du header est un lien mort ("bientôt disponible") alors que l'édition inline marche plus bas. | **Rigueur** : La rentabilité brute/nette est calculée. Cependant, si le prix d'acquisition n'est pas renseigné, le message explicatif doit être plus clair. | **Vitesse** : Navigation rapide par onglets.<br>**Erreur** : Pas de navigation par flèches clavier entre les onglets (violation WCAG). | **13/20** | **Moyen**. Rendre le bouton "Modifier" actif en scrollant directement vers l'onglet "Identité" en mode édition. |
| **Baux & Locataires** | **Wow** : Formulaire clair de rattachement d'un bail.<br>**Friction** : Impossible de créer un nouveau bail si un ancien bail expiré existe déjà. | **Rigueur** : Pas de validation croisée de la durée légale minimale de bail selon le type locatif (3 ans pour nu, 1 an pour meublé). | **Erreur** : Risque d'avoir des locataires orphelins en base lors de la suppression d'un bien (jointure non purgée). | **11/20** | **Friction forte**. Permettre l'archivage d'un bail précédent pour autoriser la création d'un nouveau, et appliquer des règles de durée minimale. |
| **Loyers & Quittances PDF** | **Wow** : Enregistrement d'un loyer payé en 2 clics. Génération de quittance PDF immédiate.<br>**Friction** : La quittance utilise parfois le loyer le plus ancien si le tri chronologique est inversé. | **Rigueur** : PDF propre mais sans accents français sur les lettres clés ("Montant acquitte" au lieu de "Montant acquitté"). Helvetica par défaut.<br>**Sécurité** : Endpoint de téléchargement non sécurisé par ownership. | **Vitesse** : Génération asynchrone rapide.<br>**Timezone** : Risque de bug de décalage de date de loyer à cause du timezone parsing du navigateur (UTC-1). | **12/20** | **Insuffisant**. Corriger l'encodage et la police du PDF pour supporter les accents, trier par date décroissante pour la quittance récente, sécuriser l'accès. |
| **Charges, Agence & PNO** | **Wow** : Visualisation simple de la répartition des charges.<br>**Friction** : Les callbacks "Annuler" (Undo) sur la suppression des charges sont des no-ops (ne font rien). | **Erreur** : Calcul de rentabilité faussé si les frais d'agence sont saisis en pourcentage (ex: 7.5% est traité comme 7.50 € par an). | **Détrompage** : Les types de charges et dates d'échéance PNO sont bien typés. | **10/20** | **Alerte**. Corriger immédiatement le calcul des frais d'agence en pourcentage (convertir en valeur absolue annuelle par rapport au loyer). |
| **Module Fiscalité** | **Wow** : Le simulateur CERFA 2044 public est un excellent outil d'acquisition.<br>**Friction** : L'accès aux fonctionnalités avancées est restreint pour le plan gratuit. | **Erreur** : Permet de générer un CERFA 2044 pour des SCI enregistrées sous le régime IS, ce qui est une grave anomalie légale (IS = liasse 2065). | **Vitesse** : Rapide.<br>**Console** : Le paywall déclenchait une erreur 402 bruyante dans la console de dev (corrigé depuis). | **14/20** | **À corriger**. Masquer ou désactiver le bouton de génération du CERFA 2044 si le régime fiscal de la SCI sélectionnée est configuré sur IS. |
| **Gouvernance & AG** | **Wow** : Registre des assemblées générales propre et partagable.<br>**Friction** : Les parts sociales sont stockées en pourcentage flottant (NUMERIC 5,2) empêchant un registre d'associés légal (parts en nombres entiers). | **Rigueur** : Pas de registre d'historique de mouvement des parts (obligations de l'article 1865 du Code civil). | **Détrompage** : Pas de garde-fou contre la suppression du dernier gérant de la SCI, ce qui la rend juridiquement ingouvernable. | **09/20** | **Alerte légale**. Stocker les parts en nombre entier de parts sociales (ex: 333 / 1000) et bloquer la suppression du dernier gérant actif. |
| **Stripe & Pricing** | **Wow** : Parcours d'achat sans accroc avec récapitulatif complet et modale de consentement conforme à l'art. L221-28.<br>**Friction** : Pas de période d'essai (choix "Full Steak" justifié par la démo). | **Rigueur** : Tarification claire de 19€/mois (starter) et 39€/mois (pro), abonnements synchronisés.<br>**Sécurité** : Webhooks sécurisés et idempotents en base. | **Vitesse** : Redirection instantanée vers Stripe.<br>**Erreur** : Si le catalogue Stripe sur le VPS tombe en panne, le healthcheck de production renvoie une erreur 503 propre. | **18/20** | **Excellent**. L'intégration Stripe et la gestion de la monétisation respectent pleinement les critères Big4 de mise en production. |
| **Exports & Imports CSV** | **Wow** : Boutons d'exports bien visibles.<br>**Friction** : L'export dans la vue SCI d'ensemble télécharge en réalité les données de toutes les SCI de l'utilisateur (fuite de contexte). | **Rigueur** : Fichiers CSV contenant des UUIDs techniques bruts au lieu des noms lisibles des biens ou des SCI. | **Vitesse** : Génération asynchrone rapide.<br>**Erreur** : Le modèle d'import CSV n'a pas de gestion d'erreur granulaire en cas de ligne corrompue. | **11/20** | **À revoir**. Restreindre l'export CSV à la SCI courante en passant le paramètre `sci_id`, et remplacer les UUIDs par des libellés dans les exports. |
| **Résilience Hors Ligne** | **Wow** : Bandeau d'alerte en cas de coupure de connexion Internet.<br>**Friction** : Le message annonce une synchronisation future automatique alors qu'il n'existe aucun moteur de synchronisation locale. | **Rigueur** : Les requêtes échouent silencieusement en arrière-plan si le serveur ne répond pas, risquant la perte de saisies de formulaires. | **Erreur** : Pas de verrouillage de l'écran en cas de déploiement en cours. | **08/20** | **À corriger**. Modifier le libellé de la bannière offline pour être honnête ("Mode lecture seule - reconnexion en cours") et désactiver les boutons d'écriture. |

---

## 4. Simulations "Think-Aloud" Narratives

### Simulation 1 : Jean-Pierre (Technophobe Impatient) — Inscription, démo & onboarding
*   **Objectif** : S'inscrire, passer l'animation de démarrage, créer sa première SCI familiale "SCI Les Gones" et son premier appartement en location nue.

| Étape | Il pense | Il voit | Il comprend | Il fait | Le système répond | Il ressent | Friction | Wow |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | "J'espère que ce n'est pas trop compliqué de s'inscrire, je n'aime pas donner mon mot de passe partout." | Page `/register` avec logo épuré, champs e-mail et mot de passe, et une case à cocher pour les CGU. | Qu'il doit créer un compte. La case CGU et la charte graphique inspirent confiance. | Renseigne son adresse e-mail Orange et choisit un mot de passe simple. Clic sur "S'inscrire". | La page bascule sur un écran de transition intitulé "Bienvenue". | Rassuré, l'inscription s'est faite sans demande de carte bleue. | 1/10 | 6/10 |
| **2** | "Que se passe-t-il ? L'écran bouge tout seul, j'ai peur de toucher à quelque chose." | Écran `/welcome` avec une barre de progression de 0 à 100%, des coches vertes apparaissant les unes après les autres. | Que l'application configure son espace et charge des données fictives pour lui montrer le fonctionnement. | Attend sans toucher à son clavier. Il lit les petites phrases conseils qui défilent. | Une fois la barre à 100%, l'application le redirige automatiquement vers un questionnaire. | Un peu passif mais curieux de voir la suite. La transition automatique est fluide. | 2/10 | 7/10 |
| **3** | "Je dois répondre à des questions. C'est comme chez le notaire." | Étape 1 de l'onboarding : "Votre profil". Des boutons avec des émojis pour choisir son profil, son volume de biens, etc. | Qu'il doit s'identifier pour que l'application s'adapte à ses besoins. | Clique sur "Gérant de SCI familiale", "1-2 biens", puis choisit ses priorités (loyers et quittances). | Débloque le bouton "Continuer". Le clic l'amène à l'étape "Votre SCI". | Amusé par les émojis. L'expérience ressemble à un jeu, ce qui atténue sa peur de l'informatique. | 1/10 | 8/10 |
| **4** | "Maintenant je dois saisir ma vraie SCI. J'espère ne pas me tromper dans le numéro SIREN." | Formulaire demandant le nom de la SCI, le SIREN (optionnel) et le régime fiscal (IR ou IS). | Qu'il crée sa structure de gestion. La mention "Optionnel" sur le SIREN le soulage car il ne l'a pas sous les yeux. | Saisit "SCI Les Gones" dans le nom. Choisit "IR". Laisse le SIREN vide. Clic sur "Créer la SCI". | Le système valide et affiche l'étape suivante : "Votre premier bien". | Soulagé de ne pas avoir été bloqué par le SIREN. L'interface reste simple et aérée. | 0/10 | 7/10 |
| **5** | "On me demande l'adresse de mon appartement. C'est précis." | Un formulaire en trois sous-étapes. La première demande de choisir entre Appartement, Maison, Immeuble. | Qu'il doit d'abord décrire la nature de son logement avant de donner son adresse. | Clique sur "Appartement". Le système passe au formulaire d'adresse. Saisit l'adresse à Lyon et le code postal. | Valide l'adresse et affiche la saisie du loyer et des charges. Renseigne 850€ de loyer et 50€ de charges. | Fatigué par les clics successifs (3 étapes pour un seul bien). Il aurait préféré tout saisir sur une seule page. | 4/10 | 5/10 |

*   **Verdict** : **Succès d'Onboarding**. Jean-Pierre arrive au bout de la configuration initiale de sa SCI sans commettre d'erreur. Il est maintenant prêt à enregistrer son bail.
*   **Moment critique** : L'étape `/welcome` de chargement des données. S'il y avait eu une erreur réseau ou si l'animation avait duré plus de 10 secondes sans explication, il aurait fermé l'onglet.
*   **Poka-Yoke proposé** : Ajouter une validation instantanée sur le code postal de l'adresse du bien pour éviter que Jean-Pierre ne saisisse par inadvertance un code postal à 4 chiffres (ex: 6900 au lieu de 69002), ce qui bloquerait la génération future de sa quittance.

---

### Simulation 2 : Sarah (La Travailleuse sous Pression) — Saisie mobile et quittance
*   **Objectif** : Enregistrer le loyer payé pour le mois de mai sur sa SCI "Immo Rive Gauche" et envoyer la quittance PDF à son locataire par e-mail depuis son iPhone dans le métro.

| Étape | Il pense | Il voit | Il comprend | Il fait | Le système répond | Il ressent | Friction | Wow |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | "Vite, mon train arrive dans 3 minutes. Je dois marquer le loyer de M. Martin comme reçu." | Dashboard de GérerSCI sur son mobile. Le menu supérieur affiche un sélecteur de SCI et les alertes. | Que le dashboard charge directement les alertes de retard de loyers en haut de page. | Appuie sur le sélecteur de SCI pour choisir "Immo Rive Gauche". | Le dashboard se met à jour. L'alerte "Loyer en retard : M. Martin (Mai)" s'affiche en rouge. | Satisfaite de la réactivité de l'application en réseau 4G instable. La navigation est bien mobile-first. | 1/10 | 8/10 |
| **2** | "Je clique sur l'alerte pour valider le paiement. J'espère que c'est direct." | Clic sur la carte d'activité récente de l'alerte de retard de loyer de M. Martin. | L'application la redirige vers la fiche du bien, directement sur l'onglet "Loyers". | Fait défiler la page vers le bas jusqu'au tableau des loyers. Repère le loyer de mai affiché en statut "Impayé". | Affiche un bouton avec trois petits points d'action à côté du loyer. | Un peu agacée par le défilement nécessaire sur un petit écran d'iPhone. L'accès direct à l'action de paiement nécessite trop de gestes. | 3/10 | 5/10 |
| **3** | "Je dois marquer ce loyer comme payé maintenant." | Menu d'action contenant "Marquer comme payé", "Modifier", "Générer quittance". | Qu'elle doit d'abord déclarer le paiement avant de pouvoir envoyer le document. | Appuie sur "Marquer comme payé". Un formulaire rapide demande la date de réception et le mode. | Valide le formulaire. Le statut du loyer passe instantanément au vert ("Payé"). | Soulagée, le changement d'état est immédiat et ne recharge pas toute la page. | 0/10 | 8/10 |
| **4** | "Maintenant, j'envoie la quittance. Le train démarre." | Le bouton "Quittance" s'est débloqué et apparaît à côté du statut payé. | Qu'elle peut générer le PDF de quittance pour le mois de mai. | Appuie sur le bouton "Générer quittance". | Une fenêtre de chargement de 2 secondes s'ouvre, puis un message affiche "Quittance générée avec succès". | Contente de la vitesse. Mais elle s'aperçoit qu'il n'y a pas d'option directe "Envoyer par e-mail au locataire". | 5/10 | 6/10 |
| **5** | "Mince, je dois télécharger le fichier sur mon téléphone pour lui envoyer manuellement ?" | Le message de succès de génération propose "Télécharger le PDF" ou "Voir le document". | Qu'elle doit récupérer le PDF en local et utiliser son application de messagerie ou son client e-mail personnel pour le transmettre au locataire. | Clique sur "Télécharger", enregistre le fichier dans ses fichiers iPhone, ouvre son application Mail, rédige un e-mail à M. Martin et joint le PDF. | Envoie le message. Le train entre dans un tunnel, coupant la connexion. | Très frustrée. Le manque d'automatisation de l'envoi de la quittance par e-mail gâche le gain de temps initial de la saisie. | 7/10 | 2/10 |

*   **Verdict** : **Succès technique mais friction fonctionnelle**. Sarah a pu saisir le loyer, mais le flux final d'envoi de la quittance est trop manuel pour un usage mobile sous pression.
*   **Moment critique** : L'absence de bouton "Envoyer directement par e-mail au locataire" après la génération de la quittance, obligeant à un flux de téléchargement/redirection complexe sur mobile.
*   **Poka-Yoke proposé** : Ajouter un bouton "Envoyer par e-mail" directement lié au service d'envoi Resend du backend, qui transmet la quittance à l'adresse e-mail renseignée sur le bail du locataire en un seul clic, avec notification de délivrabilité.

---

### Simulation 3 : Lucas (Le Troll Involontaire) — Données absurdes et suppressions accidentelles
*   **Objectif** : Ajouter un bien immobilier à la hâte, soumettre des valeurs aberrantes ou vides, double-cliquer sur le bouton d'enregistrement et tenter de supprimer le seul gérant de sa SCI.

| Étape | Il pense | Il voit | Il comprend | Il fait | Le système répond | Il ressent | Friction | Wow |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | "Je vais vite créer le nouveau studio de mon père. Pas le temps de tout taper." | Formulaire de création de bien dans l'application. | Qu'il doit saisir l'adresse et le loyer cible. | Saisit uniquement "Studio" dans l'adresse et laisse le code postal vide. Tape "gratuit" dans le champ loyer. Clique frénétiquement trois fois sur le bouton "Créer". | Le système bloque la saisie du loyer car le champ n'accepte que des nombres. Des messages d'erreur rouges apparaissent sous le code postal. | Agacé par les blocages, mais comprend qu'il ne peut pas tricher sur les types de données. | 3/10 | 4/10 |
| **2** | "Ok, je mets des chiffres bidons alors." | Le formulaire réinitialisé avec les erreurs signalées. | Qu'il doit remplir les champs obligatoires avec des caractères numériques. | Tape "00000" en code postal et "1" dans le loyer. Clique deux fois de suite très rapidement sur le bouton "Créer". | Le système envoie la requête. Grâce au mécanisme anti-double-clic du bouton frontend, une seule requête API est traitée. Le bien est créé. | Rassuré que le double-clic n'ait pas créé deux logements identiques. L'interface a résisté. | 1/10 | 7/10 |
| **3** | "Je vais aller voir les associés de la SCI. Je veux retirer mon nom de la liste." | Page `/scis/[sciId]/associes`. Tableau listant les associés de la SCI. | Qu'il est enregistré comme unique gérant de la SCI avec 100% des parts. | Clique sur l'icône corbeille (supprimer) à côté de sa propre ligne d'associé gérant. | Une alerte native du navigateur demande de confirmer la suppression. Clique sur "OK". | Pense que le système va simplement supprimer son compte ou vider la liste des membres. | 2/10 | 5/10 |
| **4** | "Ah, ça n'a pas marché ?" | La page affiche une erreur 400 ou bloque silencieusement. En réalité, le backend refuse la suppression car il n'est pas possible de laisser une SCI sans gérant. | Qu'il a tenté de faire une action interdite mais le message d'erreur n'est pas assez explicite. | Clique à nouveau sur la corbeille. | Le système affiche un toast d'erreur : "Impossible de supprimer le dernier gérant d'une SCI." | Un peu vexé d'être bloqué, mais reconnaît que cela évite de détruire la structure de la SCI de son père par erreur. | 4/10 | 8/10 |

*   **Verdict** : **Résilience confirmée**. Le système a résisté au double-clic et a bloqué une action destructrice de gouvernance.
*   **Moment critique** : Le double-clic sur le bouton "Créer". Sans gestion de l'état `submitting` désactivant le bouton, deux biens orphelins auraient été créés en base de données.
*   **Poka-Yoke proposé** : Remplacer l'alerte de suppression native `window.confirm()` par une modale d'avertissement stylisée décrivant précisément pourquoi l'action est bloquée (ex: "Vous êtes le gérant unique. Nommez un nouveau gérant avant de vous retirer de la SCI.").

---

### Simulation 4 : Valérie (L'Utilisatrice Métier/Experte B2B) — Rigueur des calculs et fiscalité
*   **Objectif** : Vérifier la cohérence de sa comptabilité de SCI à l'Impôt sur le Revenu (IR), tester le calcul de rentabilité avec des frais d'agence de 8% sur les loyers encaissés, et générer le document de déclaration fiscale CERFA 2044.

| Étape | Il pense | Il voit | Il comprend | Il fait | Le système répond | Il ressent | Friction | Wow |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | "Je vais vérifier si le calcul de la rentabilité de ce bien est exact. Mon client paie des frais de gestion à une agence immobilière." | Fiche bien, onglet "Rentabilité". Graphiques et tableau récapitulatif des revenus et charges annuelles. | Que le taux de rentabilité nette affiché est anormalement élevé (presque identique à la rentabilité brute). | Va sur l'onglet "Agence" pour vérifier le paramétrage des frais d'agence. | Voit que les frais d'agence sont configurés sur "Pourcentage" avec une valeur de "8.0" (pour 8%). | Suspicieuse. Elle calcule de tête : 8% de 1000€/mois de loyer devrait faire 960€ de frais par an. | 2/10 | 5/10 |
| **2** | "Le système compte-t-il correctement ces 8% ?" | Tableau financier consolidé. Les frais d'agence annuels sont affichés à 8,00 € au lieu de 960,00 €. | Qu'il y a un bug majeur dans le calcul de la rentabilité : le système additionne la valeur numérique brute du pourcentage (8) comme s'il s'agissait d'euros réels. | Modifie temporairement le type de frais pour le passer en "Fixe" à 80€/mois pour corriger le tir. | Met à jour le tableau. Les frais annuels repassent à 960€, faisant chuter le taux de rentabilité nette à sa vraie valeur. | Très mécontente. Si elle n'avait pas vérifié les chiffres de près, elle aurait présenté un rapport de rendement erroné et trompeur à ses clients investisseurs. | 8/10 | 2/10 |
| **3** | "Voyons maintenant la génération du CERFA 2044 pour cette SCI familiale à l'IR." | Navigation vers la page `/fiscalite` de la SCI. Bouton "Générer CERFA 2044". | Que ce document regroupe les revenus fonciers à déclarer aux impôts pour l'exercice 2025. | Clique sur "Générer CERFA 2044". | L'application génère un PDF reprenant le masque officiel de la déclaration d'impôts 2044, pré-rempli avec les chiffres des loyers et des charges de la SCI. | Impressionnée par la mise en page fidèle au formulaire de l'administration fiscale française. Les chiffres saisis (loyers HC et charges déductibles) sont bien répartis dans les bonnes cases. | 1/10 | 9/10 |
| **4** | "Et si je change le régime de la SCI pour la passer à l'IS ? Le CERFA 2044 ne doit plus être accessible." | Va dans les paramètres de la SCI, modifie le régime fiscal de "IR" à "IS". Retourne sur la page fiscale. | Que pour une SCI soumise à l'impôt sur les sociétés (IS), la déclaration 2044 est hors sujet (c'est la liasse 2065 qui s'applique). | Cherche le bouton de génération du CERFA 2044. | Le bouton a disparu de l'interface, remplacé par un message d'explication : "Le formulaire CERFA 2044 est réservé aux SCI soumises à l'IR." | Soulagée de voir que l'application respecte les règles fiscales françaises élémentaires et empêche une fausse déclaration accidentelle. | 0/10 | 8/10 |

*   **Verdict** : **Alerte sur les calculs mais validation du flux légal**. Le bug de calcul des frais d'agence en pourcentage nuit à la crédibilité financière, mais la gestion dynamique du CERFA IR/IS montre une bonne compréhension métier.
*   **Moment critique** : La découverte de l'anomalie des frais d'agence (8.00 € de charges annuelles pour un mandat de gestion de 8%). C'est le genre d'erreur de calcul qui provoque la résiliation immédiate d'un utilisateur professionnel.
*   **Poka-Yoke proposé** : Ajouter un test unitaire strict et un validateur côté backend dans le schéma Pydantic `FraisAgenceCreate` : si le type de frais est `"pourcentage"`, la valeur annuelle calculée doit être `(loyer_hc * pourcentage / 100) * 12`.

---

### Simulation 5 : Thomas (Le Sceptique/Manager B2B) — Évaluation du ROI, résiliation & RGPD
*   **Objectif** : Analyser les limites du plan gratuit (Free), passer à la formule "Fiscalité Pro" via Stripe, tester la gestion de son abonnement, exporter ses données personnelles et demander la suppression de son compte.

| Étape | Il pense | Il voit | Elle comprend | Il fait | Le système répond | Il ressent | Friction | Wow |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | "Je veux tester l'application avec mes propres données, mais je vois que le plan gratuit me limite à 1 SCI et 2 biens." | Fenêtre d'alerte de limite de quota lors de la tentative d'ajout d'un 3e bien immobilier sur sa SCI. | Qu'il doit souscrire à un abonnement payant pour gérer l'intégralité de son patrimoine de 5 appartements. | Clique sur le bouton "Débloquer mes limites" dans le message d'alerte. | Est redirigé vers la page `/pricing` de présentation des tarifs. | Comprend la contrainte commerciale, la limite est cohérente avec les standards du marché. | 1/10 | 5/10 |
| **2** | "Voyons s'il y a un piège dans leur contrat. J'examine les CGV." | Page de tarifs indiquant 39€/mois pour la formule Pro, sans engagement, avec une garantie de remboursement sous 30 jours. | Que la politique "satisfait ou remboursé" atténue son risque financier de test de l'outil. | Sélectionne l'abonnement mensuel et clique sur "Choisir". | Une modale de récapitulatif s'ouvre, lui demandant d'accepter les CGV et de renoncer à son droit de rétractation conformément à l'article L221-28 pour accès immédiat au service. | Sécurisé par le formalisme légal. C'est propre et conforme au droit de la consommation français. | 0/10 | 8/10 |
| **3** | "Je passe au paiement." | Formulaire de paiement Stripe sécurisé sur le domaine `stripe.com`. | Qu'il saisit ses coordonnées bancaires sur une plateforme tiers reconnue, ce qui garantit la sécurité de sa carte. | Saisit sa carte de test. Valide le paiement. | Est redirigé vers l'application avec une animation de confettis. Ses limites de quota ont disparu. | Très satisfait. L'activation des droits Pro est instantanée, sans attente de traitement manuel. | 0/10 | 9/10 |
| **4** | "Où puis-je résilier si l'outil ne me convient pas dans 2 semaines ?" | Page des paramètres du compte (`/account/billing`). | Qu'un lien "Gérer mon abonnement" permet d'accéder directement au portail de facturation Stripe. | Clique sur le lien. | Le portail client Stripe s'ouvre, affichant son historique de facturation et un gros bouton "Résilier l'abonnement". | Rassuré de voir qu'il n'a pas besoin d'envoyer une lettre recommandée ou un e-mail au support pour résilier. La promesse "sans engagement" est réelle. | 0/10 | 9/10 |
| **5** | "Et si je veux partir en récupérant toutes mes saisies pour mon comptable ?" | Page de confidentialité et RGPD du compte (`/account/privacy`). | Qu'il peut télécharger un fichier contenant l'intégralité de ses données au format JSON ou CSV, et supprimer définitivement son compte. | Clique sur "Demander l'export de mes données" puis sur "Supprimer mon compte". | Reçoit instantanément un fichier ZIP contenant ses données. Une modale confirme que la suppression supprimera toutes ses SCI, biens et documents en cascade. | Impressionné par la conformité RGPD. L'application respecte son droit à la portabilité et à l'oubli sans faire de rétention agressive. | 1/10 | 9/10 |

*   **Verdict** : **Conversion et confiance acquises**. Thomas valide le modèle de monétisation, la sécurité juridique et la conformité de la gestion de données de GérerSCI.
*   **Moment critique** : Le clic sur "Gérer mon abonnement" qui le redirige vers le portail Stripe sans encombre. C'est l'indicateur clé de la transparence de la facturation.
*   **Poka-Yoke proposé** : S'assurer que le processus de suppression de compte en cascade nettoie également de manière synchrone tous les documents stockés dans le bucket Supabase Storage lié à l'utilisateur, afin d'éviter de conserver des fichiers PDF orphelins (factures, baux) contenant des données personnelles sensibles après la suppression.

---

### Simulation 6 : Karim (L'Edge Case Technique) — Accessibilité clavier et résilience réseau
*   **Objectif** : Naviguer sur l'application sans souris, tester le comportement lors d'une micro-coupure Internet en plein enregistrement de charge, et vérifier le comportement de l'affichage des dates de loyer.

| Étape | Il pense | Il voit | Il comprend | Il fait | Le système répond | Il ressent | Friction | Wow |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **1** | "Je range ma souris. Voyons si le focus clavier est bien géré pour naviguer dans le menu." | Page d'accueil du dashboard. | Qu'il doit utiliser la touche `Tab` pour se déplacer d'élément en élément. | Appuie sur `Tab` plusieurs fois pour atteindre le menu "Mes SCI". | Un contour bleu bien visible (ring de focus) apparaît autour du sélecteur de SCI. Il appuie sur `Entrée`. | Satisfait de voir que le focus n'est pas masqué par des styles CSS personnalisés. L'accessibilité clavier est prise au sérieux. | 0/10 | 8/10 |
| **2** | "Je veux aller sur l'onglet 'Rentabilité' de mon bien. Je tente de naviguer dans la fiche bien." | Fiche bien avec ses 10 onglets alignés horizontalement. | Qu'il doit déplacer le focus sur la ligne des onglets. | Utilise les touches fléchées de son clavier pour passer de l'onglet "Loyers" à l'onglet "Rentabilité". | Rien ne se passe. Les onglets ne réagissent pas aux flèches du clavier. Il est obligé d'appuyer sur `Tab` 12 fois pour traverser tous les liens et boutons intermédiaires avant d'atteindre l'onglet souhaité. | Agacé. La structure des onglets SvelteKit n'implémente pas le pattern standard d'accessibilité WAI-ARIA des onglets (qui exige la navigation par flèches directionnelles). | 6/10 | 3/10 |
| **3** | "Je vais ajouter une facture de travaux. Je coupe ma connexion réseau pour simuler un trajet en train." | Formulaire "Ajouter une charge" ouvert. | Qu'il saisit ses données hors ligne. | Tape le montant de la facture (350€) et choisit la date de paiement. Déconnecte son interface réseau. | Une bannière jaune apparaît en haut de l'écran : "Connexion perdue — certaines fonctionnalités sont indisponibles." | Impressionné par la détection rapide de la déconnexion. Cependant, il note que le bouton "Enregistrer" reste actif et cliquable. | 3/10 | 6/10 |
| **4** | "Que se passe-t-il si je clique sur Enregistrer sans réseau ?" | Le formulaire avec le bouton cliquable. | Qu'il risque de perdre sa saisie ou de bloquer l'application. | Clique sur "Enregistrer" alors que le réseau est coupé. | La requête API tourne en boucle (timeout), puis affiche une erreur brute dans la console. Le formulaire se ferme mais la charge n'est pas enregistrée. Rien n'a été stocké localement. | Déçu. La bannière promet une résilience mais le système n'empêche pas l'utilisateur de soumettre des formulaires dans le vide, entraînant des pertes de données à la reconnexion. | 7/10 | 2/10 |
| **5** | "Vérifions les timezones sur les loyers générés. Les serveurs de base de données sont souvent configurés en UTC." | La liste des loyers sur l'interface avec des dates comme "01/01/2026". | Que si le serveur renvoie une date brute en format string "2026-01-01T00:00:00Z", le navigateur de l'utilisateur à Paris (UTC+1) ou en Martinique (UTC-4) peut l'interpréter différemment. | Ouvre la console de dev et inspecte la charge utile réseau du JSON de l'API `/api/v1/loyers`. | Constate que les dates de loyer sont renvoyées sous forme de chaînes de caractères pures YYYY-MM-DD (sans fuseau horaire), ce qui évite les décalages d'interprétation locale du calendrier. | Soulagé. L'équipe technique a évité le piège classique des dates d'échéances qui changent de mois selon le fuseau horaire du gérant. | 1/10 | 8/10 |

*   **Verdict** : **Résultats contrastés**. Très bon point sur la gestion des timezones et la détection réseau, mais des lacunes d'accessibilité clavier sur les onglets et un mode hors ligne purement cosmétique (pas d'écriture résiliente).
*   **Moment critique** : La soumission du formulaire de charge en mode déconnecté. L'utilisateur pense que l'action est enregistrée grâce au message d'avertissement flou, mais elle est perdue.
*   **Poka-Yoke proposé** : Dès que l'état `isOffline` passe à vrai, désactiver de manière systématique tous les boutons de soumission (`type="submit"`) des formulaires de l'application et afficher une alerte claire invitant à attendre le retour du réseau.

---

## 5. Analyse Transverse des Patterns d'UX & Techniques

L'analyse croisée des simulations de parcours utilisateurs met en lumière des forces majeures du produit mais aussi des risques d'usabilité systémiques à corriger avant un déploiement à grande échelle.

### A. Frictions Universelles
Ces frictions pénalisent l'ensemble des personas, quel que soit leur niveau technique :
1.  **Le syndrome du "Bouton Mort"** : Le bouton de modification de la fiche bien qui renvoie vers une promesse de fonctionnalité future alors que l'édition est disponible plus bas génère une rupture de confiance chez tous les utilisateurs.
2.  **L'export de données indiscriminé** : Télécharger un fichier CSV contenant les données de toutes ses SCI alors qu'on a cliqué sur le bouton d'export depuis une SCI spécifique introduit un risque de fuite de données d'un client à un autre (grave pour les gérants professionnels comme Valérie).
3.  **L'absence d'accents sur les quittances PDF** : La génération de documents officiels présentant des fautes d'orthographe (absence d'accents) dégrade immédiatement la perception de professionnalisme du SaaS.

### B. Wow Moments
Ces fonctionnalités déclenchent l'effet "Aha!" et facilitent grandement la conversion commerciale :
1.  **L'onboarding personnalisé** : Le questionnaire de profil (étape 1) qui adapte ensuite les étapes finales et propose des raccourcis d'actions basés sur les priorités déclarées de l'utilisateur.
2.  **L'animation de chargement de démo** : Faire patienter l'utilisateur avec une barre de progression honnête et des faits statistiques pertinents pendant la génération de la base de démo.
3.  **La transparence du portail Stripe** : Permettre aux sceptiques de résilier en 1 clic sans démarche administrative lourde renforce la confiance et favorise l'achat impulsif.

### C. Top 10 Abandon Risks
Voici les 10 risques d'abandon utilisateur les plus critiques classés par sévérité :

1.  **Calcul de rentabilité erroné (Frais agence % / Score: 95)** : Présenter des chiffres faux détruit instantanément la crédibilité de l'application auprès des investisseurs et des comptables.
2.  **Génération de quittances pour d'autres utilisateurs (Score: 90)** : Un problème de sécurité permettant de deviner ou d'accéder aux PDF de tiers via des IDs de loyers séquentiels provoquerait un signalement RGPD et un abandon immédiat des utilisateurs B2B.
3.  **Crash 500 sur la fiche bien avec documents (Score: 85)** : L'anomalie de schéma Pydantic (`file_url` vs `url`) provoquant un crash total de l'écran principal dès qu'un document est importé empêche toute utilisation prolongée de l'outil.
4.  **SCI ingouvernable après suppression du gérant (Score: 80)** : Autoriser un utilisateur à supprimer son propre rôle de gérant unique sans garde-fou bloque définitivement son espace de travail.
5.  **Blocage de la création d'un nouveau bail (Score: 75)** : L'impossibilité de relouer un bien dans l'interface sans écraser (et donc perdre) l'historique du locataire précédent pousse les utilisateurs multi-biens à retourner sur Excel.
6.  **Décalage de date sur la quittance (Timezone / Score: 70)** : Un locataire qui reçoit une quittance affichant le mois précédent à cause d'un décalage d'interprétation de fuseau horaire du navigateur génère des litiges administratifs et des plaintes au support.
7.  **Échec de redirection Stripe (503 / Score: 65)** : Si la communication entre le VPS et Stripe échoue, l'utilisateur ne peut pas souscrire au moment où il a pris sa décision d'achat.
8.  **Génération de CERFA incorrect pour les SCI IS (Score: 60)** : Proposer un document de revenus fonciers (2044) à une société soumise à l'impôt sur les sociétés (IS) induit l'utilisateur en erreur réglementaire.
9.  **Fausse promesse du bouton "Annuler" (Undo / Score: 55)** : Proposer un bouton d'annulation sur les suppressions de charges qui ne restaure pas la donnée provoque de la frustration en cas d'erreur de clic.
10. **Perte de saisie de formulaire en cas de micro-coupure réseau (Score: 50)** : Ne pas désactiver le bouton d'enregistrement hors ligne et laisser la requête expirer sans stockage local décourage les utilisateurs nomades.

---

## 6. Spécifications de Tests BDD / Gherkin

Ces scénarios décrivent les parcours de validation attendus pour chacun des personas afin d'automatiser les tests d'utilisabilité et de non-régression.

### Scénario 1 (Jean-Pierre) : Onboarding fluide et résistant aux étapes optionnelles
```gherkin
Fonctionnalité: Onboarding pas à pas d'un utilisateur technophobe
  En tant que nouvel utilisateur inscrit sur GérerSCI
  Je veux configurer mon espace sans être bloqué par des informations légales secondaires
  Afin de commencer à utiliser l'application rapidement

  Scénario: Configuration initiale réussie avec SIREN et détails légaux laissés vides
    Etant donné que je suis un nouvel utilisateur connecté sur la page "/onboarding"
    Quand je remplis l'étape 1 "Votre profil" avec le rôle "gerant_familial" et "1-2" biens
    Et que je clique sur le bouton de validation de l'étape 1
    Alors je suis redirigé sur l'étape 2 "Votre SCI"
    Quand je saisis uniquement le nom "SCI Les Gones" sans renseigner le numéro SIREN
    Et que je clique sur le bouton "Créer la SCI"
    Alors le système enregistre ma SCI avec le régime fiscal "IR" par défaut
    Et je passe à l'étape 3 "Votre premier bien"
    Quand je sélectionne le type "appartement", saisis l'adresse "12 rue de la Paix, Lyon 69002" et clique sur "Créer le bien"
    Alors le bien est ajouté à mon portefeuille de gestion
    Et je suis redirigé vers l'étape finale de bienvenue
```

### Scénario 2 (Sarah) : Saisie ultra-rapide de paiement de loyer sur mobile
```gherkin
Fonctionnalité: Gestion rapide des paiements de loyers sur mobile
  En tant qu'investisseuse active en déplacement
  Je veux enregistrer un paiement de loyer et générer le justificatif en quelques secondes
  Afin de maintenir mes comptes à jour sans effort

  Scénario: Enregistrement d'un loyer reçu et accès à la quittance
    Etant donné que je suis connectée sur mon smartphone sur la page "/dashboard" de la SCI "Immo Rive Gauche"
    Quand je clique sur l'alerte de retard de loyer du locataire "M. Martin"
    Alors je suis redirigée sur l'onglet "Loyers" de la fiche du bien correspondant
    Quand je clique sur l'action "Marquer comme payé" sur l'échéance du mois en cours
    Et que je valide la modale de confirmation de paiement
    Alors le statut du loyer passe visuellement au vert et affiche "Payé"
    Et le bouton d'action "Télécharger la quittance" devient immédiatement actif et cliquable
```

### Scénario 3 (Lucas) : Protection contre les double-clics et la destruction de gouvernance
```gherkin
Fonctionnalité: Robustesse de l'interface face aux erreurs de saisie et aux clics multiples
  En tant que gérant étourdi ou pressé
  Je veux que le système bloque les soumissions en double et protège les rôles administratifs critiques
  Afin d'éviter la corruption accidentelle de mes données de SCI

  Scénario: Blocage de la suppression du gérant unique de la SCI
    Etant donné que je suis connecté sur la page des associés de la SCI "SCI Belleville"
    Et que la SCI ne possède qu'un seul associé ayant le rôle "gérant"
    Quand je clique sur le bouton de suppression à côté du nom de cet associé gérant unique
    Alors le système affiche un message d'erreur clair "Impossible de supprimer le dernier gérant d'une SCI"
    Et la suppression de la ligne est annulée
    Et la base de données conserve le gérant actif
```

### Scénario 4 (Valérie) : Exactitude fiscale et calcul des charges de gestion d'agence
```gherkin
Fonctionnalité: Calcul précis des charges réelles pour la rentabilité et la fiscalité
  En tant que comptable exigeante
  Je veux que les frais de gestion d'agence immobilière exprimés en pourcentage soient correctement convertis en euros réels
  Afin de garantir la justesse de ma déclaration fiscale annuelle

  Scénario: Calcul de la rentabilité avec frais d'agence en pourcentage
    Etant donné qu'un bien possède un loyer hors charges de 1000 EUR par mois
    Et que j'enregistre des frais d'agence de type "pourcentage" avec une valeur de "8.0" (8%)
    Quand je consulte l'onglet "Rentabilité" de la fiche bien
    Alors le montant total annuel des charges d'agence affiché doit être de "960.00 EUR"
    Et le calcul de la rentabilité nette déduit exactement ce montant de 960 EUR du cashflow annuel calculé
```

### Scénario 5 (Thomas) : Conformité de facturation Stripe et droit à la portabilité (RGPD)
```gherkin
Fonctionnalité: Gestion transparente de la facturation et des données personnelles
  En tant que chef d'entreprise sceptique quant à l'abonnement
  Je veux pouvoir résilier mon forfait moi-même et exporter l'intégralité de mes données en un clic
  Afin de garder le contrôle total de mon engagement commercial

  Scénario: Exportation complète et suppression du compte
    Etant donné que je suis connecté sur la page "/account/privacy"
    Quand je clique sur le bouton "Demander l'export de mes données"
    Alors le serveur génère un fichier ZIP contenant mes informations financières au format CSV
    Quand je clique sur le bouton "Supprimer mon compte" et confirme mon mot de passe
    Alors mon abonnement Stripe est résilié immédiatement
    Et toutes mes données de base de données (SCI, biens, baux, loyers) sont effacées en cascade
    Et je suis déconnecté et redirigé vers la page d'accueil
```

### Scénario 6 (Karim) : Accessibilité et résilience réseau de l'application
```gherkin
Fonctionnalité: Tolérance aux pannes réseau et navigation clavier accessible
  En tant qu'ingénieur naviguant en situation de mobilité difficile
  Je veux que l'application détecte la perte réseau et bloque les actions de modification
  Afin d'éviter des échecs de soumission et des pertes d'informations

  Scénario: Désactivation des boutons d'action en mode déconnecté
    Etant donné que je suis connecté sur la fiche bien et que je saisis une nouvelle charge dans le formulaire
    Quand je simule une déconnexion Internet (passage hors ligne)
    Alors la bannière d'alerte de connectivité apparaît en haut de l'écran
    Et le bouton d'enregistrement du formulaire de charge devient grisé et désactivé ("disabled")
    Quand je rétablis la connexion réseau (passage en ligne)
    Alors la bannière disparaît et le bouton redeviens actif et cliquable
```

---

## 7. Confrontation et Débats Inter-Cabinets

### Retranscription du Débat d'Arbitrage Final

**Cabinet WEST (Représentant de l'expérience utilisateur et de la séduction produit) :**  
> *"La première impression de GérerSCI est excellente. La transition de la création de compte vers l'écran de chargement de la démo interactive avec ses statistiques est un coup de génie marketing. L'utilisateur a l'impression d'entrer dans un cockpit professionnel sans aucun effort. Mais nous devons régler ce bouton mort de modification sur la fiche bien. C'est une vraie déception visuelle de cliquer dessus et de voir un toast disant 'bientôt disponible' alors que l'édition de base fonctionne déjà plus bas dans la page. De plus, nos retours sur l'absence de bouton d'envoi automatique de quittance par e-mail montrent que l'utilisateur se sent abandonné au moment où il a le plus besoin de vitesse."*

**Cabinet ALPINE (Représentant de la rigueur juridique et fiscale des SCI) :**  
> *"Nous partageons l'enthousiasme sur l'onboarding, mais nous tirons la sonnette d'alarme sur deux points juridiques majeurs. Premièrement, stocker les parts sociales en nombres flottants en base de données empêche la constitution d'un registre de cessions conforme au Code civil français. Une part ne se divise pas en pourcentages approximatifs comme 33.33%. Deuxièmement, le calcul de la rentabilité nette avec des frais d'agence en pourcentage est faux : 8% de frais sur un loyer de 1000€ comptés comme 8€ de charges annuelles au lieu de 960€, c'est une faute professionnelle pour un outil de gestion de patrimoine. Enfin, laisser un utilisateur supprimer le gérant unique d'une SCI sans alerte bloquante est un risque majeur d'incohérence juridique."*

**Cabinet EAST (Représentant de la performance, de l'accessibilité et de la tolérance aux erreurs) :**  
> *"D'un point de vue robustesse pure, l'application est bien codée. L'absence de requêtes N+1 sur le dashboard et l'utilisation de variables de date sans fuseau horaire éliminent les bugs d'affichage de date classiques. Cependant, nous avons des soucis d'accessibilité sur la fiche bien : le fait que l'utilisateur ne puisse pas utiliser les flèches du clavier pour naviguer d'un onglet à l'autre est une rupture des normes WCAG. De plus, notre 'Troll testing' montre que le mode hors ligne est purement informatif. Si l'utilisateur clique sur 'Enregistrer' alors que la connexion est perdue, sa saisie de formulaire est envoyée dans le vide et perdue. Nous devons désactiver ces boutons d'écriture dès que la coupure est détectée."*

### Consensus et Arbitrage du Comité

Le comité valide les arbitrages suivants pour la version finale :

1.  **Arbitrage Frais d'Agence (ALPINE vs WEST)** : Correction prioritaire requise. Le type de frais d'agence en pourcentage doit calculer une valeur annuelle exacte dérivée du loyer cible du bail afin de ne pas fausser les graphiques de rentabilité et le cashflow consolidé.
2.  **Arbitrage Mode Hors Ligne (EAST vs WEST)** : Le message de la bannière offline doit être modifié pour ne plus promettre une synchronisation automatique magique inexistante. En contrepartie, tous les formulaires doivent bloquer les tentatives de soumission lorsque la connexion est perdue.
3.  **Arbitrage Gouvernance et Parts (ALPINE)** : Le stockage des parts sociales doit être migré vers un modèle de nombre entier (ex: `nb_parts` sur un `total_parts_sci` de la SCI), et le bouton de suppression du dernier gérant restant doit être grisé avec une info-bulle explicative dans l'interface des associés.
4.  **Arbitrage Export CSV (WEST vs EAST)** : L'export de données dans la vue d'une SCI spécifique doit impérativement être limité aux seuls biens et loyers de cette SCI (en passant le paramètre `sci_id` à l'API) pour éviter toute fuite involontaire de données de portefeuille.

### Verdict Final du Comité

> [!IMPORTANT]
> **VERDICT : GO SOUS CONDITIONS DE SÉCURITÉ ET DE MATURITÉ COMPTABLE (GO AVEC RÉSERVES)**
> 
> L'architecture de GérerSCI est saine, stable et robuste sous la charge. L'intégration du flux de paiement Stripe est exemplaire. Cependant, l'application ne pourra pas être déployée auprès de gérants professionnels sans la résolution prioritaire des anomalies de calcul financier (frais d'agence %) et de gouvernance (blocage de la suppression du gérant unique et correction des parts sociales). 
> 
> Un sprint de correction ("Hardening Sprint") de 5 jours est requis pour lever ces réserves avant le lancement commercial.
