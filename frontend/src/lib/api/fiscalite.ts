import { apiFetch, apiFetchBlob } from './client';
import type {
	EntityId,
	Fiscalite,
	FiscaliteCreatePayload,
	FiscaliteUpdatePayload,
	ResumeFiscalData,
	FiscalitePrefillResult
} from './types';

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

export function updateFiscalite(fiscaliteId: EntityId, payload: FiscaliteUpdatePayload) {
	return apiFetch<Fiscalite>(`/api/v1/fiscalite/${fiscaliteId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteFiscalite(fiscaliteId: EntityId) {
	return apiFetch<void>(`/api/v1/fiscalite/${fiscaliteId}`, {
		method: 'DELETE'
	});
}

export function fetchResumeFiscal(sciId: EntityId, annee: number): Promise<ResumeFiscalData> {
	return apiFetch<ResumeFiscalData>(`/api/v1/cerfa/scis/${sciId}/resume-fiscal/${annee}`);
}

export function downloadResumeFiscalPdf(sciId: EntityId, annee: number): Promise<Blob> {
	return apiFetchBlob(`/api/v1/cerfa/scis/${sciId}/resume-fiscal/${annee}/pdf`);
}

export function prefillFiscalite(sciId: EntityId, annee: number) {
	return apiFetch<FiscalitePrefillResult>(
		`/api/v1/fiscalite/prefill/${annee}?id_sci=${encodeURIComponent(String(sciId))}`,
		{ method: 'POST' }
	);
}
