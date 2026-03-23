import { apiFetch } from './client';
import type { DashboardData, FinancesData, EcheancesResponse } from './types';

export async function fetchDashboard(annee?: number): Promise<DashboardData> {
	const params = annee ? `?annee=${annee}` : '';
	return apiFetch<DashboardData>(`/api/v1/dashboard${params}`);
}

export async function fetchFinances(period?: string): Promise<FinancesData> {
	const params = period ? `?period=${period}` : '';
	return apiFetch<FinancesData>(`/api/v1/finances${params}`);
}

export function fetchEcheances(sciId?: string): Promise<EcheancesResponse> {
	const qs = sciId ? `?sci_id=${sciId}` : '';
	return apiFetch<EcheancesResponse>(`/api/v1/echeances${qs}`);
}
