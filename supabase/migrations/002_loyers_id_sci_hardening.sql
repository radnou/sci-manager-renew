-- 002_loyers_id_sci_hardening.sql
-- Hardening tenant model for loyers: enforce explicit SCI linkage.

alter table loyers
  add column if not exists id_sci uuid references sci(id) on delete cascade;

-- Backfill from biens to keep historical rows queryable by SCI.
update loyers l
set id_sci = b.id_sci
from biens b
where b.id = l.id_bien
  and l.id_sci is null;

create index if not exists idx_loyers_id_sci on loyers (id_sci);

-- Keep id_sci aligned with id_bien on every insert/update.
create or replace function sync_loyer_id_sci()
returns trigger
language plpgsql
as $$
declare
  resolved_id_sci uuid;
begin
  select b.id_sci into resolved_id_sci
  from biens b
  where b.id = new.id_bien;

  if resolved_id_sci is null then
    raise exception 'Unknown bien for loyer: %', new.id_bien;
  end if;

  if new.id_sci is null then
    new.id_sci = resolved_id_sci;
  elsif new.id_sci <> resolved_id_sci then
    raise exception 'id_sci (%) does not match bien.id_sci (%)', new.id_sci, resolved_id_sci;
  end if;

  return new;
end;
$$;

drop trigger if exists trg_loyers_sync_id_sci on loyers;
create trigger trg_loyers_sync_id_sci
before insert or update of id_bien, id_sci on loyers
for each row execute function sync_loyer_id_sci();

-- Enforce non-null after backfill.
alter table loyers
  alter column id_sci set not null;
