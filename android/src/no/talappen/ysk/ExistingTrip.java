package no.talappen.ysk;
import org.json.*;import java.util.*;import java.util.concurrent.atomic.AtomicInteger;
/** Find an existing activity without overwriting pending local changes. */
final class ExistingTrip {
 static final AtomicInteger generation=new AtomicInteger();
 static void lookup(MainActivity a){
  if(!a.authenticated||!a.page.equals("form")||a.editId!=null||a.tripClock.running||a.distributionRun!=null)return;
  final String driver=a.inputs.get("driver").getText().toString().trim(),course=a.inputs.get("course").getText().toString().trim(),vehicle=a.inputs.get("vehicle").getText().toString().trim();if(driver.isEmpty())return;
  final int trip=a.trip,request=generation.incrementAndGet();final String scope=a.paramTrips.accountScope();final String draft;
  try{draft=a.draft().toString();}catch(Exception ignored){return;}
  new Thread(()->{try{
   Map<String,JSONObject> found=new LinkedHashMap<>();boolean offline=false;
   try{for(JSONObject row:Sync.managedRows(a))if(row.isNull("deleted_at")&&matches(row.getJSONObject("payload"),driver,course,vehicle,trip))found.put(row.getString("id"),new JSONObject(row.getJSONObject("payload").toString()).put("id",row.getString("id")).put("_managed",row));}catch(Exception ignored){offline=true;}
   List<JSONObject> local=a.db.rows(false);for(JSONObject row:local)if(matches(row.getJSONObject("payload"),driver,course,vehicle,trip)&&(!row.optString("state").equals("sent")||!found.containsKey(row.getString("id"))))found.put(row.getString("id"),new JSONObject(row.getJSONObject("payload").toString()).put("id",row.getString("id")));
   final List<JSONObject> results=new ArrayList<>(found.values());final boolean localOnly=offline;
   a.runOnUiThread(()->{try{if(a.isDestroyed()||!a.authenticated||request!=generation.get()||!scope.equals(a.paramTrips.accountScope())||!a.page.equals("form")||!draft.equals(a.draft().toString()))return;
    if(results.isEmpty()){android.widget.Toast.makeText(a,localOnly?"Ingen lokal aktivitet funnet. Kunne ikke sjekke skyen – bruk Hent registrerte turer når du har nett.":"Ingen tidligere registrering funnet for dette valget.",android.widget.Toast.LENGTH_LONG).show();return;}
    if(results.size()==1){open(a,results.get(0),localOnly);return;}
    String[] labels=new String[results.size()];for(int i=0;i<labels.length;i++){JSONObject p=results.get(i);labels[i]=p.optString("course")+" · "+p.optString("vehicle")+" · "+p.optString("date")+" "+p.optString("start_time")+" · "+p.optString("teacher");}
    a.dialog().setTitle("Velg registrert aktivitet"+(localOnly?" (lokalt)":"")).setItems(labels,(d,n)->open(a,results.get(n),localOnly)).setNegativeButton("Avbryt",null).show();
   }catch(Exception e){a.alert(e.getMessage());}});
  }catch(Exception e){a.runOnUiThread(()->{if(a.authenticated&&request==generation.get())a.alert("Kunne ikke hente aktiviteten: "+e.getMessage());});}},"YSK-existing-trip").start();
 }
 static void switchTrip(MainActivity a,int trip){
  a.dialog().setTitle("Åpne en annen aktivitet?").setMessage("Lagre eventuelle endringer først. Det valgte elev-, kurs- og biloppsettet brukes til å hente den andre turen.").setNegativeButton("Behold tur",null).setPositiveButton("Bytt tur",(d,w)->{try{JSONObject empty=new JSONObject().put("trip",trip).put("date",new java.text.SimpleDateFormat("yyyy-MM-dd",Locale.ROOT).format(new Date()));for(String key:new String[]{"driver","course","vehicle","teacher"})empty.put(key,a.inputs.get(key).getText().toString());a.clearDraft();a.form(empty);ExistingTrip.lookup(a);}catch(Exception e){a.alert(e.getMessage());}}).show();
 }
 static boolean matches(JSONObject p,String driver,String course,String vehicle,int trip){return same(p.optString("driver"),driver)&&(course.isEmpty()||same(p.optString("course"),course))&&(vehicle.isEmpty()||same(p.optString("vehicle"),vehicle))&&p.optInt("trip")==trip;}
 static boolean same(String a,String b){return a.trim().equalsIgnoreCase(b.trim());}
 static void open(MainActivity a,JSONObject p,boolean offline){
  Runnable load=()->{a.form(p);android.widget.Toast.makeText(a,offline?"Åpnet lokal aktivitet. Endringer lagres med Lagre tur.":"Registrert aktivitet hentet. Endringer lagres med Lagre tur.",android.widget.Toast.LENGTH_LONG).show();};
  boolean measurements=false;for(String key:new String[]{"minutes","km","liters","average_speed","fuel_per_100","notes"})if(a.inputs.containsKey(key)&&!a.inputs.get(key).getText().toString().trim().isEmpty())measurements=true;for(String value:a.ratings.values())if(value!=null&&!value.isEmpty())measurements=true;
  if(measurements)a.dialog().setTitle("Åpne registrert aktivitet?").setMessage("Målingene i det nye utkastet erstattes av den lagrede turen. Endringer i den lagrede turen sendes først når du trykker Lagre tur.").setNegativeButton("Behold utkast",null).setPositiveButton("Åpne aktivitet",(d,w)->load.run()).show();else load.run();
 }
}
