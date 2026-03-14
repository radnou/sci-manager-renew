import { type Page } from '@playwright/test';

// ============================================================
// Mock Data — "Famille Moreau" realistic French SCI data
// ============================================================

const MOCK_USER = {
  id: '724ab7bc-7d07-4bec-9660-c19736fea220',
  email: 'demo@gerersci.fr',
  aud: 'authenticated',
  role: 'authenticated',
  created_at: '2025-09-15T10:30:00Z',
  last_sign_in_at: '2026-03-13T08:00:00Z'
};

const SCI_ID_1 = 'aaa11111-1111-1111-1111-111111111111';
const SCI_ID_2 = 'bbb22222-2222-2222-2222-222222222222';
const BIEN_ID_1 = 101;
const BIEN_ID_2 = 102;
const BIEN_ID_3 = 201;

// --- SCIs ---

const SCI_1_OVERVIEW = {
  id: SCI_ID_1,
  nom: 'SCI Residence Belleville',
  siren: '823456789',
  regime_fiscal: 'IR',
  statut: 'exploitation',
  adresse_siege: '12 rue de Belleville, 75020 Paris',
  date_creation: '2022-01-15',
  capital_social: 150000,
  objet_social: 'Acquisition et gestion de biens immobiliers',
  rcs_ville: 'Paris',
  nb_parts_total: 1000,
  valeur_nominale_part: 150,
  associes_count: 2,
  biens_count: 2,
  loyers_count: 12,
  user_role: 'gerant',
  user_part: 600
};

const SCI_2_OVERVIEW = {
  id: SCI_ID_2,
  nom: 'SCI Patrimoine Lyon',
  siren: '912345678',
  regime_fiscal: 'IS',
  statut: 'exploitation',
  adresse_siege: '45 avenue Jean Jaures, 69007 Lyon',
  date_creation: '2023-06-01',
  capital_social: 200000,
  objet_social: 'Gestion patrimoniale immobiliere',
  rcs_ville: 'Lyon',
  nb_parts_total: 500,
  valeur_nominale_part: 400,
  associes_count: 2,
  biens_count: 1,
  loyers_count: 6,
  user_role: 'gerant',
  user_part: 300
};

// --- Biens ---

const BIEN_1 = {
  id: BIEN_ID_1,
  id_sci: SCI_ID_1,
  adresse: '12 rue de Belleville',
  ville: 'Paris',
  code_postal: '75020',
  type_locatif: 'nu',
  loyer_cc: 950,
  charges: 150,
  tmi: 30,
  surface_m2: 45,
  nb_pieces: 2,
  dpe_classe: 'C',
  photo_url: null,
  prix_acquisition: 280000,
  statut: 'loue',
  acquisition_date: '2022-03-15',
  rentabilite_brute: 4.07,
  rentabilite_nette: 3.2,
  cashflow_annuel: 2400
};

const BIEN_2 = {
  id: BIEN_ID_2,
  id_sci: SCI_ID_1,
  adresse: '8 rue des Lilas',
  ville: 'Paris',
  code_postal: '75019',
  type_locatif: 'meuble',
  loyer_cc: 1200,
  charges: 200,
  tmi: 30,
  surface_m2: 55,
  nb_pieces: 3,
  dpe_classe: 'B',
  photo_url: null,
  prix_acquisition: 350000,
  statut: 'loue',
  acquisition_date: '2023-01-10',
  rentabilite_brute: 4.11,
  rentabilite_nette: 3.5,
  cashflow_annuel: 3600
};

const BIEN_3 = {
  id: BIEN_ID_3,
  id_sci: SCI_ID_2,
  adresse: '22 rue de la Republique',
  ville: 'Lyon',
  code_postal: '69002',
  type_locatif: 'nu',
  loyer_cc: 800,
  charges: 120,
  tmi: 30,
  surface_m2: 40,
  nb_pieces: 2,
  dpe_classe: 'D',
  photo_url: null,
  prix_acquisition: 220000,
  statut: 'loue',
  acquisition_date: '2023-09-01',
  rentabilite_brute: 4.36,
  rentabilite_nette: 3.1,
  cashflow_annuel: 1800
};

// --- Fiche Bien (full detail) ---

const FICHE_BIEN_1 = {
  ...BIEN_1,
  bail_actif: {
    id: 1001,
    date_debut: '2022-04-01',
    date_fin: '2025-03-31',
    loyer_hc: 800,
    charges_locatives: 150,
    depot_garantie: 800,
    revision_indice: 'IRL',
    statut: 'actif',
    locataires: [
      { id: 5001, nom: 'Dupont', prenom: 'Marie', email: 'marie.dupont@email.fr', telephone: '06 12 34 56 78' }
    ]
  },
  loyers_recents: [
    { id: 2001, date_loyer: '2026-03-01', montant: 950, statut: 'en_attente', quitus_genere: false, date_paiement: null },
    { id: 2002, date_loyer: '2026-02-01', montant: 950, statut: 'paye', quitus_genere: true, date_paiement: '2026-02-05' },
    { id: 2003, date_loyer: '2026-01-01', montant: 950, statut: 'paye', quitus_genere: true, date_paiement: '2026-01-03' },
    { id: 2004, date_loyer: '2025-12-01', montant: 950, statut: 'paye', quitus_genere: false, date_paiement: '2025-12-04' },
    { id: 2005, date_loyer: '2025-11-01', montant: 950, statut: 'en_retard', quitus_genere: false, date_paiement: null }
  ],
  charges_list: [
    { id: 3001, type_charge: 'copropriete', montant: 180, date_paiement: '2026-01-15' },
    { id: 3002, type_charge: 'taxe_fonciere', montant: 1200, date_paiement: '2025-10-15' }
  ],
  assurance_pno: {
    id: 4001,
    assureur: 'MAIF',
    numero_contrat: 'PNO-2022-4567',
    prime_annuelle: 320,
    date_debut: '2022-04-01',
    date_fin: '2026-03-31'
  },
  frais_agence: [
    { id: 6001, type_frais: 'gestion_locative', montant: 85, date_frais: '2026-02-28', description: 'Frais de gestion mensuel' }
  ],
  documents: [
    { id: 7001, nom: 'Bail signe 2022', categorie: 'bail', url: 'https://storage.example.com/bail.pdf', created_at: '2022-04-01T10:00:00Z' },
    { id: 7002, nom: 'Etat des lieux entree', categorie: 'etat_des_lieux', url: 'https://storage.example.com/edl.pdf', created_at: '2022-04-01T14:00:00Z' }
  ],
  rentabilite: {
    brute: 4.07,
    nette: 3.2,
    cashflow_mensuel: 200,
    cashflow_annuel: 2400
  }
};

const FICHE_BIEN_2 = {
  ...BIEN_2,
  bail_actif: {
    id: 1002,
    date_debut: '2023-02-01',
    date_fin: '2024-01-31',
    loyer_hc: 1000,
    charges_locatives: 200,
    depot_garantie: 2000,
    revision_indice: 'IRL',
    statut: 'actif',
    locataires: [
      { id: 5002, nom: 'Martin', prenom: 'Lucas', email: 'lucas.martin@email.fr', telephone: '06 98 76 54 32' }
    ]
  },
  loyers_recents: [
    { id: 2010, date_loyer: '2026-03-01', montant: 1200, statut: 'en_attente', quitus_genere: false, date_paiement: null },
    { id: 2011, date_loyer: '2026-02-01', montant: 1200, statut: 'paye', quitus_genere: false, date_paiement: '2026-02-03' }
  ],
  charges_list: [
    { id: 3010, type_charge: 'copropriete', montant: 220, date_paiement: '2026-01-15' }
  ],
  assurance_pno: null,
  frais_agence: [],
  documents: [],
  rentabilite: {
    brute: 4.11,
    nette: 3.5,
    cashflow_mensuel: 300,
    cashflow_annuel: 3600
  }
};

// --- SCI Detail (for /scis/:id) ---

const SCI_1_DETAIL = {
  ...SCI_1_OVERVIEW,
  charges_count: 3,
  total_monthly_rent: 2150,
  total_monthly_property_charges: 400,
  total_recorded_charges: 1600,
  paid_loyers_total: 2850,
  pending_loyers_total: 2150,
  biens: [BIEN_1, BIEN_2],
  recent_loyers: FICHE_BIEN_1.loyers_recents.slice(0, 3),
  recent_charges: FICHE_BIEN_1.charges_list,
  fiscalite: [
    { id: 8001, id_sci: SCI_ID_1, annee: 2025, total_revenus: 25800, total_charges: 8400, resultat_fiscal: 17400, regime_fiscal: 'IR' },
    { id: 8002, id_sci: SCI_ID_1, annee: 2024, total_revenus: 22800, total_charges: 7200, resultat_fiscal: 15600, regime_fiscal: 'IR' }
  ]
};

const SCI_2_DETAIL = {
  ...SCI_2_OVERVIEW,
  charges_count: 1,
  total_monthly_rent: 800,
  total_monthly_property_charges: 120,
  total_recorded_charges: 800,
  paid_loyers_total: 4800,
  pending_loyers_total: 800,
  biens: [BIEN_3],
  recent_loyers: [
    { id: 2020, date_loyer: '2026-03-01', montant: 800, statut: 'en_attente', quitus_genere: false }
  ],
  recent_charges: [
    { id: 3020, type_charge: 'taxe_fonciere', montant: 800, date_paiement: '2025-10-15' }
  ],
  fiscalite: [
    { id: 8010, id_sci: SCI_ID_2, annee: 2025, total_revenus: 9600, total_charges: 3200, resultat_fiscal: 6400, regime_fiscal: 'IS' }
  ]
};

// --- Associes ---

const ASSOCIES_SCI_1 = [
  { id: 9001, nom: 'Moreau', email: 'demo@gerersci.fr', role: 'gerant', part: 600, nb_parts: 600, id_sci: SCI_ID_1, user_id: MOCK_USER.id },
  { id: 9002, nom: 'Moreau-Dubois', email: 'sophie.moreau@email.fr', role: 'associe', part: 400, nb_parts: 400, id_sci: SCI_ID_1, user_id: null }
];

const ASSOCIES_SCI_2 = [
  { id: 9010, nom: 'Moreau', email: 'demo@gerersci.fr', role: 'gerant', part: 300, nb_parts: 300, id_sci: SCI_ID_2, user_id: MOCK_USER.id },
  { id: 9011, nom: 'Bernard', email: 'jean.bernard@email.fr', role: 'associe', part: 200, nb_parts: 200, id_sci: SCI_ID_2, user_id: null }
];

// --- Dashboard ---

const MOCK_DASHBOARD = {
  kpis: {
    sci_count: 2,
    biens_count: 3,
    taux_recouvrement: 78.5,
    cashflow_net: 6000,
    loyers_total: 29400,
    loyers_payes: 23100,
    charges_total: 10400
  },
  alertes: [
    {
      type: 'loyer_impaye',
      message: 'Loyer impaye depuis 4 mois : 12 rue de Belleville',
      severity: 'high',
      entity_id: String(BIEN_ID_1),
      entity_type: 'bien',
      id_sci: SCI_ID_1,
      montant: 950,
      date: '2025-11-01',
      sci_nom: 'SCI Residence Belleville',
      bien_adresse: '12 rue de Belleville',
      link: `/scis/${SCI_ID_1}/biens/${BIEN_ID_1}`
    },
    {
      type: 'bail_expirant',
      message: 'Bail expire dans 17 jours : 12 rue de Belleville',
      severity: 'medium',
      entity_id: String(BIEN_ID_1),
      entity_type: 'bail',
      id_sci: SCI_ID_1,
      sci_nom: 'SCI Residence Belleville',
      bien_adresse: '12 rue de Belleville',
      link: `/scis/${SCI_ID_1}/biens/${BIEN_ID_1}`
    }
  ],
  scis: [
    { id: SCI_ID_1, nom: 'SCI Residence Belleville', statut: 'exploitation', biens_count: 2, loyer_total: 2150, recouvrement: 75 },
    { id: SCI_ID_2, nom: 'SCI Patrimoine Lyon', statut: 'exploitation', biens_count: 1, loyer_total: 800, recouvrement: 85 }
  ],
  activite: [
    { id: 'act-1', type: 'loyer', description: 'Loyer encaisse : 950,00 EUR - 12 rue de Belleville', created_at: '2026-03-05T14:30:00Z', sci_nom: 'SCI Residence Belleville' },
    { id: 'act-2', type: 'quittance', description: 'Quittance generee : Fevrier 2026', created_at: '2026-03-02T10:00:00Z', sci_nom: 'SCI Residence Belleville' },
    { id: 'act-3', type: 'bien', description: 'Nouveau bien ajoute : 8 rue des Lilas', created_at: '2026-02-28T16:00:00Z', sci_nom: 'SCI Residence Belleville' }
  ]
};

// --- Finances ---

const MOCK_FINANCES = {
  revenus_total: 35400,
  charges_total: 11600,
  cashflow_net: 23800,
  taux_recouvrement: 78.5,
  patrimoine_total: 850000,
  rentabilite_moyenne: 3.95,
  evolution_mensuelle: [
    { mois: '2026-01', revenus: 2950, charges: 1400 },
    { mois: '2026-02', revenus: 2950, charges: 400 },
    { mois: '2026-03', revenus: 2150, charges: 350 }
  ],
  repartition_sci: [
    { sci_id: SCI_ID_1, sci_nom: 'SCI Residence Belleville', revenus: 25800, charges: 8400 },
    { sci_id: SCI_ID_2, sci_nom: 'SCI Patrimoine Lyon', revenus: 9600, charges: 3200 }
  ]
};

// --- Notifications ---

const MOCK_NOTIFICATIONS = [
  {
    id: 'notif-1',
    type: 'late_payment',
    title: 'Loyer impaye',
    message: 'Le loyer de novembre 2025 pour 12 rue de Belleville est en retard.',
    metadata: { bien_id: BIEN_ID_1, sci_id: SCI_ID_1 },
    read_at: null,
    created_at: '2026-03-10T08:00:00Z'
  },
  {
    id: 'notif-2',
    type: 'document_ready',
    title: 'Quittance disponible',
    message: 'La quittance de fevrier 2026 est prete au telechargement.',
    metadata: {},
    read_at: '2026-03-05T12:00:00Z',
    created_at: '2026-03-02T10:00:00Z'
  }
];

// --- Subscription / Entitlements ---

const MOCK_SUBSCRIPTION = {
  plan_key: 'pro',
  plan_name: 'Pro',
  status: 'active',
  mode: 'subscription',
  is_active: true,
  stripe_price_id: 'price_pro_mock',
  entitlements_version: 1,
  max_scis: 10,
  max_biens: 20,
  current_scis: 2,
  current_biens: 3,
  remaining_scis: 8,
  remaining_biens: 17,
  over_limit: false,
  features: {
    quittance: true,
    cerfa_2044: true,
    export_csv: true,
    multi_sci: true,
    documents: true,
    notifications_email: true
  },
  onboarding_completed: true
};

// --- Onboarding ---

const MOCK_ONBOARDING = {
  completed: true,
  sci_created: true,
  sci_id: SCI_ID_1,
  bien_created: true,
  bail_created: true,
  notifications_set: true
};

// --- Notification Preferences ---

const MOCK_NOTIFICATION_PREFS = {
  preferences: [
    { type: 'loyer_impaye', email_enabled: true, in_app_enabled: true },
    { type: 'bail_expirant', email_enabled: true, in_app_enabled: true },
    { type: 'quittance_disponible', email_enabled: false, in_app_enabled: true },
    { type: 'document_pret', email_enabled: false, in_app_enabled: true }
  ]
};

// --- Documents SCI-level ---

const MOCK_SCI_DOCUMENTS = [
  {
    id: 7001,
    id_bien: BIEN_ID_1,
    bien_adresse: '12 rue de Belleville',
    nom: 'Bail signe 2022',
    categorie: 'bail',
    url: 'https://storage.example.com/bail.pdf',
    uploaded_at: '2022-04-01T10:00:00Z'
  },
  {
    id: 7002,
    id_bien: BIEN_ID_1,
    bien_adresse: '12 rue de Belleville',
    nom: 'Etat des lieux entree',
    categorie: 'etat_des_lieux',
    url: 'https://storage.example.com/edl.pdf',
    uploaded_at: '2022-04-01T14:00:00Z'
  }
];

// --- GDPR ---

const MOCK_DATA_SUMMARY = {
  user_id: MOCK_USER.id,
  email: MOCK_USER.email,
  created_at: MOCK_USER.created_at,
  data_summary: {
    sci_count: 2,
    biens_count: 3,
    loyers_count: 18,
    associes_count: 4,
    account_created: '2025-09-15',
    last_sign_in: '2026-03-13'
  }
};

// ============================================================
// Helper to fulfill a route with JSON
// ============================================================

function json(route: any, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(data)
  });
}

// ============================================================
// Main entry point: setupApiMocks(page)
// ============================================================

export async function setupApiMocks(page: Page) {

  // ---- Supabase Auth endpoints ----
  // Intercept token refresh (the app tries to refresh on boot)
  await page.route('**/auth/v1/token*', route => json(route, {
    access_token: 'mock-jwt-token',
    token_type: 'bearer',
    expires_in: 3600,
    refresh_token: 'mock-refresh-token',
    user: MOCK_USER
  }));

  await page.route('**/auth/v1/user', route => json(route, MOCK_USER));

  // Catch any other Supabase auth calls (logout etc)
  await page.route('**/auth/v1/**', route => {
    if (route.request().url().includes('/token') || route.request().url().includes('/user')) {
      return route.fallback();
    }
    return json(route, { success: true });
  });

  // ---- Subscription / Entitlements ----
  await page.route('**/api/v1/stripe/subscription*', route => json(route, MOCK_SUBSCRIPTION));
  await page.route('**/api/v1/stripe/create-checkout*', route => json(route, { url: 'https://checkout.stripe.com/mock' }));

  // ---- Onboarding ----
  await page.route('**/api/v1/onboarding/complete', route => json(route, { completed: true }));
  await page.route('**/api/v1/onboarding*', route => json(route, MOCK_ONBOARDING));

  // ---- Dashboard ----
  await page.route('**/api/v1/dashboard*', route => json(route, MOCK_DASHBOARD));

  // ---- Finances ----
  await page.route('**/api/v1/finances*', route => json(route, MOCK_FINANCES));

  // ---- Notifications ----
  await page.route('**/api/v1/notifications/count*', route => json(route, { count: 1 }));
  await page.route('**/api/v1/notifications/read-all', route => json(route, { updated: 1 }));
  await page.route('**/api/v1/notifications/*/read', route => json(route, { ...MOCK_NOTIFICATIONS[0], read_at: new Date().toISOString() }));
  await page.route('**/api/v1/notifications*', route => {
    if (route.request().method() === 'GET') {
      return json(route, MOCK_NOTIFICATIONS);
    }
    return json(route, MOCK_NOTIFICATIONS[0]);
  });

  // ---- Notification Preferences ----
  await page.route('**/api/v1/user/notification-preferences*', route => {
    if (route.request().method() === 'PUT') {
      return json(route, MOCK_NOTIFICATION_PREFS);
    }
    return json(route, MOCK_NOTIFICATION_PREFS);
  });

  // ---- SCIs Detail (must be before /scis catch-all) ----
  // SCI 1 nested routes
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_1}/loyers*`, route => {
    if (route.request().method() === 'POST') return json(route, FICHE_BIEN_1.loyers_recents[0], 201);
    return json(route, FICHE_BIEN_1.loyers_recents);
  });
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_1}/baux*`, route => {
    if (route.request().method() === 'POST') return json(route, FICHE_BIEN_1.bail_actif, 201);
    return json(route, [FICHE_BIEN_1.bail_actif]);
  });
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_1}/charges*`, route => {
    if (route.request().method() === 'POST') return json(route, FICHE_BIEN_1.charges_list[0], 201);
    if (route.request().method() === 'DELETE') return route.fulfill({ status: 204, body: '' });
    return json(route, FICHE_BIEN_1.charges_list);
  });
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_1}/assurance-pno*`, route => {
    if (route.request().method() === 'POST') return json(route, FICHE_BIEN_1.assurance_pno, 201);
    if (route.request().method() === 'DELETE') return route.fulfill({ status: 204, body: '' });
    return json(route, FICHE_BIEN_1.assurance_pno ? [FICHE_BIEN_1.assurance_pno] : []);
  });
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_1}/frais-agence*`, route => {
    if (route.request().method() === 'POST') return json(route, FICHE_BIEN_1.frais_agence[0], 201);
    if (route.request().method() === 'DELETE') return route.fulfill({ status: 204, body: '' });
    return json(route, FICHE_BIEN_1.frais_agence);
  });
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_1}/documents*`, route => {
    if (route.request().method() === 'POST') return json(route, FICHE_BIEN_1.documents[0], 201);
    if (route.request().method() === 'DELETE') return route.fulfill({ status: 204, body: '' });
    return json(route, FICHE_BIEN_1.documents);
  });
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_2}/documents*`, route => json(route, []));
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_2}/loyers*`, route => json(route, FICHE_BIEN_2.loyers_recents));
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_2}/baux*`, route => json(route, [FICHE_BIEN_2.bail_actif]));
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_2}/charges*`, route => json(route, FICHE_BIEN_2.charges_list));
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_2}/assurance-pno*`, route => json(route, []));
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_2}/frais-agence*`, route => json(route, []));

  // Fiche bien detail (single bien)
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_1}`, route => json(route, FICHE_BIEN_1));
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens/${BIEN_ID_2}`, route => json(route, FICHE_BIEN_2));

  // SCI 1 biens list
  await page.route(`**/api/v1/scis/${SCI_ID_1}/biens*`, route => {
    if (route.request().method() === 'POST') return json(route, BIEN_1, 201);
    return json(route, [BIEN_1, BIEN_2]);
  });

  // SCI 1 associes
  await page.route(`**/api/v1/scis/${SCI_ID_1}/associes*`, route => {
    if (route.request().method() === 'POST') return json(route, ASSOCIES_SCI_1[0], 201);
    return json(route, ASSOCIES_SCI_1);
  });

  // SCI 1 documents
  await page.route(`**/api/v1/scis/${SCI_ID_1}/documents*`, route => json(route, MOCK_SCI_DOCUMENTS));

  // SCI 1 mouvements-parts, assemblees-generales
  await page.route(`**/api/v1/scis/${SCI_ID_1}/mouvements-parts*`, route => json(route, []));
  await page.route(`**/api/v1/scis/${SCI_ID_1}/assemblees-generales*`, route => json(route, []));

  // SCI 2 nested routes
  await page.route(`**/api/v1/scis/${SCI_ID_2}/biens*`, route => json(route, [BIEN_3]));
  await page.route(`**/api/v1/scis/${SCI_ID_2}/associes*`, route => json(route, ASSOCIES_SCI_2));
  await page.route(`**/api/v1/scis/${SCI_ID_2}/documents*`, route => json(route, []));
  await page.route(`**/api/v1/scis/${SCI_ID_2}/mouvements-parts*`, route => json(route, []));
  await page.route(`**/api/v1/scis/${SCI_ID_2}/assemblees-generales*`, route => json(route, []));

  // SCI detail
  await page.route(`**/api/v1/scis/${SCI_ID_1}`, route => {
    const method = route.request().method();
    if (method === 'DELETE') return route.fulfill({ status: 204, body: '' });
    if (method === 'PATCH') return json(route, SCI_1_DETAIL);
    return json(route, SCI_1_DETAIL);
  });
  await page.route(`**/api/v1/scis/${SCI_ID_2}`, route => json(route, SCI_2_DETAIL));

  // SCIs list (catch-all for /api/v1/scis and /api/v1/scis/)
  await page.route('**/api/v1/scis/', route => {
    if (route.request().method() === 'POST') return json(route, { ...SCI_1_OVERVIEW, id: 'new-sci-id' }, 201);
    return json(route, [SCI_1_OVERVIEW, SCI_2_OVERVIEW]);
  });
  await page.route('**/api/v1/scis', route => {
    // Only match exact /scis (not /scis/xxx which are handled above)
    const url = route.request().url();
    const path = new URL(url).pathname;
    if (path === '/api/v1/scis' || path === '/api/v1/scis/') {
      if (route.request().method() === 'POST') return json(route, { ...SCI_1_OVERVIEW, id: 'new-sci-id' }, 201);
      return json(route, [SCI_1_OVERVIEW, SCI_2_OVERVIEW]);
    }
    return route.fallback();
  });

  // ---- Fiscalite ----
  await page.route('**/api/v1/fiscalite*', route => {
    if (route.request().method() === 'POST') {
      return json(route, { id: 8099, id_sci: SCI_ID_1, annee: 2026, total_revenus: 0, total_charges: 0, resultat_fiscal: 0, regime_fiscal: 'IR' }, 201);
    }
    return json(route, SCI_1_DETAIL.fiscalite);
  });

  // ---- Associes (top-level) ----
  await page.route('**/api/v1/associes*', route => json(route, [...ASSOCIES_SCI_1, ...ASSOCIES_SCI_2]));

  // ---- Charges (top-level) ----
  await page.route('**/api/v1/charges*', route => json(route, FICHE_BIEN_1.charges_list));

  // ---- Loyers (top-level) ----
  await page.route('**/api/v1/loyers*', route => {
    if (route.request().method() === 'DELETE') return route.fulfill({ status: 204, body: '' });
    if (route.request().method() === 'PATCH') return json(route, FICHE_BIEN_1.loyers_recents[1]);
    return json(route, FICHE_BIEN_1.loyers_recents);
  });

  // ---- Biens (top-level) ----
  await page.route('**/api/v1/biens*', route => {
    if (route.request().method() === 'DELETE') return route.fulfill({ status: 204, body: '' });
    if (route.request().method() === 'PATCH') return json(route, BIEN_1);
    return json(route, [BIEN_1, BIEN_2, BIEN_3]);
  });

  // ---- Locataires ----
  await page.route('**/api/v1/locataires*', route => {
    if (route.request().method() === 'POST') return json(route, { id: 5099, nom: 'Test', id_bien: BIEN_ID_1 }, 201);
    return json(route, []);
  });

  // ---- Quitus / Quittances ----
  await page.route('**/api/v1/quitus/generate*', route => json(route, {
    filename: 'quittance-mars-2026.pdf',
    pdf_url: '/api/v1/files/quittance-mars-2026.pdf',
    size_bytes: 45000
  }));
  await page.route('**/api/v1/quitus/render*', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      body: Buffer.from('%PDF-1.4 mock')
    })
  );

  // ---- CERFA ----
  await page.route('**/api/v1/cerfa/2044/pdf*', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      body: Buffer.from('%PDF-1.4 cerfa mock')
    })
  );
  await page.route('**/api/v1/cerfa/2044*', route => json(route, {
    status: 'success',
    annee: 2025,
    total_revenus: 25800,
    total_charges: 8400,
    resultat_fiscal: 17400,
    formulaire: 'cerfa_2044'
  }));

  // ---- Export CSV ----
  await page.route('**/api/v1/export/loyers/csv*', route =>
    route.fulfill({
      status: 200,
      contentType: 'text/csv',
      headers: { 'Content-Disposition': 'attachment; filename="loyers-export.csv"' },
      body: 'date,montant,statut\n2026-03-01,950.00,en_attente\n2026-02-01,950.00,paye'
    })
  );
  await page.route('**/api/v1/export/biens/csv*', route =>
    route.fulfill({
      status: 200,
      contentType: 'text/csv',
      headers: { 'Content-Disposition': 'attachment; filename="biens-export.csv"' },
      body: 'adresse,ville,type\n12 rue de Belleville,Paris,nu\n8 rue des Lilas,Paris,meuble'
    })
  );

  // ---- GDPR ----
  await page.route('**/api/v1/gdpr/data-export*', route => json(route, {
    success: true,
    message: 'Export genere',
    export_url: 'https://storage.example.com/export.zip',
    expires_at: '2026-03-20T00:00:00Z'
  }));
  await page.route('**/api/v1/gdpr/data-summary*', route => json(route, MOCK_DATA_SUMMARY));
  await page.route('**/api/v1/gdpr/account*', route => json(route, { success: true, message: 'Compte supprime' }));

  // ---- Files / Storage ----
  await page.route('**/api/v1/files/**', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      body: Buffer.from('%PDF-1.4 file mock')
    })
  );

  // ---- Catch-all for any unmatched API call ----
  await page.route('**/api/v1/**', route => {
    const method = route.request().method();
    if (method === 'DELETE') return route.fulfill({ status: 204, body: '' });
    if (method === 'POST' || method === 'PATCH' || method === 'PUT') return json(route, { success: true });
    return json(route, []);
  });
}

// ============================================================
// Inject fake session into localStorage (before page navigates)
// ============================================================

export const FAKE_SESSION_DATA = {
  storageKey: 'gerersci.e2e-fake-session',
  session: {
    access_token: 'mock-jwt-token',
    refresh_token: 'mock-refresh-token',
    expires_in: 3600,
    expires_at: Math.floor(Date.now() / 1000) + 3600,
    user: MOCK_USER
  }
};

/**
 * Injects the fake E2E session into localStorage via addInitScript.
 * Must be called BEFORE any page.goto().
 */
export async function injectFakeSession(page: Page) {
  await page.addInitScript((data) => {
    window.localStorage.setItem(data.storageKey, JSON.stringify(data.session));
  }, FAKE_SESSION_DATA);
}

/**
 * Full setup: inject session + set up all API mocks.
 * Call this BEFORE page.goto() in beforeEach.
 */
export async function setupAuthedMocks(page: Page) {
  await injectFakeSession(page);
  await setupApiMocks(page);
}

// Re-export constants for use in tests
export { SCI_ID_1, SCI_ID_2, BIEN_ID_1, BIEN_ID_2, MOCK_USER };
