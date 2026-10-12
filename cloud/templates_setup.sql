create table if not exists public.ysk_parameter_bank(organization_id uuid not null references public.ysk_organizations(id),id text not null check(length(id) between 1 and 80),definition jsonb not null,primary key(organization_id,id));
create table if not exists public.ysk_trip_templates(organization_id uuid not null references public.ysk_organizations(id),id uuid not null,revision integer not null,name text not null,definition jsonb not null,primary key(organization_id,id));
create table if not exists public.ysk_trip_template_versions(organization_id uuid not null references public.ysk_organizations(id),id uuid not null,revision integer not null,definition jsonb not null,primary key(organization_id,id,revision));
create table if not exists public.ysk_template_courses(organization_id uuid not null references public.ysk_organizations(id),name text not null check(length(name) between 1 and 100),template_ids jsonb not null,primary key(organization_id,name));
create table if not exists public.ysk_template_runs(id uuid primary key,organization_id uuid not null references public.ysk_organizations(id),owner_id uuid not null references auth.users(id),revision integer not null default 1,template_id uuid not null,template_revision integer not null,snapshot jsonb not null,payload jsonb not null,created_at timestamptz not null default now(),updated_at timestamptz not null default now());
create index if not exists ysk_template_runs_school on public.ysk_template_runs(organization_id,updated_at desc,id);
create index if not exists ysk_template_runs_owner on public.ysk_template_runs(owner_id,updated_at desc,id);
alter table public.ysk_parameter_bank enable row level security;
alter table public.ysk_trip_templates enable row level security;
alter table public.ysk_trip_template_versions enable row level security;
alter table public.ysk_template_courses enable row level security;
alter table public.ysk_template_runs enable row level security;
revoke all on public.ysk_parameter_bank,public.ysk_trip_templates,public.ysk_trip_template_versions,public.ysk_template_courses,public.ysk_template_runs from public,anon,authenticated;
grant all on public.ysk_parameter_bank,public.ysk_trip_templates,public.ysk_trip_template_versions,public.ysk_template_courses,public.ysk_template_runs to service_role;
create or replace function public.ysk_save_template(p_org uuid,p_id uuid,p_expected integer,p_definition jsonb) returns jsonb language plpgsql security invoker set search_path='' as $$
declare current_revision integer;next_revision integer;
begin
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_org::text||p_id::text,0));
 select revision into current_revision from public.ysk_trip_templates where organization_id=p_org and id=p_id;
 if coalesce(current_revision,0)<>p_expected then return jsonb_build_object('status',409,'message','Turmalen er endret. Hent siste versjon først.');end if;
 next_revision:=coalesce(current_revision,0)+1;
 insert into public.ysk_trip_template_versions values(p_org,p_id,next_revision,p_definition);
 insert into public.ysk_trip_templates values(p_org,p_id,next_revision,p_definition->>'name',p_definition) on conflict(organization_id,id) do update set revision=excluded.revision,name=excluded.name,definition=excluded.definition;
 return jsonb_build_object('id',p_id,'revision',next_revision,'definition',p_definition);
end;$$;
revoke all on function public.ysk_save_template(uuid,uuid,integer,jsonb) from public,anon,authenticated;
grant execute on function public.ysk_save_template(uuid,uuid,integer,jsonb) to service_role;
create or replace function public.ysk_save_template_run(p_user uuid,p_body jsonb) returns jsonb language plpgsql security invoker set search_path='' as $$
declare m public.ysk_memberships;old public.ysk_template_runs;result public.ysk_template_runs;run_id uuid;expected integer;
begin
 select * into m from public.ysk_memberships where user_id=p_user and active;
 if m.user_id is null then return jsonb_build_object('status',403,'message','Ingen aktiv skoletilgang.');end if;
 run_id:=(p_body->>'id')::uuid;expected:=(p_body->>'expected_revision')::integer;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(run_id::text,0));
 select * into old from public.ysk_template_runs where id=run_id;
 if old.id is not null then
  if old.organization_id<>m.organization_id or (old.owner_id<>p_user and m.role<>'admin') then return jsonb_build_object('status',403,'message','Turen tilhører en annen bruker.');end if;
  if old.revision<>expected then
   if old.payload=p_body->'payload' then return to_jsonb(old);end if;
   return jsonb_build_object('status',409,'message','Turen er endret. Hent siste versjon.');
  end if;
  if old.template_id<>(p_body->>'template_id')::uuid or old.template_revision<>(p_body->>'template_revision')::integer then return jsonb_build_object('status',400,'message','Gamle turer beholder turmalen.');end if;
  update public.ysk_template_runs set payload=p_body->'payload',revision=revision+1,updated_at=now() where id=run_id returning * into result;
 else
  if expected<>0 then return jsonb_build_object('status',409,'message','Turen finnes ikke.');end if;
  insert into public.ysk_template_runs(id,organization_id,owner_id,template_id,template_revision,snapshot,payload) values(run_id,m.organization_id,p_user,(p_body->>'template_id')::uuid,(p_body->>'template_revision')::integer,p_body->'snapshot',p_body->'payload') returning * into result;
 end if;
 return to_jsonb(result);
end;$$;
revoke all on function public.ysk_save_template_run(uuid,jsonb) from public,anon,authenticated;
grant execute on function public.ysk_save_template_run(uuid,jsonb) to service_role;
