import { getCurrentSession } from '$lib/auth/session';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export type EntityId = number | string;

export type BienType = 'nu' | 'meuble' | 'mixte';
export type LoyerStatus = 'en_attente' | 'paye' | 'en_retard';

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

export type Loyer = {
	id?: EntityId;
	id_bien: EntityId;
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
	loyer_cc: number;
	charges: number;
	tmi: number;
	acquisition_date?: string;
	prix_acquisition?: number;
};

export type LoyerCreatePayload = {
	id_bien: EntityId;
	id_locataire?: EntityId;
	date_loyer: string;
	montant: number;
	statut: LoyerStatus;
	quitus_genere?: boolean;
};

export type QuitusRequestPayload = {
	id_loyer: EntityId;
	id_bien: EntityId;
	nom_locataire: string;
	periode: string;
	montant: number;
};

export type QuitusResponsePayload = {
	filename: string;
	pdf_url: string;
	size_bytes: number;
};

export type CheckoutMode = 'subscription' | 'payment';

export type CheckoutSessionRequestPayload = {
	price_id: string;
	mode?: CheckoutMode;
};

export type CheckoutSessionResponsePayload = {
	url: string;
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

export function createBien(bien: BienCreatePayload) {
	return apiFetch<Bien>('/api/v1/biens/', {
		method: 'POST',
		body: JSON.stringify(bien)
	});
}

export function fetchLoyers() {
	return apiFetch<Loyer[]>('/api/v1/loyers/');
}

export function createLoyer(loyer: LoyerCreatePayload) {
	return apiFetch<Loyer>('/api/v1/loyers/', {
		method: 'POST',
		body: JSON.stringify(loyer)
	});
}

export function generateQuitus(payload: QuitusRequestPayload) {
	return apiFetch<QuitusResponsePayload>('/api/v1/quitus/generate', {
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
