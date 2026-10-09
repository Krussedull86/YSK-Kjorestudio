-- Synthetic transaction, tested as the trusted server role; always rolls back.
begin;
set local role service_role;
do $$
declare u uuid;org uuid;ticket uuid:=gen_random_uuid();result jsonb;payload jsonb;i integer;
begin
 select user_id,organization_id into u,org from public.ysk_memberships where active limit 1;
 payload:=jsonb_build_object('id',ticket,'kind','bug','title','__feedback_test','body','Synthetic test','platform','android','version','test','organization_id',gen_random_uuid(),'author','Spoof');
 result:=public.ysk_submit_feedback(u,payload);
 if result ? 'status' or result->'row'->>'organization_id'<>org::text or result->'row'->>'author'='Spoof' or not (result->>'created')::boolean then raise exception 'Create/school/author check failed';end if;
 result:=public.ysk_submit_feedback(u,payload);
 if result ? 'status' or (result->>'created')::boolean then raise exception 'Duplicate submission was not idempotent';end if;
 result:=public.ysk_submit_feedback(gen_random_uuid(),payload);
 if result->>'status'<>'403' then raise exception 'Inactive/nonmember accepted';end if;
 result:=public.ysk_submit_feedback(u,payload||jsonb_build_object('id',gen_random_uuid(),'body',''));
 if result->>'status'<>'400' then raise exception 'Empty message accepted';end if;
 for i in 2..10 loop
  result:=public.ysk_submit_feedback(u,payload||jsonb_build_object('id',gen_random_uuid()));
  if result ? 'status' then raise exception 'Rate limit triggered too early';end if;
 end loop;
 result:=public.ysk_submit_feedback(u,payload||jsonb_build_object('id',gen_random_uuid()));
 if result->>'status'<>'429' then raise exception 'Hourly rate limit missing';end if;
 result:=public.ysk_submit_feedback(u,payload);if result ? 'status' or (result->>'created')::boolean then raise exception 'Idempotent retry rejected at rate limit';end if;
 if has_table_privilege('authenticated','public.ysk_feedback','select') or has_table_privilege('anon','public.ysk_feedback_hooks','select') or has_function_privilege('authenticated','public.ysk_submit_feedback(uuid,jsonb)','execute') then raise exception 'Unexpected client access';end if;
end $$;
rollback;
