import { templateAction } from './templates.ts';
import { feedbackAction } from './feedback.ts';
import { schoolAction, managedSchools, schoolTarget } from './schools.ts';
import { updateAction } from './updates.ts';
import { tripAction } from './trips.ts';
// Server-side only. Project service key stays in Edge Function environment.
const headers = { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'Access-Control-Allow-Origin':'*', 'Access-Control-Allow-Headers':'authorization,apikey,content-type', 'Access-Control-Allow-Methods':'POST,OPTIONS' };
const reply = (body, status = 200) => new Response(JSON.stringify(body), { status, headers });
const base = Deno.env.get('SUPABASE_URL');
const secret = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
async function server(path, method = 'GET', body = undefined) {
 const response = await fetch(base + path, { method, headers: { apikey: secret, Authorization: 'Bearer ' + secret, 'Content-Type': 'application/json', Prefer: 'resolution=merge-duplicates,return=representation' }, body: body === undefined ? undefined : JSON.stringify(body) });
 const text = await response.text(); const value = text ? JSON.parse(text) : null;
 if (!response.ok) throw new Error('server'); return value;
}
Deno.serve(async (req) => {
 if(req.method==='OPTIONS')return new Response('ok',{headers});
 if (req.method !== 'POST') return reply({ message: 'Bruk POST.' }, 405);
 const token = req.headers.get('Authorization') || '';
 if (!token.startsWith('Bearer ')) return reply({ message: 'Logg inn først.' }, 401);
 try {
  const response = await fetch(base + '/auth/v1/user', { headers: { apikey: secret, Authorization: token } });
  if (!response.ok) return reply({ message: 'Innloggingen er utløpt.' }, 401);
  const user = await response.json();
  const matches = await server('/rest/v1/ysk_memberships?user_id=eq.' + encodeURIComponent(user.id) + '&select=user_id,organization_id,display_name,email,role,active,update_channel,division_id');
  const member = matches?.[0];
  if (!member?.active) return reply({ message: 'Brukeren har ikke aktiv tilgang til skolen.' }, 403);
  const raw = await req.text(); if (raw.length > 128000) return reply({ message: 'For stor forespørsel.' }, 413);
  const body = JSON.parse(raw || '{}');
  if (body.action === 'me') {
   const schools=await server('/rest/v1/ysk_organizations?id=eq.'+encodeURIComponent(member.organization_id)+'&select=id,name');
   const divisions=member.division_id?await server('/rest/v1/ysk_divisions?id=eq.'+encodeURIComponent(member.division_id)+'&organization_id=eq.'+encodeURIComponent(member.organization_id)+'&select=id,name'):[];
   return reply({ member, school:schools[0]||null, division:divisions[0]||null });
  }
  const templates=await templateAction(body,member,server);if(templates)return reply(templates.data,templates.status||200);
  const feedback=await feedbackAction(body,member,server);if(feedback)return reply(feedback.data,feedback.status||200);
  const schoolResult=await schoolAction(body,member,server);if(schoolResult)return reply(schoolResult.data,schoolResult.status||200);
  const tripResult=await tripAction(body,member,server);if(tripResult)return reply(tripResult.data,tripResult.status||200);
  const update=await updateAction(body,member,server,base,secret);if(update)return reply(update.data,update.status||200);
  if (member.role !== 'admin') return reply({ message: 'Bare administrator kan administrere brukere.' }, 403);
  const org = encodeURIComponent(member.organization_id);
  if (body.action === 'list') {
   const ids=await managedSchools(member,server);
   const members = []; for (let offset = 0; ; offset += 500) {
    const page = await server('/rest/v1/ysk_memberships?organization_id=in.(' + ids.map(encodeURIComponent).join(',') + ')&select=user_id,organization_id,division_id,display_name,email,role,active,update_channel&order=display_name,user_id&limit=500&offset=' + offset); members.push(...page); if (page.length < 500) break;
   } return reply({ members });
  }
  if (body.action === 'create') {
   const email = String(body.email || '').trim().toLowerCase(), name = String(body.name || '').trim(), password = String(body.password || ''), role = body.role || 'teacher';
   if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 254 || !name || name.length > 100 || password.length < 12 || password.length > 128 || !['teacher', 'admin'].includes(role)) return reply({ message: 'Kontroller navn, e-post, rolle og passord (12–128 tegn).' }, 400);
   const target=await schoolTarget(body,member,server);if(!target)return reply({message:'Velg en skole og avdeling du administrerer.'},403);
   let created; try { created = await server('/auth/v1/admin/users', 'POST', { email, password, email_confirm: true, user_metadata: { name } }); } catch { return reply({ message: 'Kunne ikke opprette kontoen. E-posten kan finnes fra før, eller passordet oppfyller ikke kravene.' }, 409); }
   if (!created?.id) return reply({ message: 'Kontoen kunne ikke opprettes.' }, 500);
   try { await server('/rest/v1/ysk_memberships', 'POST', { user_id: created.id, organization_id: target.organization_id, division_id: target.division_id, email, display_name: name, role, active: true }); }
   catch { try { await server('/auth/v1/admin/users/' + created.id, 'DELETE'); } catch { /* New orphan account has no membership and therefore no trip access. */ } return reply({ message: 'Tilgangen kunne ikke opprettes. Kontoen har ingen skoletilgang.' }, 500); }
   return reply({ message: 'Bruker opprettet.', user_id: created.id });
  }
  if (body.action === 'set_active') {
   const id = String(body.user_id || ''); if (!/^[0-9a-f-]{36}$/i.test(id) || typeof body.active !== 'boolean') return reply({ message: 'Ugyldig bruker.' }, 400);
   const ids=await managedSchools(member,server);const scope='&organization_id=in.('+ids.map(encodeURIComponent).join(',')+')';
   const rows = await server('/rest/v1/ysk_memberships?user_id=eq.' + encodeURIComponent(id) + scope + '&select=user_id,role');
   if (!rows?.length || rows[0].role === 'admin') return reply({ message: 'Bare lærerkontoer i din skole kan aktiveres/deaktiveres her.' }, 403);
   await server('/rest/v1/ysk_memberships?user_id=eq.' + encodeURIComponent(id) + scope, 'PATCH', { active: body.active }); return reply({ message: body.active ? 'Lærer aktivert.' : 'Lærer deaktivert.' });
  }
  return reply({ message: 'Ukjent handling.' }, 400);
 } catch { return reply({ message: 'Handlingen kunne ikke fullføres. Prøv igjen eller kontroller tjenesten.' }, 503); }
});
