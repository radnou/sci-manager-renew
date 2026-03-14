import { test, expect } from '@playwright/test';
import { takeScreenshots, SCREENSHOT_DIR } from './helpers/auth';

test.describe.serial('01 — Pages publiques (landing, pricing, login)', () => {
	test('Page d\'accueil — hero et proposition de valeur', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Verify hero headline
		const h1 = page.locator('h1');
		await expect(h1).toBeVisible();
		await expect(h1).toContainText('Votre SCI mérite mieux');

		// Verify trust bar elements
		await expect(page.getByText('Hébergé en UE')).toBeVisible();
		await expect(page.getByText('RGPD')).toBeVisible();
		await expect(page.getByText('Sans engagement')).toBeVisible();

		// Verify primary CTA
		await expect(page.getByRole('link', { name: /Démarrer/i })).toBeVisible();
		await expect(page.getByRole('link', { name: /Essayer gratuitement/i })).toBeVisible();

		await takeScreenshots(page, '01-landing-hero');
	});

	test('Page d\'accueil — section audience cible', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Scroll to audience section
		const audienceSection = page.getByText('Conçu pour ceux qui gèrent des SCI');
		await audienceSection.scrollIntoViewIfNeeded();
		await page.waitForTimeout(300);

		await expect(audienceSection).toBeVisible();
		await expect(page.getByText('Gérant SCI indépendant')).toBeVisible();
		await expect(page.getByText('Cabinet comptable')).toBeVisible();
		await expect(page.getByText('Investisseur patrimonial')).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/01-landing-audience.png`,
			fullPage: false
		});
	});

	test('Page d\'accueil — section fonctionnalites', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		const featuresHeading = page.getByText('Tout ce dont vous avez besoin');
		await featuresHeading.scrollIntoViewIfNeeded();
		await page.waitForTimeout(300);

		await expect(featuresHeading).toBeVisible();
		await expect(page.getByText('Quittances PDF automatiques')).toBeVisible();
		await expect(page.getByText('Résumé fiscal par exercice')).toBeVisible();
		await expect(page.getByText('Suivi des retards de paiement')).toBeVisible();
		await expect(page.getByText('Toutes vos SCI en un seul compte')).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/01-landing-features.png`,
			fullPage: false
		});
	});

	test('Page d\'accueil — section tarifs (integrée)', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		// Scroll to pricing anchor
		await page.goto('/#pricing');
		await page.waitForTimeout(500);

		// Verify plan names
		await expect(page.getByText('Essentiel').first()).toBeVisible();
		await expect(page.getByText('Gestion').first()).toBeVisible();
		await expect(page.getByText('Fiscal').first()).toBeVisible();

		// Verify "Populaire" badge on Fiscal plan
		await expect(page.getByText('Populaire').first()).toBeVisible();

		// Verify free plan shows "Gratuit"
		await expect(page.getByText('Gratuit').first()).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/01-landing-pricing.png`,
			fullPage: false
		});
	});

	test('Page d\'accueil — toggle mensuel/annuel', async ({ page }) => {
		await page.goto('/#pricing');
		await page.waitForLoadState('networkidle');
		await page.waitForTimeout(300);

		// Default is monthly — verify 19 EUR visible
		await expect(page.getByText('19€').first()).toBeVisible();
		await expect(page.getByText('39€').first()).toBeVisible();

		// Switch to annual
		const annuelButton = page.getByRole('button', { name: /Annuel/i }).first();
		await annuelButton.click();
		await page.waitForTimeout(300);

		// Verify annual prices
		await expect(page.getByText('180€').first()).toBeVisible();
		await expect(page.getByText('348€').first()).toBeVisible();

		// Verify savings badge
		await expect(page.getByText('Économisez 2 mois').first()).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/01-landing-pricing-annual.png`,
			fullPage: false
		});
	});

	test('Page d\'accueil — FAQ', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		const faqHeading = page.getByText('Tout ce que vous devez savoir');
		await faqHeading.scrollIntoViewIfNeeded();
		await page.waitForTimeout(300);

		await expect(faqHeading).toBeVisible();

		// Verify first FAQ question
		const firstQuestion = page.getByText('Le produit est-il adapté à une petite SCI familiale ?');
		await expect(firstQuestion).toBeVisible();

		// Open first FAQ item
		await firstQuestion.click();
		await page.waitForTimeout(200);

		// Verify answer is now visible
		await expect(page.getByText("L'interface est pensée pour démarrer simple")).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/01-landing-faq.png`,
			fullPage: false
		});
	});

	test('Page d\'accueil — CTA final', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		const ctaHeading = page.getByText('Créez votre compte gratuitement');
		await ctaHeading.scrollIntoViewIfNeeded();
		await page.waitForTimeout(300);

		await expect(ctaHeading).toBeVisible();
		await expect(page.getByText('Sans engagement. Annulez quand vous voulez.')).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/01-landing-cta-final.png`,
			fullPage: false
		});
	});

	test('Page d\'accueil — donnees du secteur', async ({ page }) => {
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		const marketSection = page.getByText('Chiffres clés de la gestion immobilière');
		await marketSection.scrollIntoViewIfNeeded();
		await page.waitForTimeout(300);

		await expect(marketSection).toBeVisible();
		await expect(page.getByText('3,50%')).toBeVisible();
		await expect(page.getByText('50%')).toBeVisible();
		await expect(page.getByText('72%')).toBeVisible();

		await page.screenshot({
			path: `${SCREENSHOT_DIR}/01-landing-market-data.png`,
			fullPage: false
		});
	});

	test('Page tarifs dediee — /pricing', async ({ page }) => {
		await page.goto('/pricing');
		await page.waitForLoadState('networkidle');

		// Verify page title
		await expect(page).toHaveTitle(/Tarifs/);

		// Verify all 3 plans
		await expect(page.getByText('Essentiel')).toBeVisible();
		await expect(page.getByText('Gestion')).toBeVisible();
		await expect(page.getByText('Fiscal')).toBeVisible();

		// Verify billing toggle
		await expect(page.getByRole('button', { name: 'Mensuel' })).toBeVisible();
		await expect(page.getByRole('button', { name: /Annuel/i })).toBeVisible();

		// Verify feature lists
		await expect(page.getByText('Quittances PDF')).toBeVisible();
		await expect(page.getByText('Gestion documentaire')).toBeVisible();
		await expect(page.getByText('Résumé fiscal PDF (CERFA 2044)')).toBeVisible();

		// Verify CTAs
		await expect(page.getByText('Commencer gratuitement')).toBeVisible();
		await expect(page.getByText('Choisir Gestion')).toBeVisible();
		await expect(page.getByText('Choisir Fiscal')).toBeVisible();

		await takeScreenshots(page, '01-pricing-page');
	});
});
