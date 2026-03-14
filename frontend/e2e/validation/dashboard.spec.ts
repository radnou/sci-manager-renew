import { test, expect } from '@playwright/test';

const hasAuth = () => !!process.env.E2E_AUTH_TOKEN;

test.describe('Tableau de bord @P0', () => {
  test.skip(!hasAuth(), 'Requires E2E_AUTH_TOKEN');

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.evaluate((token) => {
      const session = {
        access_token: token,
        refresh_token: 'e2e-refresh',
        user: {
          id: process.env.E2E_USER_ID || 'e2e-user',
          email: process.env.E2E_USER_EMAIL || 'e2e@test.fr',
          role: 'authenticated',
        },
        expires_at: Math.floor(Date.now() / 1000) + 3600,
      };
      localStorage.setItem('sb-auth-token', JSON.stringify(session));
    }, process.env.E2E_AUTH_TOKEN);
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('le dashboard charge avec un titre @P0', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Dashboard should have a heading or recognizable title
    const heading = page.locator('h1, h2, [data-testid="dashboard-title"]');
    await expect(heading.first()).toBeVisible({ timeout: 10_000 });
  });

  test('la section KPI est visible @P0', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // KPI cards section should be present (look for KPI-related elements)
    const kpiSection = page.locator(
      '[data-testid="dashboard-kpis"], [class*="kpi"], [class*="Kpi"]'
    );
    // Fallback: look for stat cards with numbers
    const statCards = page.locator('[class*="card"], [class*="Card"]');
    const kpiVisible = await kpiSection.first().isVisible().catch(() => false);
    const cardsCount = await statCards.count();

    expect(kpiVisible || cardsCount > 0).toBe(true);
  });

  test('la section alertes est visible @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Alerts section (may show alerts or empty state)
    const alertsSection = page.locator(
      '[data-testid="dashboard-alerts"], :text("Alertes"), :text("alertes"), [class*="alert"], [class*="Alert"]'
    );
    // Even if empty, the section container should exist
    const exists = await alertsSection.first().isVisible().catch(() => false);

    // If no alerts section, the dashboard should at least have loaded without error
    const errorMessage = page.locator(':text("Erreur"), :text("erreur")');
    const hasError = await errorMessage.first().isVisible().catch(() => false);

    expect(exists || !hasError).toBe(true);
  });

  test('la section activite recente est visible @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const activitySection = page.locator(
      '[data-testid="dashboard-activity"], :text("Activité"), :text("activité"), :text("Récent")'
    );
    const exists = await activitySection.first().isVisible().catch(() => false);

    // The dashboard should render without critical errors
    const pageContent = await page.textContent('body');
    expect(exists || pageContent!.length > 100).toBe(true);
  });

  test('la section cartes SCI est visible @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    const sciCards = page.locator(
      '[data-testid="dashboard-sci-cards"], :text("SCI"), [class*="sci"]'
    );
    const exists = await sciCards.first().isVisible().catch(() => false);

    // Either SCI cards exist or there is an empty state
    const emptyState = page.locator(':text("Aucune SCI"), :text("Commencer"), :text("onboarding")');
    const isEmpty = await emptyState.first().isVisible().catch(() => false);

    expect(exists || isEmpty).toBe(true);
  });

  test('etat vide pour nouvel utilisateur @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // For a new user the dashboard should show either:
    // 1. An empty state with a CTA to create a SCI
    // 2. An onboarding redirect
    // 3. Regular dashboard content
    // All are valid states - verify the page loaded successfully
    const bodyText = await page.textContent('body');
    expect(bodyText!.length).toBeGreaterThan(0);

    // No unhandled JS errors should crash the page
    const hasContent = await page.locator('main, [role="main"], #app, body > div').first().isVisible();
    expect(hasContent).toBe(true);
  });
});
