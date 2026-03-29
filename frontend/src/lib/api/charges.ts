import { apiFetch } from './client';
import type {
	EntityId,
	Charge,
	ChargeUpdatePayload,
	ChargeEmbed,
	ChargeCreate,
	RegularisationResult,
	RegularisationSaved
} from './types';

export function fetchCharges(sciId?: EntityId) {
	const query = sciId != null ? `?id_sci=${encodeURIComponent(String(sciId))}` : '';
	return apiFetch<Charge[]>(`/api/v1/charges/${query}`);
}

export function updateCharge(chargeId: EntityId, payload: ChargeUpdatePayload) {
	return apiFetch<Charge>(`/api/v1/charges/${chargeId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteCharge(chargeId: EntityId) {
	return apiFetch<void>(`/api/v1/charges/${chargeId}`, {
		method: 'DELETE'
	});
}

export async function fetchBienCharges(sciId: EntityId, bienId: EntityId): Promise<ChargeEmbed[]> {
	return apiFetch<ChargeEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/charges`);
}

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

export function fetchRegularisation(sciId: string, bienId: string, bailId: string, annee: number) {
	return apiFetch<RegularisationResult>(
		`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/regularisation/${annee}`
	);
}

export function confirmRegularisation(
	sciId: string,
	bienId: string,
	bailId: string,
	annee: number,
	notes?: string
) {
	return apiFetch<RegularisationSaved>(
		`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/regularisation`,
		{
			method: 'POST',
			body: JSON.stringify({ annee, notes }),
			headers: { 'Content-Type': 'application/json' }
		}
	);
}
