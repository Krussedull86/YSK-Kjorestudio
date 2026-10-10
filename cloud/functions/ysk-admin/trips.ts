import {distributionPlan,validDistribution} from './distribution.ts';
// Called only after JWT verification and active school membership lookup.
export async function tripAction(body,member,server) {
 const action=body.action;
 if(action==='course_setup_list')return {data:{rows:await server('/rest/v1/ysk_course_setup?organization_id=eq.'+encodeURIComponent(member.organization_id)+'&select=name,active_trips,distribution_plan&order=name')}};
 if(action==='course_setup_save'){
  if(member.role!=='admin')return {status:403,data:{message:'Bare admin kan endre kursoppsett.'}};
  const name=String(body.name||'').trim(),count=Number(body.active_trips);
  if(!name||name.length>100||!Number.isInteger(count)||count<1||count>5)return {status:400,data:{message:'Velg kursnavn og 1–5 aktive turer.'}};
  const row={organization_id:member.organization_id,name,active_trips:count};
  if(body.distribution_plan!==undefined){try{row['distribution_plan']=distributionPlan(body.distribution_plan);}catch(e){return {status:400,data:{message:e.message}};}}
  await server('/rest/v1/ysk_course_setup','POST',row);
  return {data:{message:'Kursoppsettet er lagret.'}};
 }
 if(action==='trip_list'){
  const offset=Number(body.offset||0);if(!Number.isInteger(offset)||offset<0)return {status:400,data:{message:'Ugyldig side.'}};
  const scope='organization_id=eq.'+encodeURIComponent(member.organization_id)+(member.role==='admin'?'':'&owner_id=eq.'+encodeURIComponent(member.user_id));
  const rows=await server('/rest/v1/ysk_trips?'+scope+'&select=id,owner_id,payload,revision,deleted_at,updated_at&order=id&limit=500&offset='+offset);
  return {data:{rows}};
 }
 if(!['trip_save','trip_delete','trip_restore','catalog_rename','catalog_delete'].includes(action))return null;
 if(action.startsWith('catalog_')&&member.role!=='admin')return {status:403,data:{message:'Bare admin kan endre kurs og biler.'}};
 if(action==='trip_save'&&body.payload&&'distribution' in body.payload){try{if(body.payload.trip!==4)throw Error('Distribusjonslogg gjelder tur 4.');validDistribution(body.payload.distribution);}catch(e){return {status:400,data:{message:e.message}};}}
 const result=await server('/rest/v1/rpc/ysk_manage_trips','POST',{p_user:member.user_id,p_body:body});
 return {status:result.status||200,data:result};
}
