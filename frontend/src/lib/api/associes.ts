import { apiFetch } from './client';
import type {
	EntityId,
	Associe,
	AssocieUpdatePayload,
	InviteAssociePayload,
	AssocieEmbed
} from './types';

export function fetchAssocies(sciId?: EntityId) {
	const query = sciId != null ? `?id_sci=${encodeURIComponent(String(sciId))}` : '';
	return apiFetch<Associe[]>(`/api/v1/associes/${query}`);
}

export function updateAssocie(associeId: EntityId, payload: AssocieUpdatePayload) {
	return apiFetch<Associe>(`/api/v1/associes/${associeId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteAssocie(associeId: EntityId) {
	return apiFetch<void>(`/api/v1/associes/${associeId}`, {
		method: 'DELETE'
	});
}

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
