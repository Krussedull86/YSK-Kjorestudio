-- Soft deletion retains tombstones for offline clients. Only the verified Edge
-- Function can invoke this transaction; the browser/app never gets a service key.
alter table public.ysk_trips add column if not exists deleted_at timestamptz;
alter table public.ysk_trips drop constraint if exists ysk_class_trip_unique;
alter table public.ysk_trips drop constraint if exists ysk_trips_owner_id_driver_course_vehicle_trip_key;
create unique index if not exists ysk_active_class_trip on public.ysk_trips(organization_id,driver,course,vehicle,trip) where deleted_at is null;
create unique index if not exists ysk_active_owner_trip on public.ysk_trips(owner_id,driver,course,vehicle,trip) where deleted_at is null;
drop policy if exists ysk_update on public.ysk_trips;
create policy ysk_update on public.ysk_trips for update to authenticated
 using(owner_id=(select auth.uid()) and organization_id=(select ysk_private.organization_for_user()) and deleted_at is null)
 with check(owner_id=(select auth.uid()) and organization_id=(select ysk_private.organization_for_user()) and deleted_at is null);
drop policy if exists ysk_insert on public.ysk_trips;
create policy ysk_insert on public.ysk_trips for insert to authenticated
 with check(owner_id=(select auth.uid()) and organization_id=(select ysk_private.organization_for_user()) and deleted_at is null);

create or replace function public.ysk_manage_trips(p_user uuid,p_body jsonb)
returns jsonb language plpgsql security invoker set search_path='' as $$
declare
 m public.ysk_memberships%rowtype; t public.ysk_trips%rowtype;
 a text:=p_body->>'action'; item jsonb:=p_body->'payload';
 ident uuid; rev uuid; kind text:=p_body->>'kind'; old_name text:=p_body->>'name'; new_name text:=btrim(p_body->>'new_name'); affected integer;
begin
 select * into m from public.ysk_memberships where user_id=p_user and active;
 if not found then return jsonb_build_object('status',403,'message','Ingen aktiv skoletilgang.'); end if;
 -- Serialize school writes, including name changes and restoration.
 perform pg_advisory_xact_lock(hashtextextended(m.organization_id::text,17));
 if a in ('catalog_rename','catalog_delete') then
  if m.role<>'admin' then return jsonb_build_object('status',403,'message','Bare admin kan endre kurs og biler.'); end if;
  if kind not in ('course','vehicle') or old_name is null or length(old_name)>100 then
   return jsonb_build_object('status',400,'message','Velg kurs eller bil.'); end if;
  if a='catalog_rename' then
   if new_name is null or length(new_name) not between 1 and 100 then return jsonb_build_object('status',400,'message','Navnet må ha 1–100 tegn.'); end if;
   update public.ysk_trips set course=case when kind='course' then new_name else course end,
    vehicle=case when kind='vehicle' then new_name else vehicle end,
    payload=jsonb_set(payload,array[kind],to_jsonb(new_name)),revision=gen_random_uuid()
    where organization_id=m.organization_id and deleted_at is null and (case when kind='course' then course else vehicle end)=old_name;
  else
   update public.ysk_trips set deleted_at=now(),revision=gen_random_uuid()
    where organization_id=m.organization_id and deleted_at is null and (case when kind='course' then course else vehicle end)=old_name;
  end if;
  get diagnostics affected=row_count;
  return jsonb_build_object('message',case when a='catalog_delete' then 'Turer flyttet til papirkurven.' else 'Navnet er endret på tilhørende turer.' end,'count',affected);
 end if;
 if a not in ('trip_save','trip_delete','trip_restore') then return jsonb_build_object('status',400,'message','Ukjent handling.'); end if;
 ident:=(case when a='trip_save' then item->>'id' else p_body->>'id' end)::uuid;
 rev:=coalesce(nullif(p_body->>'revision','')::uuid,gen_random_uuid());
 select * into t from public.ysk_trips where id=ident for update;
 if found then
  if t.organization_id is distinct from m.organization_id or (t.owner_id<>m.user_id and m.role<>'admin') then return jsonb_build_object('status',403,'message','Du kan bare endre egne turer i din skole.'); end if;
  if t.revision=rev then return jsonb_build_object('row',to_jsonb(t),'message','Lagret.'); end if;
  if coalesce(p_body->>'expected_revision','')<>t.revision::text then return jsonb_build_object('status',409,'message','Turen er endret siden du åpnet den. Hent ny versjon før du prøver igjen.'); end if;
  if a='trip_save' and t.deleted_at is not null then return jsonb_build_object('status',409,'message','Turen ligger i papirkurven. Gjenopprett den først.'); end if;
 elsif a<>'trip_save' or coalesce(p_body->>'expected_revision','')<>'' then
  return jsonb_build_object('status',404,'message','Turen finnes ikke lenger.');
 end if;
 if a='trip_save' then
  insert into public.ysk_trips(id,owner_id,organization_id,driver,course,vehicle,trip,revision,payload)
   values(ident,coalesce(t.owner_id,m.user_id),m.organization_id,item->>'driver',item->>'course',item->>'vehicle',(item->>'trip')::integer,rev,item)
   on conflict(id) do update set driver=excluded.driver,course=excluded.course,vehicle=excluded.vehicle,trip=excluded.trip,revision=excluded.revision,payload=excluded.payload;
 else
  update public.ysk_trips set deleted_at=case when a='trip_delete' then now() else null end,revision=rev where id=ident;
 end if;
 select * into t from public.ysk_trips where id=ident;
 return jsonb_build_object('row',to_jsonb(t),'message',case when a='trip_delete' then 'Turen er i papirkurven.' when a='trip_restore' then 'Turen er gjenopprettet.' else 'Turen er lagret.' end);
exception
 when unique_violation then return jsonb_build_object('status',409,'message','Sjåfør, kurs, bil og turnummer finnes allerede. Ingen endringer ble gjort.');
 when check_violation or invalid_text_representation or not_null_violation or numeric_value_out_of_range then return jsonb_build_object('status',400,'message','Kontroller turens felter og verdier. Ingen endringer ble gjort.');
end;
$$;
revoke all on function public.ysk_manage_trips(uuid,jsonb) from public,anon,authenticated;
grant execute on function public.ysk_manage_trips(uuid,jsonb) to service_role;
