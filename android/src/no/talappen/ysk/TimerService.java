package no.talappen.ysk;
import android.app.*;import android.content.*;import android.os.*;import org.json.*;
public class TimerService extends Service {
 static final String CHANNEL="ysk_trip_timer_priority";static final int ID=42;static boolean active=false;
 static TripTimer load(Context c){SharedPreferences p=c.getSharedPreferences("trip_clock",0);TripTimer t=new TripTimer();t.accumulated=p.getLong("total",0);t.startedElapsed=p.getLong("elapsed",0);t.startedWall=p.getLong("wall",0);t.firstWall=p.getLong("first",0);t.boot=p.getInt("boot",0);t.running=p.getBoolean("running",false);return t;}
 static void store(Context c,TripTimer t){c.getSharedPreferences("trip_clock",0).edit().putLong("total",t.accumulated).putLong("elapsed",t.startedElapsed).putLong("wall",t.startedWall).putLong("first",t.firstWall).putInt("boot",t.boot).putBoolean("running",t.running).commit();}
 static void show(Context c,String action){c.startForegroundService(new Intent(c,TimerService.class).setAction(action));}
 static void dismiss(Context c){c.stopService(new Intent(c,TimerService.class));((NotificationManager)c.getSystemService(NOTIFICATION_SERVICE)).cancel(ID);}
 int boot(){return android.provider.Settings.Global.getInt(getContentResolver(),android.provider.Settings.Global.BOOT_COUNT,0);}
 public IBinder onBind(Intent i){return null;}
 static String channelId(Context c){NotificationManager manager=(NotificationManager)c.getSystemService(NOTIFICATION_SERVICE);NotificationChannel old=manager.getNotificationChannel("ysk_trip_timer");if(Build.VERSION.SDK_INT>=29&&old!=null&&old.hasUserSetImportance())return old.getId();return CHANNEL;}
 static void ensureChannel(Context c){NotificationManager manager=(NotificationManager)c.getSystemService(NOTIFICATION_SERVICE);NotificationChannel channel=new NotificationChannel(CHANNEL,"Prioritert tidtaking",NotificationManager.IMPORTANCE_HIGH);channel.setDescription("Kjøretid og stans: høyt prioritert varsel med Pause, Gjenoppta og Stopp.");channel.setSound(null,null);channel.enableVibration(false);manager.createNotificationChannel(channel);}
 public void onCreate(){super.onCreate();active=true;ensureChannel(this);}
 PendingIntent action(String name,int code){return PendingIntent.getForegroundService(this,code,new Intent(this,TimerService.class).setAction(name),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
 public int onStartCommand(Intent intent,int flags,int startId){TripTimer t=load(this);String command=intent==null?"show":intent.getAction();
  if("add_stop".equals(command)){SharedPreferences prefs=getSharedPreferences("draft",0);try{String raw=prefs.getString("payload","");if(raw.isEmpty())throw new IllegalArgumentException("Åpne et turskjema før du registrerer stans.");JSONObject p=new JSONObject(raw);p.put("stops",StopCounter.next(p.optString("stops","0")));prefs.edit().putString("payload",p.toString()).putLong("stops_version",prefs.getLong("stops_version",0)+1).commit();}catch(Exception e){android.widget.Toast.makeText(this,e.getMessage(),android.widget.Toast.LENGTH_LONG).show();}}
  if("pause".equals(command))t.stop(SystemClock.elapsedRealtime(),System.currentTimeMillis(),boot());
  if("resume".equals(command))t.start(SystemClock.elapsedRealtime(),System.currentTimeMillis(),boot());
  if("stop".equals(command)){
   t.stop(SystemClock.elapsedRealtime(),System.currentTimeMillis(),boot());store(this,t);
   SharedPreferences draft=getSharedPreferences("draft",0);try{String raw=draft.getString("payload","");if(!raw.isEmpty()){JSONObject p=new JSONObject(raw);p.put("minutes",t.accumulated/60000.0);draft.edit().putString("payload",p.toString()).commit();}}catch(Exception ignored){}
   getSharedPreferences("trip_clock",0).edit().putBoolean("completed",true).commit();stopForeground(STOP_FOREGROUND_REMOVE);stopSelf();return START_NOT_STICKY;
  }
  store(this,t);long elapsed=t.elapsed(SystemClock.elapsedRealtime(),System.currentTimeMillis(),boot());
  PendingIntent open=PendingIntent.getActivity(this,0,new Intent(this,MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);
  String count="?";try{count=new JSONObject(getSharedPreferences("draft",0).getString("payload","{}")).optString("stops","0");}catch(Exception ignored){}
  Notification.Builder n=new Notification.Builder(this,channelId(this)).setCategory(Notification.CATEGORY_SERVICE).setSmallIcon(android.R.drawable.ic_media_play).setContentTitle(t.running?"YSK · "+count+" unødige stanser":"YSK · Pause · "+count+" unødige stanser").setContentText(t.running?"Pause eller stopp kjøreturen":"Målt tid: "+TripTimer.format(elapsed)).setContentIntent(open).setOngoing(true).setOnlyAlertOnce(true).setWhen(System.currentTimeMillis()-elapsed).setShowWhen(t.running).setUsesChronometer(t.running);
  n.addAction(new Notification.Action.Builder(null,"🔴 + Stans",action("add_stop",3)).build());
  n.addAction(new Notification.Action.Builder(null,t.running?"Pause":"Gjenoppta",action(t.running?"pause":"resume",1)).build());
  n.addAction(new Notification.Action.Builder(null,"Stopp",action("stop",2)).build());
  startForeground(ID,n.build());return START_STICKY;
 }
 public void onDestroy(){active=false;stopForeground(STOP_FOREGROUND_REMOVE);super.onDestroy();}
}
