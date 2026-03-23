import { apiFetch, apiFetchBlob } from './client';
import type {
	EntityId,
	Bien,
	BienCreatePayload,
	BienUpdatePayload,
	FicheBien,
	BailEmbed,
	BailCreate,
	BailUpdate,
	AssurancePnoEmbed,
	PnoCreate,
	PnoUpdate,
	FraisAgenceEmbed,
	FraisCreate,
	Evenement,
	EvenementCreatePayload,
	ObligationsData,
	ClotureBailPayload,
	CongeBailPayload,
	AvenantBailPayload,
	DeclarerSinistrePayload,
	SinistreResult,
	ImportResult,
	CederBienPayload,
	CessionBienResult
} from './types';

export function updateBien(bienId: EntityId, payload: BienUpdatePayload) {
	return apiFetch<Bien>(`/api/v1/biens/${bienId}`, {
		method: 'PATCH',
		body: JSON.stringify(payload)
	});
}

export function deleteBien(bienId: EntityId) {
	return apiFetch<void>(`/api/v1/biens/${bienId}`, {
		method: 'DELETE'
	});
}

export async function fetchFicheBien(sciId: EntityId, bienId: EntityId): Promise<FicheBien> {
	return apiFetch<FicheBien>(`/api/v1/scis/${sciId}/biens/${bienId}`);
}

export async function fetchSciBiensList(sciId: EntityId): Promise<Bien[]> {
	return apiFetch<Bien[]>(`/api/v1/scis/${sciId}/biens`);
}

export async function createBienForSci(sciId: EntityId, data: BienCreatePayload): Promise<Bien> {
	return apiFetch<Bien>(`/api/v1/scis/${sciId}/biens`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function cederBien(
	sciId: EntityId,
	bienId: EntityId,
	data: CederBienPayload
): Promise<CessionBienResult> {
	return apiFetch<CessionBienResult>(`/api/v1/scis/${sciId}/biens/${bienId}/cession`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function fetchEvenements(sciId: EntityId, bienId: EntityId): Promise<Evenement[]> {
	return apiFetch<Evenement[]>(`/api/v1/scis/${sciId}/biens/${bienId}/evenements`);
}

export async function createEvenement(
	sciId: EntityId,
	bienId: EntityId,
	data: EvenementCreatePayload
): Promise<Evenement> {
	return apiFetch<Evenement>(`/api/v1/scis/${sciId}/biens/${bienId}/evenements`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deleteEvenement(
	sciId: EntityId,
	bienId: EntityId,
	eventId: EntityId
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/evenements/${eventId}`, {
		method: 'DELETE'
	});
}

export async function fetchObligations(
	sciId: EntityId,
	bienId: EntityId
): Promise<ObligationsData> {
	return apiFetch<ObligationsData>(`/api/v1/scis/${sciId}/biens/${bienId}/obligations`);
}

export async function fetchBienBaux(sciId: EntityId, bienId: EntityId): Promise<BailEmbed[]> {
	return apiFetch<BailEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/baux`);
}

export async function createBail(
	sciId: EntityId,
	bienId: EntityId,
	data: BailCreate
): Promise<BailEmbed> {
	return apiFetch<BailEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/baux`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function updateBail(
	sciId: EntityId,
	bienId: EntityId,
	bailId: EntityId,
	data: BailUpdate
): Promise<BailEmbed> {
	return apiFetch<BailEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}`, {
		method: 'PATCH',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deleteBail(
	sciId: EntityId,
	bienId: EntityId,
	bailId: EntityId
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}`, {
		method: 'DELETE'
	});
}

export function cloturerBail(
	sciId: string,
	bienId: string,
	bailId: string,
	data: ClotureBailPayload
) {
	return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/cloturer`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export function donnerConge(sciId: string, bienId: string, bailId: string, data: CongeBailPayload) {
	return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/conge`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export function creerAvenant(
	sciId: EntityId,
	bienId: EntityId,
	bailId: EntityId,
	data: AvenantBailPayload
) {
	return apiFetch<{ success: boolean }>(
		`/api/v1/scis/${sciId}/biens/${bienId}/baux/${bailId}/avenant`,
		{
			method: 'POST',
			body: JSON.stringify(data),
			headers: { 'Content-Type': 'application/json' }
		}
	);
}

export async function fetchBienPno(
	sciId: EntityId,
	bienId: EntityId
): Promise<AssurancePnoEmbed[]> {
	return apiFetch<AssurancePnoEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno`);
}

export async function createPnoForBien(
	sciId: EntityId,
	bienId: EntityId,
	data: PnoCreate
): Promise<AssurancePnoEmbed> {
	return apiFetch<AssurancePnoEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function updatePnoForBien(
	sciId: EntityId,
	bienId: EntityId,
	pnoId: number,
	data: PnoUpdate
): Promise<AssurancePnoEmbed> {
	return apiFetch<AssurancePnoEmbed>(
		`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno/${pnoId}`,
		{
			method: 'PATCH',
			body: JSON.stringify(data),
			headers: { 'Content-Type': 'application/json' }
		}
	);
}

export async function deletePnoForBien(
	sciId: EntityId,
	bienId: EntityId,
	pnoId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno/${pnoId}`, {
		method: 'DELETE'
	});
}

export function declarerSinistre(sciId: EntityId, bienId: EntityId, data: DeclarerSinistrePayload) {
	return apiFetch<SinistreResult>(`/api/v1/scis/${sciId}/biens/${bienId}/sinistre`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function fetchBienFraisAgence(
	sciId: EntityId,
	bienId: EntityId
): Promise<FraisAgenceEmbed[]> {
	return apiFetch<FraisAgenceEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/frais-agence`);
}

export async function createFraisForBien(
	sciId: EntityId,
	bienId: EntityId,
	data: FraisCreate
): Promise<FraisAgenceEmbed> {
	return apiFetch<FraisAgenceEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/frais-agence`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deleteFraisForBien(
	sciId: EntityId,
	bienId: EntityId,
	fraisId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/frais-agence/${fraisId}`, {
		method: 'DELETE'
	});
}

export function exportBiensCsv(sciId?: EntityId): Promise<Blob> {
	const params = sciId != null ? `?sci_id=${encodeURIComponent(String(sciId))}` : '';
	return apiFetchBlob(`/api/v1/export/biens/csv${params}`);
}
