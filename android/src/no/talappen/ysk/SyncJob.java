package no.talappen.ysk;
import android.app.job.*;import android.content.*;import java.util.concurrent.*;
public class SyncJob extends JobService {
 private final ConcurrentHashMap<Integer,Thread> threads=new ConcurrentHashMap<>();
 public static void schedule(Context c){JobScheduler s=c.getSystemService(JobScheduler.class);ComponentName name=new ComponentName(c,SyncJob.class);s.schedule(new JobInfo.Builder(71,name).setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY).setBackoffCriteria(30000,JobInfo.BACKOFF_POLICY_EXPONENTIAL).setPersisted(true).build());if(s.getPendingJob(72)==null)s.schedule(new JobInfo.Builder(72,name).setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY).setPeriodic(15*60*1000L).setPersisted(true).build());}
 public boolean onStartJob(JobParameters p){Thread t=new Thread(()->{boolean retry=false;try{String msg=Sync.run(this);getSharedPreferences("cloud",0).edit().putString("last_status",msg).apply();try(TripDb db=new TripDb(this)){retry=!db.rows(true).isEmpty()&&!getSharedPreferences("cloud",0).getString("url","").isEmpty();}}catch(Exception e){retry=!(e instanceof Sync.LoginRequired||e instanceof Sync.ApiFailure&&((Sync.ApiFailure)e).status==401);getSharedPreferences("cloud",0).edit().putString("last_status","Venter: "+e.getMessage()).apply();}if(threads.remove(p.getJobId(),Thread.currentThread()))jobFinished(p,retry);},"YSK-sync");threads.put(p.getJobId(),t);t.start();return true;}
 public boolean onStopJob(JobParameters p){Thread t=threads.remove(p.getJobId());if(t!=null)t.interrupt();return true;}
}
