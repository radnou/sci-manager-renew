import { apiFetch, apiFetchBlob } from './client';
import type { BilanData, BilanPeriodesResponse } from './types';

export async function fetchBilan(
	periode: string,
	scope: string,
	scopeId?: string,
	forceRefresh?: boolean
): Promise<BilanData> {
	const params = new URLSearchParams({ periode, scope });
	if (scopeId) params.set('scope_id', scopeId);
	if (forceRefresh) params.set('force_refresh', 'true');
	return apiFetch<BilanData>(`/api/v1/bilans?${params}`);
}

export async function fetchBilanPeriodes(): Promise<string[]> {
	const data = await apiFetch<BilanPeriodesResponse>('/api/v1/bilans/periodes');
	return data.periodes;
}

export function downloadBilanPdf(
	periode: string,
	scope: string,
	scopeId?: string
): Promise<Blob> {
	const params = new URLSearchParams({ periode, scope });
	if (scopeId) params.set('scope_id', scopeId);
	return apiFetchBlob(`/api/v1/bilans/pdf?${params}`);
}
