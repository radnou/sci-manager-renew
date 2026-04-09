'use strict';
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE_URL = 'https://gerersci.fr';
const VIDEO_DIR = path.join(__dirname, '..', 'test-results');
const OUTPUT_NAME = 'demo-landing-gerersci.webm';

const DEMO_EMAIL = 'demo@gerersci.fr';
const DEMO_PASSWORD = 'DemoGererSCI2026!';
const REHEARSAL = process.argv.includes('--rehearse');

// ─── Helpers ──────────────────────────────────────────

async function injectCursor(page) {
  await page.evaluate(() => {
    if (document.getElementById('demo-cursor')) return;
    const c = document.createElement('div');
    c.id = 'demo-cursor';
    c.innerHTML = `<svg width="28" height="28" viewBox="0 0 24 24" fill="none"><path d="M5 3L19 12L12 13L9 20L5 3Z" fill="white" stroke="black" stroke-width="1.5" stroke-linejoin="round"/></svg>`;
    c.style.cssText = 'position:fixed;z-index:999999;pointer-events:none;width:28px;height:28px;transition:left 0.15s ease-out,top 0.15s ease-out;filter:drop-shadow(1px 2px 3px rgba(0,0,0,0.35));left:-50px;top:-50px;';
    document.body.appendChild(c);
    document.addEventListener('mousemove', e => { c.style.left = e.clientX+'px'; c.style.top = e.clientY+'px'; });
  });
}

async function injectSubtitle(page) {
  await page.evaluate(() => {
    if (document.getElementById('demo-sub')) return;
    const b = document.createElement('div');
    b.id = 'demo-sub';
    b.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:999998;text-align:center;padding:18px 32px;background:linear-gradient(180deg,rgba(0,0,0,0) 0%,rgba(0,0,0,0.8) 100%);color:white;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:20px;font-weight:500;letter-spacing:0.3px;transition:opacity 0.4s;pointer-events:none;opacity:0;text-shadow:0 1px 3px rgba(0,0,0,0.5);';
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
  if (text) await page.waitForTimeout(800);
}

async function mc(page, loc, label, delay = 800) {
  const el = typeof loc === 'string' ? page.locator(loc).first() : loc;
  const visible = await el.isVisible().catch(() => false);
  if (!visible) { console.warn(`SKIP: ${label}`); return false; }
  try {
    await el.scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    const box = await el.boundingBox();
    if (box) await page.mouse.move(box.x + box.width/2, box.y + box.height/2, { steps: 12 });
    await page.waitForTimeout(400);
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
  await el.pressSequentially(text, { delay: 30 });
  await page.waitForTimeout(500);
}

async function overlays(page) { await injectCursor(page); await injectSubtitle(page); }
async function wait(page) { await page.waitForLoadState('networkidle', { timeout: 8000 }).catch(() => {}); await page.waitForTimeout(1500); }
async function scroll(page, y) { await page.evaluate(v => window.scrollTo({ top: v, behavior: 'smooth' }), y); await page.waitForTimeout(1500); }

async function panElements(page, selector, maxCount = 6) {
  const elements = await page.locator(selector).all();
  for (let i = 0; i < Math.min(elements.length, maxCount); i++) {
    try {
      const box = await elements[i].boundingBox();
      if (box && box.y > 0 && box.y < 900) {
        await page.mouse.move(box.x + box.width/2, box.y + box.height/2, { steps: 8 });
        await page.waitForTimeout(500);
      }
    } catch (e) { /* skip */ }
  }
}

async function ensureVisible(page, locator, label) {
  const el = typeof locator === 'string' ? page.locator(locator).first() : locator;
  const visible = await el.isVisible().catch(() => false);
  if (!visible) {
    console.error(`REHEARSAL FAIL: "${label}" — selector: ${typeof locator === 'string' ? locator : '(locator)'}`);
    return false;
  }
  console.log(`REHEARSAL OK: "${label}"`);
  return true;
}

// ─── Rehearsal ─────────────────────────────────────────

async function rehearse() {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
  const page = await context.newPage();

  const steps = [];
  let allOk = true;

  // Landing
  await page.goto(`${BASE_URL}/`);
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});

  // Dismiss cookie first so it doesn't overlay other elements
  const cookieBtn = page.locator('button:has-text("Tout accepter")');
  if (await cookieBtn.isVisible().catch(() => false)) await cookieBtn.click();
  await page.waitForTimeout(500);

  // Scroll to hero CTAs (may be below cookie banner fold)
  await page.evaluate(() => window.scrollTo({ top: 300 }));
  await page.waitForTimeout(500);

  // Soft checks (non-blocking — elements may be below fold or inside animation)
  const softChecks = [
    { label: 'CTA Voir comment', selector: 'button:has-text("Voir comment")' },
    { label: 'CTA Comparer plans', selector: 'button:has-text("Comparer les plans")' },
  ];
  for (const step of softChecks) {
    await ensureVisible(page, step.selector, step.label); // warn but don't fail
  }

  // Login — hard checks
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  steps.push(
    { label: 'Email input', selector: 'input[type="email"]' },
    { label: 'Password input', selector: 'input[type="password"]' },
    { label: 'Login submit', selector: 'button[type="submit"]:has-text("Se connecter")' },
  );

  for (const step of steps) {
    if (!await ensureVisible(page, step.selector, step.label)) allOk = false;
  }

  await browser.close();
  if (!allOk) { console.error('\nREHEARSAL FAILED'); process.exit(1); }
  console.log('\nREHEARSAL PASSED — all selectors verified');
}

// ─── Main Recording ──────────────────────────────────

async function record() {
  fs.mkdirSync(VIDEO_DIR, { recursive: true });
  const browser = await chromium.launch({ headless: false, slowMo: 20 });
  const context = await browser.newContext({
    recordVideo: { dir: VIDEO_DIR, size: { width: 1920, height: 1080 } },
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  try {
    // ── Scene 1: Landing Page Hero ───────────────────
    await page.goto(BASE_URL);
    await wait(page);
    await overlays(page);

    // Dismiss cookie banner
    const cookie = page.locator('button:has-text("Tout accepter")');
    if (await cookie.isVisible().catch(() => false)) await cookie.click();
    await page.waitForTimeout(800);

    await sub(page, 'GérerSCI — Gestion simplifiée de vos SCI');
    await page.waitForTimeout(3000);
    await sub(page, '');

    // ── Scene 2: Scroll landing — steps + features ───
    await sub(page, 'Créez, gérez, pilotez — en 3 étapes');
    await scroll(page, 600);
    await page.waitForTimeout(2000);

    // Click step ①
    const step1 = page.locator('button:has-text("① Créez votre SCI")');
    if (await step1.isVisible().catch(() => false)) {
      await mc(page, step1, 'Step 1', 1200);
    }
    await page.waitForTimeout(1000);

    // Click step ③
    const step3 = page.locator('button:has-text("③ Pilotez chaque mois")');
    if (await step3.isVisible().catch(() => false)) {
      await mc(page, step3, 'Step 3', 1200);
    }
    await sub(page, '');

    // ── Scene 3: Pricing section (embedded in landing) ──
    await scroll(page, 2000);
    await page.waitForTimeout(1000);
    await sub(page, 'Des plans simples, à partir de 19€/mois');
    await page.waitForTimeout(2500);

    // Hover over plans
    await panElements(page, 'button:has-text("Démarrer pour")');
    await sub(page, '');

    // ── Scene 4: Login ────────────────────────────────
    await page.goto(`${BASE_URL}/login`);
    await wait(page); await overlays(page);

    // Dismiss cookie again if needed
    const cookie2 = page.locator('button:has-text("Tout accepter")');
    if (await cookie2.isVisible().catch(() => false)) await cookie2.click();
    await page.waitForTimeout(400);

    await sub(page, 'Connexion au compte de démonstration');

    // Use Playwright native fill (triggers input events for Svelte bindings)
    const emailInput = page.locator('input[type="email"]').first();
    const passwordInput = page.locator('input[type="password"]').first();
    if (await emailInput.isVisible().catch(() => false)) {
      await emailInput.click();
      await emailInput.fill(DEMO_EMAIL);
      await page.waitForTimeout(300);
    }
    if (await passwordInput.isVisible().catch(() => false)) {
      await passwordInput.click();
      await passwordInput.fill(DEMO_PASSWORD);
      await page.waitForTimeout(300);
    }
    await page.waitForTimeout(800);

    // Click submit and wait for navigation
    const loginBtn = page.locator('button[type="submit"]:has-text("Se connecter")').first();
    const btnEnabled = await loginBtn.isEnabled().catch(() => false);
    console.log(`Login button enabled: ${btnEnabled}`);
    if (btnEnabled) {
      await loginBtn.click();
      // Wait for SPA navigation away from /login
      await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 15000 }).catch(() => {});
    } else {
      console.warn('Login button disabled — fields may not have triggered validation');
    }
    await page.waitForTimeout(2000);

    // Handle welcome page if triggered
    const url = page.url();
    console.log(`After login: ${url}`);
    if (url.includes('welcome')) {
      await overlays(page);
      await sub(page, 'Chargement des données de démonstration...');
      await page.waitForTimeout(6000);
    }
    await wait(page);
    await overlays(page);

    // ── Scene 5: Onboarding tour (skip if shown) ─────
    const tourDialog = page.locator('[role="dialog"][aria-modal="true"]');
    if (await tourDialog.isVisible().catch(() => false)) {
      await sub(page, 'Visite guidée rapide');
      await page.waitForTimeout(1000);
      for (let i = 0; i < 3; i++) {
        const next = page.locator('button:has-text("Suivant")');
        if (await next.isVisible().catch(() => false)) await mc(page, next, `Tour ${i+1}`, 800);
      }
      const start = page.locator('button:has-text("Commencer")');
      if (await start.isVisible().catch(() => false)) await mc(page, start, 'Start', 1000);
    }
    await sub(page, '');

    // ── Scene 6: Dashboard — KPIs + alertes ──────────
    await sub(page, 'Dashboard — Vue consolidée de votre patrimoine');
    await page.waitForTimeout(2000);

    // Pan KPI cards
    await panElements(page, '[data-testid="dashboard-kpis"] > div', 4);
    await page.waitForTimeout(1000);

    // Scroll to SCI cards
    await scroll(page, 600);
    await sub(page, 'Vos SCI en un coup d\'œil');
    await page.waitForTimeout(2000);
    await scroll(page, 0);
    await sub(page, '');

    // ── Scene 7: SCI Detail ──────────────────────────
    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (await sciLink.isVisible().catch(() => false)) {
      await mc(page, sciLink, 'SCI detail', 2000);
      await wait(page); await overlays(page);
      await sub(page, 'Fiche SCI — associés, biens, fiscalité');
      await page.waitForTimeout(2000);
      await scroll(page, 400);
      await page.waitForTimeout(1500);
      await scroll(page, 0);
    }
    await sub(page, '');

    // ── Scene 8: Fiche bien + onglets ────────────────
    const sciIdMatch = page.url().match(/scis\/([^/]+)/);
    if (sciIdMatch) {
      await page.goto(`${BASE_URL}/scis/${sciIdMatch[1]}/biens`);
      await wait(page); await overlays(page);
      await sub(page, 'Grille des biens immobiliers');
      await page.waitForTimeout(1500);

      const bienLink = page.locator('a[href*="/biens/"]').first();
      if (await bienLink.isVisible().catch(() => false)) {
        await mc(page, bienLink, 'Fiche bien', 2000);
        await wait(page); await overlays(page);
        await sub(page, 'Fiche bien — 10 onglets métier');
        await page.waitForTimeout(1500);

        // Click through tabs: Bail, Loyers, Charges, Crédit
        const tabLabels = ['Bail', 'Loyers', 'Charges', 'Crédit'];
        for (const label of tabLabels) {
          const tab = page.locator(`[role="tab"]:has-text("${label}")`).first();
          if (await tab.isVisible().catch(() => false)) {
            await mc(page, tab, `Tab ${label}`, 1200);
          }
        }
        await sub(page, '');
      }
    }

    // ── Scene 9: Finances ────────────────────────────
    await page.goto(`${BASE_URL}/finances`);
    await wait(page); await overlays(page);
    await sub(page, 'Finances — revenus, charges, cashflow');
    await page.waitForTimeout(2000);
    await scroll(page, 300);
    await page.waitForTimeout(1000);
    await sub(page, '');

    // ── Scene 10: Pricing + Stripe Checkout ──────────
    await page.goto(`${BASE_URL}/pricing`);
    await wait(page); await overlays(page);

    // Dismiss cookie if it reappears
    const cookie3 = page.locator('button:has-text("Tout accepter")');
    if (await cookie3.isVisible().catch(() => false)) await cookie3.click();
    await page.waitForTimeout(500);

    await sub(page, 'Choisir un plan — souscription sécurisée');
    await page.waitForTimeout(2000);

    // Click Pilotage (popular)
    const ctaPilotage = page.locator('button:has-text("Démarrer pour 39€/mois")');
    console.log(`Pilotage CTA visible: ${await ctaPilotage.isVisible().catch(() => false)}`);
    if (await ctaPilotage.isVisible().catch(() => false)) {
      await mc(page, ctaPilotage, 'CTA Pilotage', 2000);

      // CheckoutConfirmModal
      const confirmModal = page.locator('[role="dialog"]');
      console.log(`Modal visible: ${await confirmModal.isVisible().catch(() => false)}`);
      if (await confirmModal.isVisible().catch(() => false)) {
        await sub(page, 'Récapitulatif + consentement avant paiement');
        await page.waitForTimeout(2500);

        // Check the L221-28 consent checkbox (click the label wrapper, not the input)
        const consentLabel = confirmModal.locator('label, [class*="cursor-pointer"]').first();
        if (await consentLabel.isVisible().catch(() => false)) {
          await mc(page, consentLabel, 'Consent checkbox', 800);
        } else {
          // Fallback: click the checkbox input directly
          const checkbox = confirmModal.locator('input[type="checkbox"]').first();
          if (await checkbox.isVisible().catch(() => false)) {
            await checkbox.click();
            await page.waitForTimeout(500);
          }
        }

        await sub(page, 'Consentement accepté — confirmation du paiement');
        await page.waitForTimeout(1500);

        // Click confirm button (now enabled)
        const confirmBtn = confirmModal.locator('button:has-text("Confirmer")').first();
        const confirmVisible = await confirmBtn.isVisible().catch(() => false);
        const confirmEnabled = await confirmBtn.isEnabled().catch(() => false);
        console.log(`Confirm btn visible: ${confirmVisible}, enabled: ${confirmEnabled}`);
        if (confirmVisible && confirmEnabled) {
          await mc(page, confirmBtn, 'Confirm checkout', 3000);
          console.log(`After confirm, URL: ${page.url()}`);
        }
      }

      // ── Scene 11: Stripe Checkout ──────────────────
      // Wait for redirect to checkout.stripe.com
      try {
        await page.waitForURL('**/checkout.stripe.com/**', { timeout: 10000 });
        await wait(page); await overlays(page);
        await sub(page, 'Paiement sécurisé par Stripe');
        await page.waitForTimeout(2000);

        // Fill Stripe test card
        const emailField = page.locator('input[name="email"], input[id="email"]').first();
        if (await emailField.isVisible().catch(() => false)) {
          await type(page, emailField, DEMO_EMAIL, 'Stripe email');
        }

        // Card number — Stripe uses iframes
        const cardFrame = page.frameLocator('iframe[name*="__privateStripeFrame"]').first();
        const cardNumber = cardFrame.locator('input[name="cardnumber"], input[placeholder*="1234"]').first();
        if (await cardNumber.isVisible({ timeout: 5000 }).catch(() => false)) {
          await cardNumber.fill('4242424242424242');
          await page.waitForTimeout(300);

          const expiry = cardFrame.locator('input[name="exp-date"], input[placeholder*="MM"]').first();
          if (await expiry.isVisible().catch(() => false)) await expiry.fill('1230');

          const cvc = cardFrame.locator('input[name="cvc"], input[placeholder*="CVC"]').first();
          if (await cvc.isVisible().catch(() => false)) await cvc.fill('424');
        }

        // Stripe sometimes uses a single card input
        const singleCard = page.locator('input[id="cardNumber"]').first();
        if (await singleCard.isVisible().catch(() => false)) {
          await type(page, singleCard, '4242 4242 4242 4242', 'Card number');
          const singleExpiry = page.locator('input[id="cardExpiry"]').first();
          if (await singleExpiry.isVisible().catch(() => false)) await type(page, singleExpiry, '12 / 30', 'Expiry');
          const singleCvc = page.locator('input[id="cardCvc"]').first();
          if (await singleCvc.isVisible().catch(() => false)) await type(page, singleCvc, '424', 'CVC');
        }

        // Cardholder name if present
        const nameField = page.locator('input[name="billingName"], input[id="billingName"]').first();
        if (await nameField.isVisible().catch(() => false)) {
          await type(page, nameField, 'Demo GérerSCI', 'Name');
        }

        await page.waitForTimeout(1500);
        await sub(page, 'Paiement test avec carte 4242');
        await page.waitForTimeout(2000);

        // Submit payment
        const payBtn = page.locator('button[type="submit"]:has-text("Payer"), button:has-text("S\'abonner"), button:has-text("Subscribe")').first();
        if (await payBtn.isVisible().catch(() => false)) {
          await mc(page, payBtn, 'Pay', 8000);
        }

        // ── Scene 12: Post-purchase redirect ─────────
        await page.waitForURL(`${BASE_URL}/**`, { timeout: 30000 }).catch(() => {});
        await wait(page); await overlays(page);
        await sub(page, 'Paiement réussi !');
        await page.waitForTimeout(2000);

        // Take screenshot of celebration card (upgraded=true)
        await sub(page, 'Données demo nettoyées — place à vos vraies SCI');
        await page.waitForTimeout(3000);

        // ── Scene 13: Navigate to onboarding ─────────
        // Click "Commencer la mise en route" if visible, or navigate directly
        const onboardingCta = page.locator('a:has-text("Commencer la mise en route")').first();
        if (await onboardingCta.isVisible().catch(() => false)) {
          await mc(page, onboardingCta, 'Start onboarding', 2000);
        } else {
          await page.goto(`${BASE_URL}/onboarding`);
        }
        await wait(page); await overlays(page);

        await sub(page, 'Créez votre première SCI avec vos vraies données');
        await page.waitForTimeout(3000);

        // Show the onboarding wizard steps
        await scroll(page, 300);
        await page.waitForTimeout(2000);
        await sub(page, '');

      } catch (stripeErr) {
        console.warn('Stripe checkout not reached (test keys needed):', stripeErr.message);
        await sub(page, '(Pré-requis : clés Stripe test sur le VPS)');
        await page.waitForTimeout(2000);
      }
    }
    await sub(page, '');

    // ── Scene 13: Dark mode showcase ─────────────────
    await page.goto(`${BASE_URL}/dashboard`);
    await wait(page); await overlays(page);
    const theme = page.locator('button:has-text("Basculer le thème")');
    if (await theme.isVisible().catch(() => false)) {
      await sub(page, 'Mode sombre disponible');
      await mc(page, theme, 'Dark toggle', 2000);
      await page.waitForTimeout(2000);
      await mc(page, theme, 'Light toggle', 1000);
    }
    await sub(page, '');

    // ── Final ─────────────────────────────────────────
    await sub(page, 'GérerSCI — Votre SCI mérite mieux qu\'un tableur Excel');
    await page.waitForTimeout(4000);
    await sub(page, '');
    await page.waitForTimeout(1500);

  } catch (err) {
    console.error('DEMO ERROR:', err.message);
  } finally {
    await context.close();
    const video = page.video();
    if (video) {
      const src = await video.path();
      const dest = path.join(VIDEO_DIR, OUTPUT_NAME);
      try { fs.copyFileSync(src, dest); console.log(`✅ Video saved: ${dest}`); }
      catch (e) { console.error(`Copy error: ${e.message}`); }
    }
    await browser.close();
  }
}

// ─── Entry Point ─────────────────────────────────────

(async () => {
  if (REHEARSAL) {
    await rehearse();
  } else {
    await record();
  }
})();
