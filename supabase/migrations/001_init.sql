-- Tables SCI + RLS
CREATE TABLE sci (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nom TEXT NOT NULL,
  siren TEXT UNIQUE,
  regime_fiscal TEXT CHECK(regime_fiscal IN ('IR', 'IS'))
);

CREATE TABLE associes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_sci UUID REFERENCES sci(id),
  nom TEXT,
  part DECIMAL(5,2) CHECK(part > 0 AND part <= 100)
);

CREATE TABLE biens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_sci UUID REFERENCES sci(id),
  adresse TEXT,
  ville TEXT,
  code_postal TEXT,
  type_locatif TEXT,
  loyer_cc DECIMAL(10,2),
  charges DECIMAL(10,2),
  tmi DECIMAL(10,2),
  occupation_rate DECIMAL(5,2) DEFAULT 0
);

CREATE TABLE loyers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID REFERENCES biens(id),
  date_loyer DATE,
  montant DECIMAL(10,2),
  quitus_genere BOOLEAN DEFAULT false
);

-- RLS Policies
ALTER TABLE sci ENABLE ROW LEVEL SECURITY;
CREATE POLICY "SCI owners only" ON sci FOR ALL USING (auth.uid() IN (SELECT id FROM associes WHERE id_sci = sci.id));

ALTER TABLE biens ENABLE ROW LEVEL SECURITY;
CREATE POLICY "SCI biens only" ON biens FOR ALL USING (EXISTS (SELECT 1 FROM sci WHERE sci.id = biens.id_sci AND auth.uid() IN (SELECT id FROM associes WHERE id_sci = sci.id)));
