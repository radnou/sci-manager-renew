import { apiFetch, apiFetchBlob } from './client';
import type {
	EntityId,
	QuitusRequestPayload,
	QuitusResponsePayload,
	Cerfa2044Request,
	SciDocumentItem,
	DocumentBienEmbed,
	Cerfa2044RequestPayload,
	Cerfa2044ResponsePayload,
	FileUploadResponse,
	FileDownloadResponse,
	FileListResponse
} from './types';

export function generateQuitus(payload: QuitusRequestPayload) {
	return apiFetch<QuitusResponsePayload>('/api/v1/quitus/generate', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function renderQuitus(payload: QuitusRequestPayload) {
	return apiFetchBlob('/api/v1/quitus/render', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function downloadQuitus(filePath: string) {
	return apiFetchBlob(filePath);
}

export function generateCerfa2044Pdf(payload: Cerfa2044Request): Promise<Blob> {
	return apiFetchBlob('/api/v1/cerfa/2044/pdf', {
		method: 'POST',
		body: JSON.stringify(payload),
		headers: { 'Content-Type': 'application/json' }
	});
}

export function downloadReport2042Pdf(
	sciId: EntityId,
	annee: number,
	associeId: EntityId
): Promise<Blob> {
	return apiFetchBlob(`/api/v1/cerfa/scis/${sciId}/report-2042/${annee}/${associeId}/pdf`);
}

export async function fetchSciDocuments(sciId: EntityId): Promise<SciDocumentItem[]> {
	return apiFetch<SciDocumentItem[]>(`/api/v1/scis/${sciId}/documents`);
}

export async function fetchBienDocuments(
	sciId: EntityId,
	bienId: EntityId
): Promise<DocumentBienEmbed[]> {
	return apiFetch<DocumentBienEmbed[]>(`/api/v1/scis/${sciId}/biens/${bienId}/documents`);
}

export async function uploadDocumentBien(
	sciId: EntityId,
	bienId: EntityId,
	file: File,
	nom: string,
	categorie: string = 'autre'
): Promise<DocumentBienEmbed> {
	const formData = new FormData();
	formData.append('file', file);
	formData.append('nom', nom);
	formData.append('categorie', categorie);

	return apiFetch<DocumentBienEmbed>(`/api/v1/scis/${sciId}/biens/${bienId}/documents`, {
		method: 'POST',
		body: formData
	});
}

export async function deleteDocumentBien(
	sciId: EntityId,
	bienId: EntityId,
	docId: number
): Promise<void> {
	return apiFetch<void>(`/api/v1/scis/${sciId}/biens/${bienId}/documents/${docId}`, {
		method: 'DELETE'
	});
}

export function uploadQuitusFile(filePath: string) {
	return apiFetch<FileUploadResponse>(
		`/api/v1/files/upload-quitus?file_path=${encodeURIComponent(filePath)}`,
		{
			method: 'POST'
		}
	);
}

export function downloadFile(filePath: string) {
	return apiFetch<FileDownloadResponse>(`/api/v1/files/download/${encodeURIComponent(filePath)}`);
}

export function deleteFile(filePath: string) {
	return apiFetch<{ success: boolean; message: string }>(
		`/api/v1/files/delete/${encodeURIComponent(filePath)}`,
		{
			method: 'DELETE'
		}
	);
}

export function listFiles(folder: string) {
	return apiFetch<FileListResponse>(`/api/v1/files/list/${encodeURIComponent(folder)}`);
}

export function generateCerfa2044(payload: Cerfa2044RequestPayload) {
	return apiFetch<Cerfa2044ResponsePayload>('/api/v1/cerfa/2044', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}
