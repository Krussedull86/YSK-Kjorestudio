import no.talappen.ysk.DistributionRun;
public class DistributionRunTest {
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 static void rejects(Runnable f){try{f.run();throw new AssertionError("Expected rejection");}catch(IllegalArgumentException expected){}}
 public static void main(String[] args){
  double[] d=DistributionRun.validatePlan(3,60,new double[0]);check(d[0]==20&&d[2]==60);rejects(()->DistributionRun.validatePlan(3,60,new double[]{20,10,60}));rejects(()->DistributionRun.validatePlan(31,60,new double[0]));
  DistributionRun r=new DistributionRun(60,d,10000000,1000,2);check(r.elapsed(601000,10000000,2)==600000); // monotonic, ignores wall adjustment
  r.mark("ramp","",1081000,10000000,2);check(r.events.get(0).elapsedMillis==1080000);r.mark("aborted","Stengt rampe",2581000,10000000,2);check(r.events.get(1).elapsedMillis-r.events.get(0).elapsedMillis==1500000);rejects(()->r.finish(3001000,10000000,2));r.mark("ramp","",4081000,10000000,2);r.finish(4201000,10000000,2);check(r.finishedMillis==4200000&&r.elapsed(9999999,99999999,2)==4200000);rejects(()->r.mark("ramp","",9999999,99999999,2));
  DistributionRun reboot=new DistributionRun(60,d,10000000,1000,2);check(reboot.elapsed(100,11200000,3)==1200000);reboot.restoreEvent(1,"ramp",1200000,"");check(reboot.elapsed(100,9000000,3)==1200000);rejects(()->reboot.restoreEvent(2,"aborted",1000,""));
  check(reboot.remainingStops()==2);check(reboot.remainingMillis(1200000)==2400000);check(reboot.remainingMillis(4000000)==0);check(r.remainingStops()==0);check(reboot.remainingText(1200000).contains("20,0")||reboot.remainingText(1200000).contains("20.0"));
  r.comment(1,"Trang rampe");check(r.events.get(0).reason.equals("Trang rampe")&&r.events.get(0).elapsedMillis==1080000);check(r.returnMillis(9999999,99999999,2)==120000);rejects(()->r.comment(4,"No such stop"));d[0]=1;check(r.deadlines[0]==20);System.out.println("Delivery clock: continuous timing, reboot recovery, snapshots, aborts and finish validation passed.");
 }
}
