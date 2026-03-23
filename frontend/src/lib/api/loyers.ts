import { apiFetch, apiFetchBlob } from './client';
import type {
	EntityId,
	Loyer,
	LoyerUpdatePayload,
	LoyerCreatePayload,
	LoyerEmbed,
	ImportResult
} from './types';

export function updateLoyer(loyerId: EntityId, payload: LoyerUpdatePayload) {
	return apiFetch<Loyer>(`/api/v1/loyers/${loyerId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteLoyer(loyerId: EntityId) {
	return apiFetch<void>(`/api/v1/loyers/${loyerId}`, {
		method: 'DELETE'
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

export function exportLoyersCsv(sciId?: EntityId, period?: string): Promise<Blob> {
	const searchParams = new URLSearchParams();
	if (sciId != null) searchParams.set('sci_id', String(sciId));
	if (period) searchParams.set('period', period);
	const qs = searchParams.toString();
	return apiFetchBlob(`/api/v1/export/loyers/csv${qs ? `?${qs}` : ''}`);
}
