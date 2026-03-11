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
	if (!headers.has('Content-Type')) {
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

export function fetchBiens() {
	return apiFetch<Bien[]>('/api/v1/biens/');
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

export function createBien(bien: BienCreatePayload) {
	return apiFetch<Bien>('/api/v1/biens/', {
		method: 'POST',
		body: JSON.stringify(bien)
	});
}

export function fetchLoyers() {
	return apiFetch<Loyer[]>('/api/v1/loyers/');
}

export function fetchLocataires() {
	return apiFetch<Locataire[]>('/api/v1/locataires/');
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

export function createLoyer(loyer: LoyerCreatePayload) {
	return apiFetch<Loyer>('/api/v1/loyers/', {
		method: 'POST',
		body: JSON.stringify(loyer)
	});
}

export function createLocataire(locataire: LocataireCreatePayload) {
	return apiFetch<Locataire>('/api/v1/locataires/', {
		method: 'POST',
		body: JSON.stringify(locataire)
	});
}

export function createAssocie(associe: AssocieCreatePayload) {
	return apiFetch<Associe>('/api/v1/associes/', {
		method: 'POST',
		body: JSON.stringify(associe)
	});
}

export function createCharge(charge: ChargeCreatePayload) {
	return apiFetch<Charge>('/api/v1/charges/', {
		method: 'POST',
		body: JSON.stringify(charge)
	});
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
	type: 'loyer_retard' | 'bail_expirant' | 'quittance_pending';
	message: string;
	severity: 'error' | 'warning' | 'info';
	sci_nom?: string;
	bien_adresse?: string;
	link?: string;
};

export type DashboardKpis = {
	sci_count: number;
	biens_count: number;
	taux_recouvrement: number;
	cashflow_net: number;
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
	return apiFetch('/api/v1/dashboard');
}

// --- Nested SCI/Biens API ---

export function fetchSciBiens(sciId: EntityId) {
	return apiFetch<Bien[]>(`/api/v1/scis/${sciId}/biens`);
}

export function fetchSciAssocies(sciId: EntityId) {
	return apiFetch<Associe[]>(`/api/v1/scis/${sciId}/associes`);
}
