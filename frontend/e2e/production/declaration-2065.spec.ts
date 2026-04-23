import { test, expect } from '@playwright/test';

const apiBaseUrl = process.env.E2E_API_BASE_URL || 'https://api.gerersci.fr';

/**
 * Tests E2E pour le parcours déclaration 2065.
 * 
 * Prérequis : API backend déployée avec les endpoints 2065
 * Tags : @P0 @fiscal @2065
 */
test.describe('Déclaration 2065 - Parcours complet @P0', () => {
	test.beforeEach(async ({ request }) => {
		// Vérifier que l'API est ready
		const response = await request.get(`${apiBaseUrl}/health/ready`);
		expect(response.ok()).toBeTruthy();
	});

	test('Génération 2065 - création SCI + bien + déclaration', async ({ request }) => {
		// 1. Créer une SCI
		const sciResponse = await request.post(`${apiBaseUrl}/api/v1/scis`, {
			data: {
				nom: 'SCI Test 2065',
				capital_social: 10000,
				date_cloture_exercice: '2025-12-31'
			}
		});
		expect(sciResponse.ok()).toBeTruthy();
		const sci = await sciResponse.json();
		const sciId = sci.id;

		// 2. Ajouter un bien
		const bienResponse = await request.post(`${apiBaseUrl}/api/v1/scis/${sciId}/biens`, {
			data: {
				designation: 'Appartement Paris',
				type_bien: 'appartement',
				loyer_mensuel: 1200,
				acquisition_prix: 250000,
				travaux_montant: 15000
			}
		});
		expect(bienResponse.ok()).toBeTruthy();

		// 3. Générer la déclaration 2065
		const declResponse = await request.post(
			`${apiBaseUrl}/api/v1/scis/${sciId}/declaration-2065/generate`,
			{
				data: {
					exercice: 2025,
					tresorerie: 5000,
					reserves: 2000
				}
			}
		);
		expect(declResponse.ok()).toBeTruthy();

		const declaration = await declResponse.json();
		expect(declaration.sci_id).toBe(sciId);
		expect(declaration.exercice).toBe(2025);
		expect(declaration.ecart).toBe(0);
		expect(declaration.actif).toBeDefined();
		expect(declaration.passif).toBeDefined();

		// 4. Récupérer la déclaration
		const getResponse = await request.get(
			`${apiBaseUrl}/api/v1/scis/${sciId}/declaration-2065/2025`
		);
		expect(getResponse.ok()).toBeTruthy();
		const fetched = await getResponse.json();
		expect(fetched.exercice).toBe(2025);
	});

	test('Erreur 501 - PDF non implémenté', async ({ request }) => {
		const response = await request.get(
			`${apiBaseUrl}/api/v1/scis/test-uuid/declaration-2065/2025/pdf`
		);
		expect(response.status()).toBe(501);
		const body = await response.json();
		expect(body.detail).toContain('développement');
	});

	test('Erreur 404 - déclaration inexistante', async ({ request }) => {
		const response = await request.get(
			`${apiBaseUrl}/api/v1/scis/test-uuid/declaration-2065/1999`
		);
		expect(response.status()).toBe(404);
	});

	test('Erreur 422 - exercice invalide', async ({ request }) => {
		const response = await request.post(
			`${apiBaseUrl}/api/v1/scis/test-uuid/declaration-2065/generate`,
			{
				data: {
					exercice: 1999
				}
			}
		);
		expect(response.status()).toBe(422);
	});
});
