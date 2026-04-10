export type EntityId = number | string;
export type PlanKey = 'free' | 'starter' | 'pro' | 'lifetime';

export type BienType = 'nu' | 'meuble' | 'mixte' | 'mobilite';
export type LoyerStatus = 'en_attente' | 'paye' | 'en_retard';
export type SCIStatus = 'configuration' | 'mise_en_service' | 'exploitation';

export type Associe = {
	id: EntityId;
	id_sci?: EntityId | null;
	user_id?: EntityId | null;
	nom: string;
	email?: string | null;
	part?: number | null;
	nb_parts?: number | null;
	role?: string | null;
	is_account_member?: boolean | null;
	created_at?: string;
	updated_at?: string;
};

export type SCIOverview = {
	id: EntityId;
	nom: string;
	siren?: string | null;
	regime_fiscal?: 'IR' | 'IS' | string | null;
	statut?: SCIStatus | string | null;
	adresse_siege?: string | null;
	date_creation?: string | null;
	capital_social?: number | null;
	objet_social?: string | null;
	rcs_ville?: string | null;
	rcs_numero?: string | null;
	forme_juridique?: string | null;
	nom_gerant?: string | null;
	nb_parts_total?: number | null;
	valeur_nominale_part?: number | null;
	associes_count?: number;
	biens_count?: number;
	loyers_count?: number;
	user_role?: string | null;
	user_part?: number | null;
	associes?: Associe[];
	jour_loyer?: number | null;
};

export type SCICreatePayload = {
	nom: string;
	siren?: string | null;
	regime_fiscal?: 'IR' | 'IS';
	adresse_siege?: string | null;
	date_creation?: string | null;
	capital_social?: number | null;
	objet_social?: string | null;
	rcs_ville?: string | null;
	rcs_numero?: string | null;
	forme_juridique?: string | null;
	nom_gerant?: string | null;
};

export type SCIDetail = SCIOverview & {
	charges_count?: number;
	total_monthly_rent?: number;
	total_monthly_property_charges?: number;
	total_recorded_charges?: number;
	paid_loyers_total?: number;
	pending_loyers_total?: number;
	biens?: Bien[];
	recent_loyers?: Loyer[];
	recent_charges?: Charge[];
	fiscalite?: Fiscalite[];
};

export type SCIUpdatePayload = {
	nom?: string;
	siren?: string | null;
	regime_fiscal?: 'IR' | 'IS';
	adresse_siege?: string | null;
	date_creation?: string | null;
	capital_social?: number | null;
	objet_social?: string | null;
	rcs_ville?: string | null;
	rcs_numero?: string | null;
	forme_juridique?: string | null;
	nom_gerant?: string | null;
	jour_loyer?: number | null;
};

export type Charge = {
	id?: EntityId;
	id_bien: EntityId;
	id_sci?: EntityId | null;
	type_charge: string;
	montant: number;
	date_paiement: string;
	bien_adresse?: string | null;
	bien_ville?: string | null;
	created_at?: string;
	updated_at?: string;
};

export type Fiscalite = {
	id?: EntityId;
	id_sci: EntityId;
	annee: number;
	total_revenus?: number | null;
	total_charges?: number | null;
	resultat_fiscal?: number | null;
	regime_fiscal?: string | null;
	nom_sci?: string | null;
	interets_emprunt?: number | null;
	travaux?: number | null;
	frais_gestion?: number | null;
	assurance?: number | null;
	taxe_fonciere?: number | null;
	copropriete?: number | null;
	created_at?: string;
	updated_at?: string;
};

export type BienCategory =
	| 'appartement'
	| 'maison'
	| 'immeuble'
	| 'local_commercial'
	| 'parking'
	| 'autre';

export type Bien = {
	id?: EntityId;
	id_sci?: EntityId;
	adresse: string;
	ville?: string | null;
	code_postal?: string | null;
	type_locatif?: BienType | string | null;
	type_bien?: BienCategory | string | null;
	statut?: string | null;
	loyer_cc?: number | null;
	charges?: number | null;
	tmi?: number | null;
	acquisition_date?: string | null;
	prix_acquisition?: number | null;
	rentabilite_brute?: number;
	rentabilite_nette?: number;
	cashflow_annuel?: number;
	created_at?: string;
	updated_at?: string;
};

export type Locataire = {
	id?: EntityId;
	id_bien: EntityId;
	id_sci?: EntityId | null;
	nom: string;
	email?: string | null;
	date_debut: string;
	date_fin?: string | null;
	created_at?: string;
	updated_at?: string;
};

export type Loyer = {
	id?: EntityId;
	id_bien: EntityId;
	id_sci?: EntityId;
	id_locataire?: EntityId | null;
	date_loyer: string;
	montant: number;
	statut?: LoyerStatus | 'retard' | string | null;
	quitus_genere?: boolean;
	created_at?: string;
	updated_at?: string;
};

export type BienCreatePayload = {
	id_sci: EntityId;
	adresse: string;
	ville: string;
	code_postal: string;
	type_locatif: BienType;
	type_bien?: BienCategory;
	loyer_cc: number;
	charges: number;
	tmi: number;
	acquisition_date?: string;
	prix_acquisition?: number;
	surface_m2?: number;
	nb_pieces?: number;
	dpe_classe?: 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G';
};

export type BienUpdatePayload = {
	adresse?: string;
	ville?: string;
	code_postal?: string;
	type_locatif?: BienType;
	type_bien?: string;
	loyer_cc?: number;
	charges?: number;
	tmi?: number;
	acquisition_date?: string | null;
	prix_acquisition?: number | null;
	jour_loyer?: number | null;
	zone_tendue?: boolean;
};

export type LocataireCreatePayload = {
	id_bien: EntityId;
	nom: string;
	email?: string | null;
	date_debut: string;
	date_fin?: string | null;
};

export type LocataireUpdatePayload = {
	nom?: string;
	email?: string | null;
	telephone?: string | null;
	date_debut?: string;
	date_fin?: string | null;
};

export type AssocieCreatePayload = {
	id_sci: EntityId;
	nom: string;
	email?: string | null;
	part: number;
	role: string;
	user_id?: EntityId | null;
};

export type AssocieUpdatePayload = {
	nom?: string;
	email?: string | null;
	part?: number;
	role?: string;
};

export type ChargeCreatePayload = {
	id_bien: EntityId;
	type_charge: string;
	montant: number;
	date_paiement: string;
};

export type ChargeUpdatePayload = {
	type_charge?: string;
	montant?: number;
	date_paiement?: string;
};

export type FiscaliteCreatePayload = {
	id_sci: EntityId;
	annee: number;
	total_revenus: number;
	total_charges: number;
	interets_emprunt?: number;
	travaux?: number;
	frais_gestion?: number;
	assurance?: number;
	taxe_fonciere?: number;
	copropriete?: number;
};

export type FiscaliteUpdatePayload = {
	annee?: number;
	total_revenus?: number;
	total_charges?: number;
	interets_emprunt?: number;
	travaux?: number;
	frais_gestion?: number;
	assurance?: number;
	taxe_fonciere?: number;
	copropriete?: number;
};

export type LoyerCreatePayload = {
	id_bien: EntityId;
	id_locataire?: EntityId;
	date_loyer: string;
	montant: number;
	statut: LoyerStatus;
	quitus_genere?: boolean;
};

export type LoyerUpdatePayload = {
	date_loyer?: string;
	montant?: number;
	statut?: LoyerStatus;
	date_paiement?: string;
	quitus_genere?: boolean;
};

export type QuitusRequestPayload = {
	id_loyer: EntityId;
	id_bien: EntityId;
	nom_locataire: string;
	periode: string;
	montant: number;
	nom_sci?: string;
	adresse_bien?: string;
	ville_bien?: string;
};

export type QuitusResponsePayload = {
	filename: string;
	pdf_url: string;
	size_bytes: number;
};

export type CheckoutMode = 'subscription' | 'payment';

export type CheckoutSessionRequestPayload = {
	plan_key: PlanKey;
	mode?: CheckoutMode;
};

export type CheckoutSessionResponsePayload = {
	url: string;
};

export type SubscriptionEntitlements = {
	plan_key: PlanKey;
	plan_name: string;
	status: string;
	mode: CheckoutMode;
	is_active: boolean;
	stripe_price_id?: string | null;
	entitlements_version: number;
	max_scis?: number | null;
	max_biens?: number | null;
	current_scis: number;
	current_biens: number;
	remaining_scis?: number | null;
	remaining_biens?: number | null;
	over_limit: boolean;
	features: Record<string, boolean>;
	onboarding_completed: boolean;
	demo_seeded?: boolean;
};

export interface Cerfa2044Request {
	annee: number;
	total_revenus: number;
	total_charges: number;
	sci_nom?: string;
	siren?: string;
	regime_fiscal?: 'IR' | 'IS' | string;
}

export type DeficitAnterieur = {
	annee: number;
	montant_initial: number;
	total_impute: number;
	solde_restant: number;
	annee_prescription: number;
};

export type AssocieQuotePart = {
	associe_id: string;
	nom: string;
	email: string;
	part_pct: number;
	quote_part_resultat: number;
	case_4ba: number;
	case_4bb: number;
	case_4bc: number;
	case_4bd: number;
};

export type ResumeFiscalData = {
	sci_nom: string;
	annee: number;
	total_revenus: number;
	total_charges: number;
	total_interets: number;
	resultat_global: number;
	associes: AssocieQuotePart[];
	micro_foncier_eligible: boolean;
	micro_foncier_abattement: number;
	micro_foncier_resultat: number;
	regime_recommande: string;
	economie_regime_recommande: number;
	is_deficit: boolean;
	deficit_total: number;
	deficit_interets_emprunt: number;
	deficit_imputable_revenu_global: number;
	deficit_reportable_foncier: number;
	deficits_anterieurs: DeficitAnterieur[];
	total_deficits_anterieurs_imputes: number;
};

export type Notification = {
	id: string;
	type: 'late_payment' | 'status_change' | 'document_ready' | 'system' | 'info';
	title: string;
	message: string;
	metadata: Record<string, unknown>;
	read_at: string | null;
	created_at: string;
};

export type OnboardingStatus = {
	completed: boolean;
	sci_created: boolean;
	sci_id: string | null;
	bien_created: boolean;
	bail_created: boolean;
	notifications_set: boolean;
};

export type DashboardAlerte = {
	type: string;
	message: string;
	severity: string;
	entity_id?: string;
	entity_type?: string;
	id_sci?: string;
	montant?: number;
	date?: string;
	sci_nom?: string;
	bien_adresse?: string;
	link?: string;
};

export type DashboardKpis = {
	sci_count: number;
	biens_count: number;
	taux_recouvrement: number;
	cashflow_net: number;
	loyers_total?: number;
	loyers_payes?: number;
	charges_total?: number;
};

export type SCICard = {
	id: number;
	nom: string;
	statut: string;
	biens_count: number;
	loyer_total: number;
	recouvrement: number;
};

export type ActivityItem = {
	id: string;
	type: 'loyer' | 'bien' | 'quittance' | 'bail';
	description: string;
	created_at: string;
	sci_nom?: string;
	id_sci?: string;
	id_bien?: string;
};

export type DashboardData = {
	alertes: DashboardAlerte[];
	kpis: DashboardKpis;
	scis: SCICard[];
	activite: ActivityItem[];
};

export type BailEmbed = {
	id: number;
	date_debut: string;
	date_fin: string | null;
	loyer_hc: number;
	charges_locatives: number;
	depot_garantie: number;
	revision_indice: string | null;
	statut: string;
	etat_lieux_entree: string | null;
	etat_lieux_entree_document_url: string | null;
	etat_lieux_entree_notes: string | null;
	locataires: Array<{
		id: number;
		nom: string;
		prenom?: string;
		email?: string;
		telephone?: string;
	}>;
};

export type AssurancePnoEmbed = {
	id: number;
	assureur: string;
	numero_contrat: string | null;
	prime_annuelle: number;
	date_debut: string;
	date_fin: string | null;
};

export type FraisAgenceEmbed = {
	id: number;
	type_frais: string;
	montant: number;
	date_frais: string;
	description: string | null;
};

export type LoyerEmbed = {
	id: number;
	date_loyer: string;
	montant: number;
	statut: LoyerStatus;
	quitus_genere: boolean;
	date_paiement?: string | null;
};

export type ChargeEmbed = {
	id: number;
	type_charge: string;
	montant: number;
	date_paiement: string;
};

export type ChargeCreate = {
	type_charge: string;
	montant: number;
	date_paiement: string;
};

export type PnoCreate = {
	assureur: string;
	numero_contrat?: string;
	prime_annuelle: number;
	date_debut: string;
	date_fin?: string;
};

export type PnoUpdate = Partial<PnoCreate>;

export type FraisCreate = {
	type_frais: string;
	montant: number;
	date_frais: string;
	description?: string;
};

export type CreditImmobilierEmbed = {
	id: number | string;
	banque: string;
	numero_contrat: string | null;
	montant_emprunte: number;
	taux_nominal: number;
	taux_assurance: number;
	duree_mois: number;
	date_debut: string;
	mensualite: number;
	capital_restant_du: number | null;
	type_credit: string;
	statut: string;
};

export type CreditCreate = {
	banque: string;
	numero_contrat?: string;
	montant_emprunte: number;
	taux_nominal: number;
	taux_assurance?: number;
	duree_mois: number;
	date_debut: string;
	mensualite: number;
	capital_restant_du?: number;
	type_credit?: string;
	statut?: string;
	notes?: string;
};

export type CreditUpdate = Partial<CreditCreate>;

export type AmortissementRow = {
	mois: number;
	date: string;
	mensualite: number;
	capital: number;
	interets: number;
	assurance: number;
	capital_restant: number;
};

export type InviteAssociePayload = {
	nom: string;
	email?: string | null;
	part: number;
	role: string;
};

export type AssocieEmbed = {
	id: number | string;
	nom: string;
	email: string | null;
	role: string | null;
	part: number | null;
	email_sent?: boolean;
};

export type BailCreate = {
	date_debut: string;
	date_fin?: string;
	loyer_hc: number;
	charges_locatives?: number;
	depot_garantie?: number;
	revision_indice?: string;
	etat_lieux_entree?: string;
	etat_lieux_entree_document_url?: string;
	etat_lieux_entree_notes?: string;
};

export type BailUpdate = Partial<BailCreate>;

export type DocumentBienEmbed = {
	id: number;
	nom: string;
	categorie: string;
	url: string;
	created_at?: string;
	uploaded_at?: string;
};

export type RentabiliteCalculee = {
	brute: number;
	nette: number;
	cashflow_mensuel: number;
	cashflow_annuel: number;
	cashflow_apres_credit_mensuel: number;
	cashflow_apres_credit_annuel: number;
};

export type FicheBien = {
	id: number;
	id_sci: number;
	adresse: string;
	ville: string;
	code_postal: string;
	type_locatif: string;
	type_bien: string | null;
	loyer_cc: number;
	charges: number;
	surface_m2: number | null;
	nb_pieces: number | null;
	dpe_classe: string | null;
	photo_url: string | null;
	prix_acquisition: number | null;
	statut: string | null;
	zone_tendue: boolean;
	jour_loyer: number | null;
	bail_actif: BailEmbed | null;
	loyers_recents: LoyerEmbed[];
	charges_list: ChargeEmbed[];
	assurance_pno: AssurancePnoEmbed | null;
	frais_agence: FraisAgenceEmbed[];
	credits_immobiliers: CreditImmobilierEmbed[];
	documents: DocumentBienEmbed[];
	rentabilite: RentabiliteCalculee;
};

export type NotificationPreference = {
	type: string;
	email_enabled: boolean;
	in_app_enabled: boolean;
};

export type FinancesData = {
	revenus_total: number;
	charges_total: number;
	cashflow_net: number;
	taux_recouvrement: number;
	patrimoine_total: number;
	rentabilite_moyenne: number;
	evolution_mensuelle: Array<{ mois: string; revenus: number; charges: number }>;
	repartition_sci: Array<{ sci_id?: string; sci_nom: string; revenus: number; charges: number }>;
};

export interface SciDocumentItem {
	id: string | number;
	id_bien: string | number;
	bien_adresse?: string;
	nom: string;
	categorie: string;
	url: string;
	uploaded_at?: string;
}

export type Cerfa2044RequestPayload = {
	annee: number;
	total_revenus: number;
	total_charges: number;
	sci_nom?: string;
	siren?: string;
	regime_fiscal?: 'IR' | 'IS' | string;
};

export type Cerfa2044ResponsePayload = {
	status: string;
	annee: number;
	total_revenus: number;
	total_charges: number;
	resultat_fiscal: number;
	formulaire: string;
};

export type FileUploadResponse = {
	success: boolean;
	url: string;
	message: string;
};

export type FileDownloadResponse = {
	success: boolean;
	url: string;
};

export type FileListResponse = {
	success: boolean;
	files: Array<Record<string, unknown>>;
};

export type AssembleeGeneraleType = 'ordinaire' | 'extraordinaire' | string;

export type AssembleeGenerale = {
	id: EntityId;
	id_sci: EntityId;
	date_ag: string;
	type_ag: AssembleeGeneraleType;
	exercice_annee: number;
	ordre_du_jour?: string | null;
	pv_url?: string | null;
	quorum_atteint: boolean;
	resolutions?: string | null;
	notes?: string | null;
	created_at?: string | null;
};

export type AssembleeGeneraleInput = {
	date_ag: string;
	type_ag: AssembleeGeneraleType;
	exercice_annee: number;
	ordre_du_jour?: string | null;
	pv_url?: string | null;
	quorum_atteint: boolean;
	resolutions?: string | null;
	notes?: string | null;
};

export interface ImportResult {
	success: boolean;
	imported: number;
	skipped: number;
	errors: string[];
	type: string;
}

export type DataExportResponse = {
	success: boolean;
	message: string;
	export_url: string | null;
	expires_at: string | null;
};

export type DataSummaryResponse = {
	user_id: string;
	email: string;
	created_at: string;
	data_summary: {
		sci_count: number;
		biens_count: number;
		loyers_count: number;
		associes_count: number;
		account_created: string;
		last_sign_in: string;
	};
};

export type AccountDeleteResponse = {
	success: boolean;
	message: string;
};

export type ComptabiliteLigne = {
	bien_id: EntityId;
	adresse: string;
	ville: string;
	revenus: number;
	charges: number;
	evenements_deductibles: number;
	resultat: number;
};

export type ComptabiliteAnnuelle = {
	annee: number;
	biens: ComptabiliteLigne[];
	totaux: {
		revenus: number;
		charges: number;
		evenements_deductibles: number;
		resultat: number;
	};
	variation_n1: {
		revenus: number | null;
		charges: number | null;
		resultat: number | null;
	} | null;
};

export type ComptabiliteMoisItem = {
	mois: string;
	revenus: number;
	charges: number;
};

export type EvenementType =
	| 'reparation'
	| 'travaux'
	| 'sinistre'
	| 'visite'
	| 'controle'
	| 'diagnostic'
	| 'autre';

export type Evenement = {
	id: EntityId;
	id_bien: EntityId;
	type_evenement: EvenementType;
	titre: string;
	date_evenement: string;
	montant?: number | null;
	prestataire?: string | null;
	deductible_fiscal: boolean;
	created_at?: string;
};

export type EvenementCreatePayload = {
	type_evenement: EvenementType;
	titre: string;
	date_evenement: string;
	montant?: number | null;
	prestataire?: string | null;
	deductible_fiscal?: boolean;
};

export type ObligationStatus = 'ok' | 'warning' | 'danger' | 'unknown';

export type ObligationItem = {
	key: string;
	label: string;
	status: ObligationStatus;
	detail: string;
	date_expiration?: string | null;
};

export type ObligationsData = {
	pno: ObligationItem;
	dpe: ObligationItem;
	bail: ObligationItem;
	locataire: ObligationItem;
	depot_garantie: ObligationItem;
	edl_entree: ObligationItem;
};

export type Echeance = {
	type: string;
	entite: string;
	titre: string;
	description: string;
	date_echeance: string;
	urgence: 'depassee' | 'critique' | 'urgente' | 'normale' | 'lointaine';
	reference_legale: string;
	consequence: string;
	action_url: string;
};

export type EcheancesResume = {
	depassee: number;
	critique: number;
	urgente: number;
	normale: number;
	lointaine: number;
};

export type EcheancesResponse = {
	echeances: Echeance[];
	resume: EcheancesResume;
};

export type ClotureBailPayload = {
	date_fin_effective: string;
	date_etat_lieux_sortie: string;
	montant_depot_restitue: number;
	detail_retenues?: string;
	motif: 'conge_locataire' | 'conge_bailleur' | 'resiliation_amiable' | 'resiliation_judiciaire';
};

export type CongeType = 'locataire' | 'bailleur';

export interface CongeBailPayload {
	type_conge: CongeType;
	date_notification: string;
	motif?: string;
	date_effet?: string;
}

export interface RegularisationResult {
	bail_id: string;
	bien_id: string;
	annee: number;
	provisions_annuelles: number;
	charges_reelles: number;
	solde: number;
	sens: 'trop_percu' | 'complement_du' | 'equilibre';
	saved: RegularisationSaved | null;
}

export interface RegularisationSaved {
	id: string;
	id_bien: string;
	id_bail: string;
	annee: number;
	total_provisions: number;
	total_charges_reelles: number;
	solde: number;
	sens: string;
	statut: string;
	date_regularisation: string | null;
	notes: string | null;
	created_at: string;
	updated_at: string;
}

export interface AgModele {
	type_ag: string;
	ordre_du_jour: string;
	resolutions: string;
	notes: string;
}

export interface ConvocationResult {
	texte: string;
	date_envoi: string;
	ag_id: EntityId;
}

export interface SimulationCessionResult {
	nb_parts: number;
	prix_unitaire: number;
	prix_total: number;
	droits_enregistrement: number;
	taux_droits: number;
	checklist: string[];
}

export interface FiscalitePrefillResult {
	annee: number;
	total_revenus: number;
	total_charges: number;
	interets_emprunt: number;
	travaux: number;
	frais_gestion: number;
	assurance: number;
	taxe_fonciere: number;
	copropriete: number;
	resultat_fiscal: number;
}

export interface DissoudreSciPayload {
	motif: string;
	date_dissolution?: string;
}

export interface ChangerGerantPayload {
	associe_id: EntityId;
	date_effet: string;
}

export interface ModifierCapitalPayload {
	nouveau_capital: number;
	nb_parts: number;
}

export interface CederBienPayload {
	prix_cession: number;
	date_cession: string;
	acquereur: string;
}

export interface CessionBienResult {
	success: boolean;
	plus_value_brute: number;
}

export interface AvenantBailPayload {
	type_avenant: 'revision_loyer' | 'modif_charges' | 'ajout_locataire' | 'autre';
	nouvelle_valeur: string;
	date_effet: string;
	motif: string;
}

export interface DeclarerSinistrePayload {
	date_sinistre: string;
	description: string;
	montant_estime?: number | null;
	numero_dossier?: string | null;
}

export interface SinistreResult {
	evenement: Record<string, unknown>;
	assurance_pno: Record<string, unknown> | null;
}

// --- Bilans mensuels ---

export type BilanLigne = {
	date: string;
	libelle: string;
	entrees: number;
	sorties: number;
	solde: number;
	type: 'loyer' | 'charge' | 'sous_total_bien' | 'sous_total_sci' | 'total';
	statut?: LoyerStatus | string | null;
};

export type BilanBien = {
	bien_id: EntityId;
	adresse: string;
	ville?: string | null;
	lignes: BilanLigne[];
	total_entrees: number;
	total_sorties: number;
	solde: number;
};

export type BilanSci = {
	sci_id: EntityId;
	sci_nom: string;
	biens: BilanBien[];
	total_entrees: number;
	total_sorties: number;
	solde: number;
};

export type BilanKpis = {
	revenus_attendus: number;
	revenus_encaisses: number;
	charges_totales: number;
	cashflow_net: number;
	taux_recouvrement: number;
	nb_biens: number;
	nb_scis: number;
};

export type BilanData = {
	periode: string;
	scope: string;
	scope_id?: string | null;
	scis: BilanSci[];
	total_entrees: number;
	total_sorties: number;
	solde: number;
	kpis: BilanKpis;
};

export type BilanPeriodesResponse = {
	periodes: string[];
};
