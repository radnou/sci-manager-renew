import { apiFetch } from './client';
import type {
	EntityId,
	SCIOverview,
	SCIDetail,
	SCICreatePayload,
	SCIUpdatePayload,
	Bien,
	Associe,
	AssocieEmbed,
	AssembleeGenerale,
	AssembleeGeneraleInput,
	AgModele,
	ConvocationResult,
	SimulationCessionResult,
	DissoudreSciPayload,
	ChangerGerantPayload,
	ModifierCapitalPayload,
	ComptabiliteAnnuelle
} from './types';

export function fetchScis() {
	return apiFetch<SCIOverview[]>('/api/v1/scis/');
}

export function createSci(payload: SCICreatePayload) {
	return apiFetch<SCIOverview>('/api/v1/scis/', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function fetchSciDetail(sciId: EntityId) {
	return apiFetch<SCIDetail>(`/api/v1/scis/${sciId}`);
}

export async function updateSci(sciId: EntityId, data: SCIUpdatePayload): Promise<SCIOverview> {
	return apiFetch<SCIOverview>(`/api/v1/scis/${sciId}`, {
		method: 'PATCH',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export async function deleteSci(sciId: EntityId): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}`, {
		method: 'DELETE'
	});
}

export function fetchSciBiens(sciId: EntityId) {
	return apiFetch<Bien[]>(`/api/v1/scis/${sciId}/biens`);
}

export function fetchSciAssocies(sciId: EntityId) {
	return apiFetch<Associe[]>(`/api/v1/scis/${sciId}/associes`);
}

export async function fetchSciAssociesList(sciId: EntityId): Promise<AssocieEmbed[]> {
	return apiFetch<AssocieEmbed[]>(`/api/v1/scis/${sciId}/associes`);
}

export function fetchMouvementsParts(sciId: EntityId) {
	return apiFetch<any[]>(`/api/v1/scis/${sciId}/mouvements-parts`);
}

export function createMouvementParts(sciId: EntityId, data: any) {
	return apiFetch<any>(`/api/v1/scis/${sciId}/mouvements-parts`, {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export function deleteMouvementParts(sciId: EntityId, id: EntityId) {
	return apiFetch<void>(`/api/v1/scis/${sciId}/mouvements-parts/${id}`, {
		method: 'DELETE'
	});
}

export function fetchAssembleesGenerales(sciId: EntityId) {
	return apiFetch<AssembleeGenerale[]>(`/api/v1/scis/${sciId}/assemblees-generales`);
}

export function createAssembleeGenerale(sciId: EntityId, data: AssembleeGeneraleInput) {
	return apiFetch<AssembleeGenerale>(`/api/v1/scis/${sciId}/assemblees-generales`, {
		method: 'POST',
		body: JSON.stringify(data)
	});
}

export function updateAssembleeGenerale(
	sciId: EntityId,
	id: EntityId,
	data: AssembleeGeneraleInput
) {
	return apiFetch<AssembleeGenerale>(`/api/v1/scis/${sciId}/assemblees-generales/${id}`, {
		method: 'PATCH',
		body: JSON.stringify(data)
	});
}

export function deleteAssembleeGenerale(sciId: EntityId, id: EntityId) {
	return apiFetch<void>(`/api/v1/scis/${sciId}/assemblees-generales/${id}`, {
		method: 'DELETE'
	});
}

export function fetchAgModele(sciId: EntityId, type: string) {
	return apiFetch<AgModele>(`/api/v1/scis/${sciId}/assemblees-generales/modele/${type}`);
}

export function genererConvocation(sciId: EntityId, agId: EntityId) {
	return apiFetch<ConvocationResult>(
		`/api/v1/scis/${sciId}/assemblees-generales/${agId}/convocation`,
		{ method: 'POST' }
	);
}

export function simulerDroitsCession(sciId: EntityId, nbParts: number, prixUnitaire: number) {
	return apiFetch<SimulationCessionResult>(`/api/v1/scis/${sciId}/mouvements-parts/simulation`, {
		method: 'POST',
		body: JSON.stringify({ nb_parts: nbParts, prix_unitaire: prixUnitaire }),
		headers: { 'Content-Type': 'application/json' }
	});
}

export function dissoudreSci(sciId: EntityId, data: DissoudreSciPayload) {
	return apiFetch<{ success: boolean }>(`/api/v1/scis/${sciId}/dissoudre`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export function changerGerant(sciId: EntityId, data: ChangerGerantPayload) {
	return apiFetch<{ success: boolean }>(`/api/v1/scis/${sciId}/changer-gerant`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export function modifierCapital(sciId: EntityId, data: ModifierCapitalPayload) {
	return apiFetch<{ success: boolean }>(`/api/v1/scis/${sciId}/modifier-capital`, {
		method: 'POST',
		body: JSON.stringify(data),
		headers: { 'Content-Type': 'application/json' }
	});
}

export function marquerEcheanceFiscaleFaite(sciId: EntityId, annee: number, key: string) {
	return apiFetch<{ success: boolean }>(
		`/api/v1/scis/${sciId}/calendrier-fiscal/${annee}/${key}/marquer-fait`,
		{
			method: 'POST'
		}
	);
}

export function demarquerEcheanceFiscale(sciId: EntityId, annee: number, key: string) {
	return apiFetch<{ success: boolean }>(
		`/api/v1/scis/${sciId}/calendrier-fiscal/${annee}/${key}/demarquer`,
		{
			method: 'POST'
		}
	);
}

export function fetchCalendrierFiscalStatut(sciId: EntityId, annee: number) {
	return apiFetch<Record<string, boolean>>(`/api/v1/scis/${sciId}/calendrier-fiscal/${annee}/statut`);
}

export async function fetchComptabiliteAnnuelle(
	sciId: EntityId,
	annee: number
): Promise<ComptabiliteAnnuelle> {
	return apiFetch<ComptabiliteAnnuelle>(`/api/v1/scis/${sciId}/comptabilite/${annee}`);
}
