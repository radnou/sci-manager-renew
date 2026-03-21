import { test, expect } from '@playwright/test';
import { setupAuthedMocks } from '../fixtures/api-mocks';

const SCI_ID = 'aaa11111-1111-1111-1111-111111111111';
const BIEN_ID = 101;
const BIEN_ADRESSE = '12 rue de Belleville';

type MutableDocument = {
  id: number;
  id_bien: number;
  bien_adresse: string;
  nom: string;
  categorie: string;
  url: string;
  uploaded_at: string;
};

test.describe('Documents agreges @P1', () => {

  test.beforeEach(async ({ page }) => {
    await setupAuthedMocks(page);
  });

  async function goToDocuments(page: import('@playwright/test').Page): Promise<boolean> {
    await page.goto('/scis');
    await page.waitForLoadState('networkidle');

    const sciLink = page.locator('a[href*="/scis/"]').first();
    if (!(await sciLink.isVisible().catch(() => false))) return false;
    await sciLink.click();
    await page.waitForLoadState('networkidle');

    const docsLink = page.locator('a[href*="documents"]');
    if (!(await docsLink.first().isVisible().catch(() => false))) return false;
    await docsLink.first().click();
    await page.waitForLoadState('networkidle');
    return true;
  }

  async function installMutableDocumentRoutes(page: import('@playwright/test').Page) {
    let nextId = 7900;
    let docs: MutableDocument[] = [
      {
        id: 7001,
        id_bien: BIEN_ID,
        bien_adresse: BIEN_ADRESSE,
        nom: 'Bail signe 2022',
        categorie: 'bail',
        url: 'https://storage.example.com/bail.pdf',
        uploaded_at: '2022-04-01T10:00:00Z'
      },
      {
        id: 7002,
        id_bien: BIEN_ID,
        bien_adresse: BIEN_ADRESSE,
        nom: 'Etat des lieux entree',
        categorie: 'diagnostic',
        url: 'https://storage.example.com/edl.pdf',
        uploaded_at: '2022-04-01T14:00:00Z'
      }
    ];

    await page.route(`**/api/v1/scis/${SCI_ID}/documents*`, async route => {
      await route.fulfill({ json: docs });
    });

    await page.route(`**/api/v1/scis/${SCI_ID}/biens/${BIEN_ID}/documents`, async route => {
      if (route.request().method() !== 'POST') {
        await route.fulfill({
          json: docs
            .filter(doc => doc.id_bien === BIEN_ID)
            .map(({ bien_adresse, ...doc }) => doc)
        });
        return;
      }

      const body = route.request().postDataBuffer()?.toString('utf8') ?? '';
      const nom = body.match(/name="nom"\r\n\r\n([^\r\n]+)/)?.[1] ?? 'Document uploadé';
      const categorie = body.match(/name="categorie"\r\n\r\n([^\r\n]+)/)?.[1] ?? 'autre';
      const created = {
        id: nextId++,
        id_bien: BIEN_ID,
        bien_adresse: BIEN_ADRESSE,
        nom,
        categorie,
        url: `https://storage.example.com/${encodeURIComponent(nom)}.pdf`,
        uploaded_at: '2026-03-21T10:00:00Z'
      };
      docs = [created, ...docs];
      await route.fulfill({
        status: 201,
        json: {
          id: created.id,
          id_bien: created.id_bien,
          nom: created.nom,
          categorie: created.categorie,
          url: created.url,
          uploaded_at: created.uploaded_at
        }
      });
    });

    await page.route(`**/api/v1/scis/${SCI_ID}/biens/${BIEN_ID}/documents/*`, async route => {
      if (route.request().method() !== 'DELETE') {
        await route.fallback();
        return;
      }

      const url = new URL(route.request().url());
      const docId = Number(url.pathname.split('/').pop());
      docs = docs.filter(doc => doc.id !== docId);
      await route.fulfill({ status: 204, body: '' });
    });
  }

  test('la vue documents agreges charge @P1', async ({ page }) => {
    const navigated = await goToDocuments(page);
    if (!navigated) return;

    await expect(page.getByRole('heading', { name: 'Documents' })).toBeVisible();
    await expect(page.getByText(BIEN_ADRESSE)).toBeVisible();
    await expect(page.getByText('Bail signe 2022')).toBeVisible();
    await expect(page.getByText('Etat des lieux entree')).toBeVisible();
  });

  test('documents groupes par bien @P1', async ({ page }) => {
    const navigated = await goToDocuments(page);
    if (!navigated) return;

    await expect(page.getByText(BIEN_ADRESSE)).toBeVisible();
    await expect(page.getByText('Bail signe 2022')).toBeVisible();
    await expect(page.getByText('Etat des lieux entree')).toBeVisible();
    await expect(page.getByRole('link', { name: 'Ouvrir' }).first()).toBeVisible();
  });

  test('etat vide utile pour un gerant sans document @P1', async ({ page }) => {
    await page.route(`**/api/v1/scis/${SCI_ID}/documents*`, async route => {
      await route.fulfill({ json: [] });
    });

    const navigated = await goToDocuments(page);
    if (!navigated) return;

    await expect(page.getByText(BIEN_ADRESSE)).toBeVisible();
    await expect(page.getByText('Aucun document pour ce bien.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Ajouter' }).first()).toBeVisible();
  });

  test('upload et suppression mettent a jour la vue agregée @P1', async ({ page }) => {
    await installMutableDocumentRoutes(page);

    const navigated = await goToDocuments(page);
    if (!navigated) return;

    const uploadRequest = page.waitForRequest(request =>
      request.method() === 'POST' &&
      request.url().includes(`/api/v1/scis/${SCI_ID}/biens/${BIEN_ID}/documents`)
    );

    await page.getByRole('button', { name: 'Ajouter' }).first().click();
    await expect(page.getByRole('dialog', { name: 'Ajouter un document' })).toBeVisible();
    await page.locator('#upload-file').setInputFiles({
      name: 'attestation-locataire.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 attestation locataire')
    });
    await page.locator('#upload-nom').fill('Attestation locataire 2026');
    await page.locator('#upload-categorie').selectOption('assurance');
    await page.getByRole('button', { name: 'Uploader' }).click();

    await uploadRequest;
    await expect(page.getByText('Attestation locataire 2026')).toBeVisible();

    page.once('dialog', dialog => dialog.accept());
    const deleteRequest = page.waitForRequest(request =>
      request.method() === 'DELETE' && request.url().includes('/documents/')
    );

    const card = page.locator('div').filter({ hasText: 'Attestation locataire 2026' }).first();
    await card.getByRole('button').click();
    await deleteRequest;
    await expect(page.getByText('Attestation locataire 2026')).toHaveCount(0);
  });
});
