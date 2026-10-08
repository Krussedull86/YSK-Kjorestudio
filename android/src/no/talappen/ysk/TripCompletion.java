package no.talappen.ysk;
import java.util.Map;
/** Missing and deliberately omitted measurements have different meanings. */
public final class TripCompletion {
 public static final String[] KEYS={"driver","course","vehicle","minutes","km","liters","stops","trafikksikkerhet","avpassing","økning","komfort","date","start_time","teacher"};
 public static final String[] LABELS={"sjåfør","kurs","bil","forbrukt tid","km","liter","stopp","trafikksikkerhet","fartsavpassing","fartsøkning","komfort","dato","starttid","lærer"};
 public static String missing(Map<String,String> fields){StringBuilder out=new StringBuilder();for(int i=0;i<KEYS.length;i++){String value=fields.get(KEYS[i]);if(value==null||value.trim().isEmpty()){if(out.length()>0)out.append(", ");out.append(LABELS[i]);}}return out.toString();}
 private TripCompletion(){}
}
