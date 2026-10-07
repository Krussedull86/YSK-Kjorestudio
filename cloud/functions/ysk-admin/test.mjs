import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const trips=fs.readFileSync(new URL('./trips.ts',import.meta.url),'utf8').replace('export async function','async function');
const source=trips+'\n'+fs.readFileSync(new URL('./updates.ts',import.meta.url),'utf8').replace('export async function','async function')+'\n'+fs.readFileSync(new URL('./index.ts',import.meta.url),'utf8').replace(/^import .*$/gm,'');
async function scenario({role='admin',active=true,valid=true,target=true,insertFails=false,created=true},body){
 let handler;const calls=[];
 const fetch=async(url,options={})=>{calls.push({url,options});let payload,status=200;
  if(url.endsWith('/auth/v1/user')){payload={id:'caller',user_metadata:{role:'admin'}};if(!valid)status=401;}
  else if(url.includes('ysk_memberships?user_id=eq.caller'))payload=[{user_id:'caller',organization_id:'school-A',role,active,display_name:'Admin'}];
  else if(url.endsWith('/auth/v1/admin/users')){payload=created?{id:'created-user'}:{message:'exists'};if(!created)status=409;}
  else if(url.endsWith('/rest/v1/ysk_memberships')){payload=[{}];if(insertFails)status=500;}
  else if(url.includes('user_id=eq.11111111-1111-4111-8111-111111111111'))payload=target?[{user_id:'target',role:'teacher'}]:[];
  else if(url.includes('/auth/v1/admin/users/created-user'))payload={};
  else payload=[];
  return new Response(JSON.stringify(payload),{status});
 };
 vm.runInNewContext(source,{Deno:{env:{get:k=>k==='SUPABASE_URL'?'https://school.example':'server-secret'},serve:f=>handler=f},fetch,Response,JSON,encodeURIComponent,String,Error});
 const response=await handler(new Request('https://school.example/functions/v1/ysk-admin',{method:'POST',headers:{Authorization:'Bearer user-token'},body:JSON.stringify(body)}));return {status:response.status,result:await response.json(),calls};
}
const create={action:'create',name:'Teacher',email:'teacher@example.com',password:'a-long-start-password',role:'teacher',organization_id:'attacker-school'};
let result=await scenario({role:'teacher'},create);assert.equal(result.status,403);assert(!result.calls.some(c=>c.url.endsWith('/auth/v1/admin/users')));
result=await scenario({active:false},create);assert.equal(result.status,403);
result=await scenario({valid:false},create);assert.equal(result.status,401);
result=await scenario({},create);assert.equal(result.status,200);const insert=result.calls.find(c=>c.url.endsWith('/rest/v1/ysk_memberships'));assert.equal(JSON.parse(insert.options.body).organization_id,'school-A');assert(!JSON.stringify(result.result).includes(create.password));
result=await scenario({}, {...create,password:'short'});assert.equal(result.status,400);
result=await scenario({}, {...create,role:'owner'});assert.equal(result.status,400);
result=await scenario({target:false},{action:'set_active',user_id:'11111111-1111-4111-8111-111111111111',active:false});assert.equal(result.status,403);
result=await scenario({insertFails:true},create);assert.equal(result.status,500);assert(result.calls.some(c=>c.options.method==='DELETE'));
result=await scenario({created:false},create);assert.equal(result.status,409);assert(!result.calls.some(c=>c.url.endsWith('/rest/v1/ysk_memberships')));
console.log('9 admin authorization and failure scenarios passed (mocked server).');
