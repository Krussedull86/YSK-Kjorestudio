// Versioned school templates. Only the server accesses these RLS-protected tables.
const templateUUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function parameter(value){
 if(!value||typeof value!=='object'||!/^[a-z][a-z0-9_]{0,79}$/.test(value.id)||typeof value.label!=='string'||!value.label.trim()||value.label.length>100||!['number','integer','minutes','rating','boolean','choice','text','stopwatch','fuel'].includes(value.type))throw Error('Kontroller parameternavn og felttype.');
 const p={id:value.id,label:value.label.trim(),type:value.type,unit:String(value.unit||'').slice(0,30),required:value.required===true,graph:value.graph===true,weight:value.weight??0,direction:value.direction||'none',min:value.min??null,max:value.max??null,options:value.options||[]};
 if(typeof p.weight!=='number'||!Number.isFinite(p.weight)||p.weight<0||p.weight>100||!['none','low','high'].includes(p.direction)||!Array.isArray(p.options)||p.options.length>30||p.options.some(x=>typeof x!=='string'||!x||x.length>80))throw Error('Ugyldig vekting eller valg.');
 for(const k of ['min','max'])if(p[k]!==null&&(typeof p[k]!=='number'||!Number.isFinite(p[k])))throw Error('Ugyldig grense.');
 if(p.min!==null&&p.max!==null&&p.min>=p.max)throw Error('Min må være mindre enn maks.');
 if(p.type==='choice'&&!p.options.length)throw Error('Legg inn valgene.');
 if(p.weight>0){if(['text','choice'].includes(p.type)||p.direction==='none'||!['rating','boolean'].includes(p.type)&&(p.min===null||p.max===null))throw Error('Poeng krever retning og faste min/maks-grenser.');}
 return p;
}
export function templateDefinition(value){
 if(!value||typeof value.name!=='string'||!value.name.trim()||value.name.length>100||!Array.isArray(value.parameters)||value.parameters.length<1||value.parameters.length>40)throw Error('Turmalen trenger navn og 1–40 parametre.');
 const parameters=value.parameters.map(parameter);if(new Set(parameters.map(p=>p.id)).size!==parameters.length)throw Error('Samme parameter kan bare brukes én gang.');
 if(parameters.some(p=>p.type==='fuel')&&(!parameters.some(p=>p.id==='km')||!parameters.some(p=>p.id==='liters')))throw Error('Beregnet forbruk krever Kjørt distanse og Forbruk totalt.');
 return {name:value.name.trim(),base_trip:Number.isInteger(value.base_trip)&&value.base_trip>=1&&value.base_trip<=5?value.base_trip:null,parameters};
}
export function defaultParameters(){
 const field=(id,label,type,unit='',required=true)=>parameter({id,label,type,unit,required,graph:['number','integer','minutes','fuel','stopwatch'].includes(type),weight:0});
 return [field('minutes','Forbrukt tid','stopwatch','min'),field('km','Kjørt distanse','number','km'),field('liters','Forbruk totalt','number','liter'),field('fuel','Forbruk per mil','fuel','l/mil',false),field('stops','Unødige stopp','integer'),...['trafikksikkerhet','avpassing','okning','komfort'].map((id,i)=>parameter({...field(id,['Trafikksikkerhet','Fartsavpassing','Fartsøkning','Komfort'][i],'rating'),weight:[25,10,5,10][i],direction:'high'})),field('average_speed','Gjennomsnittsfart','number','km/t',false),field('notes','Notater','text','',false),field('reversing','Antall rygginger','integer','',false),field('loading','Lasting / lossing','minutes','min',false),field('waiting','Ventetid','minutes','min',false),field('rampe','Rygget til rampe','boolean','',false),field('secured','Last sikret','boolean','',false),field('planning','Planlegging','rating','',false),field('weather','Vær og føre','text','',false),field('cargo','Lastvekt','number','kg',false),field('deviations','Avvik / hendelser','text','',false)];
}
export function defaultTemplates(){const names=['Optimaltur 1','Optimaltur 2','Optimaltur 3','Transportoppdrag 1 (distribusjon)','Transportoppdrag 2 (langtur)'];return names.map((name,i)=>({id:'00000000-0000-4000-8000-'+String(i+1).padStart(12,'0'),revision:0,definition:{name,base_trip:i+1,parameters:defaultParameters().slice(0,11)}}));}
export function templatePayload(input,definition){
 if(!input||typeof input.driver!=='string'||!input.driver.trim()||input.driver.length>100||typeof input.course!=='string'||!input.course.trim()||input.course.length>100||typeof input.vehicle!=='string'||!input.vehicle.trim()||input.vehicle.length>100||typeof input.date!=='string'||!/^\d{4}-\d{2}-\d{2}$/.test(input.date)||typeof input.complete!=='boolean'||!input.values||typeof input.values!=='object'||Array.isArray(input.values))throw Error('Fyll inn elev, kurs, bil og dato.');
 const values={},missing=[];let weighted=0,total=0,unscored=false;
 for(const p of definition.parameters){let v=input.values[p.id];if(p.type==='fuel'){const l=Number(input.values.liters),km=Number(input.values.km);v=typeof input.values.liters==='number'&&typeof input.values.km==='number'&&km>0?10*l/km:null;}
  if(v===null||v===undefined||v===''){if(p.required)missing.push(p.label);if(p.weight>0)unscored=true;values[p.id]=null;continue;}
  if(v==='-'){values[p.id]='-';if(p.weight>0)unscored=true;continue;}
  if(['number','integer','minutes','stopwatch','fuel'].includes(p.type)){if(typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>1e9||['integer'].includes(p.type)&&!Number.isInteger(v)||['minutes','stopwatch','fuel','integer'].includes(p.type)&&v<0)throw Error('Ugyldig tall: '+p.label);}
  else if(p.type==='rating'&&!['Bra','Middels','Svak'].includes(v)||p.type==='boolean'&&typeof v!=='boolean'||p.type==='choice'&&!p.options.includes(v)||p.type==='text'&&(typeof v!=='string'||v.length>2000))throw Error('Ugyldig verdi: '+p.label);
  values[p.id]=v;
  if(p.weight>0){let s=p.type==='rating'?({Bra:100,Middels:50,Svak:0})[v]:p.type==='boolean'?(v?100:0):100*Math.max(0,Math.min(1,(v-p.min)/(p.max-p.min)));if(p.direction==='low')s=100-s;weighted+=s*p.weight;total+=p.weight;}
 }
 if(input.complete&&missing.length)throw Error('Mangler: '+missing.join(', '));
 return {driver:input.driver.trim(),course:input.course.trim(),vehicle:input.vehicle.trim(),date:input.date,teacher:String(input.teacher||'').slice(0,100),complete:input.complete,values,missing,score:input.complete&&!unscored&&total>0?Math.round(weighted/total*10)/10:null};
}
export async function templateAction(body,member,server){
 if(!String(body.action).startsWith('template_')&&!String(body.action).startsWith('parameter_'))return null;
 const org=encodeURIComponent(member.organization_id),scope='organization_id=eq.'+org;const fail=(message,status=400)=>({status,data:{message}});
 try{
  if(body.action==='template_catalog'){
   const saved=await server('/rest/v1/ysk_trip_templates?'+scope+'&order=name&limit=200');const byid=new Map(defaultTemplates().map(t=>[t.id,t]));saved.forEach(t=>byid.set(t.id,t));const bank=new Map(defaultParameters().map(p=>[p.id,p]));(await server('/rest/v1/ysk_parameter_bank?'+scope+'&limit=200')).forEach(r=>bank.set(r.id,r.definition));
   return {data:{templates:[...byid.values()],parameters:[...bank.values()],courses:await server('/rest/v1/ysk_template_courses?'+scope+'&limit=500'),role:member.role,organization_id:member.organization_id,user_id:member.user_id}};
  }
  if(body.action==='template_runs'){
   const offset=body.offset??0;if(!Number.isInteger(offset)||offset<0||offset>100000) return fail('Ugyldig side.');const own=member.role==='admin'?'':'&owner_id=eq.'+encodeURIComponent(member.user_id);
   return {data:{runs:await server('/rest/v1/ysk_template_runs?'+scope+own+'&order=updated_at.desc,id&limit=100&offset='+offset)}};
  }
  if(body.action==='template_run_save'){
   if(!templateUUID.test(String(body.id))||!templateUUID.test(String(body.template_id))||!Number.isInteger(body.template_revision)||body.template_revision<0||!Number.isInteger(body.expected_revision)||body.expected_revision<0)return fail('Ugyldig tur / versjon.');
   const previous=(await server('/rest/v1/ysk_template_runs?'+scope+'&id=eq.'+body.id+'&select=template_id,template_revision,snapshot'))[0];
   let definition;if(previous){if(previous.template_id!==body.template_id||previous.template_revision!==body.template_revision)return fail('Gamle turer beholder turmalen.');definition=previous.snapshot;}else if(body.template_revision===0)definition=defaultTemplates().find(t=>t.id===body.template_id)?.definition;else definition=(await server('/rest/v1/ysk_trip_template_versions?'+scope+'&id=eq.'+body.template_id+'&revision=eq.'+body.template_revision+'&select=definition'))[0]?.definition;
   if(!definition)return fail('Turmalen finnes ikke i skolen.',404);
   if(!previous){const courses=await server('/rest/v1/ysk_template_courses?'+scope+'&name=eq.'+encodeURIComponent(body.payload?.course||'')+'&select=template_ids');if(courses.length&&!courses[0].template_ids.includes(body.template_id))return fail('Denne turmalen er ikke aktivert i kurset.');}
   const payload=templatePayload(body.payload,definition);payload.teacher=member.display_name||member.email||'';
   const run=await server('/rest/v1/rpc/ysk_save_template_run','POST',{p_user:member.user_id,p_body:{...body,snapshot:definition,payload}});if(run.status)return fail(run.message,run.status);return {data:{run,message:'Turen er lagret.'}};
  }
  if(member.role!=='admin')return fail('Bare administrator kan endre parameterbank og turmaler.',403);
  if(body.action==='parameter_save'){
   const p=parameter(body.parameter);await server('/rest/v1/ysk_parameter_bank','POST',{organization_id:member.organization_id,id:p.id,definition:p});return {data:{message:'Parameter lagret.'}};
  }
  if(body.action==='template_save'){
   if(!templateUUID.test(String(body.id))||!Number.isInteger(body.expected_revision)||body.expected_revision<0)return fail('Ugyldig turmal.');const definition=templateDefinition(body.definition);
   const r=await server('/rest/v1/rpc/ysk_save_template','POST',{p_org:member.organization_id,p_id:body.id,p_expected:body.expected_revision,p_definition:definition});if(r.status)return fail(r.message,r.status);return {data:{template:r,message:'Ny malversjon lagret. Gamle turer beholder sitt oppsett.'}};
  }
  if(body.action==='template_course_save'){
   if(typeof body.name!=='string'||!body.name.trim()||body.name.length>100||!Array.isArray(body.template_ids)||body.template_ids.length>30||new Set(body.template_ids).size!==body.template_ids.length||body.template_ids.some(id=>!templateUUID.test(id)))return fail('Velg kurs og inntil 30 turmaler.');
   const ids=new Set(defaultTemplates().map(t=>t.id));(await server('/rest/v1/ysk_trip_templates?'+scope+'&select=id')).forEach(t=>ids.add(t.id));if(body.template_ids.some(id=>!ids.has(id)))return fail('Turmal fra annen skole.');
   await server('/rest/v1/ysk_template_courses','POST',{organization_id:member.organization_id,name:body.name.trim(),template_ids:body.template_ids});return {data:{message:'Kursets turmaler er lagret.'}};
  }
  return fail('Ukjent malhandling.');
 }catch(e){return fail(e.message==='server'?'Tjenesten kunne ikke fullføre. Prøv igjen.':e.message,e.message==='server'?503:400);}
}
