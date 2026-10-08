package no.talappen.ysk;
public final class StopCounter {
 private StopCounter(){}
 public static int next(String raw){double v;try{String s=raw==null?"":raw.trim();v=s.isEmpty()?0:Double.parseDouble(s.replace(',','.'));}catch(Exception e){throw new IllegalArgumentException("Skriv et helt, ikke-negativt antall stopp.");}
 if(!Double.isFinite(v)||v<0||v!=Math.floor(v)||v>=Integer.MAX_VALUE)throw new IllegalArgumentException("Skriv et helt, ikke-negativt antall stopp.");return (int)v+1;}
}
