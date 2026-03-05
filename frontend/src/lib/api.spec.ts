import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { getCurrentSessionMock } = vi.hoisted(() => ({
	getCurrentSessionMock: vi.fn()
}));

vi.mock(
	'$lib/auth/session',
	() => ({
		getCurrentSession: getCurrentSessionMock
	})
);

import { API_URL, createBien, createLoyer, fetchBiens, fetchLoyers, fetchSciDetail, fetchScis } from './api';

describe('api helpers', () => {
	afterEach(() => {
		vi.restoreAllMocks();
	});

	beforeEach(() => {
		getCurrentSessionMock.mockReset();
		getCurrentSessionMock.mockResolvedValue(null);
	});

	it('fetchBiens returns parsed payload', async () => {
		const payload = [{ id_sci: 'sci-1', adresse: '14 rue Saint-Honore', ville: 'Paris' }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/biens/`);
		expect(options).toBeDefined();
		const headers = new Headers(options.headers);
		expect(headers.get('Content-Type')).toBe('application/json');
		expect(headers.get('Authorization')).toBeNull();
	});

	it('fetchLoyers returns parsed payload', async () => {
		const payload = [{ id_bien: 'BIEN-001', date_loyer: '2026-03-01', montant: 1200, statut: 'paye' }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchLoyers()).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/loyers/`);
	});

	it('fetchScis returns parsed payload', async () => {
		const payload = [{ id: 'sci-1', nom: 'SCI Mosa Belleville', regime_fiscal: 'IR' }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchScis()).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/`);
	});

	it('fetchSciDetail targets the selected SCI detail endpoint', async () => {
		const payload = { id: 'sci-1', nom: 'SCI Mosa Belleville', biens_count: 2 };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchSciDetail('sci-1')).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1`);
	});

	it('createBien posts JSON body', async () => {
		const payload = {
			id_sci: 'sci-1',
			adresse: '8 avenue des Tilleuls',
			ville: 'Lyon',
			code_postal: '69001',
			type_locatif: 'nu' as const,
			loyer_cc: 1100,
			charges: 120,
			tmi: 30
		};
		const created = { id: 'bien-1', ...payload };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createBien(payload)).resolves.toEqual(created);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/biens/`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
		const headers = new Headers(options.headers);
		expect(headers.get('Content-Type')).toBe('application/json');
	});

	it('createLoyer posts JSON body', async () => {
		const payload = {
			id_bien: 'BIEN-004',
			date_loyer: '2026-03-02',
			montant: 930,
			statut: 'paye' as const
		};
		const created = { id: 'loyer-8', ...payload };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createLoyer(payload)).resolves.toEqual(created);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/loyers/`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
		const headers = new Headers(options.headers);
		expect(headers.get('Content-Type')).toBe('application/json');
	});

	it('adds authorization header when a supabase session is available', async () => {
		const payload = [{ adresse: '10 rue Victor Hugo' }];
		getCurrentSessionMock.mockResolvedValue({ access_token: 'token-test' });
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).resolves.toEqual(payload);

		const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		const headers = new Headers(options.headers);
		expect(headers.get('Authorization')).toBe('Bearer token-test');
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

		await expect(fetchBiens()).rejects.toThrowError(/API error: 500/);
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});

	it('returns undefined for 204 responses', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).resolves.toBeUndefined();
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});
});
