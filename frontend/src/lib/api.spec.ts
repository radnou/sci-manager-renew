import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { getCurrentSessionMock } = vi.hoisted(() => ({
	getCurrentSessionMock: vi.fn()
}));

vi.mock('$lib/auth/session', () => ({
	getCurrentSession: getCurrentSessionMock
}));

import {
	API_URL,
	createCheckoutSession,
	createBien,
	createSci,
	createLoyer,
	deleteBien,
	deleteLoyer,
	downloadQuitus,
	fetchBiens,
	fetchLoyers,
	fetchSciDetail,
	fetchScis,
	fetchSubscriptionEntitlements,
	generateQuitus,
	renderQuitus,
	updateBien,
	updateLoyer
} from './api';

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
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
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
		const payload = [
			{ id_bien: 'BIEN-001', date_loyer: '2026-03-01', montant: 1200, statut: 'paye' }
		];
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchLoyers()).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/loyers/`);
	});

	it('fetchScis returns parsed payload', async () => {
		const payload = [{ id: 'sci-1', nom: 'SCI Mosa Belleville', regime_fiscal: 'IR' }];
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchScis()).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/`);
	});

	it('fetchSciDetail targets the selected SCI detail endpoint', async () => {
		const payload = { id: 'sci-1', nom: 'SCI Mosa Belleville', biens_count: 2 };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchSciDetail('sci-1')).resolves.toEqual(payload);
		expect(fetchMock).toHaveBeenCalledTimes(1);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1`);
	});

	it('createSci posts JSON body', async () => {
		const payload = { nom: 'SCI Delta Paris', siren: '111222333', regime_fiscal: 'IR' as const };
		const created = { id: 'sci-3', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createSci(payload)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
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
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
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
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
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

	it('updateBien patches JSON body', async () => {
		const payload = {
			ville: 'Bordeaux',
			charges: 180
		};
		const updated = { id: 'bien-1', adresse: '8 avenue des Tilleuls', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(updated), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(updateBien('bien-1', payload)).resolves.toEqual(updated);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/biens/bien-1`);
		expect(options.method).toBe('PATCH');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('deleteBien sends DELETE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(deleteBien('bien-1')).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/biens/bien-1`);
		expect(options.method).toBe('DELETE');
	});

	it('updateLoyer patches JSON body', async () => {
		const payload = {
			statut: 'paye' as const,
			montant: 1450
		};
		const updated = { id: 'loyer-1', id_bien: 'bien-1', date_loyer: '2026-03-01', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(updated), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(updateLoyer('loyer-1', payload)).resolves.toEqual(updated);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/loyers/loyer-1`);
		expect(options.method).toBe('PATCH');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('deleteLoyer sends DELETE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(deleteLoyer('loyer-1')).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/loyers/loyer-1`);
		expect(options.method).toBe('DELETE');
	});

	it('renderQuitus posts JSON and returns a blob', async () => {
		const pdfResponse = new Response('pdf-binary', {
			status: 200,
			headers: { 'Content-Type': 'application/pdf' }
		});
		const fetchMock = vi.fn().mockResolvedValue(pdfResponse);
		vi.stubGlobal('fetch', fetchMock);

		const payload = {
			id_loyer: 'loyer-1',
			id_bien: 'bien-1',
			nom_locataire: 'Jean Dupont',
			periode: 'Mars 2026',
			montant: 1200,
			nom_sci: 'SCI Mosa Belleville',
			adresse_bien: '1 rue Seed',
			ville_bien: 'Paris'
		};

		const blob = await renderQuitus(payload);
		expect(blob.type).toBe('application/pdf');

		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/quitus/render`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
		const headers = new Headers(options.headers);
		expect(headers.get('Content-Type')).toBe('application/json');
	});

	it('generateQuitus posts JSON payload', async () => {
		const payload = {
			id_loyer: 'loyer-1',
			id_bien: 'bien-1',
			nom_locataire: 'Jean Dupont',
			periode: 'Mars 2026',
			montant: 1200
		};
		const fetchMock = vi
			.fn()
			.mockResolvedValue(
				new Response(JSON.stringify({ filename: 'q.pdf', pdf_url: '/api/v1/quitus/files/q.pdf', size_bytes: 42 }), { status: 200 })
			);
		vi.stubGlobal('fetch', fetchMock);

		await expect(generateQuitus(payload)).resolves.toEqual({
			filename: 'q.pdf',
			pdf_url: '/api/v1/quitus/files/q.pdf',
			size_bytes: 42
		});
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/quitus/generate`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('downloadQuitus fetches a PDF blob', async () => {
		const fetchMock = vi.fn().mockResolvedValue(
			new Response('pdf-binary', {
				status: 200,
				headers: { 'Content-Type': 'application/pdf' }
			})
		);
		vi.stubGlobal('fetch', fetchMock);

		const blob = await downloadQuitus('/api/v1/quitus/files/q.pdf');
		expect(blob.type).toBe('application/pdf');
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/quitus/files/q.pdf`);
		expect(options.method).toBeUndefined();
	});

	it('createCheckoutSession posts JSON payload', async () => {
		const payload = { plan_key: 'starter' as const, mode: 'subscription' as const };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify({ url: 'https://checkout.test' }), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createCheckoutSession(payload)).resolves.toEqual({ url: 'https://checkout.test' });
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/stripe/create-checkout-session`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('fetchSubscriptionEntitlements returns the active offer summary', async () => {
		const payload = {
			plan_key: 'starter',
			plan_name: 'Starter',
			status: 'active',
			mode: 'subscription',
			is_active: true,
			entitlements_version: 1,
			max_scis: 1,
			max_biens: 5,
			current_scis: 1,
			current_biens: 2,
			remaining_scis: 0,
			remaining_biens: 3,
			over_limit: false,
			features: { multi_sci_enabled: false, quitus_enabled: true }
		};
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchSubscriptionEntitlements()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/stripe/subscription`);
	});

	it('adds authorization header when a supabase session is available', async () => {
		const payload = [{ adresse: '10 rue Victor Hugo' }];
		getCurrentSessionMock.mockResolvedValue({ access_token: 'token-test' });
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).resolves.toEqual(payload);

		const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		const headers = new Headers(options.headers);
		expect(headers.get('Authorization')).toBe('Bearer token-test');
	});

	it('throws response text when backend returns an error', async () => {
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response('Erreur fonctionnelle', { status: 422 }));
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

	it('api blob helpers propagate API status fallback errors', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 404 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(downloadQuitus('/api/v1/quitus/files/missing.pdf')).rejects.toThrowError(
			/API error: 404/
		);
	});

	it('continues without auth header when session lookup throws', async () => {
		getCurrentSessionMock.mockRejectedValue(new Error('session unavailable'));
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify([]), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).resolves.toEqual([]);
		const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		const headers = new Headers(options.headers);
		expect(headers.get('Authorization')).toBeNull();
	});

	it('returns undefined for 204 responses', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBiens()).resolves.toBeUndefined();
		expect(fetchMock).toHaveBeenCalledTimes(1);
	});
});
