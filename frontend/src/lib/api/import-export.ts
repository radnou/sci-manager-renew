import { apiFetch, apiFetchBlob } from './client';
import type { EntityId, ImportResult } from './types';

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
