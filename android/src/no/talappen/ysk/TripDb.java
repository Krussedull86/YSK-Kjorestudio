package no.talappen.ysk;
import android.content.*;import android.database.*;import android.database.sqlite.*;import org.json.*;import java.util.*;
public class TripDb extends SQLiteOpenHelper {
 public TripDb(Context c){super(c,"ysk_offline.db",null,1);}
 public void onCreate(SQLiteDatabase d){d.execSQL("CREATE TABLE trips(id TEXT PRIMARY KEY, driver TEXT, course TEXT, vehicle TEXT, trip INTEGER, payload TEXT NOT NULL, revision TEXT NOT NULL, state TEXT NOT NULL, error TEXT NOT NULL DEFAULT '', UNIQUE(driver,course,vehicle,trip))");d.execSQL("CREATE TABLE meta(k TEXT PRIMARY KEY,v TEXT)");}
 public void onUpgrade(SQLiteDatabase d,int a,int b){}
 public synchronized void bind(String owner)throws Exception{SQLiteDatabase d=getWritableDatabase();try(Cursor c=d.rawQuery("SELECT v FROM meta WHERE k='account'",null)){if(c.moveToFirst()&&!owner.equals(c.getString(0)))throw new Exception("Denne telefonens data er knyttet til en annen konto. Bruk samme konto.");}ContentValues v=new ContentValues();v.put("k","account");v.put("v",owner);d.insertWithOnConflict("meta",null,v,SQLiteDatabase.CONFLICT_REPLACE);}
 public void save(JSONObject p)throws Exception{
  ContentValues v=new ContentValues();String id=p.getString("id");v.put("id",id);for(String k:new String[]{"driver","course","vehicle"})v.put(k,p.getString(k));v.put("trip",p.getInt("trip"));v.put("payload",p.toString());v.put("revision",UUID.randomUUID().toString());v.put("state","pending");v.put("error","");
  SQLiteDatabase d=getWritableDatabase();d.beginTransaction();try{
   try(Cursor c=d.rawQuery("SELECT id FROM trips WHERE driver=? AND course=? AND vehicle=? AND trip=?",new String[]{p.getString("driver"),p.getString("course"),p.getString("vehicle"),String.valueOf(p.getInt("trip"))})){if(c.moveToFirst()&&!c.getString(0).equals(id))throw new Exception("Denne turen finnes allerede. Åpne den under Mine turer og rediger.");}
   if(d.update("trips",v,"id=?",new String[]{id})==0)d.insertOrThrow("trips",null,v);d.setTransactionSuccessful();
  }finally{d.endTransaction();}
 }
 public List<JSONObject> rows(boolean pending)throws Exception{
  List<JSONObject> result=new ArrayList<>();try(Cursor c=getReadableDatabase().rawQuery("SELECT id,payload,revision,state,error FROM trips "+(pending?"WHERE state!='sent' ":"")+"ORDER BY course,vehicle,driver,trip",null)){while(c.moveToNext()){JSONObject r=new JSONObject();r.put("id",c.getString(0));r.put("payload",new JSONObject(c.getString(1)));r.put("revision",c.getString(2));r.put("state",c.getString(3));r.put("error",c.getString(4));result.add(r);}}return result;
 }
 public void mark(String id,String revision,String state,String error){ContentValues v=new ContentValues();v.put("state",state);v.put("error",error);getWritableDatabase().update("trips",v,"id=? AND revision=?",new String[]{id,revision});}
}
