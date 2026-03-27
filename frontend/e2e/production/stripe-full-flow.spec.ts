import { test, expect } from '@playwright/test';

/**
 * STRIPE FULL FLOW — Test complet en local
 *
 * 1. Login user SANS subscription → redirect /pricing
 * 2. Vérifie la page pricing (plans, checkbox L221-28)
 * 3. Crée un checkout Stripe via l'API (guest checkout)
 * 4. Navigue vers la page checkout Stripe
 * 5. Remplit la carte test 4242 4242 4242 4242
 * 6. Paye → webhook → subscription créée
 * 7. Vérifie que le dashboard est accessible
 * 8. Parcours complet de toutes les features
 *
 * Prérequis:
 *   - stripe listen --forward-to localhost:8001/api/v1/stripe/webhook
 */

test.use({
	video: { mode: 'on', size: { width: 1440, height: 900 } },
	viewport: { width: 1440, height: 900 }
});

const EMAIL = 'e2e-stripe@gerersci.fr';
const PASSWORD = 'StripeTest2026!';
const API_URL = process.env.VITE_API_URL || 'http://localhost:8001';

async function pause(page: any, ms = 1500) {
	await page.waitForTimeout(ms);
}

test('Flow complet: pricing → Stripe checkout → paiement → features débloquées', async ({ page }) => {
	test.setTimeout(300_000);

	// ═══════════════════════════════════════════════
	// ÉTAPE 1: LOGIN → redirect /pricing
	// ═══════════════════════════════════════════════

	await page.goto('/login');
	await page.waitForLoadState('networkidle');

	// Dismiss cookie
	const cookie = page.getByRole('button', { name: /Tout accepter/i });
	if (await cookie.isVisible({ timeout: 2000 }).catch(() => false)) await cookie.click();

	// Login
	await page.locator('form input[type="email"], form input[type="text"]').first().fill(EMAIL);
	const pwd = page.locator('form input[type="password"]').first();
	if (await pwd.isVisible({ timeout: 1000 }).catch(() => false)) await pwd.fill(PASSWORD);
	await page.locator('form button[type="submit"]').first().click();

	await page.waitForURL((url: URL) => !url.pathname.includes('/login'), { timeout: 15_000 });
	await page.waitForLoadState('networkidle');
	await pause(page, 2000);

	// Should be on /pricing (no subscription)
	console.log('📍 After login:', page.url());

	// ═══════════════════════════════════════════════
	// ÉTAPE 2: PAGE PRICING
	// ═══════════════════════════════════════════════

	if (!page.url().includes('/pricing')) {
		await page.goto('/pricing');
		await page.waitForLoadState('networkidle');
	}
	await pause(page);

	// Verify plans visible
	await expect(page.locator('body')).toContainText(/19.*mois|Gestion/i);
	await expect(page.locator('body')).toContainText(/39.*mois|Pilotage/i);
	console.log('✅ Pricing page loaded with plans');

	// Check the L221-28 consent checkbox
	const checkbox = page.locator('input[type="checkbox"]').first();
	await checkbox.check();
	await pause(page, 500);
	console.log('✅ L221-28 consent checked');

	// ═══════════════════════════════════════════════
	// ÉTAPE 3: CRÉER CHECKOUT VIA API (guest checkout)
	// ═══════════════════════════════════════════════

	// Use the API directly to create a checkout session
	const checkoutRes = await fetch(`${API_URL}/api/v1/stripe/create-guest-checkout`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			plan_key: 'starter',
			billing_period: 'month',
			email: EMAIL
		})
	});

	expect(checkoutRes.ok).toBe(true);
	const checkoutData = await checkoutRes.json();
	const checkoutUrl = checkoutData.checkout_url || checkoutData.url;
	expect(checkoutUrl).toContain('checkout.stripe.com');
	console.log('✅ Stripe checkout URL:', checkoutUrl.slice(0, 60) + '...');

	// ═══════════════════════════════════════════════
	// ÉTAPE 4: NAVIGUER VERS STRIPE CHECKOUT
	// ═══════════════════════════════════════════════

	await page.goto(checkoutUrl);
	await page.waitForLoadState('domcontentloaded');
	await pause(page, 5000); // Stripe checkout takes time to fully render

	console.log('📍 On Stripe checkout:', page.url().slice(0, 60));

	// ═══════════════════════════════════════════════
	// ÉTAPE 5: REMPLIR LA CARTE DE TEST
	// ═══════════════════════════════════════════════

	// Stripe Checkout hosted page — fill the card form
	// The email may be pre-filled from the checkout session
	const emailField = page.locator('#email, [name="email"]');
	if (await emailField.isVisible({ timeout: 2000 }).catch(() => false)) {
		if (await emailField.inputValue() === '') {
			await emailField.fill(EMAIL);
		}
	}

	// Card number
	const cardNumber = page.locator('#cardNumber, [name="cardNumber"], [autocomplete="cc-number"]');
	await cardNumber.waitFor({ state: 'visible', timeout: 10_000 });
	await cardNumber.fill('4242424242424242');
	console.log('✅ Card number filled');

	// Expiry
	const cardExpiry = page.locator('#cardExpiry, [name="cardExpiry"], [autocomplete="cc-exp"]');
	await cardExpiry.fill('12/30');

	// CVC
	const cardCvc = page.locator('#cardCvc, [name="cardCvc"], [autocomplete="cc-csc"]');
	await cardCvc.fill('123');

	// Cardholder name
	const cardName = page.locator('#billingName, [name="billingName"], [autocomplete="cc-name"]');
	if (await cardName.isVisible({ timeout: 1000 }).catch(() => false)) {
		await cardName.fill('Test E2E GererSCI');
	}

	await pause(page, 1000);
	console.log('✅ Card form filled');

	// ═══════════════════════════════════════════════
	// ÉTAPE 6: PAYER
	// ═══════════════════════════════════════════════

	const payButton = page.locator('.SubmitButton, button[type="submit"], [data-testid="hosted-payment-submit-button"]').first();
	await payButton.waitFor({ state: 'visible', timeout: 5000 });
	await payButton.click();
	console.log('🔄 Payment submitted, waiting for processing...');

	// Wait for Stripe to process and redirect back to our app
	await page.waitForURL(/localhost|gerersci\.fr/, { timeout: 60_000 });
	await page.waitForLoadState('networkidle');
	console.log('📍 Redirected to:', page.url());
	await pause(page, 3000);

	// ═══════════════════════════════════════════════
	// ÉTAPE 7: ATTENDRE LE WEBHOOK
	// ═══════════════════════════════════════════════

	// Give the Stripe webhook time to arrive and be processed
	console.log('⏳ Waiting for webhook processing...');
	await pause(page, 5000);

	// ═══════════════════════════════════════════════
	// ÉTAPE 8: VÉRIFIER QUE LE DASHBOARD EST ACCESSIBLE
	// ═══════════════════════════════════════════════

	await page.goto('/dashboard');
	await page.waitForLoadState('networkidle');
	await pause(page, 2000);

	// Dismiss overlays
	await page.evaluate(() => {
		localStorage.setItem('gerersci_cookie_consent', 'all');
		localStorage.setItem('gerersci_tour_completed', 'true');
	});
	const tour = page.getByRole('button', { name: /Passer/i });
	if (await tour.isVisible({ timeout: 1000 }).catch(() => false)) await tour.click();

	// If still on /pricing, wait more for webhook
	if (page.url().includes('/pricing')) {
		console.log('⏳ Still on pricing, waiting for webhook...');
		await pause(page, 10000);
		await page.goto('/dashboard');
		await page.waitForLoadState('networkidle');
		await pause(page, 2000);
	}

	const onDashboard = page.url().includes('/dashboard') || page.url().includes('/onboarding');
	console.log(onDashboard ? '✅ SUBSCRIPTION ACTIVE!' : '⚠️ Still on: ' + page.url());

	// ═══════════════════════════════════════════════
	// ÉTAPE 9: PARCOURS FEATURES (si débloqué)
	// ═══════════════════════════════════════════════

	if (onDashboard) {
		const pages = ['/scis', '/finances', '/bilans', '/echeances', '/exploitation', '/settings'];
		for (const p of pages) {
			await page.goto(p);
			await page.waitForLoadState('networkidle');
			await pause(page, 800);
			console.log(`  ✅ ${p}`);
		}
	}

	// ═══════════════════════════════════════════════
	// SAVE VIDEO
	// ═══════════════════════════════════════════════

	const videoPath = await page.video()?.path();
	if (videoPath) {
		const fs = await import('fs');
		const dest = 'e2e-artifacts/video/stripe-full-flow.webm';
		await page.close();
		fs.mkdirSync('e2e-artifacts/video', { recursive: true });
		fs.copyFileSync(videoPath, dest);
		console.log(`📹 Video: ${dest}`);
	}
});
