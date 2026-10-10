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
 public void editEvent(int stop,String status,String text){if(stop<1||stop>events.size()||!("ramp".equals(status)||"aborted".equals(status))||text==null||text.length()>300)throw new IllegalArgumentException("Velg registrert stopp, status og kommentar på maks 300 tegn.");Event e=events.get(stop-1);events.set(stop-1,new Event(e.stop,status,e.elapsedMillis,text));}
 public void comment(int stop,String text){if(stop<1||stop>events.size()||text==null||text.length()>300)throw new IllegalArgumentException("Kommentar: maks 300 tegn.");Event e=events.get(stop-1);events.set(stop-1,new Event(e.stop,e.status,e.elapsedMillis,text));}
 public long returnMillis(long monotonic,long wall,int boot){if(events.size()!=deadlines.length)return 0;return Math.max(0,elapsed(monotonic,wall,boot)-events.get(events.size()-1).elapsedMillis);}
 public int remainingStops(){return Math.max(0,deadlines.length-events.size());}
 public long remainingMillis(long elapsed){return Math.max(0,Math.round(expectedMinutes*60000)-elapsed);}
 public String remainingText(long elapsed){int stops=remainingStops();long left=remainingMillis(elapsed);String text=stops+" stopp igjen · "+String.format(Locale.ROOT,"%02d:%02d:%02d",left/3600000,left/60000%60,left/1000%60)+" igjen";if(stops>0)text+=String.format(Locale.getDefault(),"\nTilgjengelig snitt per stopp: %.1f min",left/60000.0/stops)+" (inkl. retur)";else text+="\nRetur til skolen";return text;}
 public void finish(long monotonic,long wall,int boot){if(events.size()!=deadlines.length)throw new IllegalArgumentException("Merk alle stopp til rampe eller avbrutt først.");long value=elapsed(monotonic,wall,boot);if(value>2592000000L)throw new IllegalArgumentException("Ugyldig oppdragstid.");finishedMillis=value;}
}

