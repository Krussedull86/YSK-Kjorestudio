package no.talappen.ysk;
import java.util.*;
/** Continuous delivery clock. Waiting/loading/breaks are included. */
public final class DistributionRun {
 public final double expectedMinutes; public final double[] deadlines;public final long startedWall,startedElapsed;public final int startedBoot;
 public final List<Event> events=new ArrayList<>();public long finishedMillis=-1;
 public static final class Event {public final int stop;public final String status,reason;public final long elapsedMillis;public Event(int s,String state,long elapsed,String why){stop=s;status=state;elapsedMillis=elapsed;reason=why;}}
 public DistributionRun(double expected,double[] limits,long wall,long elapsed,int boot){validatePlan(limits.length,expected,limits);if(limits.length==0||wall<=0)throw new IllegalArgumentException("Distribusjonsplan mangler.");expectedMinutes=expected;deadlines=limits.clone();startedWall=wall;startedElapsed=elapsed;startedBoot=boot;}
 public static double[] validatePlan(int count,double total,double[] limits){
  if(count<0||count>30||!Double.isFinite(total)||total<0||total>1440)throw new IllegalArgumentException("Velg 0–30 stopp og inntil 1440 minutter.");
  if(count==0){if(total!=0||limits.length!=0)throw new IllegalArgumentException("Angi antall stopp først.");return new double[0];}
  if(total<=0)throw new IllegalArgumentException("Angi forventet gjennomføringstid.");double[] result=limits.length==0?new double[count]:limits.clone();if(result.length!=count)throw new IllegalArgumentException("Angi én frist per stopp, adskilt med ;");
  for(int i=0;i<count;i++){if(limits.length==0)result[i]=total*(i+1)/count;if(!Double.isFinite(result[i])||result[i]<=0||result[i]>total||i>0&&result[i]<=result[i-1])throw new IllegalArgumentException("Frister må være stigende minutter fra start, innen totaltiden.");}return result;
 }
 public long elapsed(long monotonic,long wall,int boot){if(finishedMillis>=0)return finishedMillis;long value=startedBoot==boot&&startedElapsed>=0?monotonic-startedElapsed:wall-startedWall;return Math.max(events.isEmpty()?0:events.get(events.size()-1).elapsedMillis,value);}
 public void restoreEvent(int stop,String status,long elapsed,String reason){if(finishedMillis>=0||stop!=events.size()+1||stop>deadlines.length||!(status.equals("ramp")||status.equals("aborted"))||elapsed<0||elapsed>2592000000L||!events.isEmpty()&&elapsed<events.get(events.size()-1).elapsedMillis||reason==null||reason.length()>300)throw new IllegalArgumentException("Ugyldig distribusjonsstopp.");events.add(new Event(stop,status,elapsed,reason));}
 public void mark(String status,String reason,long monotonic,long wall,int boot){restoreEvent(events.size()+1,status,elapsed(monotonic,wall,boot),reason);}
 public void finish(long monotonic,long wall,int boot){if(events.size()!=deadlines.length)throw new IllegalArgumentException("Merk alle stopp til rampe eller avbrutt først.");long value=elapsed(monotonic,wall,boot);if(value>2592000000L)throw new IllegalArgumentException("Ugyldig oppdragstid.");finishedMillis=value;}
 public static String delta(double minutes){return Math.abs(minutes)<0.005?"I rute":String.format(java.util.Locale.getDefault(),"%.1f min %s",Math.abs(minutes),minutes>0?"over tid":"foran planen");}
}
