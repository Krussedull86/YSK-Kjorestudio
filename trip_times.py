"""Clock times and elapsed minutes for retrospective registration."""
def clock_text(raw):
 raw=str(raw or '').strip().replace('.',':')
 if raw in ('','-'):return raw
 if ':' not in raw and raw.isdigit() and len(raw) in (3,4):raw=raw[:-2]+':'+raw[-2:]
 try:
  h,m=raw.split(':')
  if not h.isdigit() or not m.isdigit() or len(m)!=2 or not 0<=int(h)<24 or not 0<=int(m)<60:raise ValueError()
 except ValueError:raise ValueError('Klokkeslett: bruk timer og minutter, for eksempel 08:15.') from None
 return f'{int(h):02}:{int(m):02}'

def clock_minutes(start,end):
 start,end=clock_text(start),clock_text(end)
 if start in ('','-') or end in ('','-'):return None
 minutes=lambda t:int(t[:2])*60+int(t[3:])
 elapsed=(minutes(end)-minutes(start))%1440
 if elapsed==0:raise ValueError('Start og slutt er like. Skriv tidsbruk i minutter manuelt hvis turen varte et helt døgn.')
 return elapsed

