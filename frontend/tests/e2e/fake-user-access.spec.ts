import { expect, test, type Page } from '@playwright/test';
import { seedFakeUserContext } from './helpers/fake-user';

async function installCoreApiMocks(page: Page) {
	let bienCounter = 2;
	let loyerCounter = 2;
	let checkoutCalls = 0;

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
		}
	];

	let loyers = [
		{
			id: 'loyer-seed',
			id_bien: 'bien-seed',
			id_sci: 'sci-1',
			date_loyer: '2026-03-01',
			montant: 1200,
			statut: 'en_attente',
			quitus_genere: false
		}
	];

	const normalizeIdFromPath = (path: string) => path.replace(/\/+$/, '').split('/').pop() || '';

	await page.route('**/api/v1/**', async (route) => {
		const request = route.request();
		const method = request.method();
		const url = new URL(request.url());
		const path = url.pathname;
		const idSci = url.searchParams.get('id_sci');
		const dateFrom = url.searchParams.get('date_from');
		const dateTo = url.searchParams.get('date_to');

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
				body: JSON.stringify([{ id: 'sci-1', nom: 'SCI Demo QA', regime_fiscal: 'IR' }])
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			const filtered = idSci ? biens.filter((bien) => String(bien.id_sci) === idSci) : biens;
			await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(filtered) });
			return;
		}

		if (method === 'POST' && (path === '/api/v1/biens' || path === '/api/v1/biens/')) {
			const payload = request.postDataJSON();
			const created = {
				...payload,
				id: `bien-e2e-${bienCounter}`
			};
			bienCounter += 1;
			biens = [created, ...biens];
			await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(created) });
			return;
		}

		if (method === 'PATCH' && path.startsWith('/api/v1/biens/')) {
			const bienId = normalizeIdFromPath(path);
			const patch = request.postDataJSON();
			biens = biens.map((bien) => (String(bien.id) === bienId ? { ...bien, ...patch } : bien));
			const updated = biens.find((bien) => String(bien.id) === bienId);
			await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(updated) });
			return;
		}

		if (method === 'DELETE' && path.startsWith('/api/v1/biens/')) {
			const bienId = normalizeIdFromPath(path);
			biens = biens.filter((bien) => String(bien.id) !== bienId);
			loyers = loyers.filter((loyer) => String(loyer.id_bien) !== bienId);
			await route.fulfill({ status: 204, body: '' });
			return;
		}

		if (method === 'GET' && (path === '/api/v1/loyers' || path === '/api/v1/loyers/')) {
			let filtered = [...loyers];
			if (idSci) {
				filtered = filtered.filter((loyer) => String(loyer.id_sci || '') === idSci);
			}
			if (dateFrom) {
				filtered = filtered.filter((loyer) => String(loyer.date_loyer) >= dateFrom);
			}
			if (dateTo) {
				filtered = filtered.filter((loyer) => String(loyer.date_loyer) <= dateTo);
			}
			await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(filtered) });
			return;
		}

		if (method === 'POST' && (path === '/api/v1/loyers' || path === '/api/v1/loyers/')) {
			const payload = request.postDataJSON();
			const created = {
				...payload,
				id: `loyer-e2e-${loyerCounter}`,
				id_sci: idSci || 'sci-1',
				quitus_genere: Boolean(payload?.quitus_genere)
			};
			loyerCounter += 1;
			loyers = [created, ...loyers];
			await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify(created) });
			return;
		}

		if (method === 'PATCH' && path.startsWith('/api/v1/loyers/')) {
			const loyerId = normalizeIdFromPath(path);
			const patch = request.postDataJSON();
			loyers = loyers.map((loyer) => (String(loyer.id) === loyerId ? { ...loyer, ...patch } : loyer));
			const updated = loyers.find((loyer) => String(loyer.id) === loyerId);
			await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(updated) });
			return;
		}

		if (method === 'DELETE' && path.startsWith('/api/v1/loyers/')) {
			const loyerId = normalizeIdFromPath(path);
			loyers = loyers.filter((loyer) => String(loyer.id) !== loyerId);
			await route.fulfill({ status: 204, body: '' });
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

		if (method === 'POST' && path === '/api/v1/stripe/create-checkout-session') {
			checkoutCalls += 1;
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ url: 'http://localhost:5173/success?session_id=cs_test_fake' })
			});
			return;
		}

		await route.fulfill({ status: 404, contentType: 'application/json', body: JSON.stringify({ detail: 'Not mocked' }) });
	});

	return {
		getCheckoutCalls: () => checkoutCalls
	};
}

test.describe('Fake user access E2E', () => {
	test('fake user can navigate and use core screens', async ({ page, isMobile }) => {
		test.skip(isMobile, 'Ce scénario valide la navigation desktop authentifiée.');

		const mocks = await installCoreApiMocks(page);
		await seedFakeUserContext(page, { email: 'fake.user@sci.test' });

		await page.goto('/dashboard');
		await expect(page.getByText('fake.user@sci.test')).toBeVisible();
		await expect(page.locator('h1')).toContainText('Tableau de bord opérationnel');
		await expect(page.getByText('Actifs suivis')).toBeVisible();

		await page.goto('/biens');
		await expect(page.locator('h1')).toContainText('Gestion des biens');
		await expect(page.getByText('1 rue Seed')).toBeVisible();
		await page.evaluate(async () => {
			await fetch('http://localhost:8000/api/v1/biens/', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					id_sci: 'sci-1',
					adresse: '42 avenue QA',
					ville: 'Lyon',
					code_postal: '69002',
					type_locatif: 'meuble',
					loyer_cc: 1650,
					charges: 120,
					tmi: 28
				})
			});
		});
		await page.reload();
		await expect(page.getByText('42 avenue QA')).toBeVisible();

		const createdBienRow = page.locator('tr', { hasText: '42 avenue QA' }).first();
		await createdBienRow.getByRole('button', { name: 'Modifier' }).click();
		await page.getByLabel('Adresse').last().fill('42 avenue QA Modifie');
		await page.getByRole('button', { name: 'Enregistrer les modifications' }).click();
		await expect(page.getByText('42 avenue QA Modifie')).toBeVisible();

		page.once('dialog', async (dialog) => {
			await dialog.accept();
		});
		await page.locator('tr', { hasText: '42 avenue QA Modifie' }).first().getByRole('button', { name: 'Supprimer' }).click();
		await expect(page.locator('tr', { hasText: '42 avenue QA Modifie' })).toHaveCount(0);

		await page.goto('/loyers');
		await expect(page.locator('h1')).toContainText('Suivi des loyers');
		await page.evaluate(async () => {
			await fetch('http://localhost:8000/api/v1/loyers/?id_sci=sci-1', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					id_bien: 'bien-seed',
					id_locataire: 'loc-42',
					date_loyer: '2026-05-01',
					montant: 1350,
					statut: 'en_attente'
				})
			});
		});
		await page.reload();
		await expect(page.locator('tr', { hasText: '1 350 €' })).toBeVisible();

		const createdLoyerRow = page.locator('tr', { hasText: '1 350 €' }).first();
		await createdLoyerRow.getByRole('button', { name: 'Modifier' }).click();
		await page.getByLabel('Montant (€)').last().fill('1400');
		const editLoyerForm = page.locator('form').filter({ has: page.getByRole('button', { name: 'Enregistrer les modifications' }) });
		await editLoyerForm.locator('select').first().selectOption('paye');
		await page.getByRole('button', { name: 'Enregistrer les modifications' }).click();
		await expect(page.locator('tr', { hasText: '1 400 €' })).toBeVisible();
		await expect(page.locator('tr', { hasText: 'Payé' })).toBeVisible();

		page.once('dialog', async (dialog) => {
			await dialog.accept();
		});
		await page.locator('tr', { hasText: '1 400 €' }).first().getByRole('button', { name: 'Supprimer' }).click();
		await expect(page.locator('tr', { hasText: '1 400 €' })).toHaveCount(0);

		await page.goto('/dashboard');
		const quitusResult = await page.evaluate(async () => {
			const generatedResponse = await fetch('http://localhost:8000/api/v1/quitus/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					id_loyer: 'loyer-test',
					id_bien: 'bien-seed',
					nom_locataire: 'Locataire Test',
					periode: 'Mai 2026',
					montant: 1400
				})
			});
			const generated = await generatedResponse.json();
			const pdfResponse = await fetch(`http://localhost:8000${generated.pdf_url}`);
			const blob = await pdfResponse.blob();
			return { filename: generated.filename, size: blob.size };
		});
		expect(quitusResult.filename).toBe('quitus-e2e.pdf');
		expect(quitusResult.size).toBeGreaterThan(0);

		await page.goto('/pricing');
		const checkoutResult = await page.evaluate(async () => {
			const response = await fetch('http://localhost:8000/api/v1/stripe/create-checkout-session', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					price_id: 'price_starter_placeholder',
					mode: 'subscription'
				})
			});
			return response.json();
		});
		expect(checkoutResult.url).toContain('/success?session_id=cs_test_fake');
		await expect.poll(() => mocks.getCheckoutCalls()).toBe(1);
	});
});
