import { getCurrentSession } from '$lib/auth/session';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export type EntityId = number | string;
export type PlanKey = 'free' | 'starter' | 'pro' | 'lifetime';

export type BienType = 'nu' | 'meuble' | 'mixte';
export type LoyerStatus = 'en_attente' | 'paye' | 'en_retard';
export type SCIStatus = 'configuration' | 'mise_en_service' | 'exploitation';

export type Associe = {
	id: EntityId;
	id_sci?: EntityId | null;
	user_id?: EntityId | null;
	nom: string;
	email?: string | null;
	part?: number | null;
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
	associes_count?: number;
	biens_count?: number;
	loyers_count?: number;
	user_role?: string | null;
	user_part?: number | null;
	associes?: Associe[];
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
	created_at?: string;
	updated_at?: string;
};

export type Bien = {
	id?: EntityId;
	id_sci?: EntityId;
	adresse: string;
	ville?: string | null;
	code_postal?: string | null;
	type_locatif?: BienType | string | null;
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

export type BienCreatePayload = {
	id_sci: EntityId;
	adresse: string;
	ville: string;
	code_postal: string;
	type_locatif: BienType;
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
	loyer_cc?: number;
	charges?: number;
	tmi?: number;
	acquisition_date?: string | null;
	prix_acquisition?: number | null;
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
};

export type FiscaliteUpdatePayload = {
	annee?: number;
	total_revenus?: number;
	total_charges?: number;
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
};

type ApiErrorPayload = {
	error?: string;
	code?: string;
	details?: unknown;
	request_id?: string;
};

export async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
	let accessToken: string | undefined;
	try {
		const session = await getCurrentSession();
		accessToken = session?.access_token;
	} catch {
		accessToken = undefined;
	}

	const headers = new Headers(options?.headers);
	const isFormData = options?.body instanceof FormData;
	if (isFormData) {
		// Let the browser set Content-Type with boundary for FormData
		headers.delete('Content-Type');
	} else if (!headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}
	if (accessToken) {
		headers.set('Authorization', `Bearer ${accessToken}`);
	}

	const response = await fetch(`${API_URL}${endpoint}`, {
		...options,
		headers
	});

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `API error: ${response.status} ${response.statusText}`);
	}

	if (response.status === 204) {
		return undefined as T;
	}

	return (await response.json()) as T;
}

export async function apiFetchBlob(endpoint: string, options?: RequestInit): Promise<Blob> {
	let accessToken: string | undefined;
	try {
		const session = await getCurrentSession();
		accessToken = session?.access_token;
	} catch {
		accessToken = undefined;
	}

	const headers = new Headers(options?.headers);
	if (options?.body && !headers.has('Content-Type')) {
		headers.set('Content-Type', 'application/json');
	}
	if (accessToken) {
		headers.set('Authorization', `Bearer ${accessToken}`);
	}

	const response = await fetch(`${API_URL}${endpoint}`, {
		...options,
		headers
	});

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `API error: ${response.status} ${response.statusText}`);
	}

	return response.blob();
}

export function fetchScis() {
	return apiFetch<SCIOverview[]>('/api/v1/scis/');
}

export function createSci(payload: SCICreatePayload) {
	return apiFetch<SCIOverview>('/api/v1/scis/', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function fetchSciDetail(sciId: EntityId) {
	return apiFetch<SCIDetail>(`/api/v1/scis/${sciId}`);
}

export function fetchAssocies(sciId?: EntityId) {
	const query = sciId != null ? `?id_sci=${encodeURIComponent(String(sciId))}` : '';
	return apiFetch<Associe[]>(`/api/v1/associes/${query}`);
}

export function fetchCharges(sciId?: EntityId) {
	const query = sciId != null ? `?id_sci=${encodeURIComponent(String(sciId))}` : '';
	return apiFetch<Charge[]>(`/api/v1/charges/${query}`);
}

export function fetchFiscalite(sciId?: EntityId) {
	const query = sciId != null ? `?id_sci=${encodeURIComponent(String(sciId))}` : '';
	return apiFetch<Fiscalite[]>(`/api/v1/fiscalite/${query}`);
}

export function createFiscalite(exercice: FiscaliteCreatePayload) {
	return apiFetch<Fiscalite>('/api/v1/fiscalite/', {
		method: 'POST',
		body: JSON.stringify(exercice)
	});
}

export function updateBien(bienId: EntityId, payload: BienUpdatePayload) {
	return apiFetch<Bien>(`/api/v1/biens/${bienId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteBien(bienId: EntityId) {
	return apiFetch<void>(`/api/v1/biens/${bienId}`, {
		method: 'DELETE'
	});
}

export function updateLoyer(loyerId: EntityId, payload: LoyerUpdatePayload) {
	return apiFetch<Loyer>(`/api/v1/loyers/${loyerId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function updateLocataire(locataireId: EntityId, payload: LocataireUpdatePayload) {
	return apiFetch<Locataire>(`/api/v1/locataires/${locataireId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function updateAssocie(associeId: EntityId, payload: AssocieUpdatePayload) {
	return apiFetch<Associe>(`/api/v1/associes/${associeId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function updateCharge(chargeId: EntityId, payload: ChargeUpdatePayload) {
	return apiFetch<Charge>(`/api/v1/charges/${chargeId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function updateFiscalite(fiscaliteId: EntityId, payload: FiscaliteUpdatePayload) {
	return apiFetch<Fiscalite>(`/api/v1/fiscalite/${fiscaliteId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteLoyer(loyerId: EntityId) {
	return apiFetch<void>(`/api/v1/loyers/${loyerId}`, {
		method: 'DELETE'
	});
}

export function deleteLocataire(locataireId: EntityId) {
	return apiFetch<void>(`/api/v1/locataires/${locataireId}`, {
		method: 'DELETE'
	});
}

export function deleteAssocie(associeId: EntityId) {
	return apiFetch<void>(`/api/v1/associes/${associeId}`, {
		method: 'DELETE'
	});
}

export function deleteCharge(chargeId: EntityId) {
	return apiFetch<void>(`/api/v1/charges/${chargeId}`, {
		method: 'DELETE'
	});
}

export function deleteFiscalite(fiscaliteId: EntityId) {
	return apiFetch<void>(`/api/v1/fiscalite/${fiscaliteId}`, {
		method: 'DELETE'
	});
}

export function generateQuitus(payload: QuitusRequestPayload) {
	return apiFetch<QuitusResponsePayload>('/api/v1/quitus/generate', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function renderQuitus(payload: QuitusRequestPayload) {
	return apiFetchBlob('/api/v1/quitus/render', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function downloadQuitus(filePath: string) {
	return apiFetchBlob(filePath);
}

export interface Cerfa2044Request {
	annee: number;
	total_revenus: number;
	total_charges: number;
	sci_nom?: string;
	siren?: string;
}

export function generateCerfa2044Pdf(payload: Cerfa2044Request): Promise<Blob> {
	return apiFetchBlob('/api/v1/cerfa/2044/pdf', {
		method: 'POST',
		body: JSON.stringify(payload),
		headers: { 'Content-Type': 'application/json' }
	});
}

export function createCheckoutSession(payload: CheckoutSessionRequestPayload) {
	return apiFetch<CheckoutSessionResponsePayload>('/api/v1/stripe/create-checkout-session', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function fetchSubscriptionEntitlements() {
	return apiFetch<SubscriptionEntitlements>('/api/v1/stripe/subscription');
}

// --- Notifications ---

export type Notification = {
	id: string;
	type: 'late_payment' | 'status_change' | 'document_ready' | 'system' | 'info';
	title: string;
	message: string;
	metadata: Record<string, unknown>;
	read_at: string | null;
	created_at: string;
};

export function fetchNotifications(unreadOnly = false): Promise<Notification[]> {
	const params = unreadOnly ? '?unread_only=true' : '';
	return apiFetch<Notification[]>(`/api/v1/notifications/${params}`);
}

export function fetchUnreadCount(): Promise<{ count: number }> {
	return apiFetch<{ count: number }>('/api/v1/notifications/count');
}

export function markNotificationRead(id: string): Promise<Notification> {
	return apiFetch<Notification>(`/api/v1/notifications/${id}/read`, { method: 'PATCH' });
}

export function markAllNotificationsRead(): Promise<{ updated: number }> {
	return apiFetch<{ updated: number }>('/api/v1/notifications/read-all', { method: 'PATCH' });
}

// --- Onboarding ---

export type OnboardingStatus = {
	completed: boolean;
	sci_created: boolean;
	sci_id: string | null;
	bien_created: boolean;
	bail_created: boolean;
	notifications_set: boolean;
};

export function fetchOnboardingStatus() {
	return apiFetch<OnboardingStatus>('/api/v1/onboarding');
}

export function completeOnboarding() {
	return apiFetch<{ completed: boolean }>('/api/v1/onboarding/complete', { method: 'POST' });
}

// --- Dashboard V2 ---

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
};

export type DashboardData = {
	alertes: DashboardAlerte[];
	kpis: DashboardKpis;
	scis: SCICard[];
	activite: ActivityItem[];
};

export async function fetchDashboard(): Promise<DashboardData> {
	return apiFetch<DashboardData>('/api/v1/dashboard');
}

// --- Nested SCI/Biens API ---

export function fetchSciBiens(sciId: EntityId) {
	return apiFetch<Bien[]>(`/api/v1/scis/${sciId}/biens`);
}

export function fetchSciAssocies(sciId: EntityId) {
	return apiFetch<Associe[]>(`/api/v1/scis/${sciId}/associes`);
}

// --- Fiche Bien (Sprint 3) ---

export type BailEmbed = {
	id: number;
	date_debut: string;
	date_fin: string | null;
	loyer_hc: number;
	charges_locatives: number;
	depot_garantie: number;
	revision_indice: string | null;
	statut: string;
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

// --- CRUD Wiring Types ---

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
};

export type BailCreate = {
	date_debut: string;
	date_fin?: string;
	loyer_hc: number;
	charges_locatives?: number;
	depot_garantie?: number;
	revision_indice?: string;
};

export type BailUpdate = Partial<BailCreate>;

export type DocumentBienEmbed = {
	id: number;
	nom: string;
	categorie: string;
	url: string;
	created_at: string;
};

export type RentabiliteCalculee = {
	brute: number;
	nette: number;
	cashflow_mensuel: number;
	cashflow_annuel: number;
};

export type FicheBien = {
	id: number;
	id_sci: number;
	adresse: string;
	ville: string;
	code_postal: string;
	type_locatif: string;
	loyer_cc: number;
	charges: number;
	surface_m2: number | null;
	nb_pieces: number | null;
	dpe_classe: string | null;
	photo_url: string | null;
	prix_acquisition: number | null;
	statut: string | null;
	bail_actif: BailEmbed | null;
	loyers_recents: LoyerEmbed[];
	charges_list: ChargeEmbed[];
	assurance_pno: AssurancePnoEmbed | null;
	frais_agence: FraisAgenceEmbed[];
	documents: DocumentBienEmbed[];
	rentabilite: RentabiliteCalculee;
};

export async function fetchFicheBien(
	sciId: EntityId,
	bienId: EntityId
): Promise<FicheBien> {
	return apiFetch<FicheBien>(`/api/v1/scis/${sciId}/biens/${bienId}`);
}

export async function fetchSciBiensList(sciId: EntityId): Promise<Bien[]> {
	return apiFetch<Bien[]>(`/api/v1/scis/${sciId}/biens`);
}

export async function createBienForSci(sciId: EntityId, data: BienCreatePayload): Promise<Bien> {
	return apiFetch<Bien>(`/api/v1/scis/${sciId}/biens`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function createLoyerForBien(
	sciId: EntityId,
	bienId: EntityId,
	data: LoyerCreatePayload
): Promise<LoyerEmbed> {
	return apiFetch<LoyerEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/loyers`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

// --- Baux (Leases) ---

export async function fetchBienBaux(sciId: EntityId, bienId: EntityId): Promise<BailEmbed[]> {
	return apiFetch<BailEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/baux`);
}

export async function createBail(sciId: EntityId, bienId: EntityId, data: BailCreate): Promise<BailEmbed> {
	return apiFetch<BailEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/baux`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function updateBail(
	sciId: EntityId,
	bienId: EntityId,
	bailId: number,
	data: BailUpdate
): Promise<BailEmbed> {
	return apiFetch<BailEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}`, {
		method: 'PATCH',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deleteBail(
	sciId: EntityId,
	bienId: EntityId,
	bailId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}`, {
		method: 'DELETE'
	});
}

export async function attachLocataireToBail(
	sciId: EntityId,
	bienId: EntityId,
	bailId: number,
	locataireId: number
): Promise<{ bail_id: number; locataire_id: number }> {
	return apiFetch<{ bail_id: number; locataire_id: number }>(`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/locataires`, {
		method: 'POST',
		body: JSON.stringify({ locataire_id: locataireId }),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function detachLocataireFromBail(
	sciId: EntityId,
	bienId: EntityId,
	bailId: number,
	locataireId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/locataires/${locataireId}`, {
		method: 'DELETE'
	});
}

// --- Nested Charges / PNO / Frais Agence / Associes ---

export async function fetchBienCharges(sciId: EntityId, bienId: EntityId): Promise<ChargeEmbed[]> {
	return apiFetch<ChargeEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/charges`);
}

export async function fetchBienPno(sciId: EntityId, bienId: EntityId): Promise<AssurancePnoEmbed[]> {
	return apiFetch<AssurancePnoEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno`);
}

export async function fetchBienFraisAgence(sciId: EntityId, bienId: EntityId): Promise<FraisAgenceEmbed[]> {
	return apiFetch<FraisAgenceEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/frais-agence`);
}

export async function fetchSciAssociesList(sciId: EntityId): Promise<AssocieEmbed[]> {
	return apiFetch<AssocieEmbed[]>(`/api/v1/scis/${sciId}/associes`);
}

// --- Charge mutations ---
export async function createChargeForBien(
	sciId: EntityId,
	bienId: EntityId,
	data: ChargeCreate
): Promise<ChargeEmbed> {
	return apiFetch<ChargeEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/charges`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deleteChargeForBien(
	sciId: EntityId,
	bienId: EntityId,
	chargeId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/charges/${chargeId}`, {
		method: 'DELETE'
	});
}

// --- PNO mutations ---
export async function createPnoForBien(
	sciId: EntityId,
	bienId: EntityId,
	data: PnoCreate
): Promise<AssurancePnoEmbed> {
	return apiFetch<AssurancePnoEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function updatePnoForBien(
	sciId: EntityId,
	bienId: EntityId,
	pnoId: number,
	data: PnoUpdate
): Promise<AssurancePnoEmbed> {
	return apiFetch<AssurancePnoEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno/${pnoId}`, {
		method: 'PATCH',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deletePnoForBien(
	sciId: EntityId,
	bienId: EntityId,
	pnoId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno/${pnoId}`, {
		method: 'DELETE'
	});
}

// --- Frais Agence mutations ---
export async function createFraisForBien(
	sciId: EntityId,
	bienId: EntityId,
	data: FraisCreate
): Promise<FraisAgenceEmbed> {
	return apiFetch<FraisAgenceEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/frais-agence`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deleteFraisForBien(
	sciId: EntityId,
	bienId: EntityId,
	fraisId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/frais-agence/${fraisId}`, {
		method: 'DELETE'
	});
}

// --- Associe invite ---
export async function inviteAssocie(
	sciId: EntityId,
	data: InviteAssociePayload
): Promise<AssocieEmbed> {
	return apiFetch<AssocieEmbed>(`/api/v1/scis/${sciId}/associes`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

// --- SCI mutations ---
export type SCIUpdatePayload = {
	nom?: string;
	siren?: string | null;
	regime_fiscal?: 'IR' | 'IS';
	adresse_siege?: string | null;
	date_creation?: string | null;
	capital_social?: number | null;
	objet_social?: string | null;
	rcs_ville?: string | null;
};

export async function updateSci(
	sciId: EntityId,
	data: SCIUpdatePayload
): Promise<SCIOverview> {
	return apiFetch<SCIOverview>(`/api/v1/scis/${sciId}`, {
		method: 'PATCH',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deleteSci(sciId: EntityId): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}`, {
		method: 'DELETE'
	});
}


// --- Notification Preferences ---

export type NotificationPreference = {
	type: string;
	email_enabled: boolean;
	in_app_enabled: boolean;
};

export async function fetchNotificationPreferences(): Promise<{
	preferences: NotificationPreference[];
}> {
	return apiFetch<{ preferences: NotificationPreference[] }>('/api/v1/user/notification-preferences');
}

export async function updateNotificationPreferences(
	preferences: NotificationPreference[]
): Promise<{ preferences: NotificationPreference[] }> {
	return apiFetch<{ preferences: NotificationPreference[] }>('/api/v1/user/notification-preferences', {
		method: 'PUT',
		body: JSON.stringify({ preferences })
	});
}

// --- Finances ---

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

export async function fetchFinances(period?: string): Promise<FinancesData> {
	const params = period ? `?period=${period}` : '';
	return apiFetch<FinancesData>(`/api/v1/finances${params}`);
}

// --- Documents Bien ---

export async function fetchBienDocuments(
	sciId: EntityId,
	bienId: EntityId
): Promise<DocumentBienEmbed[]> {
	return apiFetch<DocumentBienEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/documents`);
}

export async function uploadDocumentBien(
	sciId: EntityId,
	bienId: EntityId,
	file: File,
	nom: string,
	categorie: string = 'autre'
): Promise<DocumentBienEmbed> {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('nom', nom);
	formData.append('categorie', categorie);

	return apiFetch<DocumentBienEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/documents`, {
		method: 'POST',
		body: formData
	});
}

export async function deleteDocumentBien(
	sciId: EntityId,
	bienId: EntityId,
	docId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/documents/${docId}`, {
		method: 'DELETE'
	});
}

// --- Export CSV ---

export function exportLoyersCsv(sciId?: EntityId, period?: string): Promise<Blob> {
	const searchParams = new URLSearchParams();
	if (sciId != null) searchParams.set('sci_id', String(sciId));
	if (period) searchParams.set('period', period);
	const qs = searchParams.toString();
	return apiFetchBlob(`/api/v1/export/loyers/csv${qs ? `?${qs}` : ''}`);
}

export function exportBiensCsv(sciId?: EntityId): Promise<Blob> {
	const params = sciId != null ? `?sci_id=${encodeURIComponent(String(sciId))}` : '';
	return apiFetchBlob(`/api/v1/export/biens/csv${params}`);
}

// --- CERFA 2044 ---

export type Cerfa2044RequestPayload = {
	annee: number;
	total_revenus: number;
	total_charges: number;
	sci_nom?: string;
	siren?: string;
};

export type Cerfa2044ResponsePayload = {
	status: string;
	annee: number;
	total_revenus: number;
	total_charges: number;
	resultat_fiscal: number;
	formulaire: string;
};

export function generateCerfa2044(payload: Cerfa2044RequestPayload) {
	return apiFetch<Cerfa2044ResponsePayload>('/api/v1/cerfa/2044', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

// --- Files / Storage ---

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

export function uploadQuitusFile(filePath: string) {
	return apiFetch<FileUploadResponse>(`/api/v1/files/upload-quitus?file_path=${encodeURIComponent(filePath)}`, {
		method: 'POST'
	});
}

export function downloadFile(filePath: string) {
	return apiFetch<FileDownloadResponse>(`/api/v1/files/download/${encodeURIComponent(filePath)}`);
}

export function deleteFile(filePath: string) {
	return apiFetch<{ success: boolean; message: string }>(`/api/v1/files/delete/${encodeURIComponent(filePath)}`, {
		method: 'DELETE'
	});
}

export function listFiles(folder: string) {
	return apiFetch<FileListResponse>(`/api/v1/files/list/${encodeURIComponent(folder)}`);
}

// --- GDPR / Privacy ---

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

export function exportUserData() {
	return apiFetch<DataExportResponse>('/api/v1/gdpr/data-export');
}

export function fetchDataSummary() {
	return apiFetch<DataSummaryResponse>('/api/v1/gdpr/data-summary');
}

export function deleteAccount() {
	return apiFetch<AccountDeleteResponse>('/api/v1/gdpr/account', {
		method: 'DELETE'
	});
}
