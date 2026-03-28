import { apiFetch } from './client';

export async function seedDemo(): Promise<{ message: string; sci_id?: string; already_seeded?: boolean }> {
	return apiFetch('/api/v1/demo/seed', { method: 'POST' });
}

export async function cleanupDemo(): Promise<{ message: string; deleted: number }> {
	return apiFetch('/api/v1/demo/cleanup', { method: 'DELETE' });
}
