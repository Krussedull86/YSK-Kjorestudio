-- KLARGJORT, IKKE AKTIVERT. Krever godkjenning av felles elevdata i skolen.
BEGIN;
create schema if not exists ysk_private;
revoke all on schema ysk_private from public;
grant usage on schema ysk_private to authenticated;
create table public.ysk_organizations(id uuid primary key default gen_random_uuid(), name text not null, created_at timestamptz not null default now());
create table public.ysk_memberships(user_id uuid primary key references auth.users(id) on delete cascade, organization_id uuid not null references public.ysk_organizations(id), display_name text not null check(length(display_name) between 1 and 100), email text not null, role text not null check(role in ('admin','teacher')), active boolean not null default true);
alter table public.ysk_organizations enable row level security;
alter table public.ysk_memberships enable row level security;
revoke all on public.ysk_organizations,public.ysk_memberships from authenticated;
grant select on public.ysk_organizations,public.ysk_memberships to authenticated;
grant all on public.ysk_organizations,public.ysk_memberships to service_role;
revoke all on public.ysk_organizations,public.ysk_memberships from anon;
create function ysk_private.organization_for_user() returns uuid language sql stable security invoker set search_path='' as $$select organization_id from public.ysk_memberships where user_id=(select auth.uid()) and active and auth.uid() is not null$$;
revoke all on function ysk_private.organization_for_user() from public,anon;
grant execute on function ysk_private.organization_for_user() to authenticated;
create policy ysk_member_self on public.ysk_memberships for select to authenticated using(user_id=(select auth.uid()));
create policy ysk_org_read on public.ysk_organizations for select to authenticated using(id=(select ysk_private.organization_for_user()));
with organization as (insert into public.ysk_organizations(name) values('Ta Lappen · YSK') returning id)
insert into public.ysk_memberships(user_id,organization_id,display_name,email,role)
select u.id,o.id,'Kjell Kåre',u.email,'admin' from auth.users u cross join organization o where lower(u.email)='napster1986@hotmail.com';
alter table public.ysk_trips add column organization_id uuid references public.ysk_organizations(id);
update public.ysk_trips t set organization_id=m.organization_id from public.ysk_memberships m where t.owner_id=m.user_id;
alter table public.ysk_trips alter column organization_id set not null;
alter table public.ysk_trips alter column organization_id set default ysk_private.organization_for_user();
alter table public.ysk_trips add constraint ysk_class_trip_unique unique(organization_id,driver,course,vehicle,trip);
create index ysk_trips_org_updated_idx on public.ysk_trips(organization_id,updated_at,id);
alter policy ysk_read on public.ysk_trips to authenticated using(organization_id=(select ysk_private.organization_for_user()));
alter policy ysk_insert on public.ysk_trips to authenticated with check(owner_id=(select auth.uid()) and organization_id=(select ysk_private.organization_for_user()));
alter policy ysk_update on public.ysk_trips to authenticated using(owner_id=(select auth.uid()) and organization_id=(select ysk_private.organization_for_user())) with check(owner_id=(select auth.uid()) and organization_id=(select ysk_private.organization_for_user()));
COMMIT;
