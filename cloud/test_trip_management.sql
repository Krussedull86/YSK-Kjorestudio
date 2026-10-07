-- Disposable transaction. Only synthetic trips are touched; always rollback.
begin;
do $$
declare u uuid; a uuid:=gen_random_uuid(); b uuid:=gen_random_uuid(); r jsonb; p jsonb; rev text; name text:='__test_'||gen_random_uuid()::text;
begin
 select user_id into u from public.ysk_memberships where active and role='admin' limit 1;
 if u is null then raise exception 'Test requires an active school administrator'; end if;
 p:=jsonb_build_object('id',a,'driver',name,'course',name||'A','vehicle',name,'trip',1,'minutes',60,'km',40,'liters',12,'stops',1,'trafikksikkerhet','Bra','avpassing','Middel','økning','Bra','komfort','Bra');
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p));
 if r ? 'status' then raise exception 'Create failed: %',r; end if;
 rev:=r->'row'->>'revision';
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p||'{"liters":10}'::jsonb,'expected_revision',rev));
 if (r->'row'->'payload'->>'liters')::numeric<>10 then raise exception 'Edit failed'; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p,'expected_revision',rev));
 if (r->>'status')::int<>409 then raise exception 'Stale write was allowed'; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_save','payload',p||jsonb_build_object('id',b,'course',name||'B')));
 if r ? 'status' then raise exception 'Second create failed'; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','catalog_rename','kind','course','name',name||'B','new_name',name||'A'));
 if (r->>'status')::int<>409 then raise exception 'Rename collision was allowed'; end if;
 select revision::text into rev from public.ysk_trips where id=a;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_delete','id',a,'expected_revision',rev));
 if r->'row'->>'deleted_at' is null then raise exception 'Delete failed'; end if;
 rev:=r->'row'->>'revision';
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','catalog_rename','kind','course','name',name||'B','new_name',name||'A'));
 if (r->>'count')::int<>1 then raise exception 'Rename failed'; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_restore','id',a,'expected_revision',rev));
 if (r->>'status')::int<>409 then raise exception 'Restore collision was allowed'; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','catalog_delete','kind','course','name',name||'A'));
 if (r->>'count')::int<>1 then raise exception 'Bulk delete failed'; end if;
 r:=public.ysk_manage_trips(u,jsonb_build_object('action','trip_restore','id',a,'expected_revision',rev));
 if r ? 'status' or r->'row'->>'deleted_at' is not null then raise exception 'Restore failed: %',r; end if;
 r:=public.ysk_manage_trips(gen_random_uuid(),jsonb_build_object('action','trip_save','payload',p));
 if (r->>'status')::int<>403 then raise exception 'Non-member allowed'; end if;
 if has_function_privilege('authenticated','public.ysk_manage_trips(uuid,jsonb)','execute') or not has_function_privilege('service_role','public.ysk_manage_trips(uuid,jsonb)','execute') then raise exception 'Incorrect RPC privileges'; end if;
end $$;
rollback;
