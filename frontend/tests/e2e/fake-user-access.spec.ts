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

	const biens = [
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

	const loyers = [
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

		if (method === 'GET' && (path === '/api/v1/loyers' || path === '/api/v1/loyers/')) {
			const filtered = idSci ? loyers.filter((loyer) => String(loyer.id_sci) === idSci) : loyers;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(filtered)
			});
			return;
		}

		if (method === 'POST' && path === '/api/v1/quitus/generate') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					filename: 'quitus-e2e.pdf',
					pdf_url: '/api/v1/quitus/files/quitus-e2e.pdf',
					size_bytes: 256
				})
			});
			return;
		}

		if (method === 'GET' && path.startsWith('/api/v1/quitus/files/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/pdf',
				body: '%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'
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
		await expect(page.getByText('SCI Horizon Lyon')).toBeVisible();
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
	});
});
