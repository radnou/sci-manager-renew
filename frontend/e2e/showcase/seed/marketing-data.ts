// Marketing demo data — "La Famille Moreau"
// Used by showcase tests to seed realistic French data

export const MARKETING_USER = {
  name: 'Sophie Moreau',
  email: 'sophie.moreau@gerersci.fr',
  plan: 'pro',
};

export const MARKETING_SCIS = [
  {
    nom: 'SCI Résidence Belleville',
    siren: '823456789',
    regime_fiscal: 'IR',
    adresse_siege: '12 rue de Belleville, 75020 Paris',
    capital_social: 150_000,
    date_creation: '2019-03-15',
    associes: [
      { nom: 'Sophie Moreau', email: 'sophie.moreau@gerersci.fr', part: 60, role: 'gerant', nb_parts: 600 },
      { nom: 'Marc Moreau', email: 'marc.moreau@gmail.com', part: 40, role: 'associe', nb_parts: 400 },
    ],
    biens: [
      {
        adresse: '12 rue de Belleville',
        ville: 'Paris',
        code_postal: '75020',
        type_locatif: 'nu',
        surface_m2: 65,
        nb_pieces: 3,
        loyer_cc: 1_430,
        charges: 180,
        dpe_classe: 'C',
        locataire: { nom: 'Émilie Dupont', email: 'emilie.dupont@mail.fr' },
        loyer_hc: 1_250,
      },
      {
        adresse: '8 rue des Lilas',
        ville: 'Paris',
        code_postal: '75020',
        type_locatif: 'meuble',
        surface_m2: 28,
        nb_pieces: 1,
        loyer_cc: 840,
        charges: 90,
        dpe_classe: 'D',
        locataire: { nom: 'Lucas Martin', email: 'lucas.martin@mail.fr' },
        loyer_hc: 750,
      },
    ],
  },
  {
    nom: 'SCI Patrimoine Lyon',
    siren: '912345678',
    regime_fiscal: 'IS',
    adresse_siege: '45 avenue Jean Jaurès, 69007 Lyon',
    capital_social: 200_000,
    date_creation: '2021-06-20',
    associes: [
      { nom: 'Sophie Moreau', email: 'sophie.moreau@gerersci.fr', part: 50, role: 'gerant', nb_parts: 500 },
      { nom: 'Antoine Moreau', email: 'antoine.moreau@gmail.com', part: 30, role: 'associe', nb_parts: 300 },
      { nom: 'Claire Durand', email: 'claire.durand@gmail.com', part: 20, role: 'associe', nb_parts: 200 },
    ],
    biens: [
      {
        adresse: '45 avenue Jean Jaurès',
        ville: 'Lyon',
        code_postal: '69007',
        type_locatif: 'nu',
        surface_m2: 85,
        nb_pieces: 4,
        loyer_cc: 1_250,
        charges: 150,
        dpe_classe: 'B',
        locataire: { nom: 'Fatima Benali', email: 'fatima.benali@mail.fr' },
        loyer_hc: 1_100,
      },
      {
        adresse: '22 rue Victor Hugo',
        ville: 'Lyon',
        code_postal: '69002',
        type_locatif: 'commercial',
        surface_m2: 120,
        nb_pieces: 1,
        loyer_cc: 3_150,
        charges: 350,
        dpe_classe: 'C',
        locataire: { nom: 'SARL Boulangerie Hugo', email: 'contact@boulangerie-hugo.fr' },
        loyer_hc: 2_800,
      },
    ],
  },
];

// Generate 12 months of loyer history for seeding
export function generateLoyerHistory(months = 12) {
  const now = new Date();
  return Array.from({ length: months }, (_, i) => {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    return {
      date_loyer: d.toISOString().slice(0, 10),
      statut: i === 0 ? 'en_attente' : 'paye', // Current month pending, rest paid
    };
  });
}
