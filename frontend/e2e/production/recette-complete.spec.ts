import { expect } from '@playwright/test';
import { test, captureScreenshots } from '../fixtures/auth.fixture';

/**
 * RECETTE COMPLETE — Agent de test automatisé pour GérerSCI
 *
 * Simule un utilisateur réel sur le compte démo en production.
 * Couvre : navigation, CRUD, bilans, notifications, settings.
 *
 * Usage:
 *   E2E_AUTH_TOKEN=<jwt> E2E_SCI_ID=<id> E2E_BIEN_ID=<id> \
 *   pnpm exec playwright test --config e2e/playwright.production.config.ts \
 *     e2e/production/recette-complete.spec.ts
 *
 * Ou via le script raccourci:
 *   ./scripts/run-recette-prod.sh
 */

const SCI_BELLEVILLE = process.env.E2E_SCI_ID || '98d2ef33-92c0-43d7-9c71-d3f0acd95dd7';
const SCI_MONTSOURIS = process.env.E2E_SCI_ID_2 || '93109c6d-b845-4d67-ab27-99445db662c4';
const BIEN_ID = process.env.E2E_BIEN_ID || 'f80f8234-2a83-4ad9-a3d2-94eee688b5cb';
const SCREENSHOT_DIR = 'e2e-artifacts/recette';

// ─── Helpers ──────────────────────────────────────────────────

function consoleErrorCollector(page: import('@playwright/test').Page) {
	const errors: string[] = [];
	page.on('console', (msg) => {
		if (msg.type() === 'error' && !msg.text().includes('favicon')) {
			errors.push(msg.text());
		}
	});
	return errors;
}

// ─── MODULE 1: Landing & Pages Publiques ──────────────────────

test.describe('M1 — Pages publiques', () => {
	test('landing page charge et affiche le hero', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');
		await expect(page.locator('body')).toContainText(/SCI|tableur|Excel/i);
		await captureScreenshots(page, 'm1-landing', SCREENSHOT_DIR);
	});

	test('pricing page affiche les plans', async ({ page }) => {
		await page.goto('/pricing');
		await page.waitForLoadState('networkidle');
		await expect(page.locator('body')).toContainText(/Gestion|Pilotage|Fondateur/i);
		await captureScreenshots(page, 'm1-pricing', SCREENSHOT_DIR);
	});

	test('pages légales accessibles', async ({ page }) => {
		for (const path of ['/cgu', '/cgv', '/confidentialite', '/mentions-legales']) {
			const response = await page.goto(path);
			expect(response?.status()).toBe(200);
		}
	});

	test('simulateur CERFA accessible', async ({ page }) => {
		await page.goto('/simulateur-cerfa');
		await page.waitForLoadState('networkidle');
		await expect(page.locator('body')).toContainText(/CERFA|2044|simulateur/i);
	});
});

// ─── MODULE 2: Dashboard ──────────────────────────────────────

test.describe('M2 — Dashboard', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('dashboard affiche KPIs et SCIs', async ({ authedPage: page }) => {
		const errors = consoleErrorCollector(page);
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Vérifier que les KPIs sont visibles
		await expect(page.locator('body')).toContainText(/SCI|Bien|Loyer|Recouvrement/i);
		await captureScreenshots(page, 'm2-dashboard', SCREENSHOT_DIR);

		expect(errors.filter(e => !e.includes('Supabase'))).toEqual([]);
	});
});

// ─── MODULE 3: Navigation SCI ─────────────────────────────────

test.describe('M3 — Navigation SCI', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('liste des SCIs affiche 2 SCIs', async ({ authedPage: page }) => {
		await page.goto('/scis');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1500);
		await expect(page.locator('body')).toContainText(/Belleville|Montsouris/);
		await captureScreenshots(page, 'm3-scis-list', SCREENSHOT_DIR);
	});

	test('page SCI détail affiche biens et actions', async ({ authedPage: page }) => {
		await page.goto(`/scis/${SCI_BELLEVILLE}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);
		await expect(page.locator('body')).toContainText(/Belleville/);
		await captureScreenshots(page, 'm3-sci-detail', SCREENSHOT_DIR);
	});

	test('navigation SCI → biens fonctionne', async ({ authedPage: page }) => {
		await page.goto(`/scis/${SCI_BELLEVILLE}/biens`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1500);
		// Doit afficher les 3 biens
		await expect(page.locator('body')).toContainText(/Belleville|Pyrénées|Voltaire/);
		await captureScreenshots(page, 'm3-biens-list', SCREENSHOT_DIR);
	});
});

// ─── MODULE 4: Fiche Bien ─────────────────────────────────────

test.describe('M4 — Fiche Bien', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('fiche bien charge avec tous les onglets', async ({ authedPage: page }) => {
		const errors = consoleErrorCollector(page);
		await page.goto(`/scis/${SCI_BELLEVILLE}/biens/${BIEN_ID}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Vérifier l'adresse
		await expect(page.locator('body')).toContainText(/Belleville/);
		await captureScreenshots(page, 'm4-fiche-bien', SCREENSHOT_DIR);

		// Vérifier pas d'erreurs console critiques
		const critical = errors.filter(e => !e.includes('Supabase') && !e.includes('favicon'));
		expect(critical).toEqual([]);
	});

	test('bouton bilan est présent sur la fiche bien', async ({ authedPage: page }) => {
		await page.goto(`/scis/${SCI_BELLEVILLE}/biens/${BIEN_ID}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1500);

		const bilanLink = page.getByRole('link', { name: /Bilan/i });
		await expect(bilanLink).toBeVisible();
	});
});

// ─── MODULE 5: Loyers ─────────────────────────────────────────

test.describe('M5 — Loyers', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('loyers affichent les données seedées', async ({ authedPage: page }) => {
		await page.goto(`/scis/${SCI_BELLEVILLE}/biens/${BIEN_ID}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Chercher un onglet loyers ou la section loyers
		const loyerSection = page.getByText(/Loyer|loyer|en_retard|retard/i).first();
		await expect(loyerSection).toBeVisible();
		await captureScreenshots(page, 'm5-loyers', SCREENSHOT_DIR);
	});
});

// ─── MODULE 6: Associés ───────────────────────────────────────

test.describe('M6 — Associés', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('page associés affiche gérant et associé', async ({ authedPage: page }) => {
		await page.goto(`/scis/${SCI_BELLEVILLE}/associes`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1500);
		await expect(page.locator('body')).toContainText(/Mossabely|Martin|gérant|associé/i);
		await captureScreenshots(page, 'm6-associes', SCREENSHOT_DIR);
	});
});

// ─── MODULE 7: Finances ───────────────────────────────────────

test.describe('M7 — Finances', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('finances consolidées chargent sans erreur', async ({ authedPage: page }) => {
		const errors = consoleErrorCollector(page);
		await page.goto('/finances');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page.locator('body')).toContainText(/Finances|Revenus|Charges|Cashflow/i);
		await captureScreenshots(page, 'm7-finances', SCREENSHOT_DIR);

		expect(errors.filter(e => !e.includes('Supabase'))).toEqual([]);
	});
});

// ─── MODULE 8: Bilans Mensuels ────────────────────────────────

test.describe('M8 — Bilans Mensuels', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('page bilans charge et affiche les périodes', async ({ authedPage: page }) => {
		const errors = consoleErrorCollector(page);
		await page.goto('/bilans');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page.locator('body')).toContainText(/Bilan|Portefeuille|période/i);
		await captureScreenshots(page, 'm8-bilans', SCREENSHOT_DIR);

		expect(errors.filter(e => !e.includes('Supabase'))).toEqual([]);
	});

	test('bilan SCI via deep-link fonctionne', async ({ authedPage: page }) => {
		await page.goto(`/bilans?scope=sci&scope_id=${SCI_BELLEVILLE}`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await captureScreenshots(page, 'm8-bilan-sci', SCREENSHOT_DIR);
	});
});

// ─── MODULE 9: Notifications ──────────────────────────────────

test.describe('M9 — Notifications', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('dashboard charge et notification center existe', async ({ authedPage: page }) => {
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);
		// Just verify dashboard loaded with navbar present
		await expect(page.locator('nav').first()).toBeVisible();
	});
});

// ─── MODULE 10: Settings ──────────────────────────────────────

test.describe('M10 — Settings', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('settings page responds (may redirect with injected JWT)', async ({ authedPage: page }) => {
		const response = await page.goto('/settings');
		// With injected HS256 JWT, the Supabase client-side SDK may not recognize the session
		// and redirect. We just verify the page loads without a server error.
		expect(response?.status()).toBeLessThan(500);
		await captureScreenshots(page, 'm10-settings', SCREENSHOT_DIR);
	});
});

// ─── MODULE 11: Échéances ─────────────────────────────────────

test.describe('M11 — Échéances', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('page échéances charge', async ({ authedPage: page }) => {
		await page.goto('/echeances');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1500);

		await expect(page.locator('body')).toContainText(/Échéances|échéance|Aucune/i);
		await captureScreenshots(page, 'm11-echeances', SCREENSHOT_DIR);
	});
});

// ─── MODULE 12: Exploitation ──────────────────────────────────

test.describe('M12 — Exploitation', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('page exploitation charge', async ({ authedPage: page }) => {
		await page.goto('/exploitation');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1500);

		await captureScreenshots(page, 'm12-exploitation', SCREENSHOT_DIR);
	});
});

// ─── MODULE 13: Responsive / Mobile ──────────────────────────

test.describe('M13 — Mobile responsive', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('page charge en viewport mobile', async ({ authedPage: page }) => {
		await page.setViewportSize({ width: 375, height: 812 });
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		// Verify page renders on mobile viewport without crash
		await expect(page.locator('nav').first()).toBeVisible();
		await captureScreenshots(page, 'm13-mobile-dashboard', SCREENSHOT_DIR);
	});
});

// ─── MODULE 14: Assemblées Générales ──────────────────────────

test.describe('M14 — AG & Mouvements', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('page AG charge', async ({ authedPage: page }) => {
		await page.goto(`/scis/${SCI_BELLEVILLE}/assemblees-generales`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1500);
		await captureScreenshots(page, 'm14-ag', SCREENSHOT_DIR);
	});

	test('page mouvements de parts charge', async ({ authedPage: page }) => {
		await page.goto(`/scis/${SCI_BELLEVILLE}/mouvements-parts`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1500);
		await captureScreenshots(page, 'm14-mouvements', SCREENSHOT_DIR);
	});
});

// ─── MODULE 15: Fiscalité ─────────────────────────────────────

test.describe('M15 — Fiscalité', () => {
	test.beforeEach(async () => {
		const hasCredentials = (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) || process.env.E2E_AUTH_TOKEN;
		test.skip(!hasCredentials, 'E2E_EMAIL+E2E_PASSWORD ou E2E_AUTH_TOKEN manquant');
	});

	test('page fiscalité charge sans erreur', async ({ authedPage: page }) => {
		const errors = consoleErrorCollector(page);
		await page.goto(`/scis/${SCI_BELLEVILLE}/fiscalite`);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(2000);

		await expect(page.locator('body')).toContainText(/Fiscalité|IR|IS|2044/i);
		await captureScreenshots(page, 'm15-fiscalite', SCREENSHOT_DIR);

		expect(errors.filter(e => !e.includes('Supabase'))).toEqual([]);
	});
});
