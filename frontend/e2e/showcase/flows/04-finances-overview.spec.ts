/**
 * Showcase: Vision Financiere 360
 * Consolidated financial view with charts and SCI repartition.
 *
 * NOT a functional test: focuses on visual quality, slow interactions, named screenshots.
 */
import { test, type Page } from '@playwright/test';

import { MARKETING_SCIS, MARKETING_USER } from '../seed/marketing-data';
import { capture, seedShowcaseUser, skipIfNoAuth, PRO_SUBSCRIPTION } from '../helpers/showcase-auth';

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const CORS_HEADERS = {
	'access-control-allow-origin': '*',
	'access-control-allow-methods': 'GET,POST,PATCH,DELETE,OPTIONS',
	'access-control-allow-headers': '*'
};

const SUBSCRIPTION = PRO_SUBSCRIPTION;

const belleville = MARKETING_SCIS[0];
const lyon = MARKETING_SCIS[1];

const FINANCES_DATA = {
	revenus_total: 80_040,
	charges_total: 9_240,
	cashflow_net: 70_800,
	patrimoine_total: 620_000,
	taux_recouvrement: 97.5,
	rentabilite_moyenne: 7.8,
	repartition_sci: [
		{
			sci_id: 'sci-belleville',
			sci_nom: belleville.nom,
			revenus: 27_240,
			charges: 3_240
		},
		{
			sci_id: 'sci-lyon',
			sci_nom: lyon.nom,
			revenus: 52_800,
			charges: 6_000
		}
	],
	evolution_mensuelle: Array.from({ length: 12 }, (_, i) => {
		const d = new Date(2026, 2 - i, 1);
		return {
			mois: d.toISOString().slice(0, 7),
			revenus: 6_670 + Math.round((Math.random() - 0.5) * 200),
			charges: 770 + Math.round((Math.random() - 0.5) * 50)
		};
	}).reverse()
};

const SCIS = [
	{
		id: 'sci-belleville',
		nom: belleville.nom,
		biens_count: 2,
		loyers_count: 24,
		total_monthly_rent: 2_270,
		user_role: 'gerant'
	},
	{
		id: 'sci-lyon',
		nom: lyon.nom,
		biens_count: 2,
		loyers_count: 24,
		total_monthly_rent: 4_400,
		user_role: 'gerant'
	}
];

async function installFinancesMocks(page: Page) {
	await page.route('**/api/v1/**', async (route) => {
		const request = route.request();
		const method = request.method();
		const url = new URL(request.url());
		const path = url.pathname;

		if (method === 'OPTIONS') {
			await route.fulfill({ status: 204, headers: CORS_HEADERS });
			return;
		}

		if (method === 'GET' && path === '/api/v1/stripe/subscription') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(SUBSCRIPTION)
			});
			return;
		}

		if (method === 'GET' && path === '/api/v1/finances') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(FINANCES_DATA)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(SCIS)
			});
			return;
		}

		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify([])
		});
	});
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
test.describe.serial('Showcase: Finances Overview', () => {
	test.beforeEach(async ({ page }) => {
		if (skipIfNoAuth()) test.skip();
		await installFinancesMocks(page);
		await seedShowcaseUser(page, {
			email: MARKETING_USER.email,
			sciId: 'sci-belleville'
		});
	});

	test('capture finances page', async ({ page }) => {
		await page.goto('/finances');
		// Extra delay for chart rendering (canvas/SVG animations)
		await page.waitForTimeout(2000);
		await page.evaluate(() => window.scrollTo(0, 0));
		await capture(page, 'finances-consolidated');
	});

	test('capture SCI repartition', async ({ page }) => {
		await page.goto('/finances');
		await page.waitForTimeout(2000);

		// Scroll down to the repartition table
		await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
		await page.waitForTimeout(800);

		await capture(page, 'finances-repartition');
	});
});
