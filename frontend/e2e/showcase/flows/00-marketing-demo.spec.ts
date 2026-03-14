/**
 * MARKETING DEMO — One continuous flow, slow and cinematic.
 *
 * NOT a test — a scripted product demo for the landing page.
 * Single login, smooth navigation, visible interactions.
 *
 * Run: pnpm exec playwright test --config=e2e/playwright.marketing-capture.config.ts e2e/showcase/flows/00-marketing-demo.spec.ts
 */
import { test, expect, type Page } from '@playwright/test';

const BASE = 'http://localhost:5173';
const SUPABASE = 'http://127.0.0.1:54321';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

// Use pro account for full-featured demo
const DEMO_EMAIL = 'pro@audit.test';
const DEMO_PASSWORD = 'password123';

async function pause(page: Page, ms = 1500) {
  await page.waitForTimeout(ms);
}

async function dismissCookies(page: Page) {
  const btn = page.locator('button:has-text("Tout accepter")');
  if (await btn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await btn.click();
    await pause(page, 500);
  }
}

async function screenshot(page: Page, name: string) {
  await pause(page, 800);
  await page.screenshot({ path: `marketing/demo/${name}.png` });
}

test.describe.serial('GererSCI — Démonstration Produit', () => {
  let page: Page;

  test.beforeAll(async ({ browser }) => {
    // Single browser context for the entire demo
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 },
      locale: 'fr-FR',
      timezoneId: 'Europe/Paris',
      recordVideo: {
        dir: 'marketing/demo-videos/',
        size: { width: 1440, height: 900 },
      },
    });
    page = await context.newPage();
  });

  test.afterAll(async () => {
    await page.context().close(); // This saves the video
  });

  // ═══════════════════════════════════════════════════════════
  // SCENE 1: Landing page — première impression
  // ═══════════════════════════════════════════════════════════
  test('Scène 1 — Landing page', async () => {
    await page.goto(BASE);
    await page.waitForLoadState('networkidle');
    await dismissCookies(page);
    await pause(page, 2000); // Let user see the hero

    await screenshot(page, '01-landing-hero');

    // Scroll down slowly to show features
    for (let i = 0; i < 5; i++) {
      await page.mouse.wheel(0, 400);
      await pause(page, 800);
    }

    await screenshot(page, '02-landing-features');

    // Scroll to pricing
    await page.mouse.wheel(0, 600);
    await pause(page, 1000);
    await screenshot(page, '03-landing-pricing');

    // Toggle annual pricing
    const annualBtn = page.locator('button:has-text("Annuel")');
    if (await annualBtn.isVisible()) {
      await annualBtn.click();
      await pause(page, 1500);
      await screenshot(page, '04-pricing-annual');
    }
  });

  // ═══════════════════════════════════════════════════════════
  // SCENE 2: Connexion — flow de login
  // ═══════════════════════════════════════════════════════════
  test('Scène 2 — Connexion', async () => {
    await page.goto(`${BASE}/login`);
    await page.waitForLoadState('networkidle');
    await dismissCookies(page);
    await pause(page, 1000);

    await screenshot(page, '05-login-page');

    // Type email slowly
    const emailInput = page.locator('input[type="email"]');
    await emailInput.click();
    await pause(page, 500);
    await emailInput.type(DEMO_EMAIL, { delay: 80 });
    await pause(page, 500);

    // Type password
    const passwordInput = page.locator('input[type="password"]');
    await passwordInput.click();
    await passwordInput.type(DEMO_PASSWORD, { delay: 60 });
    await pause(page, 500);

    await screenshot(page, '06-login-filled');

    // Submit
    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();

    // Wait for redirect to dashboard
    await page.waitForURL(/dashboard|scis/, { timeout: 15000 });
    await page.waitForLoadState('networkidle');
    await pause(page, 2000);

    await screenshot(page, '07-dashboard-loaded');
  });

  // ═══════════════════════════════════════════════════════════
  // SCENE 3: Dashboard — exploration des KPIs et alertes
  // ═══════════════════════════════════════════════════════════
  test('Scène 3 — Dashboard', async () => {
    // We should already be on dashboard from Scene 2
    await pause(page, 1000);

    // Hover over KPI cards
    const kpiCards = page.locator('[class*="flex"][class*="items-center"][class*="gap"]').first();
    if (await kpiCards.isVisible()) {
      await kpiCards.hover();
      await pause(page, 1000);
    }

    await screenshot(page, '08-dashboard-kpis');

    // Scroll down to see SCI cards
    await page.mouse.wheel(0, 400);
    await pause(page, 1500);

    await screenshot(page, '09-dashboard-scis');
  });

  // ═══════════════════════════════════════════════════════════
  // SCENE 4: Portefeuille SCI — liste et sélection
  // ═══════════════════════════════════════════════════════════
  test('Scène 4 — Portefeuille SCI', async () => {
    // Navigate to SCIs list
    const scisLink = page.locator('a[href="/scis"], a:has-text("Mes SCI"), a:has-text("Portefeuille")');
    if (await scisLink.first().isVisible()) {
      await scisLink.first().click();
    } else {
      await page.goto(`${BASE}/scis`);
    }
    await page.waitForLoadState('networkidle');
    await pause(page, 2000);

    await screenshot(page, '10-scis-list');

    // Click on first SCI card
    const sciCard = page.locator('a[href*="/scis/"]').first();
    if (await sciCard.isVisible()) {
      await sciCard.click();
      await page.waitForLoadState('networkidle');
      await pause(page, 2000);
      await screenshot(page, '11-sci-detail');
    }
  });

  // ═══════════════════════════════════════════════════════════
  // SCENE 5: Biens immobiliers — grille et fiche détaillée
  // ═══════════════════════════════════════════════════════════
  test('Scène 5 — Biens immobiliers', async () => {
    // Navigate to biens
    const biensLink = page.locator('a:has-text("Biens")');
    if (await biensLink.first().isVisible()) {
      await biensLink.first().click();
      await page.waitForLoadState('networkidle');
      await pause(page, 2000);
    }

    await screenshot(page, '12-biens-grid');

    // Click on first bien
    const bienCard = page.locator('[class*="rounded"] a, [class*="card"] a, a[href*="/biens/"]').first();
    if (await bienCard.isVisible()) {
      await bienCard.click();
      await page.waitForLoadState('networkidle');
      await pause(page, 2000);
      await screenshot(page, '13-fiche-bien');

      // Scroll through the fiche bien
      await page.mouse.wheel(0, 400);
      await pause(page, 1500);
      await screenshot(page, '14-fiche-bien-scroll');
    }
  });

  // ═══════════════════════════════════════════════════════════
  // SCENE 6: Finances — vue consolidée
  // ═══════════════════════════════════════════════════════════
  test('Scène 6 — Finances', async () => {
    // Navigate to finances
    const finLink = page.locator('a:has-text("Finances"), a[href="/finances"]');
    if (await finLink.first().isVisible()) {
      await finLink.first().click();
    } else {
      await page.goto(`${BASE}/finances`);
    }
    await page.waitForLoadState('networkidle');
    await pause(page, 2000);

    await screenshot(page, '15-finances');

    // Scroll to see charts/tables
    await page.mouse.wheel(0, 400);
    await pause(page, 1500);
    await screenshot(page, '16-finances-details');
  });

  // ═══════════════════════════════════════════════════════════
  // SCENE 7: Associés — gestion des parts
  // ═══════════════════════════════════════════════════════════
  test('Scène 7 — Associés', async () => {
    // Go back to SCI and navigate to associes
    await page.goto(`${BASE}/scis`);
    await page.waitForLoadState('networkidle');
    await pause(page, 1000);

    const sciCard = page.locator('a[href*="/scis/"]').first();
    if (await sciCard.isVisible()) {
      await sciCard.click();
      await page.waitForLoadState('networkidle');
      await pause(page, 1000);

      const assocLink = page.locator('a:has-text("Associés")').first();
      if (await assocLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await assocLink.click();
        await page.waitForLoadState('networkidle');
        await pause(page, 2000);
        await screenshot(page, '17-associes');
      }
    }
  });

  // ═══════════════════════════════════════════════════════════
  // SCENE 8: Fiscalité — CERFA 2044
  // ═══════════════════════════════════════════════════════════
  test('Scène 8 — Fiscalité', async () => {
    const fiscaLink = page.locator('a:has-text("Fiscalité")').first();
    if (await fiscaLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await fiscaLink.click();
      await page.waitForLoadState('networkidle');
      await pause(page, 2000);
      await screenshot(page, '18-fiscalite');

      // Scroll to see CERFA section
      await page.mouse.wheel(0, 300);
      await pause(page, 1500);
      await screenshot(page, '19-cerfa');
    }
  });
});
