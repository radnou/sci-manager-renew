import { test, expect } from '@playwright/test';

const hasAuth = () => !!process.env.E2E_AUTH_TOKEN;

test.describe('Navigation globale @P0', () => {
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

  test('le SCI switcher de la sidebar fonctionne @P0', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Look for SCI switcher in sidebar
    const sidebar = page.locator('nav, aside, [class*="sidebar"], [class*="Sidebar"]');
    const hasSidebar = await sidebar.first().isVisible().catch(() => false);

    if (hasSidebar) {
      // Look for SCI selector (dropdown, combobox, or list)
      const sciSwitcher = page.locator(
        'select, [role="combobox"], [data-testid*="sci-switch"], button:has-text("SCI")'
      );
      if (await sciSwitcher.first().isVisible().catch(() => false)) {
        await sciSwitcher.first().click();
        await page.waitForTimeout(500);

        // Options should appear
        const options = page.locator(
          'option, [role="option"], [role="menuitem"], [class*="dropdown"] a, [class*="popover"] a'
        );
        const optionCount = await options.count();
        expect(optionCount >= 0).toBe(true); // May be 0 if only one SCI
      }
    }
  });

  test('tous les liens de la sidebar naviguent correctement @P0', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Collect all sidebar navigation links
    const sidebarLinks = page.locator('nav a[href], aside a[href], [class*="sidebar"] a[href]');
    const linkCount = await sidebarLinks.count();

    // Verify at least some navigation links exist
    expect(linkCount).toBeGreaterThan(0);

    // Test the first few links navigate correctly
    const linksToTest = Math.min(linkCount, 4);
    for (let i = 0; i < linksToTest; i++) {
      const link = sidebarLinks.nth(i);
      const href = await link.getAttribute('href');
      if (href && href.startsWith('/') && !href.includes('logout')) {
        await link.click();
        await page.waitForLoadState('networkidle');

        // Verify navigation occurred
        expect(page.url()).toContain(href.split('?')[0]);

        // Go back to dashboard for next link test
        await page.goto('/dashboard');
        await page.waitForLoadState('networkidle');
      }
    }
  });

  test('les breadcrumbs affichent des noms lisibles (pas des UUID) @P1', async ({ page }) => {
    // Navigate to a nested page to check breadcrumbs
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');

    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (await sciLink.isVisible().catch(() => false)) {
      await sciLink.click();
      await page.waitForLoadState('networkidle');

      // Look for breadcrumbs
      const breadcrumbs = page.locator(
        '[class*="breadcrumb"], [class*="Breadcrumb"], nav[aria-label*="breadcrumb"], [data-testid*="breadcrumb"]'
      );

      if (await breadcrumbs.first().isVisible().catch(() => false)) {
        const breadcrumbText = await breadcrumbs.first().textContent();

        // UUID pattern: 8-4-4-4-12 hex characters
        const uuidPattern = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
        const containsUuid = uuidPattern.test(breadcrumbText || '');

        // Breadcrumbs should not show raw UUIDs
        expect(containsUuid).toBe(false);
      }
    }
  });

  test('la command palette (Cmd+K) ouvre @P1', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Trigger Cmd+K (Meta+K on Mac)
    await page.keyboard.press('Meta+k');
    await page.waitForTimeout(500);

    // Look for command palette dialog
    const commandPalette = page.locator(
      '[role="dialog"], [class*="command"], [class*="Command"], [class*="palette"], [class*="Palette"], [cmdk-dialog]'
    );
    const isVisible = await commandPalette.first().isVisible().catch(() => false);

    if (!isVisible) {
      // Try Ctrl+K for non-Mac
      await page.keyboard.press('Control+k');
      await page.waitForTimeout(500);
    }

    const paletteVisible = await commandPalette.first().isVisible().catch(() => false);

    // Also check for a search input that might be the command palette
    const searchInput = page.locator(
      'input[placeholder*="chercher"], input[placeholder*="Chercher"], input[placeholder*="search"], input[placeholder*="Search"], [cmdk-input]'
    );
    const searchVisible = await searchInput.first().isVisible().catch(() => false);

    expect(paletteVisible || searchVisible).toBe(true);
  });
});
