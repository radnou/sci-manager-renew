import { apiFetch } from './client';
import type {
	EntityId,
	Locataire,
	LocataireCreatePayload,
	LocataireUpdatePayload
} from './types';

export function createLocataire(payload: LocataireCreatePayload) {
	return apiFetch<Locataire>('/api/v1/locataires', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function updateLocataire(locataireId: EntityId, payload: LocataireUpdatePayload) {
	return apiFetch<Locataire>(`/api/v1/locataires/${locataireId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteLocataire(locataireId: EntityId) {
	return apiFetch<void>(`/api/v1/locataires/${locataireId}`, {
		method: 'DELETE'
	});
}

export async function attachLocataireToBail(
	sciId: EntityId,
	bienId: EntityId,
	bailId: EntityId,
	locataireId: EntityId
): Promise<{ bail_id: string; locataire_id: number }> {
	return apiFetch<{ bail_id: string; locataire_id: number }>(
		`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/locataires`,
		{
			method: 'POST',
			body: JSON.stringify({ locataire_id: locataireId }),
			headers: { 'Content-Type': 'application/json' }
		}
	);
}

export async function detachLocataireFromBail(
	sciId: EntityId,
	bienId: EntityId,
	bailId: EntityId,
	locataireId: EntityId
): Promise<void> {
	return apiFetch<void>(
		`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/locataires/${locataireId}`,
		{
			method: 'DELETE'
		}
	);
}
