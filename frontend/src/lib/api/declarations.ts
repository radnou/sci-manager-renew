import { apiFetch, apiFetchBlob } from './client';
import type { EntityId } from './types';

export interface Declaration2065 {
	sci_id: string;
	exercice: number;
	date_cloture: string;
	actif: Bilan2065;
	passif: Bilan2065;
	ecart: number;
	message: string;
}

export interface Bilan2065 {
	immobilisations?: number;
	travaux_en_cours?: number;
	creances_clients?: number;
	tresorerie?: number;
	capital_social?: number;
	reserves?: number;
	resultat?: number;
	emprunts?: number;
	fournisseurs?: number;
	autres_dettes?: number;
	libelles?: Record<string, number>;
}

export interface Declaration2065GeneratePayload {
	exercice: number;
	tresorerie?: number;
	reserves?: number;
}

export function generateDeclaration2065(
	sciId: EntityId,
	payload: Declaration2065GeneratePayload
): Promise<Declaration2065> {
	return apiFetch<Declaration2065>(`/api/v1/scis/${sciId}/declaration-2065/generate`, {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function fetchDeclaration2065(
	sciId: EntityId,
	exercice: number
): Promise<Declaration2065> {
	return apiFetch<Declaration2065>(`/api/v1/scis/${sciId}/declaration-2065/${exercice}`);
}

export function downloadDeclaration2065Pdf(
	sciId: EntityId,
	exercice: number
): Promise<Blob> {
	return apiFetchBlob(`/api/v1/scis/${sciId}/declaration-2065/${exercice}/pdf`);
}
