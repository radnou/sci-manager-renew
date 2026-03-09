-- 001_init.sql
-- GererSCI schema with RLS, indexes, and audit timestamps.

create extension if not exists pgcrypto;

-- -----------------------------------------------------------------------------
-- Audit helpers
-- -----------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

-- -----------------------------------------------------------------------------
-- Tables
-- -----------------------------------------------------------------------------
create table if not exists sci (
  id uuid primary key default gen_random_uuid(),
  nom text not null,
  siren text unique,
  regime_fiscal text not null check (regime_fiscal in ('IR', 'IS')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists associes (
  id uuid primary key default gen_random_uuid(),
  id_sci uuid not null references sci(id) on delete cascade,
  user_id uuid not null,
  nom text not null,
  email text,
  part numeric(5,2) not null check (part > 0 and part <= 100),
  role text not null default 'associe',
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (id_sci, user_id)
);

create table if not exists biens (
  id uuid primary key default gen_random_uuid(),
  id_sci uuid not null references sci(id) on delete cascade,
  adresse text not null,
  ville text not null,
  code_postal text not null,
  type_locatif text not null,
  loyer_cc numeric(12,2) not null default 0,
  charges numeric(12,2) not null default 0,
  tmi numeric(5,2) not null default 0,
  acquisition_date date,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists locataires (
  id uuid primary key default gen_random_uuid(),
  id_bien uuid not null references biens(id) on delete cascade,
  nom text not null,
  email text,
  date_debut date not null,
  date_fin date,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists loyers (
  id uuid primary key default gen_random_uuid(),
  id_bien uuid not null references biens(id) on delete cascade,
  id_locataire uuid references locataires(id) on delete set null,
  date_loyer date not null,
  montant numeric(12,2) not null,
  statut text not null default 'en_attente',
  quitus_genere boolean not null default false,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (id_bien, id_locataire, date_loyer)
);

create table if not exists charges (
  id uuid primary key default gen_random_uuid(),
  id_bien uuid not null references biens(id) on delete cascade,
  type_charge text not null,
  montant numeric(12,2) not null,
  date_paiement date not null,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists fiscalite (
  id uuid primary key default gen_random_uuid(),
  id_sci uuid not null references sci(id) on delete cascade,
  annee integer not null,
  total_revenus numeric(14,2) not null default 0,
  total_charges numeric(14,2) not null default 0,
  resultat_fiscal numeric(14,2) not null default 0,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (id_sci, annee)
);

-- -----------------------------------------------------------------------------
-- Indexes (performance)
-- -----------------------------------------------------------------------------
create index if not exists idx_associes_id_sci on associes (id_sci);
create index if not exists idx_associes_user_id on associes (user_id);

create index if not exists idx_biens_id_sci on biens (id_sci);

create index if not exists idx_locataires_id_bien on locataires (id_bien);

create index if not exists idx_loyers_id_bien on loyers (id_bien);
create index if not exists idx_loyers_id_locataire on loyers (id_locataire);
create index if not exists idx_loyers_date_loyer on loyers (date_loyer);

create index if not exists idx_charges_id_bien on charges (id_bien);
create index if not exists idx_charges_date_paiement on charges (date_paiement);

create index if not exists idx_fiscalite_id_sci on fiscalite (id_sci);
create index if not exists idx_fiscalite_annee on fiscalite (annee);

-- -----------------------------------------------------------------------------
-- Triggers (updated_at)
-- -----------------------------------------------------------------------------
drop trigger if exists trg_sci_updated_at on sci;
create trigger trg_sci_updated_at
before update on sci
for each row execute function set_updated_at();

drop trigger if exists trg_associes_updated_at on associes;
create trigger trg_associes_updated_at
before update on associes
for each row execute function set_updated_at();

drop trigger if exists trg_biens_updated_at on biens;
create trigger trg_biens_updated_at
before update on biens
for each row execute function set_updated_at();

drop trigger if exists trg_locataires_updated_at on locataires;
create trigger trg_locataires_updated_at
before update on locataires
for each row execute function set_updated_at();

drop trigger if exists trg_loyers_updated_at on loyers;
create trigger trg_loyers_updated_at
before update on loyers
for each row execute function set_updated_at();

drop trigger if exists trg_charges_updated_at on charges;
create trigger trg_charges_updated_at
before update on charges
for each row execute function set_updated_at();

drop trigger if exists trg_fiscalite_updated_at on fiscalite;
create trigger trg_fiscalite_updated_at
before update on fiscalite
for each row execute function set_updated_at();

-- -----------------------------------------------------------------------------
-- RLS (strict multi-tenant by associate membership)
-- -----------------------------------------------------------------------------
alter table sci enable row level security;
alter table associes enable row level security;
alter table biens enable row level security;
alter table locataires enable row level security;
alter table loyers enable row level security;
alter table charges enable row level security;
alter table fiscalite enable row level security;

drop policy if exists sci_member_select on sci;
drop policy if exists sci_member_insert on sci;
drop policy if exists sci_member_update on sci;
drop policy if exists sci_member_delete on sci;

create policy sci_member_select on sci
for select
using (
  exists (
    select 1 from associes a
    where a.id_sci = sci.id and a.user_id = auth.uid()
  )
);

create policy sci_member_insert on sci
for insert
with check (true);

create policy sci_member_update on sci
for update
using (
  exists (
    select 1 from associes a
    where a.id_sci = sci.id and a.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1 from associes a
    where a.id_sci = sci.id and a.user_id = auth.uid()
  )
);

create policy sci_member_delete on sci
for delete
using (
  exists (
    select 1 from associes a
    where a.id_sci = sci.id and a.user_id = auth.uid()
  )
);

drop policy if exists associes_member_select on associes;
drop policy if exists associes_member_insert on associes;
drop policy if exists associes_member_update on associes;
drop policy if exists associes_member_delete on associes;

create policy associes_member_select on associes
for select
using (
  exists (
    select 1 from associes a
    where a.id_sci = associes.id_sci and a.user_id = auth.uid()
  )
);

create policy associes_member_insert on associes
for insert
with check (
  user_id = auth.uid()
  or exists (
    select 1 from associes a
    where a.id_sci = associes.id_sci and a.user_id = auth.uid()
  )
);

create policy associes_member_update on associes
for update
using (
  exists (
    select 1 from associes a
    where a.id_sci = associes.id_sci and a.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1 from associes a
    where a.id_sci = associes.id_sci and a.user_id = auth.uid()
  )
);

create policy associes_member_delete on associes
for delete
using (
  exists (
    select 1 from associes a
    where a.id_sci = associes.id_sci and a.user_id = auth.uid()
  )
);

drop policy if exists biens_member_select on biens;
drop policy if exists biens_member_insert on biens;
drop policy if exists biens_member_update on biens;
drop policy if exists biens_member_delete on biens;

create policy biens_member_select on biens
for select
using (
  exists (
    select 1 from associes a
    where a.id_sci = biens.id_sci and a.user_id = auth.uid()
  )
);

create policy biens_member_insert on biens
for insert
with check (
  exists (
    select 1 from associes a
    where a.id_sci = biens.id_sci and a.user_id = auth.uid()
  )
);

create policy biens_member_update on biens
for update
using (
  exists (
    select 1 from associes a
    where a.id_sci = biens.id_sci and a.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1 from associes a
    where a.id_sci = biens.id_sci and a.user_id = auth.uid()
  )
);

create policy biens_member_delete on biens
for delete
using (
  exists (
    select 1 from associes a
    where a.id_sci = biens.id_sci and a.user_id = auth.uid()
  )
);

drop policy if exists locataires_member_select on locataires;
drop policy if exists locataires_member_insert on locataires;
drop policy if exists locataires_member_update on locataires;
drop policy if exists locataires_member_delete on locataires;

create policy locataires_member_select on locataires
for select
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = locataires.id_bien
      and a.user_id = auth.uid()
  )
);

create policy locataires_member_insert on locataires
for insert
with check (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = locataires.id_bien
      and a.user_id = auth.uid()
  )
);

create policy locataires_member_update on locataires
for update
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = locataires.id_bien
      and a.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = locataires.id_bien
      and a.user_id = auth.uid()
  )
);

create policy locataires_member_delete on locataires
for delete
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = locataires.id_bien
      and a.user_id = auth.uid()
  )
);

drop policy if exists loyers_member_select on loyers;
drop policy if exists loyers_member_insert on loyers;
drop policy if exists loyers_member_update on loyers;
drop policy if exists loyers_member_delete on loyers;

create policy loyers_member_select on loyers
for select
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = loyers.id_bien
      and a.user_id = auth.uid()
  )
);

create policy loyers_member_insert on loyers
for insert
with check (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = loyers.id_bien
      and a.user_id = auth.uid()
  )
);

create policy loyers_member_update on loyers
for update
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = loyers.id_bien
      and a.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = loyers.id_bien
      and a.user_id = auth.uid()
  )
);

create policy loyers_member_delete on loyers
for delete
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = loyers.id_bien
      and a.user_id = auth.uid()
  )
);

drop policy if exists charges_member_select on charges;
drop policy if exists charges_member_insert on charges;
drop policy if exists charges_member_update on charges;
drop policy if exists charges_member_delete on charges;

create policy charges_member_select on charges
for select
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = charges.id_bien
      and a.user_id = auth.uid()
  )
);

create policy charges_member_insert on charges
for insert
with check (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = charges.id_bien
      and a.user_id = auth.uid()
  )
);

create policy charges_member_update on charges
for update
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = charges.id_bien
      and a.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = charges.id_bien
      and a.user_id = auth.uid()
  )
);

create policy charges_member_delete on charges
for delete
using (
  exists (
    select 1
    from biens b
    join associes a on a.id_sci = b.id_sci
    where b.id = charges.id_bien
      and a.user_id = auth.uid()
  )
);

drop policy if exists fiscalite_member_select on fiscalite;
drop policy if exists fiscalite_member_insert on fiscalite;
drop policy if exists fiscalite_member_update on fiscalite;
drop policy if exists fiscalite_member_delete on fiscalite;

create policy fiscalite_member_select on fiscalite
for select
using (
  exists (
    select 1 from associes a
    where a.id_sci = fiscalite.id_sci and a.user_id = auth.uid()
  )
);

create policy fiscalite_member_insert on fiscalite
for insert
with check (
  exists (
    select 1 from associes a
    where a.id_sci = fiscalite.id_sci and a.user_id = auth.uid()
  )
);

create policy fiscalite_member_update on fiscalite
for update
using (
  exists (
    select 1 from associes a
    where a.id_sci = fiscalite.id_sci and a.user_id = auth.uid()
  )
)
with check (
  exists (
    select 1 from associes a
    where a.id_sci = fiscalite.id_sci and a.user_id = auth.uid()
  )
);

create policy fiscalite_member_delete on fiscalite
for delete
using (
  exists (
    select 1 from associes a
    where a.id_sci = fiscalite.id_sci and a.user_id = auth.uid()
  )
);
