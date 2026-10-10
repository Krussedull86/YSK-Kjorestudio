-- Synthetic records only; no real trips changed. Always roll back.
begin;
set local role service_role;
do $$
declare u uuid;org uuid;test_id uuid:=gen_random_uuid();test_name text:='__dist_test_'||gen_random_uuid()::text;p jsonb;r jsonb;log jsonb;
begin
 select user_id,organization_id into u,org from public.ysk_memberships where active and role='admin' limit 1;
 if u is null then raise exception 'Requires an active administrator';end if;
 log:='{"version":1,"started_at":1791486000000,"expected_minutes":60,"deadlines":[20,40,60],"events":[{"stop":1,"status":"ramp","elapsed_minutes":18,"reason":""},{"stop":2,"status":"aborted","elapsed_minutes":43,"reason":"Stengt rampe"},{"stop":3,"status":"ramp","elapsed_minutes":68,"reason":""}],"finished_minutes":70}';
 insert into public.ysk_course_setup(organization_id,name,active_trips,distribution_plan) values(org,test_name,5,'{"stop_count":3,"expected_minutes":60,"deadlines":[20,40,60]}');
 p:=jsonb_build_object('id',test_id,'driver',test_name,'course',test_name,'vehicle',test_name,'trip',4,'minutes',70,'km',40,'liters',12,'stops',1,'trafikksikkerhet','Bra','avpassing','Bra','økning','Bra','komfort','Bra','distribution',log);
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p));
 if r ? 'status' or r->'row'->'payload'->'distribution'<>log then raise exception 'Distribution create failed: %',r;end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p||'{"notes":"Updated rating review"}'::jsonb,'expected_revision',r->'row'->>'revision'));
 if r ? 'status' or r->'row'->'payload'->'distribution'<>log then raise exception 'Distribution edit failed: %',r;end if;
 begin
  update public.ysk_trips set payload=jsonb_set(payload,'{distribution,events,1,status}','null'::jsonb) where ysk_trips.id=test_id;
  raise exception 'Null status accepted';
 exception when check_violation then null;end;
 begin
  update public.ysk_trips set payload=jsonb_set(payload,'{trip}','1') where ysk_trips.id=test_id;
  raise exception 'Distribution on optimal trip accepted';
 exception when check_violation then null;end;
 begin
  update public.ysk_course_setup set distribution_plan='{"stop_count":2,"expected_minutes":60,"deadlines":[40,20]}' where organization_id=org and ysk_course_setup.name=test_name;
  raise exception 'Reversed deadlines accepted';
 exception when check_violation then null;end;
end $$;
rollback;
