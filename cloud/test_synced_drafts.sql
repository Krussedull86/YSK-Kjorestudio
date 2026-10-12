-- Exercise two devices, unidentified drafts, invalid data and stale edits; never retain test data.
begin;
set local role service_role;
do $$
declare u uuid; a uuid:=gen_random_uuid(); b uuid:=gen_random_uuid(); request_id uuid:=gen_random_uuid(); p jsonb; r jsonb; rev text;
begin
 select user_id into u from public.ysk_memberships where active and role='admin' limit 1;
 if u is null then raise exception 'An active test administrator is required'; end if;
 p:=jsonb_build_object('id',a,'driver','','course','','vehicle','','trip',1,'minutes','','km','','liters','','stops',0,'trafikksikkerhet','','avpassing','','økning','','komfort','','date','','start_time','08:15','end_time','09:40','teacher','','completion','incomplete');
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p,'revision',request_id));
 if r ? 'status' or r->'row'->'payload'->>'minutes'<>'' then raise exception 'Draft create failed: %',r; end if;
 rev:=r->'row'->>'revision';
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p,'revision',request_id));
 if r->'row'->>'revision'<>rev then raise exception 'Retry was not idempotent'; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p||jsonb_build_object('id',b)));
 if r ? 'status' then raise exception 'Unidentified drafts collided: %',r; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p||'{"minutes":85,"notes":"continued on PC"}'::jsonb,'expected_revision',rev));
 if r ? 'status' or r->'row'->'payload'->>'end_time'<>'09:40' then raise exception 'Draft edit lost time fields: %',r; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p||'{"notes":"stale phone"}'::jsonb,'expected_revision',rev));
 if (r->>'status')::int<>409 then raise exception 'Stale draft was accepted'; end if;
 select revision::text into rev from public.ysk_trips where id=a;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p||'{"minutes":-1}'::jsonb,'expected_revision',rev));
 if (r->>'status')::int<>400 then raise exception 'Invalid populated value was accepted'; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p||'{"komfort":"bad"}'::jsonb,'expected_revision',rev));
 if (r->>'status')::int<>400 then raise exception 'Invalid rating was accepted'; end if;
 r:=public.ysk_manage_trips(gen_random_uuid(),jsonb_build_object('action','trip_save','payload',p));
 if (r->>'status')::int<>403 then raise exception 'Unauthorized draft accepted'; end if;
end $$;
rollback;
