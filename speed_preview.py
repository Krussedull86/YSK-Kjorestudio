"""Shared preview rules: blank means calculated, '-' means intentionally omitted."""
import math

def duration_minutes(raw):
 parts=str(raw).strip().replace(',','.').split(':')
 if len(parts)>3:raise ValueError('Ugyldig tid')
 values=[float(p) for p in parts]
 if any(not math.isfinite(v) or v<0 for v in values) or any(v>=60 for v in values[1:]):raise ValueError('Ugyldig tid')
 return values[0] if len(values)==1 else sum(v*60**i for i,v in enumerate(reversed(values)))/60

def calculated_speed(km,minutes,manual=''):
 if str(manual if manual is not None else '').strip():return None
 try:
  distance=float(str(km).replace(',','.'));duration=duration_minutes(minutes)
  if not math.isfinite(distance) or distance<0 or duration<=0:return None
  return 60*distance/duration
 except (ValueError,TypeError,OverflowError):return None
