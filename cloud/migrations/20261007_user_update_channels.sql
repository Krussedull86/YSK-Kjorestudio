-- Requires the activated shared-school schema. Applied to the connected project.
alter table public.ysk_memberships add column if not exists update_channel text not null default 'stable' check(update_channel in ('dev','stable'));
create table if not exists public.ysk_releases(
 id uuid primary key default gen_random_uuid(),
 organization_id uuid not null references public.ysk_organizations(id),
 version text not null check(length(version) between 1 and 50),
 build integer not null check(build>0),
 notes text not null default '' check(length(notes)<=5000),
 assets jsonb not null default '{}'::jsonb,
 ready boolean not null default false,
 created_at timestamptz not null default now(),stable_at timestamptz,
 unique(organization_id,build)
);
create table if not exists public.ysk_update_channels(
 organization_id uuid not null references public.ysk_organizations(id),
 channel text not null check(channel in ('dev','stable')),
 release_id uuid not null references public.ysk_releases(id),
 updated_at timestamptz not null default now(),primary key(organization_id,channel)
);
alter table public.ysk_releases enable row level security;
alter table public.ysk_update_channels enable row level security;
-- Deliberately no direct user policies. Authenticated Edge Functions check membership.
revoke all on public.ysk_releases,public.ysk_update_channels from anon,authenticated;
grant all on public.ysk_releases,public.ysk_update_channels to service_role;
