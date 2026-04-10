import { apiFetch } from './client';

export interface BatchGenerateResult {
	generated: number;
	errors: string[];
}

export function batchGenerateQuittances(mois: string): Promise<BatchGenerateResult> {
	return apiFetch<BatchGenerateResult>('/api/v1/quitus/batch-generate', {
		method: 'POST',
		body: JSON.stringify({ mois })
	});
}
