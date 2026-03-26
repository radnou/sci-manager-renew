import { expect } from '@playwright/test';
import { test } from '../fixtures/auth.fixture';

/**
 * VIDEO WALKTHROUGH — Parcours complet de GérerSCI avec enregistrement vidéo
 *
 * Ce test unique traverse TOUTES les pages de l'application dans un flux
 * cohérent, générant une vidéo de démonstration complète.
 *
 * Couverture: 44 pages / 100% des features visibles
 *
 * Usage:
 *   E2E_AUTH_TOKEN=<jwt> E2E_SCI_ID=<id> E2E_BIEN_ID=<id> \
 *   pnpm exec playwright test --config e2e/playwright.production.config.ts \
 *     e2e/production/video-walkthrough.spec.ts
 */

const SCI_BELLEVILLE = process.env.E2E_SCI_ID || '98d2ef33-92c0-43d7-9c71-d3f0acd95dd7';
const SCI_MONTSOURIS = process.env.E2E_SCI_ID_2 || '93109c6d-b845-4d67-ab27-99445db662c4';
const BIEN_BELLEVILLE = process.env.E2E_BIEN_ID || 'f80f8234-2a83-4ad9-a3d2-94eee688b5cb';
const BIEN_PYRENEES = '5515df99-8cd5-4d2c-b1ef-23f47ee61dd4';
const BIEN_VOLTAIRE = '100ac1dc-9426-4eb8-8655-c05e5de87c29';
const BIEN_REILLE = 'dd000001-0000-0000-0000-000000000001';

// Force video recording — always retained even on pass
test.use({
	video: { mode: 'on', size: { width: 1440, height: 900 } },
	viewport: { width: 1440, height: 900 }
});

// Helper: pause pour que la vidéo soit lisible
async function pause(page: import('@playwright/test').Page, ms = 1500) {
	await page.waitForTimeout(ms);
}

// Helper: dismiss cookie banner if present
async function dismissCookies(page: import('@playwright/test').Page) {
	const cookieBtn = page.getByRole('button', { name: /Tout accepter/i });
	if (await cookieBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
		await cookieBtn.click();
		await page.waitForTimeout(500);
	}
}

test.describe('Walkthrough vidéo complet', () => {
	test.beforeEach(async () => {
		test.skip(!process.env.E2E_AUTH_TOKEN, 'E2E_AUTH_TOKEN manquant');
	});

	test('parcours complet — toutes les features', async ({ authedPage: page }) => {
		// Timeout long pour le walkthrough complet
		test.setTimeout(300_000); // 5 minutes

		// ═══════════════════════════════════════════════
		// SECTION 1: PAGES PUBLIQUES
		// ═══════════════════════════════════════════════

		// 1.1 Landing page
		await page.goto('/');
		await page.waitForLoadState('networkidle');
		await dismissCookies(page);
		await pause(page, 2000);

		// Scroll landing page pour montrer le contenu
		await page.evaluate(() => window.scrollTo({ top: 600, behavior: 'smooth' }));
		await pause(page);
		await page.evaluate(() => window.scrollTo({ top: 1200, behavior: 'smooth' }));
		await pause(page);
		await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
		await pause(page);

		// 1.2 Pricing
		await page.goto('/pricing');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);
		await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
		await pause(page);

		// 1.3 Simulateur CERFA (lead magnet public)
		await page.goto('/simulateur-cerfa');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// 1.4 Calendrier fiscal public
		await page.goto('/calendrier-fiscal');
		await page.waitForLoadState('networkidle');
		await pause(page);

		// 1.5 Générateur quittance public
		await page.goto('/generateur-quittance');
		await page.waitForLoadState('networkidle');
		await pause(page);

		// 1.6 Login page
		await page.goto('/login');
		await page.waitForLoadState('networkidle');
		await pause(page);

		// 1.7 Register page
		await page.goto('/register');
		await page.waitForLoadState('networkidle');
		await pause(page);

		// 1.8 Pages légales
		for (const path of ['/cgu', '/cgv', '/confidentialite', '/mentions-legales']) {
			await page.goto(path);
			await page.waitForLoadState('networkidle');
			await pause(page, 800);
		}

		// ═══════════════════════════════════════════════
		// SECTION 2: DASHBOARD (auth required)
		// ═══════════════════════════════════════════════

		// 2.1 Dashboard multi-SCI
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await pause(page, 2500);

		// Scroll pour voir les KPIs, alertes, cartes SCI
		await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
		await pause(page);
		await page.evaluate(() => window.scrollTo({ top: 800, behavior: 'smooth' }));
		await pause(page);
		await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
		await pause(page);

		// ═══════════════════════════════════════════════
		// SECTION 3: PORTEFEUILLE SCI
		// ═══════════════════════════════════════════════

		// 3.1 Liste des SCIs
		await page.goto('/scis');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// 3.2 Détail SCI Belleville
		await page.goto(`/scis/${SCI_BELLEVILLE}`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);
		await page.evaluate(() => window.scrollTo({ top: 500, behavior: 'smooth' }));
		await pause(page);
		await page.evaluate(() => window.scrollTo({ top: 1000, behavior: 'smooth' }));
		await pause(page);
		await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
		await pause(page);

		// 3.3 Détail SCI Montsouris
		await page.goto(`/scis/${SCI_MONTSOURIS}`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 4: BIENS IMMOBILIERS
		// ═══════════════════════════════════════════════

		// 4.1 Grille biens SCI Belleville
		await page.goto(`/scis/${SCI_BELLEVILLE}/biens`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// 4.2 Fiche bien — 12 rue de Belleville (tous les onglets)
		await page.goto(`/scis/${SCI_BELLEVILLE}/biens/${BIEN_BELLEVILLE}`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2500);

		// Scroll pour voir les onglets
		await page.evaluate(() => window.scrollTo({ top: 500, behavior: 'smooth' }));
		await pause(page);

		// Cliquer sur les différents onglets de la fiche bien
		const tabNames = ['Loyers', 'Charges', 'Documents', 'Rentabilité'];
		for (const tabName of tabNames) {
			const tab = page.getByRole('button', { name: new RegExp(tabName, 'i') }).or(
				page.getByText(new RegExp(tabName, 'i')).locator('visible=true')
			);
			if (await tab.first().isVisible({ timeout: 2000 }).catch(() => false)) {
				await tab.first().click();
				await pause(page, 1500);
			}
		}

		// 4.3 Fiche bien — Voltaire
		await page.goto(`/scis/${SCI_BELLEVILLE}/biens/${BIEN_VOLTAIRE}`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// 4.4 Baux page
		await page.goto(`/scis/${SCI_BELLEVILLE}/biens/${BIEN_BELLEVILLE}/baux`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 5: ASSOCIÉS
		// ═══════════════════════════════════════════════

		await page.goto(`/scis/${SCI_BELLEVILLE}/associes`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 6: FISCALITÉ
		// ═══════════════════════════════════════════════

		await page.goto(`/scis/${SCI_BELLEVILLE}/fiscalite`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);
		await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
		await pause(page);

		// ═══════════════════════════════════════════════
		// SECTION 7: ASSEMBLÉES GÉNÉRALES
		// ═══════════════════════════════════════════════

		await page.goto(`/scis/${SCI_BELLEVILLE}/assemblees-generales`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 8: MOUVEMENTS DE PARTS
		// ═══════════════════════════════════════════════

		await page.goto(`/scis/${SCI_BELLEVILLE}/mouvements-parts`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 9: DOCUMENTS
		// ═══════════════════════════════════════════════

		await page.goto(`/scis/${SCI_BELLEVILLE}/documents`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 10: EXPLOITATION (vue transversale)
		// ═══════════════════════════════════════════════

		await page.goto('/exploitation');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);
		await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
		await pause(page);

		// ═══════════════════════════════════════════════
		// SECTION 11: ÉCHÉANCES
		// ═══════════════════════════════════════════════

		await page.goto('/echeances');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 12: FINANCES CONSOLIDÉES
		// ═══════════════════════════════════════════════

		await page.goto('/finances');
		await page.waitForLoadState('networkidle');
		await pause(page, 2500);
		await page.evaluate(() => window.scrollTo({ top: 500, behavior: 'smooth' }));
		await pause(page);

		// ═══════════════════════════════════════════════
		// SECTION 13: BILANS MENSUELS
		// ═══════════════════════════════════════════════

		// 13.1 Bilan portefeuille
		await page.goto('/bilans');
		await page.waitForLoadState('networkidle');
		await pause(page, 2500);
		await page.evaluate(() => window.scrollTo({ top: 400, behavior: 'smooth' }));
		await pause(page);

		// 13.2 Bilan SCI deep-link
		await page.goto(`/bilans?scope=sci&scope_id=${SCI_BELLEVILLE}`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 14: SETTINGS
		// ═══════════════════════════════════════════════

		await page.goto('/settings');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// ═══════════════════════════════════════════════
		// SECTION 15: ADMIN DASHBOARD
		// ═══════════════════════════════════════════════

		const adminKey = process.env.ADMIN_SECRET_KEY || 'dev-admin-local';
		await page.goto(`/admin`);
		await page.waitForLoadState('networkidle');
		await pause(page, 1000);

		// Enter admin key if prompted
		const adminInput = page.getByPlaceholder(/clé|secret|admin|key/i);
		if (await adminInput.isVisible({ timeout: 2000 }).catch(() => false)) {
			await adminInput.fill(adminKey);
			const submitBtn = page.getByRole('button', { name: /Accéder|Valider|Entrer/i });
			if (await submitBtn.isVisible({ timeout: 1000 }).catch(() => false)) {
				await submitBtn.click();
			}
			await page.waitForLoadState('networkidle');
		}
		await pause(page, 2000);

		// Admin sub-pages
		for (const adminPath of ['/admin/users', '/admin/revenue', '/admin/audit']) {
			await page.goto(adminPath);
			await page.waitForLoadState('networkidle');
			await pause(page, 1500);
		}

		// ═══════════════════════════════════════════════
		// SECTION 16: MOBILE VIEW (resize)
		// ═══════════════════════════════════════════════

		await page.setViewportSize({ width: 375, height: 812 });
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// Mobile navigation demo
		await page.goto(`/scis/${SCI_BELLEVILLE}`);
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		await page.goto('/finances');
		await page.waitForLoadState('networkidle');
		await pause(page, 1500);

		// Back to desktop
		await page.setViewportSize({ width: 1440, height: 900 });

		// ═══════════════════════════════════════════════
		// FIN — Retour dashboard
		// ═══════════════════════════════════════════════

		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);

		// Save video manually before test ends
		const videoPath = await page.video()?.path();
		if (videoPath) {
			const fs = await import('fs');
			const dest = 'e2e-artifacts/video/gerersci-walkthrough.webm';
			await page.close(); // Flush video
			fs.mkdirSync('e2e-artifacts/video', { recursive: true });
			fs.copyFileSync(videoPath, dest);
		}
	});
});
