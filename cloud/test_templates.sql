begin;
set local role service_role;
do $$
declare m public.ysk_memberships;t uuid:=gen_random_uuid();r uuid:=gen_random_uuid();a jsonb;b jsonb;definition jsonb;body jsonb;
begin
 select * into m from public.ysk_memberships where active limit 1;
 if m.user_id is null then raise exception 'No test membership';end if;
 definition:='{"name":"Rollback test","base_trip":null,"parameters":[{"id":"x","label":"Test","type":"text","required":false,"weight":0}]}';
 a:=public.ysk_save_template(m.organization_id,t,0,definition);if (a->>'revision')::int<>1 then raise exception 'Template save';end if;
 a:=public.ysk_save_template(m.organization_id,t,0,definition);if (a->>'status')::int<>409 then raise exception 'Template CAS';end if;
 body:=jsonb_build_object('id',r,'expected_revision',0,'template_id',t,'template_revision',1,'snapshot',definition,'payload','{"driver":"Test","course":"Test","vehicle":"Test","date":"2026-10-10","values":{"x":"old"},"complete":false}'::jsonb);
 a:=public.ysk_save_template_run(m.user_id,body);if (a->>'revision')::int<>1 or a->>'organization_id'<>m.organization_id::text then raise exception 'Run save';end if;
 b:=public.ysk_save_template_run(m.user_id,body);if b->>'id'<>a->>'id' or b->>'revision'<>'1' then raise exception 'Idempotency';end if;
 a:=public.ysk_save_template(m.organization_id,t,1,jsonb_set(definition,'{name}','"New"'));if (a->>'revision')::int<>2 then raise exception 'New version';end if;
 body:=jsonb_set(body,'{expected_revision}','1');body:=jsonb_set(body,'{payload,values,x}','"new"');b:=public.ysk_save_template_run(m.user_id,body);if b->>'revision'<>'2' or b->'snapshot'<>definition then raise exception 'Old snapshot changed';end if;
 if has_table_privilege('authenticated','public.ysk_template_runs','SELECT') or has_table_privilege('anon','public.ysk_trip_templates','SELECT') or has_function_privilege('authenticated','public.ysk_save_template(uuid,uuid,integer,jsonb)','EXECUTE') then raise exception 'Public access';end if;
end $$;
rollback;
