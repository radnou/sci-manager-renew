import { expect, test, type Page } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

async function installCoreApiMocks(page: Page) {
	const scis = [
		{
			id: 'sci-1',
			nom: 'SCI Mosa Belleville',
			siren: '123456789',
			regime_fiscal: 'IR',
			statut: 'exploitation',
			associes_count: 2,
			biens_count: 2,
			loyers_count: 2,
			user_role: 'gerant',
			user_part: 60,
			associes: [
				{ id: 'associe-1', nom: 'Rad Noumane', email: 'rad@sci.local', part: 60, role: 'gerant' },
				{
					id: 'associe-2',
					nom: 'Camille Bernard',
					email: 'camille@sci.local',
					part: 40,
					role: 'associe'
				}
			]
		},
		{
			id: 'sci-2',
			nom: 'SCI Horizon Lyon',
			siren: '987654321',
			regime_fiscal: 'IS',
			statut: 'mise_en_service',
			associes_count: 1,
			biens_count: 1,
			loyers_count: 0,
			user_role: 'associe',
			user_part: 100,
			associes: [
				{ id: 'associe-3', nom: 'Rad Noumane', email: 'rad@sci.local', part: 100, role: 'associe' }
			]
		}
	];

	let biens = [
		{
			id: 'bien-seed',
			id_sci: 'sci-1',
			adresse: '1 rue Seed',
			ville: 'Paris',
			code_postal: '75001',
			type_locatif: 'nu',
			loyer_cc: 1200,
			charges: 150,
			tmi: 30
		},
		{
			id: 'bien-qa',
			id_sci: 'sci-1',
			adresse: '42 avenue QA',
			ville: 'Lyon',
			code_postal: '69002',
			type_locatif: 'meuble',
			loyer_cc: 1650,
			charges: 120,
			tmi: 28
		},
		{
			id: 'bien-horizon',
			id_sci: 'sci-2',
			adresse: '8 quai Rhône',
			ville: 'Lyon',
			code_postal: '69006',
			type_locatif: 'mixte',
			loyer_cc: 980,
			charges: 80,
			tmi: 20
		}
	];

	let locataires = [
		{
			id: 'loc-seed',
			id_bien: 'bien-seed',
			id_sci: 'sci-1',
			nom: 'Jean Martin',
			email: 'jean.martin@sci.local',
			date_debut: '2025-01-15',
			date_fin: null
		},
		{
			id: 'loc-qa',
			id_bien: 'bien-qa',
			id_sci: 'sci-1',
			nom: 'Claire Dupont',
			email: 'claire.dupont@sci.local',
			date_debut: '2025-09-01',
			date_fin: null
		}
	];

	let loyers: Array<{
		id: string;
		id_bien: string;
		id_sci: string;
		id_locataire: string | null;
		date_loyer: string;
		montant: number;
		statut: string;
		quitus_genere: boolean;
	}> = [
		{
			id: 'loyer-seed',
			id_bien: 'bien-seed',
			id_sci: 'sci-1',
			id_locataire: 'loc-seed',
			date_loyer: '2026-03-01',
			montant: 1200,
			statut: 'paye',
			quitus_genere: true
		},
		{
			id: 'loyer-qa',
			id_bien: 'bien-qa',
			id_sci: 'sci-1',
			id_locataire: 'loc-qa',
			date_loyer: '2026-03-05',
			montant: 1650,
			statut: 'en_attente',
			quitus_genere: false
		}
	];

	let associes = [
		{
			id: 'associe-1',
			id_sci: 'sci-1',
			user_id: 'user-e2e-001',
			nom: 'Rad Noumane',
			email: 'rad@sci.local',
			part: 60,
			role: 'gerant',
			is_account_member: true
		},
		{
			id: 'associe-2',
			id_sci: 'sci-1',
			user_id: null,
			nom: 'Camille Bernard',
			email: 'camille@sci.local',
			part: 40,
			role: 'associe',
			is_account_member: false
		},
		{
			id: 'associe-3',
			id_sci: 'sci-2',
			user_id: 'user-e2e-001',
			nom: 'Rad Noumane',
			email: 'rad@sci.local',
			part: 100,
			role: 'associe',
			is_account_member: true
		}
	];

	let charges = [
		{
			id: 'charge-1',
			id_bien: 'bien-seed',
			id_sci: 'sci-1',
			type_charge: 'assurance',
			montant: 240,
			date_paiement: '2026-02-10',
			bien_adresse: '1 rue Seed',
			bien_ville: 'Paris'
		},
		{
			id: 'charge-2',
			id_bien: 'bien-qa',
			id_sci: 'sci-1',
			type_charge: 'travaux',
			montant: 600,
			date_paiement: '2026-03-02',
			bien_adresse: '42 avenue QA',
			bien_ville: 'Lyon'
		}
	];

	let exercicesFiscaux = [
		{
			id: 'fisc-1',
			id_sci: 'sci-1',
			annee: 2025,
			total_revenus: 34200,
			total_charges: 5400,
			resultat_fiscal: 28800,
			regime_fiscal: 'IR',
			nom_sci: 'SCI Mosa Belleville'
		}
	];

	function buildSciDetail(sciId: string) {
		const sci = scis.find((entry) => String(entry.id) === sciId);
		if (!sci) {
			return null;
		}

		const scopedBiens = biens.filter((bien) => String(bien.id_sci) === sciId);
		const scopedLoyers = loyers.filter((loyer) => String(loyer.id_sci) === sciId);
		const scopedCharges = charges.filter((charge) => String(charge.id_sci || '') === sciId);
		const scopedFiscalite = exercicesFiscaux.filter((exercice) => String(exercice.id_sci) === sciId);
		const totalMonthlyRent = scopedBiens.reduce((sum, bien) => sum + Number(bien.loyer_cc || 0), 0);
		const totalMonthlyPropertyCharges = scopedBiens.reduce(
			(sum, bien) => sum + Number(bien.charges || 0),
			0
		);
		const totalRecordedCharges = scopedCharges.reduce(
			(sum, charge) => sum + Number(charge.montant || 0),
			0
		);
		const paidLoyersTotal = scopedLoyers
			.filter((loyer) => loyer.statut === 'paye')
			.reduce((sum, loyer) => sum + Number(loyer.montant || 0), 0);
		const pendingLoyersTotal = scopedLoyers
			.filter((loyer) => loyer.statut !== 'paye')
			.reduce((sum, loyer) => sum + Number(loyer.montant || 0), 0);

		return {
			...sci,
			associes: associes.filter((associe) => String(associe.id_sci || '') === sciId),
			charges_count: scopedCharges.length,
			total_monthly_rent: totalMonthlyRent,
			total_monthly_property_charges: totalMonthlyPropertyCharges,
			total_recorded_charges: totalRecordedCharges,
			paid_loyers_total: paidLoyersTotal,
			pending_loyers_total: pendingLoyersTotal,
			biens: scopedBiens,
			recent_loyers: scopedLoyers,
			recent_charges: scopedCharges,
			fiscalite: scopedFiscalite
		};
	}
	const subscription = {
		plan_key: 'pro',
		plan_name: 'Pro',
		status: 'active',
		mode: 'subscription',
		is_active: true,
		entitlements_version: 1,
		max_scis: 10,
		max_biens: 20,
		current_scis: 2,
		current_biens: 3,
		remaining_scis: 8,
		remaining_biens: 17,
		over_limit: false,
		features: {
			multi_sci_enabled: true,
			charges_enabled: true,
			fiscalite_enabled: true,
			quitus_enabled: true,
			cerfa_enabled: true,
			priority_support: true
		}
	};

	await page.route('**/api/v1/**', async (route) => {
		const request = route.request();
		const method = request.method();
		const url = new URL(request.url());
		const path = url.pathname;
		const idSci = url.searchParams.get('id_sci');

		if (method === 'OPTIONS') {
			await route.fulfill({
				status: 204,
				headers: {
					'access-control-allow-origin': '*',
					'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
					'access-control-allow-headers': '*'
				}
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(scis)
			});
			return;
		}

		if (method === 'POST' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			const payload = JSON.parse(request.postData() || '{}');
			const created = {
				id: `sci-${scis.length + 1}`,
				nom: payload.nom || 'SCI créée',
				siren: payload.siren || null,
				regime_fiscal: payload.regime_fiscal || 'IR'
			};
			scis.push({
				...created,
				statut: 'configuration',
				associes_count: 1,
				biens_count: 0,
				loyers_count: 0,
				user_role: 'gerant',
				user_part: 100,
				associes: [{ id: 'associe-new', nom: 'Rad Noumane', email: 'rad@sci.local', part: 100, role: 'gerant' }]
			});
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify(created)
			});
			return;
		}

		if (method === 'GET' && path === '/api/v1/stripe/subscription') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(subscription)
			});
			return;
		}

		if (method === 'GET' && path.startsWith('/api/v1/scis/')) {
			const sciId = path.replace(/\/+$/, '').split('/').pop() || '';
			const detail = buildSciDetail(sciId);
			await route.fulfill({
				status: detail ? 200 : 404,
				contentType: 'application/json',
				body: JSON.stringify(detail ?? { detail: 'Not mocked' })
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/associes' || path === '/api/v1/associes/')) {
			const filtered = idSci
				? associes.filter((associe) => String(associe.id_sci || '') === idSci)
				: associes;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(filtered)
			});
			return;
		}

		if (method === 'POST' && (path === '/api/v1/associes' || path === '/api/v1/associes/')) {
			const payload = JSON.parse(request.postData() || '{}');
			const created = {
				id: `associe-${associes.length + 1}`,
				id_sci: payload.id_sci,
				user_id: payload.user_id || null,
				nom: payload.nom,
				email: payload.email || null,
				part: payload.part,
				role: payload.role,
				is_account_member: false
			};
			associes = [...associes, created];
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify(created)
			});
			return;
		}

		if (method === 'PATCH' && path.startsWith('/api/v1/associes/')) {
			const associeId = path.replace(/\/+$/, '').split('/').pop() || '';
			const payload = JSON.parse(request.postData() || '{}');
			const current = associes.find((associe) => String(associe.id) === associeId);
			if (!current) {
				await route.fulfill({
					status: 404,
					contentType: 'application/json',
					body: JSON.stringify({ detail: 'Not mocked' })
				});
				return;
			}

			const updated = { ...current, ...payload };
			associes = associes.map((associe) => (String(associe.id) === associeId ? updated : associe));
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(updated)
			});
			return;
		}

		if (method === 'DELETE' && path.startsWith('/api/v1/associes/')) {
			const associeId = path.replace(/\/+$/, '').split('/').pop() || '';
			associes = associes.filter((associe) => String(associe.id) !== associeId);
			await route.fulfill({
				status: 204
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			const filtered = idSci ? biens.filter((bien) => bien.id_sci === idSci) : biens;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(filtered)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/locataires' || path === '/api/v1/locataires/')) {
			const filtered = idSci
				? locataires.filter((locataire) => String(locataire.id_sci) === idSci)
				: locataires;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(filtered)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/charges' || path === '/api/v1/charges/')) {
			const filtered = idSci
				? charges.filter((charge) => String(charge.id_sci || '') === idSci)
				: charges;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(filtered)
			});
			return;
		}

		if (method === 'POST' && (path === '/api/v1/charges' || path === '/api/v1/charges/')) {
			const payload = JSON.parse(request.postData() || '{}');
			const bien = biens.find((entry) => String(entry.id) === String(payload.id_bien));
			const created = {
				id: `charge-${charges.length + 1}`,
				id_bien: payload.id_bien,
				id_sci: bien?.id_sci || 'sci-1',
				type_charge: payload.type_charge,
				montant: payload.montant,
				date_paiement: payload.date_paiement,
				bien_adresse: bien?.adresse || '',
				bien_ville: bien?.ville || ''
			};
			charges = [created, ...charges];
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify(created)
			});
			return;
		}

		if (method === 'PATCH' && path.startsWith('/api/v1/charges/')) {
			const chargeId = path.replace(/\/+$/, '').split('/').pop() || '';
			const payload = JSON.parse(request.postData() || '{}');
			const current = charges.find((charge) => String(charge.id) === chargeId);
			if (!current) {
				await route.fulfill({
					status: 404,
					contentType: 'application/json',
					body: JSON.stringify({ detail: 'Not mocked' })
				});
				return;
			}

			const updated = { ...current, ...payload };
			charges = charges.map((charge) => (String(charge.id) === chargeId ? updated : charge));
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(updated)
			});
			return;
		}

		if (method === 'DELETE' && path.startsWith('/api/v1/charges/')) {
			const chargeId = path.replace(/\/+$/, '').split('/').pop() || '';
			charges = charges.filter((charge) => String(charge.id) !== chargeId);
			await route.fulfill({
				status: 204
			});
			return;
		}

		if (method === 'POST' && (path === '/api/v1/locataires' || path === '/api/v1/locataires/')) {
			const payload = JSON.parse(request.postData() || '{}');
			const created = {
				id: `loc-${locataires.length + 1}`,
				id_bien: payload.id_bien,
				id_sci: biens.find((bien) => String(bien.id) === String(payload.id_bien))?.id_sci || 'sci-1',
				nom: payload.nom,
				email: payload.email || null,
				date_debut: payload.date_debut,
				date_fin: payload.date_fin || null
			};
			locataires = [created, ...locataires];
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify(created)
			});
			return;
		}

		if (method === 'PATCH' && path.startsWith('/api/v1/locataires/')) {
			const locataireId = path.replace(/\/+$/, '').split('/').pop() || '';
			const payload = JSON.parse(request.postData() || '{}');
			const current = locataires.find((locataire) => String(locataire.id) === locataireId);
			if (!current) {
				await route.fulfill({
					status: 404,
					contentType: 'application/json',
					body: JSON.stringify({ detail: 'Not mocked' })
				});
				return;
			}

			const updated = { ...current, ...payload };
			locataires = locataires.map((locataire) =>
				String(locataire.id) === locataireId ? updated : locataire
			);
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(updated)
			});
			return;
		}

		if (method === 'DELETE' && path.startsWith('/api/v1/locataires/')) {
			const locataireId = path.replace(/\/+$/, '').split('/').pop() || '';
			locataires = locataires.filter((locataire) => String(locataire.id) !== locataireId);
			loyers = loyers.map((loyer) =>
				String(loyer.id_locataire || '') === locataireId ? { ...loyer, id_locataire: null } : loyer
			);
			await route.fulfill({
				status: 204
			});
			return;
		}

		if (method === 'PATCH' && path.startsWith('/api/v1/biens/')) {
			const bienId = path.replace(/\/+$/, '').split('/').pop() || '';
			const payload = JSON.parse(request.postData() || '{}');
			const current = biens.find((bien) => String(bien.id) === bienId);
			if (!current) {
				await route.fulfill({
					status: 404,
					contentType: 'application/json',
					body: JSON.stringify({ detail: 'Not mocked' })
				});
				return;
			}

			const updated = { ...current, ...payload };
			biens = biens.map((bien) => (String(bien.id) === bienId ? updated : bien));
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(updated)
			});
			return;
		}

		if (method === 'DELETE' && path.startsWith('/api/v1/biens/')) {
			const bienId = path.replace(/\/+$/, '').split('/').pop() || '';
			biens = biens.filter((bien) => String(bien.id) !== bienId);
			await route.fulfill({
				status: 204
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/loyers' || path === '/api/v1/loyers/')) {
			const filtered = idSci ? loyers.filter((loyer) => String(loyer.id_sci) === idSci) : loyers;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(filtered)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/fiscalite' || path === '/api/v1/fiscalite/')) {
			const filtered = idSci
				? exercicesFiscaux.filter((exercice) => String(exercice.id_sci || '') === idSci)
				: exercicesFiscaux;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(filtered)
			});
			return;
		}

		if (method === 'POST' && (path === '/api/v1/fiscalite' || path === '/api/v1/fiscalite/')) {
			const payload = JSON.parse(request.postData() || '{}');
			const sci = scis.find((entry) => String(entry.id) === String(payload.id_sci));
			const created = {
				id: `fisc-${exercicesFiscaux.length + 1}`,
				id_sci: payload.id_sci,
				annee: payload.annee,
				total_revenus: payload.total_revenus,
				total_charges: payload.total_charges,
				resultat_fiscal: Number(payload.total_revenus || 0) - Number(payload.total_charges || 0),
				regime_fiscal: sci?.regime_fiscal || 'IR',
				nom_sci: sci?.nom || 'SCI'
			};
			exercicesFiscaux = [created, ...exercicesFiscaux];
			await route.fulfill({
				status: 201,
				contentType: 'application/json',
				body: JSON.stringify(created)
			});
			return;
		}

		if (method === 'PATCH' && path.startsWith('/api/v1/fiscalite/')) {
			const exerciceId = path.replace(/\/+$/, '').split('/').pop() || '';
			const payload = JSON.parse(request.postData() || '{}');
			const current = exercicesFiscaux.find((exercice) => String(exercice.id) === exerciceId);
			if (!current) {
				await route.fulfill({
					status: 404,
					contentType: 'application/json',
					body: JSON.stringify({ detail: 'Not mocked' })
				});
				return;
			}

			const updated = {
				...current,
				...payload,
				resultat_fiscal:
					Number(payload.total_revenus ?? current.total_revenus ?? 0) -
					Number(payload.total_charges ?? current.total_charges ?? 0)
			};
			exercicesFiscaux = exercicesFiscaux.map((exercice) =>
				String(exercice.id) === exerciceId ? updated : exercice
			);
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(updated)
			});
			return;
		}

		if (method === 'DELETE' && path.startsWith('/api/v1/fiscalite/')) {
			const exerciceId = path.replace(/\/+$/, '').split('/').pop() || '';
			exercicesFiscaux = exercicesFiscaux.filter((exercice) => String(exercice.id) !== exerciceId);
			await route.fulfill({
				status: 204
			});
			return;
		}

		if (method === 'PATCH' && path.startsWith('/api/v1/loyers/')) {
			const loyerId = path.replace(/\/+$/, '').split('/').pop() || '';
			const payload = JSON.parse(request.postData() || '{}');
			const current = loyers.find((loyer) => String(loyer.id) === loyerId);
			if (!current) {
				await route.fulfill({
					status: 404,
					contentType: 'application/json',
					body: JSON.stringify({ detail: 'Not mocked' })
				});
				return;
			}

			const updated = { ...current, ...payload };
			loyers = loyers.map((loyer) => (String(loyer.id) === loyerId ? updated : loyer));
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(updated)
			});
			return;
		}

		if (method === 'DELETE' && path.startsWith('/api/v1/loyers/')) {
			const loyerId = path.replace(/\/+$/, '').split('/').pop() || '';
			loyers = loyers.filter((loyer) => String(loyer.id) !== loyerId);
			await route.fulfill({
				status: 204
			});
			return;
		}

		if (method === 'POST' && path === '/api/v1/quitus/render') {
			await route.fulfill({
				status: 200,
				contentType: 'application/pdf',
				body: '%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\nBT\n/F1 18 Tf\n72 72 Td\n(Quittance E2E) Tj\nET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF'
			});
			return;
		}

		await route.fulfill({
			status: 404,
			contentType: 'application/json',
			body: JSON.stringify({ detail: 'Not mocked' })
		});
	});
}

test.describe('Fake user access E2E', () => {
	test('fake user can navigate portfolio, settings and generate a PDF', async ({
		page,
		isMobile
	}) => {
		test.slow();
		test.skip(isMobile, 'Ce scénario valide la navigation desktop authentifiée.');

		await installCoreApiMocks(page);
		await seedFakeUserContext(page, { email: 'fake.user@sci.test', sciId: 'sci-1' });

		await page.goto('/dashboard');
		await expect(page.getByRole('heading', { level: 1 })).toContainText(
			'Dashboard de portefeuille'
		);
		await expect(page.getByText('Portefeuille multi-SCI')).toBeVisible();
		await expect(page.getByText('Arbitrages du portefeuille', { exact: true })).toBeVisible();
		await expect(page.getByText("Plan d’action", { exact: true })).toBeVisible();
		await expect(page.getByText('Fiche d’identité SCI active')).toBeVisible();
		await expect(page.getByText('Charges et fiscalité')).toBeVisible();
		await expect(page.getByText('Cadence opérateur')).toBeVisible();
		await expect(page.getByRole('heading', { name: 'SCI Mosa Belleville' }).first()).toBeVisible();
		await expect(page.getByRole('link', { name: 'SCI', exact: true })).toBeVisible();
		await page.getByRole('button', { name: /SCI Horizon Lyon/i }).click();
		await expect(page.getByRole('heading', { name: 'SCI Horizon Lyon' }).first()).toBeVisible();
		await expect(page.getByText('Aucun exercice consolidé pour la SCI active.')).toBeVisible();
		await page.getByLabel('SCI active').selectOption('SCI Mosa Belleville');
		await expect(page.getByRole('heading', { name: 'SCI Mosa Belleville' }).first()).toBeVisible();
		await expect(page.getByText('Dernier exercice fiscal')).toBeVisible();
		await expect(page.getByText('Exercice 2025').first()).toBeVisible();

		await page.getByRole('link', { name: 'SCI', exact: true }).click();
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Pilotage des SCI');
		await expect(page.getByText('Camille Bernard')).toBeVisible();
		await expect(page.getByText('Charges récentes')).toBeVisible();

		await page.getByRole('button', { name: /SCI Horizon Lyon/i }).click();
		await expect(page.getByRole('heading', { name: 'SCI Horizon Lyon' }).first()).toBeVisible();
		await expect(page.getByText('Aucun loyer documenté sur la période récente.')).toBeVisible();

		await page.getByRole('link', { name: 'Paramètres', exact: true }).click();
		await expect(page.getByRole('heading', { level: 1 })).toContainText(
			"Paramètres de l'application"
		);
		await page.getByLabel("Page d'ouverture par défaut").selectOption('/scis');
		await page.getByRole('button', { name: 'Enregistrer les paramètres' }).click();
		await expect(page.getByText('Paramètres enregistrés')).toBeVisible();

		await page.getByRole('link', { name: 'Compte', exact: true }).click();
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Paramètres du compte');
		await expect(page.locator('p').filter({ hasText: 'fake.user@sci.test' })).toBeVisible();

		await page.goto('/dashboard');
		await page.getByLabel('SCI active').selectOption('SCI Mosa Belleville');
		await expect(page.getByText('Journal de la SCI active')).toBeVisible();
		await page.getByRole('button', { name: 'Générer le PDF' }).click();
		await expect(page.getByText('Document généré')).toBeVisible();
		await expect(page.getByRole('link', { name: 'Télécharger', exact: true })).toBeVisible();

		await page.goto('/biens');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Gestion des biens');
		await page.getByRole('button', { name: 'Modifier 1 rue Seed' }).click();
		await page.getByRole('dialog').locator('#bien-edit-ville').fill('Bordeaux');
		await page.getByRole('button', { name: 'Enregistrer les modifications' }).click();
		await expect(page.getByText('Bordeaux')).toBeVisible();

		await page.goto('/loyers');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Suivi des loyers');
		await expect(page.getByRole('button', { name: 'Nouveau loyer' })).toBeVisible();
		await page
			.getByRole('button', { name: /Modifier le loyer du/i })
			.first()
			.click();
		await page.getByRole('dialog').locator('#loyer-edit-statut').selectOption('en_retard');
		await page.getByRole('button', { name: 'Enregistrer les modifications' }).click();
		await expect(page.getByRole('table').getByText('En retard')).toBeVisible();
		await page
			.getByRole('button', { name: /Supprimer le loyer du/i })
			.last()
			.click();
		await page.getByRole('button', { name: 'Confirmer la suppression' }).click();
		await expect(page.getByText('1 enregistrements')).toBeVisible();

		await page.goto('/biens');
		await page.getByRole('button', { name: 'Supprimer 42 avenue QA' }).click();
		await page.getByRole('button', { name: 'Confirmer la suppression' }).click();
		await expect(page.getByText('1 enregistrements')).toBeVisible();

		await page.goto('/locataires');
		await expect(page.getByRole('heading', { level: 1 })).toContainText(
			'Référentiel des locataires'
		);
		await page.getByLabel('SCI active').selectOption('SCI Mosa Belleville');
		await expect(page.getByText('Jean Martin')).toBeVisible();
		await page.getByRole('button', { name: 'Modifier' }).first().click();
		await page.getByRole('dialog').getByLabel('Nom').fill('Jean Martin QA');
		await page.getByRole('button', { name: 'Enregistrer les modifications' }).click();
		await expect(page.getByText('Jean Martin QA')).toBeVisible();

		await page.goto('/associes');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Associés et gouvernance');
		await expect(page.getByText('Camille Bernard')).toBeVisible();
		await page.getByRole('button', { name: 'Modifier' }).first().click();
		await page.getByRole('dialog').getByLabel('Nom').fill('Rad Noumane QA');
		await page.getByRole('button', { name: 'Enregistrer les modifications' }).click();
		await expect(page.getByText('Rad Noumane QA')).toBeVisible();

		await page.goto('/charges');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('charges');
		await expect(page.getByRole('button', { name: 'Modifier' }).first()).toBeVisible();
		await page.getByRole('button', { name: 'Modifier' }).first().click();
		await page.getByRole('dialog').getByLabel('Montant (€)').fill('260');
		await page.getByRole('button', { name: 'Enregistrer les modifications' }).click();
		await page.getByRole('button', { name: 'Modifier' }).first().click();
		await expect(page.getByRole('dialog').getByLabel('Montant (€)')).toHaveValue('260');
		await page.getByRole('button', { name: 'Annuler' }).click();

		await page.goto('/fiscalite');
		await expect(page.getByRole('heading', { level: 1 })).toContainText('Clôture fiscale');
		await expect(page.getByText('Exercice 2025', { exact: true })).toBeVisible();
		await page.getByRole('button', { name: 'Modifier' }).first().click();
		await page.getByRole('dialog').getByLabel('Total charges (€)').fill('5800');
		await page.getByRole('button', { name: 'Enregistrer les modifications' }).click();
		await page.getByRole('button', { name: 'Modifier' }).first().click();
		await expect(page.getByRole('dialog').getByLabel('Total charges (€)')).toHaveValue('5800');
		await page.getByRole('button', { name: 'Annuler' }).click();
	});
});
