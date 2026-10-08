package no.talappen.ysk;
import android.content.*;import android.database.*;import android.database.sqlite.*;import org.json.*;import java.util.*;
public class TripDb extends SQLiteOpenHelper {
 public TripDb(Context c){super(c,"ysk_offline.db",null,2);}
 public void onCreate(SQLiteDatabase d){d.execSQL("CREATE TABLE trips(id TEXT PRIMARY KEY, driver TEXT, course TEXT, vehicle TEXT, trip INTEGER, payload TEXT NOT NULL, revision TEXT NOT NULL, state TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', cloud_revision TEXT NOT NULL DEFAULT '', UNIQUE(driver,course,vehicle,trip))");d.execSQL("CREATE TABLE meta(k TEXT PRIMARY KEY,v TEXT)");deletionTable(d);}
 void deletionTable(SQLiteDatabase d){d.execSQL("CREATE TABLE IF NOT EXISTS deletions(id TEXT PRIMARY KEY,payload TEXT NOT NULL,revision TEXT NOT NULL,expected_revision TEXT NOT NULL,error TEXT NOT NULL DEFAULT '')");}
 public void onUpgrade(SQLiteDatabase d,int a,int b){if(a<2){d.execSQL("ALTER TABLE trips ADD COLUMN cloud_revision TEXT NOT NULL DEFAULT ''");deletionTable(d);}}
 public synchronized void bind(String owner)throws Exception{SQLiteDatabase d=getWritableDatabase();try(Cursor c=d.rawQuery("SELECT v FROM meta WHERE k='account'",null)){if(c.moveToFirst()&&!owner.equals(c.getString(0)))throw new Exception("Denne telefonens data er knyttet til en annen konto. Bruk samme konto.");}ContentValues v=new ContentValues();v.put("k","account");v.put("v",owner);d.insertWithOnConflict("meta",null,v,SQLiteDatabase.CONFLICT_REPLACE);}
 public synchronized void save(JSONObject p)throws Exception{
  ContentValues v=values(p);v.put("revision",UUID.randomUUID().toString());v.put("state",p.optString("completion").equals("incomplete")?"incomplete":"pending");v.put("error","");String id=p.getString("id");
  SQLiteDatabase d=getWritableDatabase();d.beginTransaction();try{
   try(Cursor c=d.rawQuery("SELECT id FROM trips WHERE driver=? AND course=? AND vehicle=? AND trip=?",new String[]{p.getString("driver"),p.getString("course"),p.getString("vehicle"),String.valueOf(p.getInt("trip"))})){if(c.moveToFirst()&&!c.getString(0).equals(id))throw new Exception("Denne turen finnes allerede. Åpne den under Mine turer og rediger.");}
   if(d.update("trips",v,"id=?",new String[]{id})==0)d.insertOrThrow("trips",null,v);d.setTransactionSuccessful();
  }finally{d.endTransaction();}
 }
 ContentValues values(JSONObject p)throws Exception{ContentValues v=new ContentValues();v.put("id",p.getString("id"));for(String k:new String[]{"driver","course","vehicle"}){String value=p.getString(k);if(value.trim().isEmpty())v.putNull(k);else v.put(k,value);};v.put("trip",p.getInt("trip"));v.put("payload",p.toString());return v;}
 public synchronized List<JSONObject> rows(boolean pending)throws Exception{
  List<JSONObject> result=new ArrayList<>();try(Cursor c=getReadableDatabase().rawQuery("SELECT id,payload,revision,state,error,cloud_revision FROM trips "+(pending?"WHERE state IN ('pending','error') ":"")+"ORDER BY course,vehicle,driver,trip",null)){while(c.moveToNext()){JSONObject r=new JSONObject();r.put("id",c.getString(0));r.put("payload",new JSONObject(c.getString(1)));r.put("revision",c.getString(2));r.put("state",c.getString(3));r.put("error",c.getString(4));r.put("cloud_revision",c.getString(5));result.add(r);}}return result;
 }
 public synchronized void mark(String id,String revision,String state,String error){ContentValues v=new ContentValues();v.put("state",state);v.put("error",error);getWritableDatabase().update("trips",v,"id=? AND revision=?",new String[]{id,revision});}
 public synchronized void sent(String id,String revision,String cloudRevision){ContentValues v=new ContentValues();v.put("cloud_revision",cloudRevision);getWritableDatabase().update("trips",v,"id=?",new String[]{id});v.clear();v.put("expected_revision",cloudRevision);getWritableDatabase().update("deletions",v,"id=?",new String[]{id});mark(id,revision,"sent","");}
 public synchronized boolean current(String id,String revision){try(Cursor c=getReadableDatabase().rawQuery("SELECT 1 FROM trips WHERE id=? AND revision=?",new String[]{id,revision})){return c.moveToFirst();}}
 public synchronized void delete(JSONObject row)throws Exception{SQLiteDatabase d=getWritableDatabase();d.beginTransaction();try{ContentValues v=new ContentValues();v.put("id",row.getString("id"));v.put("payload",row.getJSONObject("payload").toString());v.put("revision",UUID.randomUUID().toString());v.put("expected_revision",row.optString("cloud_revision"));d.insertOrThrow("deletions",null,v);d.delete("trips","id=?",new String[]{row.getString("id")});d.setTransactionSuccessful();}finally{d.endTransaction();}}
 public synchronized List<JSONObject> deletions()throws Exception{List<JSONObject> rows=new ArrayList<>();try(Cursor c=getReadableDatabase().rawQuery("SELECT id,payload,revision,expected_revision,error FROM deletions",null)){while(c.moveToNext())rows.add(new JSONObject().put("id",c.getString(0)).put("payload",new JSONObject(c.getString(1))).put("revision",c.getString(2)).put("expected_revision",c.getString(3)).put("error",c.getString(4)));}return rows;}
 public synchronized void deleteDone(String id,String revision){getWritableDatabase().delete("deletions","id=? AND revision=?",new String[]{id,revision});}
 public synchronized void deleteError(String id,String error){ContentValues v=new ContentValues();v.put("error",error);getWritableDatabase().update("deletions",v,"id=?",new String[]{id});}
 public synchronized void cancelDelete(JSONObject row)throws Exception{SQLiteDatabase d=getWritableDatabase();d.beginTransaction();try{ContentValues v=values(row.getJSONObject("payload"));v.put("revision",UUID.randomUUID().toString());v.put("cloud_revision",row.optString("expected_revision"));v.put("state","error");v.put("error","Sletting avbrutt. Hent skyversjonen før du redigerer.");d.insertOrThrow("trips",null,v);d.delete("deletions","id=?",new String[]{row.getString("id")});d.setTransactionSuccessful();}finally{d.endTransaction();}}
 public synchronized void remote(JSONObject row,boolean force)throws Exception{
  SQLiteDatabase d=getWritableDatabase();String id=row.getString("id");
  try(Cursor c=d.rawQuery("SELECT 1 FROM deletions WHERE id=?",new String[]{id})){if(c.moveToFirst()&&!force)return;}
  try(Cursor c=d.rawQuery("SELECT state FROM trips WHERE id=?",new String[]{id})){if(c.moveToFirst()&&!c.getString(0).equals("sent")&&!force)return;}
  if(!row.isNull("deleted_at")&&row.has("deleted_at")){d.delete("trips","id=?",new String[]{id});return;}
  ContentValues v=values(row.getJSONObject("payload"));v.put("revision",row.getString("revision"));v.put("cloud_revision",row.getString("revision"));v.put("state","sent");v.put("error","");
  if(d.update("trips",v,"id=?",new String[]{id})==0)d.insertOrThrow("trips",null,v);
 }
}
