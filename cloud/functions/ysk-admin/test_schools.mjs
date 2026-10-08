import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const code=fs.readFileSync(new URL('./schools.ts',import.meta.url),'utf8').replaceAll('export async function','async function');const context={};vm.createContext(context);vm.runInContext(code,context);
const own='11111111-1111-4111-8111-111111111111',managed='22222222-2222-4222-8222-222222222222',foreign='33333333-3333-4333-8333-333333333333',user='44444444-4444-4444-8444-444444444444';
async function scenario(body,role='admin',divisionValid=true){const calls=[];const server=async(path,method='GET',payload)=>{calls.push({path,method,payload});if(path.includes('ysk_school_admins'))return [{organization_id:managed}];if(path.includes('ysk_divisions?id='))return divisionValid?[{id:'division'}]:[];if(path.includes('/rpc/ysk_assign_school'))return {message:'saved'};if(path.includes('/rpc/ysk_create_school'))return {id:managed,name:payload.p_name};return [];};const member={user_id:user,role,organization_id:own};return {result:await context.schoolAction(body,member,server),calls,server,member};}
for(const action of ['school_list','school_save','division_save','set_school']){const r=await scenario({action,name:'School',user_id:user},'teacher');assert.equal(r.result.status,403);assert.equal(r.calls.length,0);}
let r=await scenario({action:'school_list'});assert(r.calls.find(c=>c.path.includes('ysk_organizations')).path.includes(own+','+managed));assert(!r.calls.some(c=>c.path.includes(foreign)));
r=await scenario({action:'school_save',school_id:foreign,name:'Hijack'});assert.equal(r.result.status,403);assert(!r.calls.some(c=>c.method==='PATCH'));
r=await scenario({action:'school_save',name:' New school '});assert.equal(r.result.data.school.name,'New school');assert.equal(r.calls.find(c=>c.path.includes('rpc')).payload.p_actor,user);
r=await scenario({action:'school_save',name:'   '});assert.equal(r.result.status,400);
r=await scenario({action:'division_save',school_id:foreign,name:'No'});assert.equal(r.result.status,403);
r=await scenario({action:'division_save',school_id:managed,name:'Bodø'});assert.equal(r.calls.find(c=>c.method==='POST').payload.organization_id,managed);
r=await scenario({action:'set_school',school_id:foreign,user_id:user});assert.equal(r.result.status,403);assert(!r.calls.some(c=>c.path.includes('rpc')));
r=await scenario({action:'set_school',school_id:managed,division_id:'foreign-division',user_id:user},'admin',false);assert.equal(r.result.status,403);assert(!r.calls.some(c=>c.path.includes('rpc')));
r=await scenario({action:'set_school',school_id:managed,division_id:'division',user_id:user});assert.equal(r.calls.find(c=>c.path.includes('rpc')).payload.p_actor,user);assert.equal(r.calls.find(c=>c.path.includes('rpc')).payload.p_school,managed);
r=await scenario({action:'set_school',school_id:own,user_id:'invalid'});assert.equal(r.result.status,400);
r=await scenario({action:'school_list'});assert.equal(await context.schoolTarget({school_id:foreign},r.member,r.server),null);assert.equal((await context.schoolTarget({},r.member,r.server)).organization_id,own);
console.log('School/departments: roles, delegated scope, foreign-school rejection, validation and server identity passed.');
