import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';import {webcrypto} from 'node:crypto';
const source=fs.readFileSync(new URL('./updates.ts',import.meta.url),'utf8').replace('export async function','async function');
const context={crypto:webcrypto,fetch:async()=>new Response('bad'),Response};vm.createContext(context);vm.runInContext(source,context);const action=context.updateAction;
const release={id:'release-A',version:'1.3.0',build:4,ready:true,notes:'Test',created_at:'2026-10-07',assets:{android:{name:'app.apk',path:'school-A/release-A/app.apk',sha256:'a'.repeat(64),size:3}}};
async function scenario(body,{role='admin',channel='dev',ready=true,pointer=true}={}){
 const calls=[];const server=async(path,method='GET',payload)=>{calls.push({path,method,payload});if(path.includes('ysk_update_channels'))return pointer?[{release_id:'release-A'}]:[];if(path.includes('ysk_releases'))return [{...release,ready}];if(path.includes('ysk_memberships'))return [];if(path.includes('/object/sign/'))return {signedURL:'/object/sign/ysk-updates/private?token=token'};return null;};
 return {result:await action(body,{organization_id:'school-A',role,update_channel:channel},server,'https://school.test','secret'),calls};
}
for(const name of ['set_channel','release_prepare','release_commit','release_promote','release_list']){const r=await scenario({action:name},{role:'teacher'});assert.equal(r.result.status,403);assert.equal(r.calls.length,0);}
let r=await scenario({action:'update_check',platform:'android'},{role:'teacher',channel:'stable'});assert.equal(r.result.data.channel,'stable');assert.equal(r.result.data.release.id,'release-A');assert(r.calls[0].path.includes('channel=eq.stable'));assert(!JSON.stringify(r.result).includes('secret'));assert(!JSON.stringify(r.result).includes('app.apk?'));
r=await scenario({action:'update_check',platform:'android'},{pointer:false});assert.equal(r.result.data.release,null);assert.equal(r.calls.length,2);
r=await scenario({action:'download_update',platform:'android',release_id:'obsolete'});assert.equal(r.result.status,409);assert(!r.calls.some(c=>c.path.includes('/object/sign/')));
r=await scenario({action:'set_channel',channel:'owner',user_id:'11111111-1111-4111-8111-111111111111'});assert.equal(r.result.status,400);
r=await scenario({action:'set_channel',channel:'dev',user_id:'11111111-1111-4111-8111-111111111111'});assert.equal(r.result.status,404);assert(r.calls[0].path.includes('organization_id=eq.school-A'));
r=await scenario({action:'release_commit',release_id:'release-A'});let rpc=r.calls.find(c=>c.path.includes('/rpc/'));assert.equal(rpc.payload.p_channel,'dev');assert.equal(rpc.payload.p_release,'release-A');assert(!r.calls.some(c=>c.payload?.p_channel==='stable'));
r=await scenario({action:'release_promote',release_id:'release-A'});assert.equal(r.result.status,400);assert(!r.calls.some(c=>c.path.includes('/rpc/')));
r=await scenario({action:'release_promote',release_id:'release-A',confirm:'stable'},{ready:false});assert.equal(r.result.status,400);
r=await scenario({action:'release_promote',release_id:'release-A',confirm:'stable'});rpc=r.calls.find(c=>c.path.includes('/rpc/'));assert.equal(rpc.payload.p_channel,'stable');assert.equal(rpc.payload.p_release,'release-A');assert(!r.calls.some(c=>c.payload?.assets));
r=await scenario({action:'release_commit',release_id:'release-A'},{ready:false});assert.equal(r.result.status,409);assert(!r.calls.some(c=>c.path.includes('/rpc/')));
r=await scenario({action:'release_prepare',version:'1.3.2',build:6,assets:{android:{size:50000001,sha256:'a'.repeat(64)}}});assert.equal(r.result.status,400);assert.equal(r.calls.length,0);
console.log('Update authorization, channel isolation, stale release, immutable promotion and bad hash scenarios passed.');
// Partial releases preserve the untouched platform's version and download identity.
for(const platform of ['android','windows'])for(const channel of ['dev','stable']){
 const old={...release,id:'old-'+platform,build:3,version:'1.2.9',assets:{[platform]:release.assets.android}};
 const latest={...release,id:'new',build:5,assets:{[platform==='android'?'windows':'android']:release.assets.android}};
 const calls=[];
 const server=async(path)=>{calls.push(path);if(path.includes('ysk_update_channels'))return [{release_id:'new'}];if(path.includes('id=eq.new'))return [latest];if(path.includes('build=lte.5'))return [old];if(path.includes('/object/sign/'))return {signedURL:'/object/sign/file'};throw Error(path);};
 let result=await action({action:'update_check',platform},{organization_id:'school-A',role:'teacher',update_channel:channel},server,'https://school.test','secret');
 assert.equal(result.data.release.id,old.id);assert.equal(result.data.release.build,3);
 const query=calls.find(p=>p.includes('build=lte.5'));assert(query.includes('organization_id=eq.school-A'));assert(query.includes('&ready=eq.true'));assert(query.includes('&assets->'+platform+'=not.is.null'));assert.equal(query.includes('stable_at=not.is.null'),channel==='stable');
 result=await action({action:'download_update',platform,release_id:old.id},{organization_id:'school-A',role:'teacher',update_channel:channel},server,'https://school.test','secret');assert(result.data.release.asset.url);
}
console.log('Independent Windows/Android update and download checks passed.');
