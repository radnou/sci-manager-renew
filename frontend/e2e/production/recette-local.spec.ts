import { test, expect } from '@playwright/test';

/**
 * RECETTE LOCALE — Tests E2E avec storageState (session pré-chargée par auth.setup.ts)
 *
 * Usage:
 *   E2E_EMAIL=test@gerersci.fr E2E_PASSWORD=testpassword123 \
 *   pnpm exec playwright test --config e2e/playwright.local.config.ts \
 *     e2e/production/recette-local.spec.ts
 */

const SCI_1 = process.env.E2E_SCI_ID || 'aaaa1111-0000-0000-0000-000000000001';
const SCI_2 = process.env.E2E_SCI_ID_2 || 'aaaa1111-0000-0000-0000-000000000002';
const BIEN = process.env.E2E_BIEN_ID || '00000000-0000-0000-bbbb-000000000001';

/** Login via the /login page form — called once per test that needs auth */
async function loginAndGo(page: any, targetUrl: string) {
	await page.goto('/login');
	await page.waitForLoadState('networkidle');

	// Dismiss overlays
	const cookie = page.getByRole('button', { name: /Tout accepter/i });
	if (await cookie.isVisible({ timeout: 1000 }).catch(() => false)) await cookie.click();

	// Fill login form
	const email = page.locator('form input[type="email"], form input[type="text"]').first();
	await email.waitFor({ state: 'visible', timeout: 3000 });
	await email.fill(process.env.E2E_EMAIL || 'test@gerersci.fr');
	const pwd = page.locator('form input[type="password"]').first();
	if (await pwd.isVisible({ timeout: 1000 }).catch(() => false)) {
		await pwd.fill(process.env.E2E_PASSWORD || 'testpassword123');
	}
	await page.locator('form button[type="submit"]').first().click();

	// Wait for redirect away from /login
	await page.waitForURL((url: URL) => !url.pathname.includes('/login'), { timeout: 10000 });
	await page.waitForLoadState('networkidle');

	// Dismiss tour
	await page.evaluate(() => {
		localStorage.setItem('gerersci_cookie_consent', 'all');
		localStorage.setItem('gerersci_tour_completed', 'true');
	});
	const tour = page.getByRole('button', { name: /Passer/i });
	if (await tour.isVisible({ timeout: 1000 }).catch(() => false)) await tour.click();

	// Now navigate to target (SPA navigation — session preserved in memory)
	if (!page.url().includes(targetUrl.split('?')[0])) {
		await page.goto(targetUrl);
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(1000);
	}
}

/** Navigate within the same session (works after loginAndGo) */
async function go(page: any, url: string) {
	await page.goto(url);
	await page.waitForLoadState('networkidle');
	await page.waitForTimeout(800);
	// If we ended up on /login, the session was lost — do full login
	if (page.url().includes('/login') || page.url().includes('/pricing')) {
		await loginAndGo(page, url);
	}
}

// ─── M1: Pages publiques ──────────────────────────────────

test('M1 — landing page', async ({ page }) => {
	await page.goto('/');
	await page.waitForLoadState('networkidle');
	await expect(page.locator('body')).toContainText(/SCI|tableur|Excel|GérerSCI/i);
});

test('M1 — pricing', async ({ page }) => {
	await page.goto('/pricing');
	await page.waitForLoadState('networkidle');
	await expect(page.locator('body')).toContainText(/Gestion|Pilotage|Fondateur/i);
});

test('M1 — pages légales', async ({ page }) => {
	for (const path of ['/cgu', '/cgv', '/confidentialite', '/mentions-legales']) {
		const res = await page.goto(path);
		expect(res?.status()).toBe(200);
	}
});

test('M1 — simulateur CERFA', async ({ page }) => {
	await page.goto('/simulateur-cerfa');
	await page.waitForLoadState('networkidle');
	await expect(page.locator('body')).toContainText(/CERFA|2044|simulateur/i);
});

test('M1 — calendrier fiscal public', async ({ page }) => {
	await page.goto('/calendrier-fiscal');
	await page.waitForLoadState('networkidle');
	await expect(page.locator('body')).toContainText(/fiscal|calendrier|échéance/i);
});

// ─── M2: Dashboard ────────────────────────────────────────

test('M2 — dashboard affiche KPIs', async ({ page }) => {
	await go(page, '/dashboard');
	await expect(page.locator('body')).toContainText(/SCI|Bien|Loyer|Recouvrement|Dashboard/i);
});

// ─── M3: SCIs ─────────────────────────────────────────────

test('M3 — liste SCIs', async ({ page }) => {
	await go(page, '/scis');
	await expect(page.locator('body')).toContainText(/Oliviers|Haussmann/);
});

test('M3 — détail SCI', async ({ page }) => {
	await go(page, `/scis/${SCI_1}`);
	await expect(page.locator('body')).toContainText(/Oliviers/);
});

test('M3 — biens de la SCI', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/biens`);
	await expect(page.locator('body')).toContainText(/Jean Jaures|Republique|Castellane/);
});

// ─── M4: Fiche Bien ───────────────────────────────────────

test('M4 — fiche bien charge', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/biens/${BIEN}`);
	await expect(page.locator('body')).toContainText(/Jean Jaures|Marseille/);
});

test('M4 — bouton bilan présent', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/biens/${BIEN}`);
	const bilan = page.getByRole('link', { name: /Bilan/i });
	await expect(bilan).toBeVisible();
});

// ─── M5: Loyers ───────────────────────────────────────────

test('M5 — loyers affichés', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/biens/${BIEN}`);
	await expect(page.locator('body')).toContainText(/Loyer|loyer|retard|830/i);
});

// ─── M6: Associés ─────────────────────────────────────────

test('M6 — associés affichés', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/associes`);
	await expect(page.locator('body')).toContainText(/Mossabely|Dupont|gérant|associé/i);
});

// ─── M7: Finances ─────────────────────────────────────────

test('M7 — finances consolidées', async ({ page }) => {
	await go(page, '/finances');
	await expect(page.locator('body')).toContainText(/Finances|Revenus|Charges|Cashflow/i);
});

// ─── M8: Bilans ───────────────────────────────────────────

test('M8 — bilans mensuels', async ({ page }) => {
	await go(page, '/bilans');
	await expect(page.locator('body')).toContainText(/Bilan|Portefeuille/i);
});

test('M8 — bilan SCI deep-link', async ({ page }) => {
	await go(page, `/bilans?scope=sci&scope_id=${SCI_1}`);
	await page.waitForTimeout(1500);
	// Page should load without error
	expect(page.url()).toContain('/bilans');
});

// ─── M9: Notifications ───────────────────────────────────

test('M9 — navbar avec notifications', async ({ page }) => {
	await go(page, '/dashboard');
	await expect(page.locator('nav').first()).toBeVisible();
});

// ─── M10: Settings ────────────────────────────────────────

test('M10 — settings charge', async ({ page }) => {
	const res = await page.goto('/settings');
	expect(res?.status()).toBeLessThan(500);
});

// ─── M11: Échéances ───────────────────────────────────────

test('M11 — échéances', async ({ page }) => {
	await go(page, '/echeances');
	await expect(page.locator('body')).toContainText(/Échéances|échéance|Aucune/i);
});

// ─── M12: Exploitation ────────────────────────────────────

test('M12 — exploitation', async ({ page }) => {
	await go(page, '/exploitation');
	await page.waitForTimeout(1000);
	expect(page.url()).toContain('/exploitation');
});

// ─── M13: Mobile ──────────────────────────────────────────

test('M13 — mobile responsive', async ({ page }) => {
	await page.setViewportSize({ width: 375, height: 812 });
	await go(page, '/dashboard');
	await expect(page.locator('nav').first()).toBeVisible();
});

// ─── M14: AG + Mouvements ─────────────────────────────────

test('M14 — assemblées générales', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/assemblees-generales`);
	await page.waitForTimeout(1000);
	expect(page.url()).toContain('/assemblees-generales');
});

test('M14 — mouvements de parts', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/mouvements-parts`);
	await page.waitForTimeout(1000);
	expect(page.url()).toContain('/mouvements-parts');
});

// ─── M15: Fiscalité ───────────────────────────────────────

test('M15 — fiscalité', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/fiscalite`);
	await expect(page.locator('body')).toContainText(/Fiscalité|IR|IS|2044/i);
});

// ─── M16: Documents ───────────────────────────────────────

test('M16 — documents', async ({ page }) => {
	await go(page, `/scis/${SCI_1}/documents`);
	await page.waitForTimeout(1000);
	expect(page.url()).toContain('/documents');
});

// ─── M17: Stripe Checkout ─────────────────────────────────

test('M17 — Stripe guest checkout génère une URL', async ({ request }) => {
	const apiUrl = process.env.VITE_API_URL || 'http://localhost:8001';
	const res = await request.post(`${apiUrl}/api/v1/stripe/create-guest-checkout`, {
		data: { plan_key: 'starter', billing_period: 'month', email: 'e2e-stripe@gerersci.fr' }
	});
	expect(res.status()).toBe(200);
	const body = await res.json();
	expect(body.checkout_url || body.url).toContain('checkout.stripe.com');
});

// ─── M18: Admin ───────────────────────────────────────────

test('M18 — admin dashboard', async ({ page }) => {
	await page.goto('/admin');
	await page.waitForLoadState('networkidle');
	await page.waitForTimeout(1000);
	// Enter admin key
	const input = page.getByPlaceholder(/clé|secret|admin|key/i);
	if (await input.isVisible({ timeout: 2000 }).catch(() => false)) {
		await input.fill(process.env.ADMIN_SECRET_KEY || 'dev-admin-local');
		const btn = page.getByRole('button', { name: /Accéder|Valider|Entrer/i });
		if (await btn.isVisible({ timeout: 1000 }).catch(() => false)) await btn.click();
		await page.waitForLoadState('networkidle');
	}
	await page.waitForTimeout(1500);
	// Should be on admin or have admin content
	expect(page.url()).toContain('/admin');
});

// ─── M19: API Backend sanity ──────────────────────────────

test('M19 — health ready', async ({ request }) => {
	const apiUrl = process.env.VITE_API_URL || 'http://localhost:8001';
	const res = await request.get(`${apiUrl}/health/ready`);
	expect(res.status()).toBe(200);
	const body = await res.json();
	expect(body.summary.ready_for_traffic).toBe(true);
});
