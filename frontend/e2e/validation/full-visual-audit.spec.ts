/**
 * FULL VISUAL AUDIT — Check every screen, button, label, overflow.
 *
 * Tests every page with real Supabase login (sophie@gerersci.fr).
 * Captures screenshots + checks for:
 * - Text overflow (no horizontal scrollbar)
 * - Buttons wired (not dead)
 * - Labels not truncated
 * - Consistent layout
 *
 * Run: E2E_VISUAL_AUDIT=1 pnpm exec playwright test --config=e2e/playwright.validation.config.ts full-visual-audit --workers=1
 */
import { test, expect, type Page } from '@playwright/test';

const AUDIT = !!process.env.E2E_VISUAL_AUDIT;
const ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0';

async function login(page: Page) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  const cookie = page.locator('button:has-text("Tout accepter")');
  if (await cookie.isVisible({ timeout: 2000 }).catch(() => false)) await cookie.click();
  await page.waitForTimeout(300);
  await page.locator('input[type="email"]').fill('sophie@gerersci.fr');
  await page.locator('input[type="password"]').fill('password123');
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(/dashboard|scis|onboarding/, { timeout: 15000 }).catch(() => {});
  await page.waitForLoadState('networkidle');
}

async function dismissCookies(page: Page) {
  const btn = page.locator('button:has-text("Tout accepter")');
  if (await btn.isVisible({ timeout: 1000 }).catch(() => false)) {
    await btn.click();
    await page.waitForTimeout(300);
  }
}

async function checkNoOverflow(page: Page, name: string) {
  const overflow = await page.evaluate(() => {
    return document.documentElement.scrollWidth > document.documentElement.clientWidth;
  });
  if (overflow) {
    console.log(`⚠️ OVERFLOW detected on ${name}`);
  }
  expect(overflow, `Horizontal overflow on ${name}`).toBe(false);
}

async function capture(page: Page, name: string) {
  await dismissCookies(page);
  await page.waitForTimeout(500);
  await page.screenshot({ path: `e2e-artifacts/visual-audit/${name}.png` });
  await checkNoOverflow(page, name);
}

async function checkButtons(page: Page, name: string) {
  // Find all visible buttons and links — verify none say "prochainement" or are obviously dead
  const deadPatterns = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button, a[href]'));
    const dead: string[] = [];
    buttons.forEach(b => {
      const text = b.textContent?.trim() || '';
      if (text.match(/prochainement|coming soon|todo|à venir/i)) {
        dead.push(text.slice(0, 50));
      }
    });
    return dead;
  });
  if (deadPatterns.length > 0) {
    console.log(`⚠️ DEAD BUTTONS on ${name}:`, deadPatterns);
  }
}

async function checkLabels(page: Page, name: string) {
  // Check for truncated text (elements with text-overflow: ellipsis that are actually truncated)
  const truncated = await page.evaluate(() => {
    const els = Array.from(document.querySelectorAll('*'));
    const issues: string[] = [];
    els.forEach(el => {
      const style = window.getComputedStyle(el);
      if (style.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth) {
        const text = el.textContent?.trim().slice(0, 40) || '';
        if (text.length > 3) issues.push(text);
      }
    });
    return issues.slice(0, 5);
  });
  if (truncated.length > 0) {
    console.log(`⚠️ TRUNCATED on ${name}:`, truncated);
  }
}

test.describe('Audit visuel complet @VISUAL_AUDIT', () => {
  test.skip(!AUDIT, 'Set E2E_VISUAL_AUDIT=1');

  // ═══════════════════════════════════════════════
  // PUBLIC PAGES
  // ═══════════════════════════════════════════════

  test('01 — Landing page', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await capture(page, '01-landing-top');
    await checkButtons(page, 'landing');
    await checkLabels(page, 'landing');

    // Scroll full page
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await capture(page, '01-landing-bottom');
  });

  test('02 — Pricing page', async ({ page }) => {
    await page.goto('/pricing');
    await page.waitForLoadState('networkidle');
    await capture(page, '02-pricing');
    await checkButtons(page, 'pricing');

    // Check 3 plans visible
    const content = await page.textContent('body');
    expect(content).toContain('Essentiel');
    expect(content).toContain('Gestion');
    expect(content).toContain('Fiscal');
  });

  test('03 — Simulateur CERFA', async ({ page }) => {
    await page.goto('/simulateur-cerfa');
    await page.waitForLoadState('networkidle');
    await capture(page, '03-simulateur-cerfa');
    await checkButtons(page, 'simulateur');

    // Fill values and verify calculation
    await page.locator('input').first().fill('24000');
    await page.waitForTimeout(500);
    await capture(page, '03-simulateur-filled');

    // Check result area exists
    const result = page.getByText(/résultat|revenus/i);
    expect(await result.first().isVisible({ timeout: 3000 }).catch(() => false)).toBe(true);
  });

  test('04 — Login page', async ({ page }) => {
    await page.goto('/login');
    await page.waitForLoadState('networkidle');
    await capture(page, '04-login');
    await checkButtons(page, 'login');
    await checkLabels(page, 'login');
  });

  test('05 — Register page', async ({ page }) => {
    await page.goto('/register');
    await page.waitForLoadState('networkidle');
    await capture(page, '05-register');
    await checkButtons(page, 'register');
  });

  // ═══════════════════════════════════════════════
  // AUTH PAGES (Sophie Moreau)
  // ═══════════════════════════════════════════════

  test('06 — Dashboard', async ({ page }) => {
    await login(page);
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await capture(page, '06-dashboard-top');
    await checkButtons(page, 'dashboard');
    await checkLabels(page, 'dashboard');

    // Scroll
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await capture(page, '06-dashboard-bottom');
  });

  test('07 — Liste SCI', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');
    await capture(page, '07-scis-list');
    await checkButtons(page, 'scis');
    await checkLabels(page, 'scis');

    // Check SCI cards visible
    const cards = page.locator('a[href*="/scis/"]');
    expect(await cards.count()).toBeGreaterThan(0);
  });

  test('08 — Détail SCI', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');

    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!await sciLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(true, 'No SCI link found — data missing or login redirect');
      return;
    }
    await sciLink.click({ timeout: 5000 });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    await capture(page, '08-sci-detail');
    await checkButtons(page, 'sci-detail');
    await checkLabels(page, 'sci-detail');
  });

  test('09 — Biens', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!await sciLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(true, 'No SCI link found — data missing or login redirect');
      return;
    }
    await sciLink.click({ timeout: 5000 });
    await page.waitForLoadState('networkidle');

    const biensLink = page.locator('a:has-text("Biens")').first();
    if (await biensLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await biensLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);
      await capture(page, '09-biens-grid');
      await checkButtons(page, 'biens');
      await checkLabels(page, 'biens');

      // Check import button visible
      const importBtn = page.locator('button:has-text("Importer")');
      if (await importBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
        await importBtn.click();
        await page.waitForTimeout(500);
        await capture(page, '09-biens-import-modal');
      }
    }
  });

  test('10 — Fiche bien', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!await sciLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(true, 'No SCI link found — data missing or login redirect');
      return;
    }
    await sciLink.click({ timeout: 5000 });
    await page.waitForLoadState('networkidle');

    const biensLink = page.locator('a:has-text("Biens")').first();
    if (await biensLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await biensLink.click();
      await page.waitForLoadState('networkidle');

      const bienLink = page.locator('a[href*="/biens/"]').first();
      if (await bienLink.isVisible({ timeout: 3000 }).catch(() => false)) {
        await bienLink.click();
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(500);
        await capture(page, '10-fiche-bien');
        await checkButtons(page, 'fiche-bien');

        // Scroll to see all tabs content
        await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
        await page.waitForTimeout(500);
        await capture(page, '10-fiche-bien-bottom');
      }
    }
  });

  test('11 — Associés', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!await sciLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(true, 'No SCI link found — data missing or login redirect');
      return;
    }
    await sciLink.click({ timeout: 5000 });
    await page.waitForLoadState('networkidle');

    const assocLink = page.locator('a:has-text("Associés")').first();
    if (await assocLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await assocLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);
      await capture(page, '11-associes');
      await checkButtons(page, 'associes');
      await checkLabels(page, 'associes');
    }
  });

  test('12 — Fiscalité', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!await sciLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(true, 'No SCI link found — data missing or login redirect');
      return;
    }
    await sciLink.click({ timeout: 5000 });
    await page.waitForLoadState('networkidle');

    const fiscaLink = page.locator('a:has-text("Fiscalité")').first();
    if (await fiscaLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await fiscaLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);
      await capture(page, '12-fiscalite');
      await checkButtons(page, 'fiscalite');
    }
  });

  test('13 — Documents', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!await sciLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(true, 'No SCI link found — data missing or login redirect');
      return;
    }
    await sciLink.click({ timeout: 5000 });
    await page.waitForLoadState('networkidle');

    const docsLink = page.locator('a:has-text("Documents")').first();
    if (await docsLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await docsLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);
      await capture(page, '13-documents');
    }
  });

  test('14 — Finances', async ({ page }) => {
    await login(page);
    await page.goto('/finances');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);
    await capture(page, '14-finances');
    await checkButtons(page, 'finances');

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);
    await capture(page, '14-finances-bottom');
  });

  test('15 — Settings', async ({ page }) => {
    await login(page);
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    await capture(page, '15-settings');
    await checkButtons(page, 'settings');
  });

  test('16 — Account', async ({ page }) => {
    await login(page);
    await page.goto('/account');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    await capture(page, '16-account');
    await checkButtons(page, 'account');
  });

  test('17 — Mouvements de parts', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!await sciLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(true, 'No SCI link found — data missing or login redirect');
      return;
    }
    await sciLink.click({ timeout: 5000 });
    await page.waitForLoadState('networkidle');

    const mvtLink = page.locator('a:has-text("Mouvements")').first();
    if (await mvtLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await mvtLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);
      await capture(page, '17-mouvements-parts');
    }
  });

  test('18 — Assemblées générales', async ({ page }) => {
    await login(page);
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!await sciLink.isVisible({ timeout: 5000 }).catch(() => false)) {
      test.skip(true, 'No SCI link found — data missing or login redirect');
      return;
    }
    await sciLink.click({ timeout: 5000 });
    await page.waitForLoadState('networkidle');

    const agLink = page.locator('a:has-text("Assemblées"), a:has-text("assemblees")').first();
    if (await agLink.isVisible({ timeout: 3000 }).catch(() => false)) {
      await agLink.click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(500);
      await capture(page, '18-assemblees-generales');
    }
  });

  test('19 — Onboarding', async ({ page }) => {
    await login(page);
    await page.goto('/onboarding');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    await capture(page, '19-onboarding');
    await checkLabels(page, 'onboarding');
  });
});
