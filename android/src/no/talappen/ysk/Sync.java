package no.talappen.ysk;
import android.content.*;import org.json.*;import java.net.*;import java.io.*;import java.util.*;
public class Sync {
 static class ApiFailure extends Exception {final int status;final String code;ApiFailure(int status,String message,String code){super(message);this.status=status;this.code=code;}}
 static JSONArray getRows(String url,String api,String token)throws Exception {
  HttpURLConnection h=(HttpURLConnection)new URL(url).openConnection();h.setConnectTimeout(15000);h.setReadTimeout(20000);h.setRequestProperty("apikey",api);h.setRequestProperty("Authorization","Bearer "+token);
  try{int status=h.getResponseCode();InputStream stream=status>=400?h.getErrorStream():h.getInputStream();StringBuilder raw=new StringBuilder();if(stream!=null)try(BufferedReader r=new BufferedReader(new InputStreamReader(stream,"UTF-8"))){String line;while((line=r.readLine())!=null)raw.append(line);}if(status>=400){JSONObject error=new JSONObject(raw.toString());throw new ApiFailure(status,error.optString("message","HTTP "+status),error.optString("code"));}return new JSONArray(raw.toString());}finally{h.disconnect();}
 }
 static JSONObject membership(String url,String api,JSONObject session)throws Exception{
  try{JSONArray rows=getRows(url+"/rest/v1/ysk_memberships?select=organization_id,role,active,display_name&user_id=eq."+session.getJSONObject("user").getString("id"),api,session.getString("access_token"));if(rows.length()==0||!rows.getJSONObject(0).getBoolean("active"))throw new Exception("Du har ikke aktiv tilgang til skolen.");return rows.getJSONObject(0);}catch(ApiFailure e){if(e.status==404&&(e.code.equals("PGRST205")||e.code.equals("42P01")))return null;throw e;}
 }
 public static synchronized JSONObject admin(Context c,JSONObject body)throws Exception{
  SharedPreferences p=c.getSharedPreferences("cloud",0);String url=p.getString("url",""),api=p.getString("api","");if(url.isEmpty())throw new Exception("Logg inn under Innstillinger først.");JSONObject s=session(c,url,api);
  try{return request(url+"/functions/v1/ysk-admin",api,s.getString("access_token"),body);}catch(ApiFailure e){if(e.status==404)throw new Exception("Skole/admin må aktiveres i Supabase før brukeradministrasjon virker.");throw e;}
 }

 static JSONObject request(String url,String api,String token,JSONObject body)throws Exception{
  HttpURLConnection h=(HttpURLConnection)new URL(url).openConnection();h.setConnectTimeout(15000);h.setReadTimeout(20000);h.setRequestMethod("POST");h.setRequestProperty("apikey",api);h.setRequestProperty("Content-Type","application/json");if(token!=null){h.setRequestProperty("Authorization","Bearer "+token);h.setRequestProperty("Prefer","resolution=merge-duplicates,return=minimal");}h.setDoOutput(true);
  try{byte[] b=body.toString().getBytes("UTF-8");h.setFixedLengthStreamingMode(b.length);try(OutputStream out=h.getOutputStream()){out.write(b);}int status=h.getResponseCode();InputStream in=status>=400?h.getErrorStream():h.getInputStream();String text="";if(in!=null)try(BufferedReader r=new BufferedReader(new InputStreamReader(in,"UTF-8"))){StringBuilder s=new StringBuilder();String line;while((line=r.readLine())!=null)s.append(line);text=s.toString();}if(status>=400){String error="HTTP "+status,code="";try{JSONObject e=new JSONObject(text);error=e.optString("msg",e.optString("message",e.optString("error_description",error)));code=e.optString("code");}catch(Exception ignored){}throw new ApiFailure(status,error,code);}return text.isEmpty()?new JSONObject():new JSONObject(text);}finally{h.disconnect();}
 }
 static JSONArray choices(String url,String api,String token)throws Exception{
  JSONArray all=new JSONArray();for(int offset=0;;offset+=500){HttpURLConnection h=(HttpURLConnection)new URL(url+"/rest/v1/ysk_trips?select=driver,course,vehicle&order=id&limit=500&offset="+offset).openConnection();h.setConnectTimeout(15000);h.setReadTimeout(20000);h.setRequestProperty("apikey",api);h.setRequestProperty("Authorization","Bearer "+token);try{if(h.getResponseCode()!=200)throw new Exception("Kunne ikke hente navn/biler/kurs: HTTP "+h.getResponseCode());StringBuilder text=new StringBuilder();try(BufferedReader reader=new BufferedReader(new InputStreamReader(h.getInputStream(),"UTF-8"))){String line;while((line=reader.readLine())!=null)text.append(line);}JSONArray page=new JSONArray(text.toString());for(int i=0;i<page.length();i++)all.put(page.getJSONObject(i));if(page.length()<500)return all;}finally{h.disconnect();}}
 }
 public static String endpoint(String u)throws Exception{URI x=new URI(u.trim());if(!"https".equals(x.getScheme())||x.getHost()==null||x.getUserInfo()!=null||x.getQuery()!=null||x.getFragment()!=null||!(x.getPath().isEmpty()||x.getPath().equals("/")))throw new Exception("Bruk prosjektets HTTPS-adresse, uten sti eller nøkkel.");return "https://"+x.getAuthority();}
 public static synchronized void login(Context c,String url,String api,String email,String password)throws Exception{
  url=endpoint(url);if(api.startsWith("sb_secret_")||api.trim().isEmpty())throw new Exception("Bruk publishable/anon key, aldri secret/service_role.");
  if(api.startsWith("eyJ")){try{String role=new JSONObject(new String(android.util.Base64.decode(api.split("\\.")[1],android.util.Base64.URL_SAFE),"UTF-8")).optString("role");if(!role.equals("anon"))throw new Exception("API-nøkkelen må være anon/publishable.");}catch(JSONException e){throw new Exception("Ugyldig API-nøkkel.");}}
  JSONObject b=new JSONObject().put("email",email.trim()).put("password",password);JSONObject session=request(url+"/auth/v1/token?grant_type=password",api,null,b);
  JSONObject member=membership(url,api,session);if(member!=null)c.getSharedPreferences("form",0).edit().putString("teacher",member.getString("display_name")).apply();String owner=session.getJSONObject("user").getString("id");try(TripDb db=new TripDb(c)){db.bind(url+"|"+owner);}Secure.put(c,session.toString());c.getSharedPreferences("cloud",0).edit().putString("url",url).putString("api",api).putString("email",email.trim()).putString("owner",owner).commit();
 }
 static JSONObject session(Context c,String url,String api)throws Exception{
  String raw=Secure.get(c);if(raw.isEmpty())throw new Exception("Koble til skykonto først.");JSONObject s=new JSONObject(raw);
  if(s.optLong("expires_at",0)<=System.currentTimeMillis()/1000+90){s=request(url+"/auth/v1/token?grant_type=refresh_token",api,null,new JSONObject().put("refresh_token",s.getString("refresh_token")));Secure.put(c,s.toString());}return s;
 }
 public static synchronized String run(Context context)throws Exception{
  Context c=context.getApplicationContext();try(TripDb db=new TripDb(c)){
   List<JSONObject> rows=db.rows(true);
   SharedPreferences p=c.getSharedPreferences("cloud",0);String url=p.getString("url",""),api=p.getString("api","");if(url.isEmpty())return "Lagret på telefonen. Koble til sky under Innstillinger for å sende.";
   JSONObject s=session(c,url,api);JSONObject member=membership(url,api,s);String token=s.getString("access_token"),owner=s.getJSONObject("user").getString("id");db.bind(url+"|"+owner);int sent=0,failed=0;
   for(JSONObject r:rows){if(Thread.currentThread().isInterrupted())throw new InterruptedException();JSONObject d=r.getJSONObject("payload");JSONObject body=new JSONObject().put("id",r.getString("id")).put("owner_id",owner).put("revision",r.getString("revision")).put("payload",d);for(String k:new String[]{"driver","course","vehicle"})body.put(k,d.getString(k));body.put("trip",d.getInt("trip"));if(member!=null)body.put("organization_id",member.getString("organization_id"));try{request(url+"/rest/v1/ysk_trips?on_conflict=id",api,token,body);db.mark(r.getString("id"),r.getString("revision"),"sent","");sent++;}catch(Exception e){db.mark(r.getString("id"),r.getString("revision"),"error",e.getMessage());failed++;}}
   try{c.getSharedPreferences("cloud",0).edit().putString("choices",choices(url,api,token).toString()).apply();}catch(Exception e){return sent+" turer sendt. Navn/biler/kurs kunne ikke oppdateres: "+e.getMessage();}
   return sent+" turer sendt. "+failed+" venter"+(failed>0?" – se feilen under Mine turer.":".");
  }
 }
}
