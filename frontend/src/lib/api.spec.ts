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
	createLocataire,
	createAssocie,
	createCharge,
	createFiscalite,
	deleteBien,
	deleteLoyer,
	deleteLocataire,
	deleteAssocie,
	deleteCharge,
	deleteFiscalite,
	downloadQuitus,
	fetchBiens,
	fetchLoyers,
	fetchLocataires,
	fetchAssocies,
	fetchCharges,
	fetchFiscalite,
	fetchNotifications,
	fetchUnreadCount,
	fetchSciDetail,
	fetchScis,
	fetchSubscriptionEntitlements,
	generateQuitus,
	markNotificationRead,
	markAllNotificationsRead,
	renderQuitus,
	updateBien,
	updateLoyer,
	updateLocataire,
	updateAssocie,
	updateCharge,
	updateFiscalite,
	// Sprint 2-7 additions
	fetchOnboardingStatus,
	completeOnboarding,
	fetchDashboard,
	fetchSciBiens,
	fetchSciAssocies,
	fetchFicheBien,
	fetchSciBiensList,
	createBienForSci,
	createLoyerForBien,
	fetchBienBaux,
	createBail,
	updateBail,
	deleteBail,
	attachLocataireToBail,
	detachLocataireFromBail,
	fetchBienCharges,
	fetchBienPno,
	fetchBienFraisAgence,
	fetchSciAssociesList,
	fetchNotificationPreferences,
	updateNotificationPreferences,
	fetchFinances,
	fetchBienDocuments,
	deleteDocumentBien
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

	it('fetchLocataires returns parsed payload', async () => {
		const payload = [{ id_bien: 'bien-1', nom: 'Jean Dupont', date_debut: '2025-01-01' }];
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchLocataires()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/locataires/`);
	});

	it('fetchAssocies returns parsed payload without filter', async () => {
		const payload = [{ id: 'a-1', nom: 'Rad', part: 60, role: 'gerant' }];
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchAssocies()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/associes/`);
	});

	it('fetchAssocies appends sci filter when provided', async () => {
		const payload = [{ id: 'a-1', nom: 'Rad', part: 60, role: 'gerant' }];
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchAssocies('sci-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/associes/?id_sci=sci-1`);
	});

	it('fetchCharges returns parsed payload without filter', async () => {
		const payload = [{ id_bien: 'bien-1', type_charge: 'assurance', montant: 240, date_paiement: '2026-01-15' }];
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchCharges()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/charges/`);
	});

	it('fetchCharges appends sci filter when provided', async () => {
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify([]), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchCharges('sci-2')).resolves.toEqual([]);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/charges/?id_sci=sci-2`);
	});

	it('fetchFiscalite returns parsed payload without filter', async () => {
		const payload = [{ id_sci: 'sci-1', annee: 2025, resultat_fiscal: 15000 }];
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchFiscalite()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/fiscalite/`);
	});

	it('fetchFiscalite appends sci filter when provided', async () => {
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify([]), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchFiscalite('sci-1')).resolves.toEqual([]);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/fiscalite/?id_sci=sci-1`);
	});

	it('createLocataire posts JSON body', async () => {
		const payload = { id_bien: 'bien-1', nom: 'Marie Martin', date_debut: '2026-01-01' };
		const created = { id: 'loc-1', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createLocataire(payload)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/locataires/`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('createAssocie posts JSON body', async () => {
		const payload = { id_sci: 'sci-1', nom: 'Paul Durand', part: 40, role: 'associe' };
		const created = { id: 'a-2', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createAssocie(payload)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/associes/`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('createCharge posts JSON body', async () => {
		const payload = { id_bien: 'bien-1', type_charge: 'travaux', montant: 500, date_paiement: '2026-03-01' };
		const created = { id: 'ch-1', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createCharge(payload)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/charges/`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('createFiscalite posts JSON body', async () => {
		const payload = { id_sci: 'sci-1', annee: 2025, total_revenus: 24000, total_charges: 6000 };
		const created = { id: 'fisc-1', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createFiscalite(payload)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/fiscalite/`);
		expect(options.method).toBe('POST');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('updateLocataire patches JSON body', async () => {
		const payload = { nom: 'Marie Martin-Dupont', email: 'marie@test.fr' };
		const updated = { id: 'loc-1', id_bien: 'bien-1', date_debut: '2026-01-01', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(updated), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(updateLocataire('loc-1', payload)).resolves.toEqual(updated);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/locataires/loc-1`);
		expect(options.method).toBe('PATCH');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('updateAssocie patches JSON body', async () => {
		const payload = { part: 50, role: 'gerant' };
		const updated = { id: 'a-1', nom: 'Rad', ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(updated), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(updateAssocie('a-1', payload)).resolves.toEqual(updated);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/associes/a-1`);
		expect(options.method).toBe('PATCH');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('updateCharge patches JSON body', async () => {
		const payload = { montant: 600 };
		const updated = { id: 'ch-1', id_bien: 'bien-1', type_charge: 'travaux', montant: 600, date_paiement: '2026-03-01' };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(updated), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(updateCharge('ch-1', payload)).resolves.toEqual(updated);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/charges/ch-1`);
		expect(options.method).toBe('PATCH');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('updateFiscalite patches JSON body', async () => {
		const payload = { total_revenus: 26000 };
		const updated = { id: 'fisc-1', id_sci: 'sci-1', annee: 2025, ...payload };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(updated), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(updateFiscalite('fisc-1', payload)).resolves.toEqual(updated);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/fiscalite/fisc-1`);
		expect(options.method).toBe('PATCH');
		expect(options.body).toBe(JSON.stringify(payload));
	});

	it('deleteLocataire sends DELETE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(deleteLocataire('loc-1')).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/locataires/loc-1`);
		expect(options.method).toBe('DELETE');
	});

	it('deleteAssocie sends DELETE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(deleteAssocie('a-1')).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/associes/a-1`);
		expect(options.method).toBe('DELETE');
	});

	it('deleteCharge sends DELETE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(deleteCharge('ch-1')).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/charges/ch-1`);
		expect(options.method).toBe('DELETE');
	});

	it('deleteFiscalite sends DELETE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(deleteFiscalite('fisc-1')).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/fiscalite/fisc-1`);
		expect(options.method).toBe('DELETE');
	});

	it('fetchNotifications returns parsed payload', async () => {
		const payload = [{ id: 'n-1', type: 'info', title: 'Test', message: 'Hello', metadata: {}, read_at: null, created_at: '2026-03-01' }];
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchNotifications()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/notifications/`);
	});

	it('fetchNotifications passes unread filter', async () => {
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify([]), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchNotifications(true)).resolves.toEqual([]);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/notifications/?unread_only=true`);
	});

	it('fetchUnreadCount returns count object', async () => {
		const payload = { count: 3 };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchUnreadCount()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/notifications/count`);
	});

	it('markNotificationRead patches notification', async () => {
		const payload = { id: 'n-1', type: 'info', title: 'Test', message: 'Hello', metadata: {}, read_at: '2026-03-10', created_at: '2026-03-01' };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(markNotificationRead('n-1')).resolves.toEqual(payload);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/notifications/n-1/read`);
		expect(options.method).toBe('PATCH');
	});

	it('apiFetchBlob adds auth header when session is available', async () => {
		getCurrentSessionMock.mockResolvedValue({ access_token: 'blob-token' });
		const pdfResponse = new Response('pdf-binary', {
			status: 200,
			headers: { 'Content-Type': 'application/pdf' }
		});
		const fetchMock = vi.fn().mockResolvedValue(pdfResponse);
		vi.stubGlobal('fetch', fetchMock);

		const blob = await downloadQuitus('/api/v1/quitus/files/doc.pdf');
		expect(blob.type).toBe('application/pdf');
		const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		const headers = new Headers(options.headers);
		expect(headers.get('Authorization')).toBe('Bearer blob-token');
	});

	it('apiFetchBlob continues without auth when session throws', async () => {
		getCurrentSessionMock.mockRejectedValue(new Error('no session'));
		const fetchMock = vi.fn().mockResolvedValue(
			new Response('pdf-binary', {
				status: 200,
				headers: { 'Content-Type': 'application/pdf' }
			})
		);
		vi.stubGlobal('fetch', fetchMock);

		const blob = await downloadQuitus('/api/v1/quitus/files/doc.pdf');
		expect(blob.type).toBe('application/pdf');
		const [, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		const headers = new Headers(options.headers);
		expect(headers.get('Authorization')).toBeNull();
	});

	it('markAllNotificationsRead patches all notifications', async () => {
		const payload = { updated: 5 };
		const fetchMock = vi
			.fn()
			.mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(markAllNotificationsRead()).resolves.toEqual(payload);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/notifications/read-all`);
		expect(options.method).toBe('PATCH');
	});

	// --- Sprint 2-7: Onboarding ---

	it('fetchOnboardingStatus returns onboarding state', async () => {
		const payload = { completed: false, sci_created: true, bien_created: false, bail_created: false, notifications_set: false };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchOnboardingStatus()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/onboarding`);
	});

	it('completeOnboarding posts to complete endpoint', async () => {
		const payload = { completed: true };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(completeOnboarding()).resolves.toEqual(payload);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/onboarding/complete`);
		expect(options.method).toBe('POST');
	});

	// --- Sprint 2: Dashboard ---

	it('fetchDashboard returns dashboard data', async () => {
		const payload = { alertes: [], kpis: { sci_count: 1, biens_count: 2, taux_recouvrement: 95, cashflow_net: 800 }, scis: [], activite: [] };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchDashboard()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/dashboard`);
	});

	// --- Sprint 3: Nested SCI/Biens ---

	it('fetchSciBiens returns biens for a SCI', async () => {
		const payload = [{ id: 1, adresse: '1 rue Test' }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchSciBiens('sci-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens`);
	});

	it('fetchSciAssocies returns associes for a SCI', async () => {
		const payload = [{ id: 'a-1', nom: 'Test', part: 100, role: 'gerant' }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchSciAssocies('sci-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/associes`);
	});

	it('fetchFicheBien returns full fiche bien', async () => {
		const payload = { id: 1, adresse: '1 rue Test', bail_actif: null, rentabilite: { brute: 6, nette: 4, cashflow_mensuel: 300, cashflow_annuel: 3600 } };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchFicheBien('sci-1', 'bien-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1`);
	});

	it('fetchSciBiensList returns biens list', async () => {
		const payload = [{ id: 1 }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchSciBiensList('sci-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens`);
	});

	it('createBienForSci posts JSON body', async () => {
		const data = { adresse: '5 rue Neuve', ville: 'Paris', code_postal: '75001' };
		const created = { id: 1, ...data };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createBienForSci('sci-1', data)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens`);
		expect(options.method).toBe('POST');
	});

	it('createLoyerForBien posts JSON body', async () => {
		const data = { montant: 1000, date_loyer: '2026-03-01', statut: 'paye' };
		const created = { id: 1, ...data };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createLoyerForBien('sci-1', 'bien-1', data)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/loyers`);
		expect(options.method).toBe('POST');
	});

	// --- Sprint 4: Baux ---

	it('fetchBienBaux returns baux list', async () => {
		const payload = [{ id: 1, date_debut: '2025-01-01' }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBienBaux('sci-1', 'bien-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/baux`);
	});

	it('createBail posts JSON body', async () => {
		const data = { date_debut: '2025-01-01', loyer_hc: 800 };
		const created = { id: 1, ...data };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(createBail('sci-1', 'bien-1', data)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/baux`);
		expect(options.method).toBe('POST');
	});

	it('updateBail patches JSON body', async () => {
		const data = { loyer_hc: 900 };
		const updated = { id: 1, date_debut: '2025-01-01', ...data };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(updated), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(updateBail('sci-1', 'bien-1', 1, data)).resolves.toEqual(updated);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/baux/1`);
		expect(options.method).toBe('PATCH');
	});

	it('deleteBail sends DELETE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(deleteBail('sci-1', 'bien-1', 1)).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/baux/1`);
		expect(options.method).toBe('DELETE');
	});

	it('attachLocataireToBail posts locataire id', async () => {
		const created = { bail_id: 1, locataire_id: 5 };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(attachLocataireToBail('sci-1', 'bien-1', 1, 5)).resolves.toEqual(created);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/baux/1/locataires`);
		expect(options.method).toBe('POST');
	});

	it('detachLocataireFromBail sends DELETE', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(detachLocataireFromBail('sci-1', 'bien-1', 1, 5)).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/baux/1/locataires/5`);
		expect(options.method).toBe('DELETE');
	});

	// --- Sprint 5: Charges / PNO / Frais Agence ---

	it('fetchBienCharges returns charges for a bien', async () => {
		const payload = [{ id: 1, type_charge: 'copropriete', montant: 200 }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBienCharges('sci-1', 'bien-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/charges`);
	});

	it('fetchBienPno returns PNO data', async () => {
		const payload = [{ id: 1, assureur: 'AXA', prime_annuelle: 360 }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBienPno('sci-1', 'bien-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/assurance-pno`);
	});

	it('fetchBienFraisAgence returns agency fees', async () => {
		const payload = [{ id: 1, type_frais: 'gestion', montant: 100 }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBienFraisAgence('sci-1', 'bien-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/frais-agence`);
	});

	it('fetchSciAssociesList returns associes for a SCI', async () => {
		const payload = [{ id: 'a-1', nom: 'Test', part: 100 }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchSciAssociesList('sci-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/associes`);
	});

	// --- Sprint 6: Notification Preferences ---

	it('fetchNotificationPreferences returns preferences', async () => {
		const payload = { preferences: [{ type: 'late_payment', email_enabled: true, in_app_enabled: true }] };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchNotificationPreferences()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/user/notification-preferences`);
	});

	it('updateNotificationPreferences sends PUT', async () => {
		const prefs = [{ type: 'late_payment', email_enabled: false, in_app_enabled: true }];
		const payload = { preferences: prefs };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(updateNotificationPreferences(prefs)).resolves.toEqual(payload);
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/user/notification-preferences`);
		expect(options.method).toBe('PUT');
	});

	// --- Sprint 7: Finances ---

	it('fetchFinances returns finances overview', async () => {
		const payload = { revenus_total: 12000, charges_total: 3000, cashflow_net: 9000, taux_recouvrement: 95, patrimoine_total: 200000, rentabilite_moyenne: 6, evolution_mensuelle: [], repartition_sci: [] };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchFinances()).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/finances`);
	});

	it('fetchFinances passes period parameter', async () => {
		const payload = { revenus_total: 6000, charges_total: 1500, cashflow_net: 4500, taux_recouvrement: 90, patrimoine_total: 200000, rentabilite_moyenne: 5, evolution_mensuelle: [], repartition_sci: [] };
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchFinances('6m')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/finances?period=6m`);
	});

	// --- Sprint 7: Documents ---

	it('fetchBienDocuments returns documents list', async () => {
		const payload = [{ id: 1, nom: 'bail.pdf', categorie: 'bail', url: '/files/bail.pdf', created_at: '2026-03-01' }];
		const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(fetchBienDocuments('sci-1', 'bien-1')).resolves.toEqual(payload);
		const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/documents`);
	});

	it('deleteDocumentBien sends DELETE request', async () => {
		const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
		vi.stubGlobal('fetch', fetchMock);

		await expect(deleteDocumentBien('sci-1', 'bien-1', 1)).resolves.toBeUndefined();
		const [url, options] = fetchMock.mock.calls[0] as [string, RequestInit];
		expect(url).toBe(`${API_URL}/api/v1/scis/sci-1/biens/bien-1/documents/1`);
		expect(options.method).toBe('DELETE');
	});
});
