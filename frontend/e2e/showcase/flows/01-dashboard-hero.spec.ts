/**
 * Showcase: Le Cockpit du Gerant
 * Hero shot for the landing page — dashboard in light/dark mode with interactions.
 *
 * NOT a functional test: focuses on visual quality, slow interactions, named screenshots.
 */
import { test, type Page } from '@playwright/test';

import { MARKETING_SCIS, MARKETING_USER } from '../seed/marketing-data';
import { capture, CORS_HEADERS as SHARED_CORS, seedShowcaseUser, skipIfNoAuth, PRO_SUBSCRIPTION } from '../helpers/showcase-auth';

// ---------------------------------------------------------------------------
// Shared mock data for a rich dashboard
// ---------------------------------------------------------------------------
const CORS_HEADERS = SHARED_CORS;
const SUBSCRIPTION = PRO_SUBSCRIPTION;

function buildDashboardPayload() {
	const belleville = MARKETING_SCIS[0];
	const lyon = MARKETING_SCIS[1];

	return {
		kpis: {
			total_scis: 2,
			total_biens: 4,
			total_loyers_mois: 6_670,
			total_charges_mois: 770,
			taux_occupation: 100,
			loyers_impayes: 0,
			revenus_annuels: 80_040,
			charges_annuelles: 9_240
		},
		alertes: [
			{
				type: 'bail_expiring',
				message: 'Bail de Emilie Dupont expire dans 45 jours',
				severity: 'warning',
				sci_nom: belleville.nom,
				bien_adresse: '12 rue de Belleville'
			},
			{
				type: 'loyer_pending',
				message: 'Loyer de mars 2026 en attente — Lucas Martin',
				severity: 'info',
				sci_nom: belleville.nom,
				bien_adresse: '8 rue des Lilas'
			}
		],
		scis: [
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
		],
		activite_recente: [
			{ type: 'loyer_paye', message: 'Loyer de fevrier paye — Fatima Benali', date: '2026-03-05' },
			{
				type: 'document_upload',
				message: 'Quittance generee — 12 rue de Belleville',
				date: '2026-03-04'
			},
			{
				type: 'loyer_paye',
				message: 'Loyer de fevrier paye — SARL Boulangerie Hugo',
				date: '2026-03-03'
			}
		]
	};
}

const NOTIFICATIONS = [
	{
		id: 'notif-1',
		type: 'loyer_pending',
		title: 'Loyer en attente',
		message: 'Le loyer de mars 2026 pour 8 rue des Lilas est en attente.',
		read: false,
		created_at: '2026-03-13T10:00:00Z'
	},
	{
		id: 'notif-2',
		type: 'bail_expiring',
		title: 'Bail bientot expire',
		message: 'Le bail de Emilie Dupont expire le 28 avril 2026.',
		read: false,
		created_at: '2026-03-12T14:30:00Z'
	},
	{
		id: 'notif-3',
		type: 'document',
		title: 'Quittance generee',
		message: 'Quittance de fevrier pour 12 rue de Belleville.',
		read: true,
		created_at: '2026-03-10T09:15:00Z'
	}
];

async function installDashboardMocks(page: Page) {
	const dashboardData = buildDashboardPayload();

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

		if (method === 'GET' && path === '/api/v1/dashboard') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(dashboardData)
			});
			return;
		}

		if (method === 'GET' && path === '/api/v1/notifications') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(NOTIFICATIONS)
			});
			return;
		}

		if (method === 'GET' && (path === '/api/v1/scis' || path === '/api/v1/scis/')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify(dashboardData.scis)
			});
			return;
		}

		// Default: empty array
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
test.describe.serial('Showcase: Dashboard Hero', () => {
	test.beforeEach(async ({ page }) => {
		if (skipIfNoAuth()) test.skip();
		await installDashboardMocks(page);
		await seedShowcaseUser(page, {
			email: MARKETING_USER.email,
			sciId: 'sci-belleville'
		});
	});

	test('capture dashboard light mode', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForTimeout(1200); // Let KPIs, alerts, SCI cards fully render
		await page.evaluate(() => window.scrollTo(0, 0));
		await capture(page, 'dashboard-light');
	});

	test('capture dashboard dark mode', async ({ page }) => {
		// Set dark mode before navigation
		await page.addInitScript(() => {
			localStorage.setItem('color-theme', 'dark');
			document.documentElement.classList.add('dark');
		});
		await page.goto('/dashboard');
		await page.waitForTimeout(1200);
		await page.evaluate(() => {
			document.documentElement.classList.add('dark');
		});
		await page.waitForTimeout(500);
		await page.evaluate(() => window.scrollTo(0, 0));
		await capture(page, 'dashboard-dark');
	});

	test('capture dashboard interaction', async ({ page }) => {
		await page.goto('/dashboard');
		await page.waitForTimeout(1200);

		// Hover over first KPI card to reveal tooltip / highlight effect
		const kpiCard = page.locator('[data-testid="kpi-card"], .kpi-card, .stat-card').first();
		if (await kpiCard.isVisible()) {
			await kpiCard.hover();
			await page.waitForTimeout(600);
		}

		// Click notification bell to open panel
		const notifBell = page.locator(
			'button[aria-label*="notification"], button[aria-label*="Notification"], [data-testid="notification-bell"]'
		);
		if (await notifBell.isVisible()) {
			await notifBell.click();
			await page.waitForTimeout(800);
		}

		await capture(page, 'dashboard-notifications');
	});
});
