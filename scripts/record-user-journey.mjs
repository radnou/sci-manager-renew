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
  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    recordVideo: { dir: 'test-results/', size: { width: 1440, height: 900 } },
    colorScheme: 'light',
    locale: 'fr-FR',
  });
  const page = await context.newPage();
  console.log('🎬 Recording started');

  // =============================================
  // SCENE 1: Landing page (5s)
  // =============================================
  console.log('📍 1. Landing page');
  await page.goto(BASE);
  await sleep(2000);

  // Dismiss cookies
  const cookies = page.getByRole('button', { name: 'Tout accepter' });
  if (await cookies.isVisible({ timeout: 2000 }).catch(() => false)) {
    await cookies.click();
    await sleep(SLOW);
  }

  // Scroll slowly through hero
  for (let i = 0; i < 3; i++) {
    await page.evaluate(() => window.scrollBy(0, 300));
    await sleep(800);
  }

  // Click "Voir comment ça marche"
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(500);
  await page.getByRole('button', { name: 'Voir comment ça marche' }).click();
  await sleep(2000);

  // =============================================
  // SCENE 2: Register (8s)
  // =============================================
  console.log('📍 2. Register');
  await page.goto(`${BASE}/register`);
  await sleep(1000);

  const ts = Date.now();
  const email = `journey-${ts}@gerersci.fr`;
  await page.getByRole('textbox', { name: 'Email' }).fill(email);
  await sleep(400);
  await page.getByRole('textbox', { name: 'Mot de passe', exact: true }).fill('Journey2026!');
  await sleep(400);
  await page.getByRole('textbox', { name: 'Confirmer le mot de passe' }).fill('Journey2026!');
  await sleep(400);
  await page.getByRole('checkbox', { name: "J'ai lu et j'accepte" }).setChecked(true);
  await sleep(SLOW);
  await page.getByRole('button', { name: "S'inscrire" }).click();
  console.log('📍 3. Welcome loading');

  // =============================================
  // SCENE 3: Welcome loading (10s)
  // =============================================
  await page.waitForURL('**/welcome', { timeout: 10000 }).catch(() => {});
  await sleep(9000); // Full animation

  // Wait for dashboard redirect
  await page.waitForURL('**/dashboard', { timeout: 10000 }).catch(() => {});
  await sleep(2000);

  // =============================================
  // SCENE 4: Dashboard demo (5s)
  // =============================================
  console.log('📍 4. Dashboard');

  // Dismiss modals
  const passer = page.getByRole('button', { name: 'Passer' });
  if (await passer.isVisible({ timeout: 2000 }).catch(() => false)) {
    await passer.click();
    await sleep(SLOW);
  }
  const cookies2 = page.getByRole('button', { name: 'Tout accepter' });
  if (await cookies2.isVisible({ timeout: 1000 }).catch(() => false)) {
    await cookies2.click();
    await sleep(SLOW);
  }

  // Read dashboard slowly
  await sleep(1500);
  await page.evaluate(() => window.scrollBy(0, 400));
  await sleep(1500);

  // =============================================
  // SCENE 5: Click SCI → Vue d'ensemble (4s)
  // =============================================
  console.log('📍 5. SCI detail');
  const sciLink = page.getByRole('link', { name: 'SCI Résidence Belleville' });
  if (await sciLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await sciLink.click();
    await sleep(2000);
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(1500);
  }

  // =============================================
  // SCENE 6: Biens grid (3s)
  // =============================================
  console.log('📍 6. Biens');
  const biensLink = page.getByRole('link', { name: 'Biens', exact: true });
  if (await biensLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await biensLink.click();
    await sleep(2000);
  }

  // =============================================
  // SCENE 7: Fiche bien — all tabs (15s)
  // =============================================
  console.log('📍 7. Fiche bien');
  const bienLink = page.getByRole('link', { name: 'avenue Jean Jaurès' });
  if (await bienLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await bienLink.click();
    await sleep(1500);

    // Identité tab (already shown)
    await sleep(1000);

    // Bail tab
    const bailTab = page.getByRole('tab', { name: 'Bail' });
    if (await bailTab.isVisible().catch(() => false)) {
      await bailTab.click();
      await sleep(1500);
    }

    // Loyers tab
    const loyersTab = page.getByRole('tab', { name: 'Loyers' });
    if (await loyersTab.isVisible().catch(() => false)) {
      await loyersTab.click();
      await sleep(1500);
    }

    // Charges tab
    const chargesTab = page.getByRole('tab', { name: 'Charges' });
    if (await chargesTab.isVisible().catch(() => false)) {
      await chargesTab.click();
      await sleep(1500);
    }

    // Assurance PNO tab
    const pnoTab = page.getByRole('tab', { name: 'Assurance PNO' });
    if (await pnoTab.isVisible().catch(() => false)) {
      await pnoTab.click();
      await sleep(1500);
    }

    // Rentabilité tab
    const rentaTab = page.getByRole('tab', { name: 'Rentabilité' });
    if (await rentaTab.isVisible().catch(() => false)) {
      await rentaTab.click();
      await sleep(1500);
    }

    // Documents tab
    const docsTab = page.getByRole('tab', { name: 'Documents' });
    if (await docsTab.isVisible().catch(() => false)) {
      await docsTab.click();
      await sleep(1500);
    }
  }

  // =============================================
  // SCENE 8: Associés (3s)
  // =============================================
  console.log('📍 8. Associés');
  const assocLink = page.getByRole('link', { name: 'Associés' });
  if (await assocLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await assocLink.click();
    await sleep(2000);
  }

  // =============================================
  // SCENE 9: Fiscalité (3s)
  // =============================================
  console.log('📍 9. Fiscalité');
  const fiscaLink = page.getByRole('link', { name: 'Fiscalité' });
  if (await fiscaLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await fiscaLink.click();
    await sleep(2000);
  }

  // =============================================
  // SCENE 10: Finances (3s)
  // =============================================
  console.log('📍 10. Finances');
  const finLink = page.getByRole('link', { name: 'Finances' });
  if (await finLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await finLink.click();
    await sleep(2000);
  }

  // =============================================
  // SCENE 11: Bilans (3s)
  // =============================================
  console.log('📍 11. Bilans');
  const bilansLink = page.getByRole('link', { name: 'Bilans' });
  if (await bilansLink.isVisible({ timeout: 2000 }).catch(() => false)) {
    await bilansLink.click();
    await sleep(2000);
  }

  // =============================================
  // SCENE 12: Settings (3s)
  // =============================================
  console.log('📍 12. Settings');
  await page.goto(`${BASE}/settings`);
  await sleep(2000);

  // =============================================
  // SCENE 13: Generateur quittance PUBLIC (8s)
  // =============================================
  console.log('📍 13. Generateur quittance');
  await page.goto(`${BASE}/generateur-quittance`);
  await sleep(1500);

  // Fill form
  const bailleur = page.getByRole('textbox', { name: 'Nom du bailleur' });
  if (await bailleur.isVisible().catch(() => false)) {
    await bailleur.fill('SCI Résidence Belleville');
    await sleep(300);
    await page.getByRole('textbox', { name: 'Adresse du bien' }).fill('45 avenue Jean Jaurès, 69007 Lyon');
    await sleep(300);
    await page.getByRole('textbox', { name: 'Nom du locataire' }).fill('Marie Lefèvre');
    await sleep(300);

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
  await sleep(2000);
  await page.evaluate(() => window.scrollBy(0, 300));
  await sleep(2000);

  // =============================================
  // SCENE 15: Pricing (3s)
  // =============================================
  console.log('📍 15. Pricing');
  await page.goto(`${BASE}/pricing`);
  await sleep(2000);
  await page.evaluate(() => window.scrollBy(0, 500));
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
