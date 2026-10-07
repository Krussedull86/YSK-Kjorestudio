-- Kjør i SQL Editor i ditt Supabase-prosjekt. Klienter bruker kun publishable/anon key.
create table if not exists public.ysk_trips (
 id uuid primary key,
 owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 driver text not null check(length(driver) between 1 and 100),
 course text not null check(length(course) between 1 and 100),
 vehicle text not null check(length(vehicle) between 1 and 100),
 trip integer not null check(trip between 1 and 5),
 revision uuid not null,
 payload jsonb not null,
 updated_at timestamptz not null default now(),
 unique(owner_id,driver,course,vehicle,trip),
 constraint payload_shape check (coalesce((
  payload->>'id'=id::text and payload->>'driver'=driver and payload->>'course'=course
  and payload->>'vehicle'=vehicle and (payload->>'trip')::integer=trip
  and (payload->>'minutes')::numeric>0 and (payload->>'km')::numeric>0
  and (payload->>'liters')::numeric>=0 and (payload->>'stops')::numeric>=0
  and (payload->>'stops')::numeric=trunc((payload->>'stops')::numeric)
  and payload->>'trafikksikkerhet' in ('Bra','Middel','Svak')
  and payload->>'avpassing' in ('Bra','Middel','Svak')
  and payload->>'økning' in ('Bra','Middel','Svak')
  and payload->>'komfort' in ('Bra','Middel','Svak')
  and jsonb_typeof(payload->'minutes')='number' and jsonb_typeof(payload->'km')='number'
  and jsonb_typeof(payload->'liters')='number' and jsonb_typeof(payload->'stops')='number'
  and payload ?& array['id','driver','course','vehicle','trip','minutes','km','liters','stops','trafikksikkerhet','avpassing','økning','komfort']
 ),false))
);
alter table public.ysk_trips enable row level security;
revoke all on public.ysk_trips from anon;
grant select,insert,update on public.ysk_trips to authenticated;
drop policy if exists ysk_read on public.ysk_trips;
create policy ysk_read on public.ysk_trips for select to authenticated using (owner_id=auth.uid());
drop policy if exists ysk_insert on public.ysk_trips;
create policy ysk_insert on public.ysk_trips for insert to authenticated with check(owner_id=auth.uid());
drop policy if exists ysk_update on public.ysk_trips;
create policy ysk_update on public.ysk_trips for update to authenticated using(owner_id=auth.uid()) with check(owner_id=auth.uid());
create or replace function public.ysk_stamp() returns trigger language plpgsql set search_path='' as $$
begin new.updated_at=now(); return new; end $$;
drop trigger if exists ysk_updated on public.ysk_trips;
create trigger ysk_updated before update on public.ysk_trips for each row execute function public.ysk_stamp();
