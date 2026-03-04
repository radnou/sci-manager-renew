import { afterEach, describe, expect, it, vi } from 'vitest';
import { createBien, createLoyer, fetchBiens, fetchLoyers } from './api';

describe('api helpers', () => {
	afterEach(() => {
		vi.restoreAllMocks();
	});

	it('fetchBiens returns parsed payload', async () => {
		const payload = [{ adresse: '14 rue Saint-Honore', ville: 'Paris' }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledWith('/v1/biens', undefined);
	});

	it('fetchLoyers returns parsed payload', async () => {
		const payload = [{ id_bien: 'BIEN-001', date_loyer: '2026-03-01', montant: 1200 }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchLoyers()).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledWith('/v1/loyers', undefined);
	});

	it('createBien posts JSON body', async () => {
		const payload = { adresse: '8 avenue des Tilleuls', ville: 'Lyon', statut: 'occupe' };
		const created = { id: 1, ...payload };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createBien(payload)).resolves.toEqual(created);
		expect(fetchMock).toHaveBeenCalledWith('/v1/biens', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
	});

	it('createLoyer posts JSON body', async () => {
		const payload = { id_bien: 'BIEN-004', date_loyer: '2026-03-02', montant: 930, statut: 'paye' };
		const created = { id: 8, ...payload };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createLoyer(payload)).resolves.toEqual(created);
		expect(fetchMock).toHaveBeenCalledWith('/v1/loyers', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(payload)
		});
	});

	it('throws response text when backend returns an error', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response('Erreur fonctionnelle', { status: 422 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).rejects.toThrowError('Erreur fonctionnelle');
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});

	it('falls back to status message when backend error body is empty', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 500 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).rejects.toThrowError('HTTP 500 on /v1/biens');
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});

	it('returns undefined for 204 responses', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).resolves.toBeUndefined();
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});
});
