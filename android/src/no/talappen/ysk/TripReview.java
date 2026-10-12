package no.talappen.ysk;
import android.widget.*;import org.json.*;import java.util.*;
/** Read-only review: opening data never starts a clock or changes a draft. */
final class TripReview {
 static void show(MainActivity a,JSONObject p,Runnable edit){
  LinearLayout panel=new LinearLayout(a);panel.setOrientation(1);panel.setPadding(a.dp(16),a.dp(8),a.dp(16),a.dp(12));
  String[][] fields={{"driver","Elev"},{"course","Kurs"},{"vehicle","Bil"},{"date","Dato"},{"start_time","Starttid"},{"minutes","Forbrukt tid (min)"},{"km","Kjørt distanse (km)"},{"liters","Forbruk totalt (liter)"},{"stops","Unødige stopp"},{"average_speed","Gjennomsnittsfart (km/t)"},{"trafikksikkerhet","Trafikksikkerhet"},{"avpassing","Fartsavpassing"},{"økning","Fartsøkning"},{"komfort","Komfort"},{"teacher","Lærer / signatur"},{"notes","Notater"},{"updated","Sist endret"}};
  for(String[] f:fields){String value=p.isNull(f[0])?"":p.optString(f[0]);if(f[0].equals("average_speed")&&value.trim().isEmpty()){double km=p.optDouble("km",Double.NaN),min=p.optDouble("minutes",Double.NaN);if(Double.isFinite(km)&&km>=0&&Double.isFinite(min)&&min>0)value=String.format(Locale.getDefault(),"%.1f (beregnet, inkludert stopp)",60*km/min);}panel.addView(a.text(f[1]+": "+(value.trim().isEmpty()?"Ikke registrert":value.equals("-")?"Bevisst utelatt":value),15,a.TEXT));}
  double km=p.optDouble("km",Double.NaN),liters=p.optDouble("liters",Double.NaN);if(km>0&&Double.isFinite(liters))panel.addView(a.text(String.format(Locale.getDefault(),"Beregnet forbruk: %.2f liter per mil",10*liters/km),16,a.TEAL));
  try{DistributionRun r=DistributionState.read(p.optJSONObject("distribution"));if(r!=null){panel.addView(a.text("Distribusjonsstopp",18,a.TEAL));panel.addView(a.text("Forventet skole–skole: "+r.expectedMinutes+" min",14,a.MUTED));long prior=0;for(DistributionRun.Event e:r.events){panel.addView(a.text(a.stopLine(e,prior),15,a.TEXT));prior=e.elapsedMillis;}if(r.finishedMillis>=0){panel.addView(a.text(String.format(Locale.getDefault(),"Tilbake ved skolen: %.1f min fra start\nRetur fra siste stopp: %.1f min",r.finishedMillis/60000.0,(r.finishedMillis-prior)/60000.0),16,a.TEAL));}else panel.addView(a.text("Turen er ikke avsluttet",15,a.MUTED));}}catch(Exception e){panel.addView(a.text("Kan ikke lese stopploggen: "+e.getMessage(),14,a.MUTED));}
  ScrollView view=new ScrollView(a);view.addView(panel);a.dialog().setTitle(a.tripName(p.optInt("trip"))).setView(view).setNegativeButton("Lukk",null).setPositiveButton("Rediger tur",(d,w)->edit.run()).show();
 }
}
