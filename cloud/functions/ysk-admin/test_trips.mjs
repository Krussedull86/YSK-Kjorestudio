import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const validators=fs.readFileSync(new URL('./distribution.ts',import.meta.url),'utf8').replaceAll('export function','function');
const source=fs.readFileSync(new URL('./trips.ts',import.meta.url),'utf8').replace('export async function','async function').replace(/^import .*$/gm,'');
const context={Number,encodeURIComponent};vm.createContext(context);vm.runInContext(validators+source,context);
const calls=[];const server=async(path,method,body)=>{calls.push({path,method,body});return path.includes('/rpc/')?{status:409,message:'Conflict'}:[];};
const member={user_id:'verified-user',organization_id:'verified-school',role:'teacher'};
let result=await context.tripAction({action:'catalog_delete',kind:'course'},member,server);assert.equal(result.status,403);assert.equal(calls.length,0);
result=await context.tripAction({action:'trip_list',organization_id:'attacker',user_id:'attacker'},member,server);
assert(calls[0].path.includes('organization_id=eq.verified-school'));assert(calls[0].path.includes('owner_id=eq.verified-user'));assert(!calls[0].path.includes('attacker'));
result=await context.tripAction({action:'trip_save',p_user:'attacker',payload:{id:'test'}},member,server);assert.equal(result.status,409);assert.equal(calls[1].body.p_user,'verified-user');
calls.length=0;await context.tripAction({action:'trip_list'}, {...member,role:'admin'},server);assert(!calls[0].path.includes('owner_id=eq.'));
result=await context.tripAction({action:'trip_list',offset:-1},member,server);assert.equal(result.status,400);
assert.equal(await context.tripAction({action:'me'},member,server),null);
console.log('Trip permissions, verified identity, school isolation, paging and conflict response passed.');
calls.length=0;result=await context.tripAction({action:'course_setup_save',name:'YSK',active_trips:3},member,server);assert.equal(result.status,403);assert.equal(calls.length,0);
result=await context.tripAction({action:'course_setup_list',organization_id:'attacker'},member,server);assert(calls[0].path.includes('organization_id=eq.verified-school'));assert(!calls[0].path.includes('attacker'));
for(const active_trips of [0,6,1.5]){result=await context.tripAction({action:'course_setup_save',name:'YSK',active_trips},{...member,role:'admin'},server);assert.equal(result.status,400);}
calls.length=0;result=await context.tripAction({action:'course_setup_save',name:'YSK',active_trips:3,organization_id:'attacker'},{...member,role:'admin'},server);assert.equal(calls[0].body.organization_id,'verified-school');assert.equal(calls[0].body.active_trips,3);
console.log('Course setup validation, admin authorization and school scope passed.');
