create or replace function public.ysk_set_release_channel(p_org uuid,p_channel text,p_release uuid) returns void language plpgsql security invoker set search_path='' as $$
declare target_build integer; current_build integer;
begin
 if p_channel not in ('dev','stable') then raise exception 'Invalid channel'; end if;
 perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_org::text||p_channel,0));
 select build into target_build from public.ysk_releases where id=p_release and organization_id=p_org and ready;
 if target_build is null then raise exception 'Release is not ready'; end if;
 select r.build into current_build from public.ysk_update_channels c join public.ysk_releases r on r.id=c.release_id where c.organization_id=p_org and c.channel=p_channel;
 if current_build>target_build then raise exception 'A newer release is already published'; end if;
 if p_channel='stable' then update public.ysk_releases set stable_at=coalesce(stable_at,now()) where id=p_release; end if;
 insert into public.ysk_update_channels(organization_id,channel,release_id,updated_at) values(p_org,p_channel,p_release,now()) on conflict(organization_id,channel) do update set release_id=excluded.release_id,updated_at=excluded.updated_at;
end; $$;
revoke all on function public.ysk_set_release_channel(uuid,text,uuid) from public,anon,authenticated;
grant execute on function public.ysk_set_release_channel(uuid,text,uuid) to service_role;
