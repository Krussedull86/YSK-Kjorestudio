import no.talappen.ysk.TripTimer;
public class TripTimerTest {
 static void eq(long a,long b){if(a!=b)throw new AssertionError(a+" != "+b);}
 public static void main(String[] args){
  TripTimer t=new TripTimer();t.start(1000,100000,1);eq(t.elapsed(61000,990000,1),60000); // wall-clock changes ignored
  t.stop(91000,190000,1);eq(t.elapsed(500000,999999,1),90000); // paused time excluded
  t.start(600000,300000,1);t.start(700000,400000,1);eq(t.elapsed(660000,360000,1),150000); // duplicate start ignored
  TripTimer restored=new TripTimer();restored.accumulated=t.accumulated;restored.startedElapsed=t.startedElapsed;restored.startedWall=t.startedWall;restored.boot=t.boot;restored.running=t.running;
  eq(restored.elapsed(900000,600000,1),390000); // app restart and screen-off time
  eq(restored.elapsed(10000,420000,2),210000); // phone reboot: wall-clock fallback
  eq(restored.elapsed(100,200000,2),90000); // no negative duration
  restored.reset();eq(restored.elapsed(99999,99999,3),0);if(restored.running)throw new AssertionError("reset still running");
  if(!TripTimer.format(3661000).equals("01:01:01"))throw new AssertionError("format");
  System.out.println("Trip timer start/stop/resume, restart, screen-off, reboot and clock-change tests passed.");
 }
}
