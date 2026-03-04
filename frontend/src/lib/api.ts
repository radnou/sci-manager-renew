export type EntityId = number | string;

export type Bien = {
	id?: EntityId;
	id_sci?: EntityId;
	adresse: string;
	ville?: string | null;
	loyer_cc?: number | null;
	statut?: string | null;
	created_at?: string;
};

export type Loyer = {
	id?: EntityId;
	id_bien: EntityId;
	date_loyer: string;
	montant: number;
	statut?: string | null;
	created_at?: string;
};

export type BienCreatePayload = {
	id_sci?: EntityId;
	adresse: string;
	ville?: string;
	loyer_cc?: number;
	statut?: string;
};

export type LoyerCreatePayload = {
	id_bien: EntityId;
	date_loyer: string;
	montant: number;
	statut?: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(path, init);

	if (!res.ok) {
		const message = await res.text();
		throw new Error(message || `HTTP ${res.status} on ${path}`);
	}

	if (res.status === 204) {
		return undefined as T;
	}

	return (await res.json()) as T;
}

export function fetchBiens() {
	return request<Bien[]>('/v1/biens');
}

export function createBien(bien: BienCreatePayload) {
	return request<Bien>('/v1/biens', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(bien)
	});
}

export function fetchLoyers() {
	return request<Loyer[]>('/v1/loyers');
}

export function createLoyer(loyer: LoyerCreatePayload) {
	return request<Loyer>('/v1/loyers', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(loyer)
	});
}
