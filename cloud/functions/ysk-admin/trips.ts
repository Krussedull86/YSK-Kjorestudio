// Called only after JWT verification and active school membership lookup.
export async function tripAction(body,member,server) {
 const action=body.action;
 if(action==='trip_list'){
  const offset=Number(body.offset||0);if(!Number.isInteger(offset)||offset<0)return {status:400,data:{message:'Ugyldig side.'}};
  const scope='organization_id=eq.'+encodeURIComponent(member.organization_id)+(member.role==='admin'?'':'&owner_id=eq.'+encodeURIComponent(member.user_id));
  const rows=await server('/rest/v1/ysk_trips?'+scope+'&select=id,owner_id,payload,revision,deleted_at,updated_at&order=id&limit=500&offset='+offset);
  return {data:{rows}};
 }
 if(!['trip_save','trip_delete','trip_restore','catalog_rename','catalog_delete'].includes(action))return null;
 if(action.startsWith('catalog_')&&member.role!=='admin')return {status:403,data:{message:'Bare admin kan endre kurs og biler.'}};
 const result=await server('/rest/v1/rpc/ysk_manage_trips','POST',{p_user:member.user_id,p_body:body});
 return {status:result.status||200,data:result};
}
