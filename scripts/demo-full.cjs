'use strict';
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'https://gerersci.fr';
const VIDEO_DIR = path.join(__dirname, '..', 'test-results');
const OUTPUT_NAME = 'demo-gerersci-full.webm';

const DEMO_EMAIL = 'demo@gerersci.fr';
const DEMO_PASSWORD = 'DemoGererSCI2026!';

// ─── Helpers ──────────────────────────────────────────

async function injectCursor(page) {
  await page.evaluate(() => {
    if (document.getElementById('demo-cursor')) return;
    const c = document.createElement('div');
    c.id = 'demo-cursor';
    c.innerHTML = `<svg width="28" height="28" viewBox="0 0 24 24" fill="none"><path d="M5 3L19 12L12 13L9 20L5 3Z" fill="white" stroke="black" stroke-width="1.5" stroke-linejoin="round"/></svg>`;
    c.style.cssText = 'position:fixed;z-index:999999;pointer-events:none;width:28px;height:28px;transition:left 0.1s,top 0.1s;filter:drop-shadow(1px 1px 2px rgba(0,0,0,0.3));left:0;top:0;';
    document.body.appendChild(c);
    document.addEventListener('mousemove', e => { c.style.left = e.clientX+'px'; c.style.top = e.clientY+'px'; });
  });
}

async function injectSubtitle(page) {
  await page.evaluate(() => {
    if (document.getElementById('demo-sub')) return;
    const b = document.createElement('div');
    b.id = 'demo-sub';
    b.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:999998;text-align:center;padding:16px 32px;background:rgba(0,0,0,0.75);color:white;font-family:-apple-system,sans-serif;font-size:20px;font-weight:500;transition:opacity 0.3s;pointer-events:none;opacity:0;';
    document.body.appendChild(b);
  });
}

async function sub(page, text) {
  await page.evaluate(t => {
    const b = document.getElementById('demo-sub');
    if (!b) return;
    b.textContent = t || '';
    b.style.opacity = t ? '1' : '0';
  }, text);
  if (text) await page.waitForTimeout(600);
}

async function mc(page, loc, label, delay = 800) {
  const el = typeof loc === 'string' ? page.locator(loc).first() : loc;
  if (!await el.isVisible().catch(() => false)) { console.warn(`SKIP: ${label}`); return false; }
  try {
    await el.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    const box = await el.boundingBox();
    if (box) await page.mouse.move(box.x + box.width/2, box.y + box.height/2, { steps: 10 });
    await page.waitForTimeout(300);
    await el.click();
  } catch (e) { console.warn(`FAIL: ${label}: ${e.message}`); return false; }
  await page.waitForTimeout(delay);
  return true;
}

async function type(page, loc, text, label) {
  const el = typeof loc === 'string' ? page.locator(loc).first() : loc;
  if (!await el.isVisible().catch(() => false)) { console.warn(`SKIP type: ${label}`); return; }
  await mc(page, el, label, 200);
  await el.fill('');
  await el.pressSequentially(text, { delay: 25 });
  await page.waitForTimeout(400);
}

async function overlays(page) { await injectCursor(page); await injectSubtitle(page); }
async function wait(page) { await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {}); await page.waitForTimeout(1200); }
async function scroll(page, y) { await page.evaluate(v => window.scrollTo({ top: v, behavior: 'smooth' }), y); await page.waitForTimeout(1500); }

// ─── Main ─────────────────────────────────────────────

(async () => {
  fs.mkdirSync(VIDEO_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: false, slowMo: 30 });
  const context = await browser.newContext({
    recordVideo: { dir: VIDEO_DIR, size: { width: 1920, height: 1080 } },
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  try {
    // ── Pre-flight: clear tour for fresh onboarding ──
    await page.goto(`${BASE_URL}/login`);
    await page.evaluate(() => localStorage.removeItem('gerersci_tour_completed'));
    await wait(page);
    await overlays(page);

    // Cookie
    const cookie = page.locator('button:has-text("Tout accepter")');
    if (await cookie.isVisible().catch(() => false)) await cookie.click();
    await page.waitForTimeout(500);

    // ── 1. Login ──────────────────────────────────────
    await sub(page, '① Connexion');
    await type(page, 'input[type="email"]', DEMO_EMAIL, 'Email');
    await type(page, 'input[type="password"]', DEMO_PASSWORD, 'Password');
    await page.waitForTimeout(600);
    await mc(page, 'button[type="submit"]:has-text("Se connecter")', 'Login', 5000);

    const url = page.url();
    console.log(`After login: ${url}`);
    if (url.includes('welcome')) {
      await overlays(page);
      await sub(page, 'Chargement des données...');
      await page.waitForTimeout(6000);
    }
    await wait(page);
    await overlays(page);

    // ── 2. Onboarding tour ────────────────────────────
    const tourDialog = page.locator('[role="dialog"][aria-modal="true"]');
    if (await tourDialog.isVisible().catch(() => false)) {
      await sub(page, '② Visite guidée');
      await page.waitForTimeout(1200);
      for (let i = 0; i < 3; i++) {
        await mc(page, 'button:has-text("Suivant")', `Tour ${i+1}`, 1000);
      }
      await mc(page, 'button:has-text("Commencer")', 'Commencer', 1000);
    }

    // ── 3. Dashboard ──────────────────────────────────
    await sub(page, '③ Dashboard — alertes, KPIs, SCI');
    await page.waitForTimeout(2500);
    await scroll(page, 500);
    await page.waitForTimeout(1500);
    await scroll(page, 0);
    await sub(page, '');

    // ── 4. Mes SCI ────────────────────────────────────
    await sub(page, '④ Mes SCI');
    await page.goto(`${BASE_URL}/scis`);
    await wait(page); await overlays(page);
    await page.waitForTimeout(2000);

    // Click first SCI
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (await sciLink.isVisible().catch(() => false)) {
      await mc(page, sciLink, 'SCI detail', 2000);
      await wait(page); await overlays(page);
      await sub(page, '⑤ Vue SCI — biens, associés, fiscalité');
      await page.waitForTimeout(2000);
      await scroll(page, 400);
    }
    await sub(page, '');

    // ── 5. Biens ──────────────────────────────────────
    const sciIdMatch = page.url().match(/scis\/([^/]+)/);
    if (sciIdMatch) {
      await page.goto(`${BASE_URL}/scis/${sciIdMatch[1]}/biens`);
      await wait(page); await overlays(page);
      await sub(page, '⑥ Grille des biens');
      await page.waitForTimeout(2000);

      // Click first bien
      const bienLink = page.locator('a[href*="/biens/"]').first();
      if (await bienLink.isVisible().catch(() => false)) {
        await mc(page, bienLink, 'Fiche bien', 2000);
        await wait(page); await overlays(page);
        await sub(page, '⑦ Fiche bien — 10 onglets');
        await page.waitForTimeout(1500);

        // Click through a few tabs
        const tabs = page.locator('[role="tab"], button[class*="tab"]');
        const tabCount = await tabs.count();
        for (let i = 1; i < Math.min(tabCount, 5); i++) {
          const tab = tabs.nth(i);
          if (await tab.isVisible().catch(() => false)) {
            await mc(page, tab, `Tab ${i}`, 1200);
          }
        }
      }
    }
    await sub(page, '');

    // ── 5b. Associés ──────────────────────────────────
    if (sciIdMatch) {
      await page.goto(`${BASE_URL}/scis/${sciIdMatch[1]}/associes`);
      await wait(page); await overlays(page);
      await sub(page, '⑥ Associés — répartition des parts');
      await page.waitForTimeout(2000);
      await sub(page, '');
    }

    // ── 5c. Fiscalité ─────────────────────────────────
    if (sciIdMatch) {
      await page.goto(`${BASE_URL}/scis/${sciIdMatch[1]}/fiscalite`);
      await wait(page); await overlays(page);
      await sub(page, '⑦ Fiscalité — CERFA 2044, résumé fiscal');
      await page.waitForTimeout(2500);
      await sub(page, '');
    }

    // ── 5d. Assemblées Générales ──────────────────────
    if (sciIdMatch) {
      await page.goto(`${BASE_URL}/scis/${sciIdMatch[1]}/assemblees-generales`);
      await wait(page); await overlays(page);
      await sub(page, '⑧ Registre AG — PV, résolutions, convocations');
      await page.waitForTimeout(2000);
      await sub(page, '');
    }

    // ── 5e. Mouvements de parts ───────────────────────
    if (sciIdMatch) {
      await page.goto(`${BASE_URL}/scis/${sciIdMatch[1]}/mouvements-parts`);
      await wait(page); await overlays(page);
      await sub(page, '⑨ Cessions de parts — historique, simulation droits');
      await page.waitForTimeout(2000);
      await sub(page, '');
    }

    // ── 6. Finances ───────────────────────────────────
    await page.goto(`${BASE_URL}/finances`);
    await wait(page); await overlays(page);
    await sub(page, '⑩ Finances consolidées');
    await page.waitForTimeout(2000);
    await scroll(page, 300);
    await sub(page, '');

    // ── 7. Bilans ─────────────────────────────────────
    await page.goto(`${BASE_URL}/bilans`);
    await wait(page); await overlays(page);
    await sub(page, '⑪ Bilans mensuels');
    await page.waitForTimeout(2000);
    await sub(page, '');

    // ── 8. Échéances ──────────────────────────────────
    await page.goto(`${BASE_URL}/echeances`);
    await wait(page); await overlays(page);
    await sub(page, '⑫ Échéances — baux, PNO, fiscal');
    await page.waitForTimeout(2000);
    await sub(page, '');

    // ── 9. Pricing + Checkout ─────────────────────────
    await page.goto(`${BASE_URL}/pricing`);
    await wait(page); await overlays(page);
    await sub(page, '⑬ Souscrire — choisir un plan');
    await page.waitForTimeout(2000);

    // Click "Démarrer pour 39€/mois" (Pilotage)
    const ctaPilotage = page.locator('button:has-text("Démarrer pour 39€/mois")');
    if (await ctaPilotage.isVisible().catch(() => false)) {
      await mc(page, ctaPilotage, 'CTA Pilotage', 2000);

      // CheckoutConfirmModal should appear
      const confirmModal = page.locator('[role="dialog"]');
      if (await confirmModal.isVisible().catch(() => false)) {
        await sub(page, '⑭ Confirmation avant paiement (art. L221-28)');
        await page.waitForTimeout(3000);
        // Don't click confirm — would redirect to Stripe live
      }
    }
    await sub(page, '');

    // ── 10. Dark mode ─────────────────────────────────
    await page.goto(`${BASE_URL}/dashboard`);
    await wait(page); await overlays(page);
    const theme = page.locator('button:has-text("Basculer le thème")');
    if (await theme.isVisible().catch(() => false)) {
      await sub(page, '⑮ Mode sombre');
      await mc(page, theme, 'Dark toggle', 2000);
      await page.waitForTimeout(1500);
      await mc(page, theme, 'Light toggle', 1000);
    }

    // ── Final ─────────────────────────────────────────
    await sub(page, 'GérerSCI — Votre SCI mérite mieux qu\'un tableur Excel');
    await page.waitForTimeout(3000);
    await sub(page, '');
    await page.waitForTimeout(1000);

  } catch (err) {
    console.error('DEMO ERROR:', err.message);
  } finally {
    await context.close();
    const video = page.video();
    if (video) {
      const src = await video.path();
      const dest = path.join(VIDEO_DIR, OUTPUT_NAME);
      try { fs.copyFileSync(src, dest); console.log(`✅ ${dest}`); }
      catch (e) { console.error(`Copy error: ${e.message}`); }
    }
    await browser.close();
  }
})();
