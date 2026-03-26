-- Seed data for GererSCI local development & E2E testing

-- 1. Test user
INSERT INTO auth.users (
  id, instance_id, email, encrypted_password, email_confirmed_at,
  role, aud, created_at, updated_at, confirmation_token
) VALUES (
  '11111111-1111-1111-1111-111111111111',
  '00000000-0000-0000-0000-000000000000',
  'test@gerersci.fr',
  crypt('testpassword123', gen_salt('bf')),
  now(), 'authenticated', 'authenticated',
  now() - interval '60 days', now(), ''
) ON CONFLICT (id) DO NOTHING;

INSERT INTO auth.identities (
  id, user_id, identity_data, provider, provider_id, created_at, updated_at
) VALUES (
  '11111111-1111-1111-1111-111111111111',
  '11111111-1111-1111-1111-111111111111',
  jsonb_build_object('sub', '11111111-1111-1111-1111-111111111111', 'email', 'test@gerersci.fr'),
  'email', '11111111-1111-1111-1111-111111111111', now(), now()
) ON CONFLICT DO NOTHING;

-- 2. Subscription (active, onboarding done)
INSERT INTO subscriptions (
  id, user_id, stripe_customer_id, stripe_subscription_id, stripe_price_id,
  status, current_period_end, guarantee_expires_at, onboarding_completed, created_at
) VALUES (
  '00000000-0000-0000-0000-aab000000001',
  '11111111-1111-1111-1111-111111111111',
  'cus_seed_test', 'sub_seed_test', 'price_pro_monthly',
  'active', now() + interval '15 days', now() + interval '15 days', true,
  now() - interval '15 days'
) ON CONFLICT DO NOTHING;

-- 3. SCIs
INSERT INTO sci (id, nom, regime_fiscal, adresse_siege, rcs_ville, rcs_numero, date_creation, capital_social, forme_juridique, statut, created_at) VALUES
  ('aaaa1111-0000-0000-0000-000000000001', 'SCI Les Oliviers', 'IR', '12 rue des Oliviers, 13001 Marseille', 'Marseille', '123456789', '2020-03-15', 50000, 'SCI', 'active', now() - interval '30 days'),
  ('aaaa1111-0000-0000-0000-000000000002', 'SCI Haussmann Patrimoine', 'IS', '45 boulevard Haussmann, 75009 Paris', 'Paris', '987654321', '2018-06-01', 150000, 'SCI', 'active', now() - interval '60 days')
ON CONFLICT DO NOTHING;

-- 4. Associes (no prenom column, has 'part' as percentage)
INSERT INTO associes (id, id_sci, user_id, nom, email, role, part, nb_parts, created_at) VALUES
  ('00000000-0000-0000-aaaa-000000000001', 'aaaa1111-0000-0000-0000-000000000001', '11111111-1111-1111-1111-111111111111', 'Mossabely Radnoumane', 'test@gerersci.fr', 'gerant', 50, 500, now()),
  ('00000000-0000-0000-aaaa-000000000002', 'aaaa1111-0000-0000-0000-000000000002', '11111111-1111-1111-1111-111111111111', 'Mossabely Radnoumane', 'test@gerersci.fr', 'gerant', 100, 1000, now()),
  ('00000000-0000-0000-aaaa-000000000003', 'aaaa1111-0000-0000-0000-000000000001', null, 'Dupont Marie', 'marie.dupont@example.com', 'associe', 50, 500, now())
ON CONFLICT DO NOTHING;

-- 5. Biens
INSERT INTO biens (id, id_sci, adresse, code_postal, ville, type_locatif, loyer_cc, charges, tmi, surface_m2, nb_pieces, prix_acquisition, type_bien, created_at) VALUES
  ('00000000-0000-0000-bbbb-000000000001', 'aaaa1111-0000-0000-0000-000000000001', '15 avenue Jean Jaures', '13001', 'Marseille', 'nu', 830, 80, 30, 65, 3, 185000, 'appartement', now()),
  ('00000000-0000-0000-bbbb-000000000002', 'aaaa1111-0000-0000-0000-000000000001', '8 rue de la Republique', '13002', 'Marseille', 'meuble', 630, 50, 30, 42, 2, 125000, 'appartement', now()),
  ('00000000-0000-0000-bbbb-000000000003', 'aaaa1111-0000-0000-0000-000000000001', '3 place Castellane', '13006', 'Marseille', 'meuble', 480, 30, 30, 22, 1, 95000, 'appartement', now()),
  ('00000000-0000-0000-bbbb-000000000004', 'aaaa1111-0000-0000-0000-000000000002', '45 boulevard Haussmann', '75009', 'Paris', 'nu', 2450, 250, 41, 95, 4, 850000, 'appartement', now()),
  ('00000000-0000-0000-bbbb-000000000005', 'aaaa1111-0000-0000-0000-000000000002', '12 rue du Faubourg Saint-Honore', '75008', 'Paris', 'commercial', 3900, 400, 33, 55, 2, 450000, 'local_commercial', now())
ON CONFLICT DO NOTHING;

-- 6. Baux (no id_sci column — linked via id_bien)
INSERT INTO baux (id, id_bien, date_debut, date_fin, loyer_hc, charges_locatives, depot_garantie, statut, created_at) VALUES
  ('00000000-0000-0000-cccc-000000000001', '00000000-0000-0000-bbbb-000000000001', '2024-01-01', '2027-01-01', 750, 80, 750, 'en_cours', now()),
  ('00000000-0000-0000-cccc-000000000002', '00000000-0000-0000-bbbb-000000000002', '2024-06-01', '2025-06-01', 580, 50, 1160, 'en_cours', now()),
  ('00000000-0000-0000-cccc-000000000003', '00000000-0000-0000-bbbb-000000000003', '2023-09-01', '2024-09-01', 450, 30, 900, 'expire', now()),
  ('00000000-0000-0000-cccc-000000000004', '00000000-0000-0000-bbbb-000000000004', '2023-01-01', '2026-01-01', 2200, 250, 2200, 'en_cours', now()),
  ('00000000-0000-0000-cccc-000000000005', '00000000-0000-0000-bbbb-000000000005', '2022-01-01', '2031-01-01', 3500, 400, 7000, 'en_cours', now())
ON CONFLICT DO NOTHING;

-- 7. Locataires (id_bien required, date_debut required, no prenom column)
INSERT INTO locataires (id, id_bien, nom, email, telephone, date_debut, created_at) VALUES
  ('00000000-0000-0000-dddd-000000000001', '00000000-0000-0000-bbbb-000000000001', 'Martin Pierre', 'pierre.martin@email.com', '0612345678', '2024-01-01', now()),
  ('00000000-0000-0000-dddd-000000000002', '00000000-0000-0000-bbbb-000000000002', 'Bernard Sophie', 'sophie.bernard@email.com', '0623456789', '2024-06-01', now()),
  ('00000000-0000-0000-dddd-000000000003', '00000000-0000-0000-bbbb-000000000003', 'Petit Lucas', 'lucas.petit@email.com', '0634567890', '2023-09-01', now()),
  ('00000000-0000-0000-dddd-000000000004', '00000000-0000-0000-bbbb-000000000004', 'Leroy Emma', 'emma.leroy@email.com', '0645678901', '2023-01-01', now()),
  ('00000000-0000-0000-dddd-000000000005', '00000000-0000-0000-bbbb-000000000005', 'SARL TechStore', 'contact@techstore.fr', '0156789012', '2022-01-01', now())
ON CONFLICT DO NOTHING;

INSERT INTO bail_locataires (id_bail, id_locataire) VALUES
  ('00000000-0000-0000-cccc-000000000001', '00000000-0000-0000-dddd-000000000001'), ('00000000-0000-0000-cccc-000000000002', '00000000-0000-0000-dddd-000000000002'), ('00000000-0000-0000-cccc-000000000003', '00000000-0000-0000-dddd-000000000003'),
  ('00000000-0000-0000-cccc-000000000004', '00000000-0000-0000-dddd-000000000004'), ('00000000-0000-0000-cccc-000000000005', '00000000-0000-0000-dddd-000000000005')
ON CONFLICT DO NOTHING;

-- 8. Loyers (3 mois)
INSERT INTO loyers (id, id_bien, id_sci, date_loyer, montant, statut, date_paiement, created_at) VALUES
  ('00000000-0000-0000-eeee-000000000001', '00000000-0000-0000-bbbb-000000000001', 'aaaa1111-0000-0000-0000-000000000001', '2026-01-01', 830, 'paye', '2026-01-05', now()),
  ('00000000-0000-0000-eeee-000000000002', '00000000-0000-0000-bbbb-000000000001', 'aaaa1111-0000-0000-0000-000000000001', '2026-02-01', 830, 'paye', '2026-02-03', now()),
  ('00000000-0000-0000-eeee-000000000003', '00000000-0000-0000-bbbb-000000000001', 'aaaa1111-0000-0000-0000-000000000001', '2026-03-01', 830, 'en_retard', null, now()),
  ('00000000-0000-0000-eeee-000000000004', '00000000-0000-0000-bbbb-000000000002', 'aaaa1111-0000-0000-0000-000000000001', '2026-01-01', 630, 'paye', '2026-01-02', now()),
  ('00000000-0000-0000-eeee-000000000005', '00000000-0000-0000-bbbb-000000000002', 'aaaa1111-0000-0000-0000-000000000001', '2026-02-01', 630, 'paye', '2026-02-01', now()),
  ('00000000-0000-0000-eeee-000000000006', '00000000-0000-0000-bbbb-000000000002', 'aaaa1111-0000-0000-0000-000000000001', '2026-03-01', 630, 'paye', '2026-03-05', now()),
  ('00000000-0000-0000-eeee-000000000007', '00000000-0000-0000-bbbb-000000000004', 'aaaa1111-0000-0000-0000-000000000002', '2026-01-01', 2450, 'paye', '2026-01-03', now()),
  ('00000000-0000-0000-eeee-000000000008', '00000000-0000-0000-bbbb-000000000004', 'aaaa1111-0000-0000-0000-000000000002', '2026-02-01', 2450, 'paye', '2026-02-02', now()),
  ('00000000-0000-0000-eeee-000000000009', '00000000-0000-0000-bbbb-000000000004', 'aaaa1111-0000-0000-0000-000000000002', '2026-03-01', 2450, 'en_attente', null, now()),
  ('00000000-0000-0000-eeee-000000000010', '00000000-0000-0000-bbbb-000000000005', 'aaaa1111-0000-0000-0000-000000000002', '2026-01-01', 3900, 'paye', '2026-01-10', now()),
  ('00000000-0000-0000-eeee-000000000011', '00000000-0000-0000-bbbb-000000000005', 'aaaa1111-0000-0000-0000-000000000002', '2026-02-01', 3900, 'paye', '2026-02-08', now()),
  ('00000000-0000-0000-eeee-000000000012', '00000000-0000-0000-bbbb-000000000005', 'aaaa1111-0000-0000-0000-000000000002', '2026-03-01', 3900, 'paye', '2026-03-04', now())
ON CONFLICT DO NOTHING;

-- 9. Charges
INSERT INTO charges (id, id_bien, type_charge, montant, date_paiement, created_at) VALUES
  ('00000000-0000-0000-ffff-000000000001', '00000000-0000-0000-bbbb-000000000001', 'copropriete', 1800, '2026-01-01', now()),
  ('00000000-0000-0000-ffff-000000000002', '00000000-0000-0000-bbbb-000000000001', 'taxe_fonciere', 950, '2026-10-15', now()),
  ('00000000-0000-0000-ffff-000000000003', '00000000-0000-0000-bbbb-000000000004', 'copropriete', 4200, '2026-01-01', now()),
  ('00000000-0000-0000-ffff-000000000004', '00000000-0000-0000-bbbb-000000000004', 'taxe_fonciere', 3800, '2026-10-15', now()),
  ('00000000-0000-0000-ffff-000000000005', '00000000-0000-0000-bbbb-000000000005', 'assurance', 1200, '2026-01-01', now())
ON CONFLICT DO NOTHING;

-- 10. Notifications
INSERT INTO notifications (id, user_id, type, title, message, created_at) VALUES
  ('00000000-0000-0000-1111-000000000001', '11111111-1111-1111-1111-111111111111', 'late_payment', 'Loyer en retard', 'Le loyer de mars 2026 pour 15 avenue Jean Jaures est en retard.', now()),
  ('00000000-0000-0000-1111-000000000002', '11111111-1111-1111-1111-111111111111', 'bail_expiring', 'Bail expirant', 'Le bail du 3 place Castellane expire le 01/09/2024.', now() - interval '1 day'),
  ('00000000-0000-0000-1111-000000000003', '11111111-1111-1111-1111-111111111111', 'new_loyer', 'Nouveau loyer', 'Loyer de fevrier enregistre pour 45 bd Haussmann.', now() - interval '5 days')
ON CONFLICT DO NOTHING;
