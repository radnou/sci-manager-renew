import { apiFetch } from './client';

export interface BatchGenerateResult {
	generated: number;
	errors: string[];
}

export interface SendQuittanceEmailResult {
	message: string;
}

export function batchGenerateQuittances(mois: string): Promise<BatchGenerateResult> {
	return apiFetch<BatchGenerateResult>('/api/v1/quitus/batch-generate', {
		method: 'POST',
		body: JSON.stringify({ mois })
	});
}

export function sendQuittanceEmail(
	filename: string,
	bienId: string
): Promise<SendQuittanceEmailResult> {
	const params = new URLSearchParams({ bien_id: bienId });
	return apiFetch<SendQuittanceEmailResult>(
		`/api/v1/quitus/send-email/${encodeURIComponent(filename)}?${params}`,
		{
			method: 'POST'
		}
	);
}
