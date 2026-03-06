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

	let loyers = [
		{
			id: 'loyer-seed',
			id_bien: 'bien-seed',
			id_sci: 'sci-1',
			date_loyer: '2026-03-01',
			montant: 1200,
			statut: 'paye',
			quitus_genere: true
		},
		{
			id: 'loyer-qa',
			id_bien: 'bien-qa',
			id_sci: 'sci-1',
			date_loyer: '2026-03-05',
			montant: 1650,
			statut: 'en_attente',
			quitus_genere: false
		}
	];

	const charges = [
		{
			id: 'charge-1',
			id_bien: 'bien-seed',
			type_charge: 'assurance',
			montant: 240,
			date_paiement: '2026-02-10'
		},
		{
			id: 'charge-2',
			id_bien: 'bien-qa',
			type_charge: 'travaux',
			montant: 600,
			date_paiement: '2026-03-02'
		}
	];

	const detailBySci: Record<string, object> = {
		'sci-1': {
			...scis[0],
			charges_count: 2,
			total_monthly_rent: 2850,
			total_monthly_property_charges: 270,
			total_recorded_charges: 840,
			paid_loyers_total: 1200,
			pending_loyers_total: 1650,
			biens: biens.filter((bien) => bien.id_sci === 'sci-1'),
			recent_loyers: loyers,
			recent_charges: charges,
			fiscalite: [
				{
					id: 'fisc-1',
					id_sci: 'sci-1',
					annee: 2025,
					total_revenus: 34200,
					total_charges: 5400,
					resultat_fiscal: 28800
				}
			]
		},
		'sci-2': {
			...scis[1],
			charges_count: 0,
			total_monthly_rent: 980,
			total_monthly_property_charges: 80,
			total_recorded_charges: 0,
			paid_loyers_total: 0,
			pending_loyers_total: 0,
			biens: biens.filter((bien) => bien.id_sci === 'sci-2'),
			recent_loyers: [],
			recent_charges: [],
			fiscalite: []
		}
	};
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
			await route.fulfill({
				status: detailBySci[sciId] ? 200 : 404,
				contentType: 'application/json',
				body: JSON.stringify(detailBySci[sciId] ?? { detail: 'Not mocked' })
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
		test.skip(isMobile, 'Ce scénario valide la navigation desktop authentifiée.');

		await installCoreApiMocks(page);
		await seedFakeUserContext(page, { email: 'fake.user@sci.test', sciId: 'sci-1' });

		await page.goto('/dashboard');
		await expect(page.getByRole('heading', { level: 1 })).toContainText(
			'Dashboard de portefeuille'
		);
		await expect(page.getByText('Portefeuille multi-SCI')).toBeVisible();
		await expect(page.getByText('Vue portefeuille', { exact: true })).toBeVisible();
		await expect(page.getByText('Postes de pilotage')).toBeVisible();
		await expect(page.getByText('Fiche d’identité SCI active')).toBeVisible();
		await expect(page.getByText('Charges et fiscalité')).toBeVisible();
		await expect(page.getByText('Rituels opérateur')).toBeVisible();
		await expect(page.getByRole('heading', { name: 'SCI Mosa Belleville' }).first()).toBeVisible();
		await expect(page.getByRole('link', { name: 'SCI', exact: true })).toBeVisible();
		await page.getByRole('button', { name: /SCI Horizon Lyon/i }).click();
		await expect(page.getByRole('heading', { name: 'SCI Horizon Lyon' }).first()).toBeVisible();
		await expect(page.getByText('Aucun exercice consolidé pour la SCI active.')).toBeVisible();
		await page.getByLabel('SCI active').selectOption('SCI Mosa Belleville');
		await expect(page.getByRole('heading', { name: 'SCI Mosa Belleville' }).first()).toBeVisible();
		await expect(page.getByText('Exercice 2025 consolidé')).toBeVisible();

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
	});
});
