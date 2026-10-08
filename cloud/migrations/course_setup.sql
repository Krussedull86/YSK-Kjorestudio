create table public.ysk_course_setup (organization_id uuid not null references public.ysk_organizations(id), name text not null check(length(name) between 1 and 100), active_trips integer not null check(active_trips between 1 and 5), primary key(organization_id,name));
alter table public.ysk_course_setup enable row level security;
revoke all on public.ysk_course_setup from anon,authenticated;
grant all on public.ysk_course_setup to service_role;
