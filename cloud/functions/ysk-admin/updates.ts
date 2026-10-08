import { managedSchools } from './schools.ts';
const BUCKET='ysk-updates';
const platformOK=p=>['android','windows'].includes(p);
async function urlFor(server,base,path){const result=await server('/storage/v1/object/sign/'+BUCKET+'/'+path,'POST',{expiresIn:300});const url=result.signedURL||result.signedUrl;return url.startsWith('http')?url:base+'/storage/v1'+url;}
export async function updateAction(body,member,server,base,secret){
 const org=encodeURIComponent(member.organization_id),channel=member.update_channel||'stable';
 if(body.action==='update_check'||body.action==='download_update'){
  if(!platformOK(body.platform))return {status:400,data:{message:'Ugyldig plattform.'}};
  let effectiveChannel=channel;
  let pointers=await server('/rest/v1/ysk_update_channels?organization_id=eq.'+org+'&channel=eq.'+channel+'&select=release_id');
  if(!pointers.length&&channel==='dev'){effectiveChannel='stable';pointers=await server('/rest/v1/ysk_update_channels?organization_id=eq.'+org+'&channel=eq.stable&select=release_id');}
  if(!pointers.length)return {data:{channel,release:null}};
  const releases=await server('/rest/v1/ysk_releases?id=eq.'+pointers[0].release_id+'&organization_id=eq.'+org+'&ready=eq.true');let release=releases[0];
  if(release&&!release.assets?.[body.platform]){
   const previous=await server('/rest/v1/ysk_releases?organization_id=eq.'+org+'&ready=eq.true&build=lte.'+release.build+'&assets->'+body.platform+'=not.is.null'+(effectiveChannel==='stable'?'&stable_at=not.is.null':'')+'&order=build.desc&limit=1');
   release=previous[0];
  }
  const asset=release?.assets?.[body.platform];
  if(!asset)return {data:{channel,release:null}};
  const result={id:release.id,version:release.version,build:release.build,notes:release.notes,published_at:release.created_at,stable_at:release.stable_at,asset:{name:asset.name,size:asset.size,sha256:asset.sha256}};
  if(body.action==='download_update'){
   if(body.release_id!==release.id)return {status:409,data:{message:'Utgaven er endret. Sjekk oppdateringer på nytt.'}};
   result.asset.url=await urlFor(server,base,asset.path);
  }return {data:{channel,release:result}};
 }
 if(!['set_channel','release_list','release_prepare','release_commit','release_promote'].includes(body.action))return null;
 if(member.role!=='admin')return {status:403,data:{message:'Bare admin kan styre oppdateringer.'}};
 if(body.action==='set_channel'){
  if(!['dev','stable'].includes(body.channel)||!/^[0-9a-f-]{36}$/i.test(String(body.user_id)))return {status:400,data:{message:'Ugyldig kanal eller bruker.'}};
  const ids=await managedSchools(member,server);
  const changed=await server('/rest/v1/ysk_memberships?user_id=eq.'+encodeURIComponent(body.user_id)+'&organization_id=in.('+ids.map(encodeURIComponent).join(',')+')','PATCH',{update_channel:body.channel});
  return changed.length?{data:{message:'Oppdateringskanal endret til '+body.channel+'.'}}:{status:404,data:{message:'Brukeren finnes ikke i skolen.'}};
 }
 if(body.action==='release_list')return {data:{releases:await server('/rest/v1/ysk_releases?organization_id=eq.'+org+'&order=build.desc&limit=100'),channels:await server('/rest/v1/ysk_update_channels?organization_id=eq.'+org)}};
 if(body.action==='release_prepare'){
  const version=String(body.version||''),build=Number(body.build),notes=String(body.notes||''),assets={};
  if(!/^[0-9]+\.[0-9]+\.[0-9]+$/.test(version)||!Number.isInteger(build)||build<1||notes.length>5000)return {status:400,data:{message:'Kontroller versjon, byggnummer og endringslogg.'}};
  const id=crypto.randomUUID();
  for(const [platform,meta] of Object.entries(body.assets||{})){
   if(!platformOK(platform)||!/^[0-9a-f]{64}$/.test(meta.sha256)||!Number.isInteger(meta.size)||meta.size<1||meta.size>50000000)return {status:400,data:{message:'Ugyldig releasefil eller kontrollsum.'}};
   const suffix=platform==='android'?'.apk':'.exe',name='YSK_Kjorestudio_'+platform+'_'+version+'_B'+build+'_'+new Date().toISOString().slice(0,10)+suffix;assets[platform]={name,size:meta.size,sha256:meta.sha256,path:member.organization_id+'/'+id+'/'+name};
  }
  if(!Object.keys(assets).length)return {status:400,data:{message:'Velg minst én releasefil.'}};
  const latest=await server('/rest/v1/ysk_releases?organization_id=eq.'+org+'&order=build.desc&limit=1&select=build');
  if(latest.length&&latest[0].build>=build)return {status:409,data:{message:'Byggnummeret må være høyere enn tidligere utgaver.'}};
  try{await server('/storage/v1/bucket','POST',{id:BUCKET,name:BUCKET,public:false,file_size_limit:50000000});}catch{const bucket=await server('/storage/v1/bucket/'+BUCKET);if(bucket.public)throw new Error('Oppdateringslageret må være privat.');}
  await server('/rest/v1/ysk_releases','POST',{id,organization_id:member.organization_id,version,build,notes,assets});const uploads={};
  for(const [platform,asset] of Object.entries(assets)){
   const result=await server('/storage/v1/object/upload/sign/'+BUCKET+'/'+asset.path,'POST',{});const relative=result.url;uploads[platform]={url:relative.startsWith('http')?relative:base+'/storage/v1'+relative,name:asset.name};
  }return {data:{id,uploads}};
 }
 const rows=await server('/rest/v1/ysk_releases?id=eq.'+encodeURIComponent(String(body.release_id))+'&organization_id=eq.'+org);const release=rows[0];
 if(!release)return {status:404,data:{message:'Utgaven finnes ikke i skolen.'}};
 if(body.action==='release_commit'){
  if(!release.ready){
   for(const asset of Object.values(release.assets)){
    const response=await fetch(base+'/storage/v1/object/'+BUCKET+'/'+asset.path,{headers:{apikey:secret,Authorization:'Bearer '+secret}});if(!response.ok)return {status:409,data:{message:'Alle filer må lastes opp før publisering.'}};
    const declared=Number(response.headers.get('content-length'));if(declared&&declared!==asset.size)return {status:409,data:{message:'Filstørrelsen stemmer ikke.'}};
    const buffer=await response.arrayBuffer();if(buffer.byteLength!==asset.size)return {status:409,data:{message:'Filstørrelsen stemmer ikke.'}};
    const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',buffer))).map(b=>b.toString(16).padStart(2,'0')).join('');if(hash!==asset.sha256)return {status:409,data:{message:'Kontrollsummen stemmer ikke. Utgaven er ikke publisert.'}};
   }await server('/rest/v1/ysk_releases?id=eq.'+release.id,'PATCH',{ready:true});
  }
  await server('/rest/v1/rpc/ysk_set_release_channel','POST',{p_org:member.organization_id,p_channel:'dev',p_release:release.id});return {data:{message:'Publisert til dev. Stable er uendret.'}};
 }
 if(!release.ready||body.confirm!=='stable')return {status:400,data:{message:'Velg en ferdig dev-utgave og bekreft stable.'}};
 await server('/rest/v1/rpc/ysk_set_release_channel','POST',{p_org:member.organization_id,p_channel:'stable',p_release:release.id});return {data:{message:'Den testede utgaven er publisert til stable. Filene er identiske.'}};
}
