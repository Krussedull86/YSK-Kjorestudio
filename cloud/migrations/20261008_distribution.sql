-- Delivery plans and immutable per-run snapshots; no additional user privileges.
create or replace function ysk_private.valid_distribution_plan(p jsonb)
returns boolean language plpgsql immutable set search_path='' as $$
declare n integer;t numeric;v numeric;prev numeric:=0;entry jsonb;
begin
 if jsonb_typeof(p)<>'object' or jsonb_typeof(p->'stop_count')<>'number' or jsonb_typeof(p->'expected_minutes')<>'number' or jsonb_typeof(p->'deadlines')<>'array' then return false;end if;
 n:=(p->>'stop_count')::integer;t:=(p->>'expected_minutes')::numeric;
 if (p->>'stop_count')::numeric<>n or n<0 or n>30 or t<0 or t>1440 or jsonb_array_length(p->'deadlines')<>n or n=0 and t<>0 or n>0 and t<=0 then return false;end if;
 for entry in select value from jsonb_array_elements(p->'deadlines') loop
  if jsonb_typeof(entry)<>'number' then return false;end if;v:=entry::numeric;
  if v<=prev or v>t then return false;end if;prev:=v;
 end loop;
 return true;
exception when others then return false;
end $$;
create or replace function ysk_private.valid_distribution_run(p jsonb)
returns boolean language plpgsql immutable set search_path='' as $$
declare n integer;i integer:=0;e jsonb;last_time numeric:=0;v numeric;f numeric;
begin
 if jsonb_typeof(p)<>'object' or p->'version'<>'1'::jsonb or jsonb_typeof(p->'deadlines')<>'array' then return false;end if;
 n:=jsonb_array_length(p->'deadlines');
 if n=0 or not ysk_private.valid_distribution_plan(jsonb_build_object('stop_count',n,'expected_minutes',p->'expected_minutes','deadlines',p->'deadlines')) or jsonb_typeof(p->'started_at')<>'number' or jsonb_typeof(p->'events')<>'array' then return false;end if;
 v:=(p->>'started_at')::numeric;if v<=0 or v>1e15 or v<>trunc(v) or jsonb_array_length(p->'events')>n then return false;end if;
 for e in select value from jsonb_array_elements(p->'events') loop
  i:=i+1;
  if jsonb_typeof(e)<>'object' or e->'stop'<>to_jsonb(i) or jsonb_typeof(e->'status')<>'string' or e->>'status' not in ('ramp','aborted') or jsonb_typeof(e->'elapsed_minutes')<>'number' or jsonb_typeof(e->'reason')<>'string' or length(e->>'reason')>300 then return false;end if;
  v:=(e->>'elapsed_minutes')::numeric;if v<last_time or v>43200 then return false;end if;last_time:=v;
 end loop;
 if not p ? 'finished_minutes' then return false;end if;
 if p->'finished_minutes'<>'null'::jsonb then
  if jsonb_typeof(p->'finished_minutes')<>'number' then return false;end if;
  f:=(p->>'finished_minutes')::numeric;if i<>n or f<last_time or f>43200 then return false;end if;
 end if;
 return true;
exception when others then return false;
end $$;
-- Require every key: SQL NULL must never turn a missing-key test into success.
create or replace function ysk_private.distribution_plan_checked(p jsonb)
returns boolean language sql immutable set search_path='' as $$
 select coalesce(p ?& array['stop_count','expected_minutes','deadlines'] and ysk_private.valid_distribution_plan(p),false)
$$;
create or replace function ysk_private.distribution_run_checked(p jsonb)
returns boolean language sql immutable set search_path='' as $$
 select coalesce(p ?& array['version','started_at','expected_minutes','deadlines','events','finished_minutes'] and ysk_private.valid_distribution_run(p)
 and not exists(select 1 from jsonb_array_elements(case when jsonb_typeof(p->'events')='array' then p->'events' else '[]'::jsonb end) e where not e ?& array['stop','status','elapsed_minutes','reason']),false)
$$;
revoke all on function ysk_private.valid_distribution_plan(jsonb),ysk_private.valid_distribution_run(jsonb),ysk_private.distribution_plan_checked(jsonb),ysk_private.distribution_run_checked(jsonb) from public;
grant execute on function ysk_private.valid_distribution_plan(jsonb),ysk_private.valid_distribution_run(jsonb),ysk_private.distribution_plan_checked(jsonb),ysk_private.distribution_run_checked(jsonb) to authenticated,service_role;
alter table public.ysk_course_setup add column if not exists distribution_plan jsonb not null default '{"stop_count":0,"expected_minutes":0,"deadlines":[]}';
alter table public.ysk_course_setup add constraint distribution_plan_shape check (ysk_private.distribution_plan_checked(distribution_plan));
alter table public.ysk_trips add constraint distribution_run_shape check (not payload ? 'distribution' or payload->'trip'='4'::jsonb and ysk_private.distribution_run_checked(payload->'distribution'));
