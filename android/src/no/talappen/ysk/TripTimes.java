package no.talappen.ysk;
import java.util.Locale;
/** Minute-precision wall-clock entry; a lower end time means the following day. */
public final class TripTimes {
 public static String clock(String value){String v=value.trim().replace('.',':');if(v.isEmpty()||v.equals("-"))return v;if(v.matches("[0-9]{3,4}"))v=v.substring(0,v.length()-2)+":"+v.substring(v.length()-2);if(!v.matches("[0-9]{1,2}:[0-9]{2}"))throw new IllegalArgumentException("Skriv klokkeslett som 08:15.");String[] parts=v.split(":");int h=Integer.parseInt(parts[0]),m=Integer.parseInt(parts[1]);if(h>23||m>59)throw new IllegalArgumentException("Kontroller timer og minutter.");return String.format(Locale.ROOT,"%02d:%02d",h,m);}
 public static Integer minutes(String start,String end){start=clock(start);end=clock(end);if(start.isEmpty()||end.isEmpty()||start.equals("-")||end.equals("-"))return null;int a=Integer.parseInt(start.substring(0,2))*60+Integer.parseInt(start.substring(3)),b=Integer.parseInt(end.substring(0,2))*60+Integer.parseInt(end.substring(3));int n=(b-a+1440)%1440;if(n==0)throw new IllegalArgumentException("Start og slutt er like. Skriv forbrukt tid manuelt.");return n;}
}
