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

export function downloadImportTemplate(type: 'biens' | 'loyers'): Promise<Blob> {
	return apiFetchBlob(`/api/v1/import/templates/${type}`);
}

export async function importCsv(
	sciId: EntityId,
	type: 'biens' | 'loyers',
	file: File
): Promise<ImportResult> {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('type', type);
	return apiFetch<ImportResult>(`/api/v1/scis/${sciId}/import/csv`, {
		method: 'POST',
		body: formData
	});
}
