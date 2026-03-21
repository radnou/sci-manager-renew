import { expect, test } from '@playwright/test';
import { SCI_ID_1, setupAuthedMocks } from '../fixtures/api-mocks';

const isLiveTarget = (process.env.E2E_BASE_URL || '').startsWith('https://');

test.describe('Assemblees generales @P1', () => {
	test.skip(isLiveTarget, 'Requires mock auth — skipped against live target');
	async function openAgPage(page: import('@playwright/test').Page) {
		await page.goto(`/scis/${SCI_ID_1}`);
		await page.waitForLoadState('networkidle');
		await page.goto(`/scis/${SCI_ID_1}/assemblees-generales`);
		await page.waitForLoadState('networkidle');
	}

	test.beforeEach(async ({ page }) => {
		await setupAuthedMocks(page);
	});

	test('le registre AG affiche notes resolutions et partage PV @P1', async ({ page }) => {
		await openAgPage(page);

		await expect(page.getByRole('heading', { name: 'Assemblées générales' })).toBeVisible();
		await expect(page.getByText('Approbation des comptes et affectation du resultat')).toBeVisible();
		await expect(page.getByText('Resolution 1: approbation des comptes.')).toBeVisible();
		await expect(page.getByRole('link', { name: 'Ouvrir le PV partagé' })).toBeVisible();
	});

	test('le gerant peut creer une AG avec tous les champs du dossier @P1', async ({ page }) => {
		await openAgPage(page);

		await page.getByRole('button', { name: 'Planifier une AG' }).click();
		await page.locator('#ag-date').fill('2026-12-18');
		await page.locator('#ag-type').selectOption('extraordinaire');
		await page.locator('#ag-exercice').fill('2026');
		await page.locator('#ag-quorum').check();
		await page.locator('#ag-ordre').fill('Validation du budget travaux et refinancement.');
		await page.locator('#ag-resolutions').fill('Resolution 1: budget travaux valide.');
		await page.locator('#ag-notes').fill('Le gerant mandate le courtier et partage le PV.');
		await page.locator('#ag-pv-url').fill('https://drive.example.com/pv-2026-12');
		await page.getByRole('button', { name: 'Créer l’AG' }).click();

		await expect(page.getByText('AG créée')).toBeVisible();
		await expect(page.getByText('Validation du budget travaux et refinancement.')).toBeVisible();
		await expect(page.getByText('Resolution 1: budget travaux valide.')).toBeVisible();
	});

	test('le gerant peut modifier puis supprimer une AG @P1', async ({ page }) => {
		await openAgPage(page);

		await page.getByRole('button', { name: 'Modifier' }).first().click();
		await page.locator('#ag-notes').fill('PV signe et partage avec les associes.');
		await page.getByRole('button', { name: 'Mettre à jour l’AG' }).click();

		await expect(page.getByText('AG mise à jour')).toBeVisible();
		await expect(page.getByText('PV signe et partage avec les associes.')).toBeVisible();

		const agCard = page.locator('article').filter({ hasText: 'PV signe et partage avec les associes.' }).first();
		await agCard.getByRole('button', { name: 'Supprimer' }).click();

		await expect(page.getByText('AG supprimée')).toBeVisible();
		await expect(page.getByText('PV signe et partage avec les associes.')).toHaveCount(0);
	});
});
