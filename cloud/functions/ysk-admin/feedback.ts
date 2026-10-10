const feedbackKinds=['suggestion','bug'];
const feedbackUUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export function feedbackHook(url){return typeof url==='string'&&url.length<=512&&(url===''||/^https:\/\/discord\.com\/api\/webhooks\/[0-9]+\/[A-Za-z0-9_.-]+$/.test(url));}
async function deliverFeedback(row,server,send){
 const scope='/rest/v1/ysk_feedback?id=eq.'+row.id+'&organization_id=eq.'+row.organization_id;
 const locks=await server(scope+'&delivery=neq.sent&or=(delivery.neq.sending,delivery_attempted_at.lt.'+encodeURIComponent(new Date(Date.now()-60000).toISOString())+')','PATCH',{delivery:'sending',delivery_attempted_at:new Date().toISOString(),delivery_error:''});
 if(!locks.length)return;
 const hooks=await server('/rest/v1/ysk_feedback_hooks?organization_id=eq.'+row.organization_id+'&kind=eq.'+row.kind+'&select=url');let delivery='off',error='';
 if(hooks[0]?.url){
  try{if(!feedbackHook(hooks[0].url))throw Error('Ugyldig webhook.');
   const response=await send(hooks[0].url+'?wait=true',{method:'POST',headers:{'Content-Type':'application/json'},redirect:'error',signal:AbortSignal.timeout(10000),body:JSON.stringify({username:'YSK Kjørestudio',allowed_mentions:{parse:[]},embeds:[{title:(row.kind==='bug'?'Feilmelding: ':'Forslag: ')+row.title,description:row.body.slice(0,3500),color:row.kind==='bug'?13772855:4890813,fields:[{name:'Avsender',value:row.author||'Lærer'},{name:'Program',value:row.platform+' · '+(row.version||'ukjent')},{name:'Enhet',value:row.device||'Ikke oppgitt'},{name:'Meldingsnummer',value:row.id}],footer:{text:row.body.length>3500?'Hele meldingen finnes i adminpanelet.':'Hele meldingen er også lagret i adminpanelet.'}}]})});
   if(!response.ok)throw Error('Discord svarte HTTP '+response.status);delivery='sent';
  }catch{delivery='failed';error='Discord kunne ikke nås eller avviste meldingen. Admin kan prøve igjen.';}
 }
 await server(scope,'PATCH',{delivery,delivery_error:error});
}
export async function feedbackAction(body,member,server,send=fetch){
 if(!String(body.action||'').startsWith('feedback_'))return null;
 const org=encodeURIComponent(member.organization_id);
 if(body.action==='feedback_submit'){
  const result=await server('/rest/v1/rpc/ysk_submit_feedback','POST',{p_user:member.user_id,p_body:body});
  if(result.status)return {status:result.status,data:{message:result.message}};
  if(result.created){try{await deliverFeedback(result.row,server,send);}catch{ /* Persisted inbox is the source of truth, even if Discord fails. */ }}
  return {data:{id:result.row.id,message:'Meldingen er lagret i adminpanelet.'}};
 }
 if(member.role!=='admin')return {status:403,data:{message:'Bare admin kan lese innboksen og styre Discord.'}};
 if(body.action==='feedback_list'){
  const offset=Number(body.offset||0);if(!Number.isInteger(offset)||offset<0)return {status:400,data:{message:'Ugyldig side.'}};
  return {data:{rows:await server('/rest/v1/ysk_feedback?organization_id=eq.'+org+'&order=created_at.desc,id&limit=100&offset='+offset)}};
 }
 if(body.action==='feedback_hooks_get'){
  const rows=await server('/rest/v1/ysk_feedback_hooks?organization_id=eq.'+org+'&select=kind,url');
  return {data:{hooks:feedbackKinds.map(kind=>({kind,enabled:!!rows.find(r=>r.kind===kind)?.url}))}};
 }
 if(body.action==='feedback_hooks_save'){
  if(!feedbackKinds.includes(body.kind)||!feedbackHook(body.url))return {status:400,data:{message:'Bruk en Discord-webhook fra https://discord.com/api/webhooks/…'}};
  await server('/rest/v1/ysk_feedback_hooks','POST',{organization_id:member.organization_id,kind:body.kind,url:body.url});return {data:{message:body.url?'Discord-webhook lagret.':'Discord-webhook deaktivert.'}};
 }
 if(['feedback_status','feedback_retry'].includes(body.action)){
  if(!feedbackUUID.test(String(body.id)))return {status:400,data:{message:'Ugyldig meldingsnummer.'}};
  const path='/rest/v1/ysk_feedback?id=eq.'+body.id+'&organization_id=eq.'+org,rows=await server(path);
  if(!rows.length)return {status:404,data:{message:'Meldingen finnes ikke i din skole.'}};
  if(body.action==='feedback_retry'){if(rows[0].delivery==='sent')return {data:{message:'Meldingen er allerede sendt til Discord.'}};await deliverFeedback(rows[0],server,send);return {data:{message:'Leveringsstatus er oppdatert.'}};}
  if(!['open','working','resolved'].includes(body.status))return {status:400,data:{message:'Ugyldig status.'}};
  await server(path,'PATCH',{status:body.status});return {data:{message:'Status oppdatert.'}};
 }
 return {status:400,data:{message:'Ukjent tilbakemeldingshandling.'}};
}
