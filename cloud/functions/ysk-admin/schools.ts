// Membership permissions are read from server-owned tables, never JWT user metadata.
export async function managedSchools(member,server){
 const ids=[member.organization_id];
 if(member.role==='admin')for(const row of await server('/rest/v1/ysk_school_admins?user_id=eq.'+encodeURIComponent(member.user_id)+'&select=organization_id'))ids.push(row.organization_id);
 return [...new Set(ids)];
}
export async function schoolTarget(body,member,server){
 const id=body.school_id||member.organization_id;
 if(!(await managedSchools(member,server)).includes(id))return null;
 const division=body.division_id||null;
 if(division){const rows=await server('/rest/v1/ysk_divisions?id=eq.'+encodeURIComponent(division)+'&organization_id=eq.'+encodeURIComponent(id)+'&select=id');if(!rows.length)return null;}
 return {organization_id:id,division_id:division};
}
export async function schoolAction(body,member,server){
 if(!['school_list','school_save','division_save','set_school'].includes(body.action))return null;
 if(member.role!=='admin')return {status:403,data:{message:'Bare admin kan administrere skoler og avdelinger.'}};
 const ids=await managedSchools(member,server),scope='organization_id=in.('+ids.map(encodeURIComponent).join(',')+')';
 if(body.action==='school_list')return {data:{schools:await server('/rest/v1/ysk_organizations?id=in.('+ids.map(encodeURIComponent).join(',')+')&select=id,name&order=name'),divisions:await server('/rest/v1/ysk_divisions?'+scope+'&select=id,organization_id,name&order=name')}};
 if(body.action==='set_school'){
  if(!/^[0-9a-f-]{36}$/i.test(String(body.user_id)))return {status:400,data:{message:'Ugyldig bruker.'}};
  const target=await schoolTarget(body,member,server);if(!target)return {status:403,data:{message:'Velg en skole og avdeling du administrerer.'}};
  const result=await server('/rest/v1/rpc/ysk_assign_school','POST',{p_actor:member.user_id,p_user:body.user_id,p_school:target.organization_id,p_division:target.division_id});return {status:result.status||200,data:result};
 }
 const name=String(body.name||'').trim();if(!name||name.length>100)return {status:400,data:{message:'Navn må være mellom 1 og 100 tegn.'}};
 if(body.action==='school_save'){
  if(body.school_id){if(!ids.includes(body.school_id))return {status:403,data:{message:'Ingen administratortilgang til skolen.'}};await server('/rest/v1/ysk_organizations?id=eq.'+encodeURIComponent(body.school_id),'PATCH',{name});return {data:{message:'Skolen er oppdatert.'}};}
  const school=await server('/rest/v1/rpc/ysk_create_school','POST',{p_actor:member.user_id,p_name:name});return {data:{message:'Skolen er opprettet.',school}};
 }
 const target=await schoolTarget({...body,division_id:null},member,server);if(!target)return {status:403,data:{message:'Ingen administratortilgang til skolen.'}};
 if(body.division_id){const rows=await server('/rest/v1/ysk_divisions?id=eq.'+encodeURIComponent(body.division_id)+'&organization_id=eq.'+encodeURIComponent(target.organization_id),'PATCH',{name});if(!rows.length)return {status:404,data:{message:'Avdelingen finnes ikke i skolen.'}};}
 else await server('/rest/v1/ysk_divisions','POST',{organization_id:target.organization_id,name});return {data:{message:'Avdelingen er lagret.'}};
}
