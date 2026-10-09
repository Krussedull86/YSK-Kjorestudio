-- Server-only inbox and credentials. All client operations pass verified membership checks.
create table public.ysk_feedback (
 id uuid primary key,organization_id uuid not null references public.ysk_organizations(id),owner_id uuid not null references auth.users(id),author text not null,
 kind text not null check(kind in ('suggestion','bug')),title text not null check(length(title) between 1 and 120),body text not null check(length(body) between 1 and 4000),
 platform text not null check(platform in ('android','windows')),version text not null check(length(version)<=40),device text not null default '' check(length(device)<=200),
 status text not null default 'open' check(status in ('open','working','resolved')),delivery text not null default 'pending' check(delivery in ('pending','sending','sent','failed','off')),
 delivery_error text not null default '',delivery_attempted_at timestamptz,created_at timestamptz not null default now()
);
create index ysk_feedback_school_date on public.ysk_feedback(organization_id,created_at desc,id);
create index ysk_feedback_user_date on public.ysk_feedback(owner_id,created_at desc);
create table public.ysk_feedback_hooks(organization_id uuid not null references public.ysk_organizations(id),kind text not null check(kind in ('suggestion','bug')),url text not null check(url='' or url ~ '^https://discord[.]com/api/webhooks/[0-9]+/[A-Za-z0-9_.-]+$'),primary key(organization_id,kind));
alter table public.ysk_feedback enable row level security;
alter table public.ysk_feedback_hooks enable row level security;
revoke all on public.ysk_feedback,public.ysk_feedback_hooks from public,anon,authenticated;
grant all on public.ysk_feedback,public.ysk_feedback_hooks to service_role;
create function public.ysk_submit_feedback(p_user uuid,p_body jsonb) returns jsonb language plpgsql security invoker set search_path='' as $$
declare m public.ysk_memberships%rowtype;r public.ysk_feedback%rowtype;ticket uuid;kind text;title text;message text;
begin
 select * into m from public.ysk_memberships where user_id=p_user and active;
 if not found then return '{"status":403,"message":"Ingen aktiv skoletilgang."}'::jsonb;end if;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended('feedback:'||p_user::text,0));
 begin ticket:=(p_body->>'id')::uuid;exception when others then return '{"status":400,"message":"Ugyldig meldingsnummer."}'::jsonb;end;
 if ticket is null then return '{"status":400,"message":"Meldingsnummer mangler."}'::jsonb;end if;
 select * into r from public.ysk_feedback where id=ticket;
 if found then
  if r.owner_id<>p_user or r.organization_id<>m.organization_id then return '{"status":409,"message":"Meldingsnummeret er i bruk."}'::jsonb;end if;
  return jsonb_build_object('row',to_jsonb(r),'created',false);
 end if;
 kind:=p_body->>'kind';title:=trim(p_body->>'title');message:=trim(p_body->>'body');
 if kind is null or kind not in ('suggestion','bug') or title is null or length(title) not between 1 and 120 or message is null or length(message) not between 1 and 4000 or coalesce(p_body->>'platform','') not in ('android','windows') or length(coalesce(p_body->>'version',''))>40 or length(coalesce(p_body->>'device',''))>200 then return '{"status":400,"message":"Velg type, tittel (maks 120) og melding (maks 4000 tegn)."}'::jsonb;end if;
 if (select count(*) from public.ysk_feedback where owner_id=p_user and created_at>now()-interval '1 hour')>=10 then return '{"status":429,"message":"Maks 10 meldinger per time. Prøv igjen senere."}'::jsonb;end if;
 insert into public.ysk_feedback(id,organization_id,owner_id,author,kind,title,body,platform,version,device) values(ticket,m.organization_id,p_user,coalesce(m.display_name,''),kind,title,message,p_body->>'platform',coalesce(p_body->>'version',''),coalesce(p_body->>'device','')) returning * into r;
 return jsonb_build_object('row',to_jsonb(r),'created',true);
exception when unique_violation then return '{"status":409,"message":"Meldingsnummeret er i bruk."}'::jsonb;
end $$;
revoke all on function public.ysk_submit_feedback(uuid,jsonb) from public,anon,authenticated;
grant execute on function public.ysk_submit_feedback(uuid,jsonb) to service_role;
