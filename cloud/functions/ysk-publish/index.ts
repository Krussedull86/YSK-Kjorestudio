// GitHub OIDC publisher: dev only. Activate after filling the new repository ID.
import { updateAction } from '../ysk-admin/updates.ts';
const REPOSITORY='Krussedull86/YSK-Kjorestudio';
const REPOSITORY_ID='1408989746';
const OWNER_ID='231093498',AUD='ysk-dev-publisher';
const base=Deno.env.get('SUPABASE_URL'),secret=Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
const decode=part=>Uint8Array.from(atob(part.replace(/-/g,'+').replace(/_/g,'/').padEnd(Math.ceil(part.length/4)*4,'=')),c=>c.charCodeAt(0));
export async function authorize(token,fetchKeys=fetch,now=Math.floor(Date.now()/1000)){
 const parts=token.split('.');if(parts.length!==3)throw Error('JWT');
 const header=JSON.parse(new TextDecoder().decode(decode(parts[0]))),claims=JSON.parse(new TextDecoder().decode(decode(parts[1])));
 if(header.alg!=='RS256'||typeof header.kid!=='string')throw Error('Algorithm');
 if(claims.iss!=='https://token.actions.githubusercontent.com'||claims.aud!==AUD||!Number.isInteger(claims.exp)||claims.exp<=now||!Number.isInteger(claims.nbf)||claims.nbf>now+30||!Number.isInteger(claims.iat)||claims.iat>now+30||now-claims.iat>600)throw Error('Issuer or lifetime');
 if(claims.repository!==REPOSITORY||claims.repository_id!==REPOSITORY_ID||claims.repository_owner_id!==OWNER_ID||claims.ref!=='refs/heads/dev'||claims.sub!=='repo:Krussedull86@'+OWNER_ID+'/YSK-Kjorestudio@'+REPOSITORY_ID+':ref:refs/heads/dev'||claims.workflow_ref!==REPOSITORY+'/.github/workflows/dev.yml@refs/heads/dev'||!['push','workflow_dispatch'].includes(claims.event_name))throw Error('Repository or workflow');
 const response=await fetchKeys('https://token.actions.githubusercontent.com/.well-known/jwks',{redirect:'error'});if(!response.ok)throw Error('Keys');
 const jwk=(await response.json()).keys.find(k=>k.kid===header.kid&&k.kty==='RSA'&&k.alg==='RS256');if(!jwk)throw Error('Key');
 const key=await crypto.subtle.importKey('jwk',jwk,{name:'RSASSA-PKCS1-v1_5',hash:'SHA-256'},false,['verify']);
 if(!await crypto.subtle.verify('RSASSA-PKCS1-v1_5',key,decode(parts[2]),new TextEncoder().encode(parts[0]+'.'+parts[1])))throw Error('Signature');return claims;
}
async function server(path,method='GET',body){const r=await fetch(base+path,{method,headers:{apikey:secret,Authorization:'Bearer '+secret,'Content-Type':'application/json',Prefer:'resolution=merge-duplicates,return=representation'},body:body===undefined?undefined:JSON.stringify(body)});const raw=await r.text();if(!r.ok)throw Error('Service');return raw?JSON.parse(raw):null;}
Deno.serve(async req=>{
 if(req.method!=='POST')return reply({message:'POST required'},405);
 try{await authorize((req.headers.get('Authorization')||'').replace(/^Bearer /,''));}catch{return reply({message:'GitHub identity rejected'},401);}
 try{
  const raw=await req.text();if(raw.length>12000)return reply({message:'Too large'},413);const body=JSON.parse(raw);
  if(!['release_prepare','release_commit'].includes(body.action))return reply({message:'Only dev publication is permitted'},403);
  const rows=await server('/rest/v1/ysk_memberships?email=eq.napster1986%40hotmail.com&role=eq.admin&active=eq.true&select=organization_id,role,update_channel');if(rows.length!==1)return reply({message:'School publisher is unavailable'},403);
  const result=await updateAction(body,rows[0],server,base,secret);return reply(result.data,result.status||200);
 }catch{return reply({message:'Publication failed'},503);}
});
