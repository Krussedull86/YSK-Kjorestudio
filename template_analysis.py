"""Only analyse runs with identical school, vehicle and parameter/scoring definitions."""
import json,math

def comparison_key(run):
 s=run['snapshot'];base=s.get('base_trip');identity='optimal' if base in (1,2,3) else run['template_id']
 return (run['organization_id'],run['payload']['course'],run['payload']['vehicle'],identity,run['template_revision'],json.dumps(s['parameters'],sort_keys=True,ensure_ascii=False))
def numeric(value):return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value)
def comparable(rows,selected):
 key=comparison_key(selected);return sorted([r for r in rows if comparison_key(r)==key and r['payload']['driver']==selected['payload']['driver']],key=lambda r:(r['snapshot'].get('base_trip') or 99,r['payload']['date'],r['created_at']))
def percent(a,b):return None if not numeric(a) or not numeric(b) or a==0 else 100*(b-a)/a
