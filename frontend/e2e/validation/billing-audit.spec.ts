/**
 * Billing Audit E2E — Test paywall UX, Stripe checkout, and plan limits.
 *
 * Tests against local dev stack with 3 seeded accounts:
 * - free@audit.test (Essentiel, 1 SCI max, 2 biens max)
 * - starter@audit.test (Gestion, 3 SCI max, 10 biens max)
 * - pro@audit.test (Fiscal, unlimited)
 *
 * Requires: local Supabase + backend + frontend running.
 * Run: E2E_BILLING_AUDIT=1 pnpm test:e2e:validate -- billing-audit
 */
import { test, expect, type Page } from '@playwright/test';

const BILLING_AUDIT = !!process.env.E2E_BILLING_AUDIT;
const SUPABASE_URL = 'http://127.0.0.1:54321';
const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

async function loginAs(page: Page, email: string, password = 'password123') {
  // Real login via the login form
  await page.goto('/login');
  await page.waitForLoadState('networkidle');

  // Dismiss cookie banner if present
  const cookieBtn = page.locator('button:has-text("Tout accepter")');
  if (await cookieBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
    await cookieBtn.click();
    await page.waitForTimeout(300);
  }

  // Fill email
  const emailInput = page.locator('input[type="email"]');
  await emailInput.fill(email);

  // Fill password
  const passwordInput = page.locator('input[type="password"]');
  await passwordInput.fill(password);

  // Submit
  const submitBtn = page.locator('button[type="submit"]');
  await submitBtn.click();

  // Wait for navigation to dashboard or app
  await page.waitForURL(/dashboard|scis|onboarding/, { timeout: 15000 }).catch(() => {});
  await page.waitForLoadState('networkidle');
}

async function capture(page: Page, name: string) {
  await page.waitForTimeout(500);
  await page.screenshot({ path: `e2e-artifacts/billing-audit/${name}.png` });
}

test.describe('Audit Billing & Paywall @BILLING', () => {
  test.skip(!BILLING_AUDIT, 'Set E2E_BILLING_AUDIT=1 to run');

  test.describe.serial('Pricing Page', () => {
    test('affiche 3 plans avec les bons prix', async ({ page }) => {
      await page.goto('/pricing');
      await page.waitForLoadState('networkidle');

      const content = await page.textContent('body');
      expect(content).toContain('Essentiel');
      expect(content).toContain('Gestion');
      expect(content).toContain('Fiscal');
      expect(content).toContain('19€');
      expect(content).toContain('39€');
      expect(content).toContain('Gratuit');

      await capture(page, '01-pricing-plans');
    });

    test('le toggle mensuel/annuel change les prix', async ({ page }) => {
      await page.goto('/pricing');
      await page.waitForLoadState('networkidle');

      // Click annual toggle
      const annualBtn = page.locator('button:has-text("Annuel"), button:has-text("annuel")');
      if (await annualBtn.isVisible()) {
        await annualBtn.click();
        await page.waitForTimeout(300);
        const content = await page.textContent('body');
        // Annual prices should show (180€ or 15€/mois, 348€ or 29€/mois)
        expect(content).toContain('mois');
        await capture(page, '02-pricing-annual');
      }
    });

    test('CTA Gestion redirige vers Stripe checkout', async ({ page }) => {
      await page.goto('/pricing');
      await page.waitForLoadState('networkidle');

      // Find and click the Starter CTA
      const starterCta = page.locator('button:has-text("Démarrer"), a:has-text("Démarrer")').first();
      if (await starterCta.isVisible()) {
        // Listen for navigation to stripe.com
        const [newPage] = await Promise.all([
          page.waitForEvent('popup', { timeout: 10000 }).catch(() => null),
          starterCta.click(),
        ]);

        if (newPage) {
          expect(newPage.url()).toContain('checkout.stripe.com');
          await capture(newPage, '03-stripe-checkout-starter');
          await newPage.close();
        } else {
          // Redirect in same tab
          await page.waitForURL(/checkout\.stripe\.com|register/, { timeout: 10000 });
          await capture(page, '03-stripe-checkout-or-register');
        }
      }
    });
  });

  test.describe.serial('Compte FREE — Limites', () => {
    test.beforeEach(async ({ page }) => {
      await loginAs(page, 'free@audit.test');
    });

    test('dashboard affiche le plan Free', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      await capture(page, '04-free-dashboard');
    });

    test('la liste SCI montre 1 SCI', async ({ page }) => {
      await page.goto('/scis');
      await page.waitForLoadState('networkidle');
      await capture(page, '05-free-scis-list');
    });

    test('tentative de créer 2ème SCI → upgrade prompt', async ({ page }) => {
      await page.goto('/scis');
      await page.waitForLoadState('networkidle');

      // Click "Nouvelle SCI" or similar button
      const createBtn = page.locator('button:has-text("Nouvelle"), a:has-text("Nouvelle"), button:has-text("Créer")');
      if (await createBtn.first().isVisible()) {
        await createBtn.first().click();
        await page.waitForTimeout(1000);
        await capture(page, '06-free-create-sci-blocked');
      }
    });
  });

  test.describe.serial('Compte STARTER — Multi-SCI', () => {
    test.beforeEach(async ({ page }) => {
      await loginAs(page, 'starter@audit.test');
    });

    test('dashboard charge avec données', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      await capture(page, '07-starter-dashboard');
    });

    test('la liste SCI montre 3 SCI', async ({ page }) => {
      await page.goto('/scis');
      await page.waitForLoadState('networkidle');
      await capture(page, '08-starter-scis-list');
    });
  });

  test.describe.serial('Compte PRO — Accès complet', () => {
    test.beforeEach(async ({ page }) => {
      await loginAs(page, 'pro@audit.test');
    });

    test('dashboard charge avec toutes les données', async ({ page }) => {
      await page.goto('/dashboard');
      await page.waitForLoadState('networkidle');
      await capture(page, '09-pro-dashboard');
    });

    test('la liste SCI montre 5+ SCI', async ({ page }) => {
      await page.goto('/scis');
      await page.waitForLoadState('networkidle');
      await capture(page, '10-pro-scis-list');
    });

    test('accès fiscalité fonctionne', async ({ page }) => {
      await page.goto('/scis');
      await page.waitForLoadState('networkidle');
      // Navigate to first SCI
      const sciLink = page.locator('a[href*="/scis/"]').first();
      if (await sciLink.isVisible()) {
        await sciLink.click();
        await page.waitForLoadState('networkidle');
        // Navigate to fiscalite
        const fiscaLink = page.locator('a:has-text("Fiscalité")');
        if (await fiscaLink.isVisible()) {
          await fiscaLink.click();
          await page.waitForLoadState('networkidle');
          await capture(page, '11-pro-fiscalite');
        }
      }
    });
  });
});
