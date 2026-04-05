/**
 * Record full user journey: Register → Welcome → Dashboard → All screens → PDF Quittance
 * Run: node scripts/record-user-journey.mjs
 */
import { chromium } from '../frontend/node_modules/playwright/index.mjs';
import { mkdirSync } from 'fs';

const BASE = 'http://localhost:5173';
const SLOW = 600;

mkdirSync('test-results', { recursive: true });
const sleep = ms => new Promise(r => setTimeout(r, ms));

async function main() {
  const browser = await chromium.launch({
    headless: false,
    slowMo: 150,
    args: ['--enable-features=WebContentsForceDark:inversion_method/cielab_based', '--force-device-scale-factor=1'],
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: 'test-results/', size: { width: 1440, height: 900 } },
    colorScheme: 'light',
    locale: 'fr-FR',
  });
  const page = await context.newPage();
  console.log('🎬 Recording started');

  // Inject a visible cursor overlay on every navigation
  async function injectCursor() {
    await page.evaluate(() => {
      if (document.getElementById('fake-cursor')) return;
      const cursor = document.createElement('div');
      cursor.id = 'fake-cursor';
      cursor.style.cssText = 'position:fixed;width:20px;height:20px;border-radius:50%;background:rgba(59,130,246,0.5);border:2px solid #3b82f6;pointer-events:none;z-index:99999;transition:left 0.15s ease-out,top 0.15s ease-out;transform:translate(-50%,-50%);';
      document.body.appendChild(cursor);
      document.addEventListener('mousemove', e => {
        cursor.style.left = e.clientX + 'px';
        cursor.style.top = e.clientY + 'px';
      });
    }).catch(() => {});
  }

  // Helper: move mouse smoothly to element then click
  async function humanClick(locator) {
    const box = await locator.boundingBox();
    if (!box) return;
    const x = box.x + box.width / 2;
    const y = box.y + box.height / 2;
    await page.mouse.move(x, y, { steps: 15 });
    await sleep(200);
    await locator.click();
  }

  // Helper: smooth scroll
  async function smoothScroll(amount, stepCount = 8) {
    const step = amount / stepCount;
    for (let i = 0; i < stepCount; i++) {
      await page.evaluate((s) => window.scrollBy(0, s), step);
      await sleep(80);
    }
  }

  // =============================================
  // SCENE 1: Landing page
  // =============================================
  console.log('📍 1. Landing page');
  await page.goto(BASE);
  await sleep(1500);
  await injectCursor();

  // Dismiss cookies
  const cookies = page.getByRole('button', { name: 'Tout accepter' });
  if (await cookies.isVisible({ timeout: 2000 }).catch(() => false)) {
    await humanClick(cookies);
    await sleep(SLOW);
  }

  // Scroll slowly through hero → demo video
  await smoothScroll(900);
  await sleep(1500);

  // Click "Voir comment ça marche"
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(800);
  await humanClick(page.getByRole('button', { name: 'Voir comment ça marche' }));
  await sleep(2000);

  // =============================================
  // SCENE 2: Register (8s)
  // =============================================
  console.log('📍 2. Register');
  await page.goto(`${BASE}/register`);
  await sleep(1000);
  await injectCursor();

  const ts = Date.now();
  const email = `journey-${ts}@gerersci.fr`;
  await humanClick(page.getByRole('textbox', { name: 'Email' }));
  await page.getByRole('textbox', { name: 'Email' }).fill(email);
  await sleep(400);
  await humanClick(page.getByRole('textbox', { name: 'Mot de passe', exact: true }));
  await page.getByRole('textbox', { name: 'Mot de passe', exact: true }).fill('Journey2026!');
  await sleep(400);
  await humanClick(page.getByRole('textbox', { name: 'Confirmer le mot de passe' }));
  await page.getByRole('textbox', { name: 'Confirmer le mot de passe' }).fill('Journey2026!');
  await sleep(400);
  await humanClick(page.getByRole('checkbox', { name: "J'ai lu et j'accepte" }));
  await sleep(SLOW);
  await humanClick(page.getByRole('button', { name: "S'inscrire" }));
  console.log('📍 3. Welcome loading');

  // =============================================
  // SCENE 3: Welcome loading
  // =============================================
  await page.waitForURL('**/welcome', { timeout: 10000 }).catch(() => {});
  await injectCursor();
  await sleep(9000);

  await page.waitForURL('**/dashboard', { timeout: 10000 }).catch(() => {});
  await sleep(2000);
  await injectCursor();

  // =============================================
  // SCENE 4: Dashboard demo
  // =============================================
  console.log('📍 4. Dashboard');

  const passer = page.getByRole('button', { name: 'Passer' });
  if (await passer.isVisible({ timeout: 2000 }).catch(() => false)) {
    await humanClick(passer);
    await sleep(SLOW);
  }
  const cookies2 = page.getByRole('button', { name: 'Tout accepter' });
  if (await cookies2.isVisible({ timeout: 1000 }).catch(() => false)) {
    await humanClick(cookies2);
    await sleep(SLOW);
  }

  await sleep(1500);
  await smoothScroll(500);
  await sleep(1500);

  // =============================================
  // SCENE 5: SCI detail
  // =============================================
  console.log('📍 5. SCI detail');
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'smooth' }));
  await sleep(500);
  const sciLink = page.getByRole('link', { name: 'SCI Résidence Belleville' });
  if (await sciLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await humanClick(sciLink);
    await sleep(1500);
    await injectCursor();
    await smoothScroll(500);
    await sleep(1500);
  }

  // =============================================
  // SCENE 6: Biens
  // =============================================
  console.log('📍 6. Biens');
  const biensLink = page.getByRole('link', { name: 'Biens', exact: true });
  if (await biensLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await humanClick(biensLink);
    await sleep(1500);
    await injectCursor();
  }

  // =============================================
  // SCENE 7: Fiche bien — all tabs
  // =============================================
  console.log('📍 7. Fiche bien');
  const bienLink = page.getByRole('link', { name: 'avenue Jean Jaurès' });
  if (await bienLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await humanClick(bienLink);
    await sleep(1500);
    await injectCursor();

    for (const tabName of ['Bail', 'Loyers', 'Charges', 'Assurance PNO', 'Rentabilité', 'Documents']) {
      const tab = page.getByRole('tab', { name: tabName });
      if (await tab.isVisible().catch(() => false)) {
        await humanClick(tab);
        await sleep(1200);
      }
    }
  }

  // =============================================
  // SCENE 8-11: Associés, Fiscalité, Finances, Bilans
  // =============================================
  for (const [num, name] of [['8', 'Associés'], ['9', 'Fiscalité'], ['10', 'Finances'], ['11', 'Bilans']]) {
    console.log(`📍 ${num}. ${name}`);
    const link = page.getByRole('link', { name });
    if (await link.isVisible({ timeout: 2000 }).catch(() => false)) {
      await humanClick(link);
      await sleep(1500);
      await injectCursor();
    }
  }

  // =============================================
  // SCENE 12: Settings
  // =============================================
  console.log('📍 12. Settings');
  await page.goto(`${BASE}/settings`);
  await sleep(1500);
  await injectCursor();

  // =============================================
  // SCENE 13: Generateur quittance PUBLIC (8s)
  // =============================================
  console.log('📍 13. Generateur quittance');
  await page.goto(`${BASE}/generateur-quittance`);
  await sleep(1500);
  await injectCursor();

  // Fill form with human-like clicks
  const bailleur = page.getByRole('textbox', { name: 'Nom du bailleur' });
  if (await bailleur.isVisible().catch(() => false)) {
    await humanClick(bailleur);
    await bailleur.fill('SCI Résidence Belleville');
    await sleep(400);
    const adresse = page.getByRole('textbox', { name: 'Adresse du bien' });
    await humanClick(adresse);
    await adresse.fill('45 avenue Jean Jaurès, 69007 Lyon');
    await sleep(400);
    const locataire = page.getByRole('textbox', { name: 'Nom du locataire' });
    await humanClick(locataire);
    await locataire.fill('Marie Lefèvre');
    await sleep(400);

    const loyerField = page.getByRole('textbox', { name: 'Montant du loyer hors charges' });
    if (await loyerField.isVisible().catch(() => false)) {
      await loyerField.fill('800');
      await sleep(200);
    }

    const chargesField = page.getByRole('textbox', { name: 'Montant des charges' });
    if (await chargesField.isVisible().catch(() => false)) {
      await chargesField.fill('50');
      await sleep(200);
    }

    const totalField = page.getByRole('textbox', { name: 'Montant total payé' });
    if (await totalField.isVisible().catch(() => false)) {
      await totalField.fill('850');
      await sleep(200);
    }
  }
  await sleep(2000);

  // Scroll to see preview
  await page.evaluate(() => window.scrollBy(0, 300));
  await sleep(2000);

  // =============================================
  // SCENE 14: Simulateur CERFA (5s)
  // =============================================
  console.log('📍 14. Simulateur CERFA');
  await page.goto(`${BASE}/simulateur-cerfa`);
  await sleep(1500);
  await injectCursor();
  await smoothScroll(400);
  await sleep(2000);

  // =============================================
  // SCENE 15: Pricing (3s)
  // =============================================
  console.log('📍 15. Pricing');
  await page.goto(`${BASE}/pricing`);
  await sleep(1500);
  await injectCursor();
  await smoothScroll(600);
  await sleep(2000);

  // =============================================
  // END
  // =============================================
  console.log('📍 Fin — fermeture');
  await sleep(1000);
  await context.close();
  await browser.close();

  console.log('');
  console.log('✅ Enregistrement terminé !');
  console.log('📁 Vidéo dans test-results/*.webm');
  console.log('🎬 Convertir en mp4 : ffmpeg -i test-results/VIDEO.webm -c:v libx264 -crf 20 user-journey.mp4');
}

main().catch(e => { console.error('❌ Error:', e.message); process.exit(1); });
