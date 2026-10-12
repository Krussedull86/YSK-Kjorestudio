package no.talappen.ysk;
import android.app.*;import android.widget.*;import java.util.*;import java.text.*;import org.json.*;
/** Explicit retrospective entry; never starts the foreground timer. */
final class ManualDistribution {
 static void open(MainActivity a){
  if(a.distributionRun!=null&&a.distributionRun.finishedMillis<0){a.alert("Avslutt den pågående turen før du endrer tidene.");return;}
  DistributionRun old=a.distributionRun;
  try{
   JSONObject plan=a.courseDistribution(a.inputs.get("course").getText().toString());int count=old!=null?old.deadlines.length:plan==null?0:plan.optInt("stop_count");
   if(count==0){EditText field=new EditText(a);field.setHint("Antall leveringsstopp (1–30)");field.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);a.dialog().setTitle("Etterregistrer distribusjon").setView(field).setNegativeButton("Avbryt",null).setPositiveButton("Fortsett",(d,w)->{try{int n=Integer.parseInt(field.getText().toString());if(n<1||n>30)throw new Exception("Velg 1–30 stopp.");edit(a,null,n,0);}catch(Exception e){a.alert(e.getMessage());}}).show();return;}
   edit(a,old,count,old!=null?old.expectedMinutes:plan.optDouble("expected_minutes"));
  }catch(Exception e){a.alert(e.getMessage());}
 }
 static void edit(MainActivity a,DistributionRun original,int count,double expected){
  final String draftId=a.editId;final int selectedTrip=a.trip;
  LinearLayout panel=new LinearLayout(a);panel.setOrientation(1);panel.setPadding(a.dp(16),a.dp(8),a.dp(16),a.dp(8));panel.addView(a.text("Faktiske tider i minutter fra start ved skolen. Totaltiden inkluderer retur. Alle stopp må merkes som rampe eller avbrutt.",14,a.MUTED));
  EditText date=a.setupField(panel,"Dato (ÅÅÅÅ-MM-DD)",a.inputs.get("date").getText().toString(),false),startTime=a.setupField(panel,"Starttid ved skolen (TT:MM)",a.inputs.get("start_time").getText().toString(),false);
  EditText total=a.setupField(panel,"Totalt skole–skole (min)",original==null?a.inputs.get("minutes").getText().toString():String.format(Locale.ROOT,"%.4f",original.finishedMillis/60000.0),false);
  EditText planned=a.setupField(panel,"Forventet totaltid (min)",expected>0?String.valueOf(expected):"",false);planned.setEnabled(original==null);
  ArrayList<EditText> times=new ArrayList<>(),notes=new ArrayList<>();ArrayList<Spinner> states=new ArrayList<>();
  for(int i=0;i<count;i++){DistributionRun.Event e=original==null?null:original.events.get(i);times.add(a.setupField(panel,"Stopp "+(i+1)+": minutter fra start",e==null?"":String.format(Locale.ROOT,"%.4f",e.elapsedMillis/60000.0),false));Spinner state=new Spinner(a);state.setAdapter(new ArrayAdapter<String>(a,android.R.layout.simple_spinner_dropdown_item,new String[]{"Velg status","Rygget til rampe","Avbrutt"}));state.setSelection(e==null?0:e.status.equals("ramp")?1:2);states.add(state);panel.addView(state);notes.add(a.setupField(panel,"Kommentar ved stopp "+(i+1),e==null?"":e.reason,false));}
  ScrollView view=new ScrollView(a);view.addView(panel);AlertDialog dialog=a.dialog().setTitle("Etterregistrer / endre stopptider").setView(view).setNegativeButton("Avbryt",null).setPositiveButton("Bruk stopplogg",null).show();
  dialog.getButton(-1).setOnClickListener(v->{try{
   if(!a.authenticated||!a.page.equals("form")||a.trip!=selectedTrip||!Objects.equals(a.editId,draftId)||a.distributionRun!=original)throw new Exception("Turen er endret. Åpne stopploggen på nytt.");
   SimpleDateFormat format=new SimpleDateFormat("yyyy-MM-dd HH:mm",Locale.ROOT);format.setLenient(false);String stamp=date.getText().toString().trim()+" "+startTime.getText().toString().trim();ParsePosition pos=new ParsePosition(0);Date start=format.parse(stamp,pos);if(start==null||pos.getIndex()!=stamp.length())throw new Exception("Fyll inn riktig dato og starttid i turen først.");
   double duration=a.duration(total.getText().toString()),estimate=a.duration(planned.getText().toString());double[] limits=original==null?DistributionRun.validatePlan(count,estimate,new double[0]):original.deadlines;
   long[] elapsed=new long[count];String[] status=new String[count],comments=new String[count];for(int i=0;i<count;i++){double minutes=a.duration(times.get(i).getText().toString());if(!Double.isFinite(minutes)||minutes<0||minutes>43200)throw new Exception("Kontroller stopptidene.");elapsed[i]=Math.round(minutes*60000);if(states.get(i).getSelectedItemPosition()==0)throw new Exception("Velg status for alle stopp.");status[i]=states.get(i).getSelectedItemPosition()==1?"ramp":"aborted";comments[i]=notes.get(i).getText().toString().trim();}
   if(!Double.isFinite(duration)||duration<=0||duration>43200)throw new Exception("Kontroller totaltiden.");
   DistributionRun run=DistributionRun.completed(estimate,limits,start.getTime(),elapsed,status,comments,Math.round(duration*60000));a.distributionRun=run;a.inputs.get("date").setText(date.getText().toString().trim());a.inputs.get("start_time").setText(startTime.getText().toString().trim());a.inputs.get("minutes").setText(String.format(Locale.ROOT,"%.4f",duration));a.persistDraft();a.paintDistribution();dialog.dismiss();a.alert("Stopploggen er lagt i utkastet. Trykk Lagre tur for å lagre alle data.");
  }catch(Exception e){a.alert(e.getMessage()==null?"Kontroller tidene og kommentarfeltene.":e.getMessage());}});
 }
}
