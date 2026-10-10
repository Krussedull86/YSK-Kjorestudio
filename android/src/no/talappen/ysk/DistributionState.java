package no.talappen.ysk;
import org.json.*;
/** Shared delivery draft codec for the screen and notification actions. */
final class DistributionState {
 static DistributionRun read(JSONObject d)throws Exception{
  if(d==null)return null;if(d.getInt("version")!=1)throw new Exception("Ukjent distribusjonslogg.");JSONArray limits=d.getJSONArray("deadlines");double[] a=new double[limits.length()];for(int i=0;i<a.length;i++)a[i]=limits.getDouble(i);JSONObject c=d.optJSONObject("clock");DistributionRun r=new DistributionRun(d.getDouble("expected_minutes"),a,d.getLong("started_at"),c==null?-1:c.getLong("elapsed"),c==null?-1:c.getInt("boot"));JSONArray events=d.getJSONArray("events");for(int i=0;i<events.length();i++){JSONObject e=events.getJSONObject(i);r.restoreEvent(e.getInt("stop"),e.getString("status"),Math.round(e.getDouble("elapsed_minutes")*60000),e.optString("reason"));}if(!d.isNull("finished_minutes")){long f=Math.round(d.getDouble("finished_minutes")*60000);if(r.events.size()!=a.length||f<0||f>2592000000L||f<r.events.get(r.events.size()-1).elapsedMillis)throw new Exception("Ugyldig avslutning.");r.finishedMillis=f;}return r;
 }
 static JSONObject write(DistributionRun r,boolean clock)throws Exception{
  JSONObject d=new JSONObject().put("version",1).put("started_at",r.startedWall).put("expected_minutes",r.expectedMinutes).put("deadlines",new JSONArray(r.deadlines));JSONArray events=new JSONArray();for(DistributionRun.Event e:r.events)events.put(new JSONObject().put("stop",e.stop).put("status",e.status).put("elapsed_minutes",e.elapsedMillis/60000.0).put("reason",e.reason));d.put("events",events).put("finished_minutes",r.finishedMillis<0?JSONObject.NULL:r.finishedMillis/60000.0);if(clock)d.put("clock",new JSONObject().put("elapsed",r.startedElapsed).put("boot",r.startedBoot));return d;
 }
}
