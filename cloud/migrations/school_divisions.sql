create table public.ysk_school_admins (
 user_id uuid not null references auth.users(id) on delete cascade,
 organization_id uuid not null references public.ysk_organizations(id),
 primary key(user_id,organization_id));
create table public.ysk_divisions (
 id uuid primary key default gen_random_uuid(),
 organization_id uuid not null references public.ysk_organizations(id),
 name text not null check(length(name) between 1 and 100),
 unique(organization_id,name), unique(id,organization_id));
alter table public.ysk_memberships add column division_id uuid;
alter table public.ysk_memberships add constraint ysk_member_division_school foreign key(division_id,organization_id) references public.ysk_divisions(id,organization_id);
alter table public.ysk_school_admins enable row level security;
alter table public.ysk_divisions enable row level security;
revoke all on public.ysk_school_admins,public.ysk_divisions from anon,authenticated;
grant all on public.ysk_school_admins,public.ysk_divisions to service_role;
create function public.ysk_create_school(p_actor uuid,p_name text) returns jsonb language plpgsql security invoker set search_path='' as $$
declare school public.ysk_organizations;
begin
 if not exists(select 1 from public.ysk_memberships where user_id=p_actor and role='admin' and active) then raise exception 'Admin required';end if;
 if length(trim(p_name)) not between 1 and 100 then raise exception 'Invalid name';end if;
 insert into public.ysk_organizations(name) values(trim(p_name)) returning * into school;
 insert into public.ysk_school_admins values(p_actor,school.id);
 return jsonb_build_object('id',school.id,'name',school.name);
end;$$;
create function public.ysk_assign_school(p_actor uuid,p_user uuid,p_school uuid,p_division uuid default null) returns jsonb language plpgsql security invoker set search_path='' as $$
declare actor public.ysk_memberships; target public.ysk_memberships;
begin
 select * into actor from public.ysk_memberships where user_id=p_actor and active and role='admin' for update;
 if not found then return jsonb_build_object('status',403,'message','Bare admin kan tildele skole.');end if;
 select * into target from public.ysk_memberships where user_id=p_user for update;
 if not found then return jsonb_build_object('status',404,'message','Brukeren finnes ikke.');end if;
 if (target.organization_id<>actor.organization_id and not exists(select 1 from public.ysk_school_admins where user_id=p_actor and organization_id=target.organization_id)) or
 (p_school<>actor.organization_id and not exists(select 1 from public.ysk_school_admins where user_id=p_actor and organization_id=p_school)) then
 return jsonb_build_object('status',403,'message','Du kan bare tildele brukere i skoler du administrerer.');end if;
 if p_division is not null and not exists(select 1 from public.ysk_divisions where id=p_division and organization_id=p_school) then return jsonb_build_object('status',400,'message','Avdelingen tilhører ikke skolen.');end if;
 if target.organization_id<>p_school and target.role='admin' then return jsonb_build_object('status',409,'message','Administratorkontoer kan ikke flyttes til en annen skole. Opprett en admin i den nye skolen.');end if;
 update public.ysk_memberships set organization_id=p_school,division_id=p_division where user_id=p_user;
 return jsonb_build_object('message','Skole og avdeling er lagret. Tidligere turer beholdes i opprinnelig skole.');
end;$$;
revoke all on function public.ysk_create_school(uuid,text),public.ysk_assign_school(uuid,uuid,uuid,uuid) from public,anon,authenticated;
grant execute on function public.ysk_create_school(uuid,text),public.ysk_assign_school(uuid,uuid,uuid,uuid) to service_role;
