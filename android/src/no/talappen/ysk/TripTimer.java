package no.talappen.ysk;
/** Stopwatch state independent of Android; monotonic time includes screen-off sleep. */
public final class TripTimer {
 public long accumulated,startedElapsed,startedWall,firstWall;public int boot;public boolean running;
 public long elapsed(long monotonic,long wall,int currentBoot){if(!running)return accumulated;long delta=currentBoot==boot?monotonic-startedElapsed:wall-startedWall;return accumulated+Math.max(0,delta);}
 public void start(long monotonic,long wall,int currentBoot){if(running)return;if(firstWall==0)firstWall=wall;startedElapsed=monotonic;startedWall=wall;boot=currentBoot;running=true;}
 public void stop(long monotonic,long wall,int currentBoot){accumulated=elapsed(monotonic,wall,currentBoot);running=false;}
 public void reset(){accumulated=startedElapsed=startedWall=firstWall=0;running=false;}
 public static String format(long millis){long seconds=Math.max(0,millis)/1000;return String.format(java.util.Locale.ROOT,"%02d:%02d:%02d",seconds/3600,(seconds/60)%60,seconds%60);}
}
