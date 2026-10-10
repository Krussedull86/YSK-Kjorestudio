import json
from distribution import plan
"""Shared trip names and course settings, with old courses defaulting to five trips."""
NAMES=['Optimaltur 1','Optimaltur 2','Optimaltur 3','Transportoppdrag 1 (distribusjon)','Transportoppdrag 2 (langtur)']
def trip_number(value):
 if str(value) in ('Alle','Første tur'):return value
 for i,name in enumerate(NAMES,1):
  if value==name:return i
 return int(value)
def trip_name(value):
 try:return NAMES[int(value)-1] if 1<=int(value)<=5 else str(value)
 except (ValueError,TypeError):return str(value)
def ensure(c):
 c.execute('CREATE TABLE IF NOT EXISTS course_setup (name TEXT PRIMARY KEY, active_trips INTEGER NOT NULL)')
 if 'distribution_plan' not in [r[1] for r in c.execute('PRAGMA table_info(course_setup)')]:c.execute("ALTER TABLE course_setup ADD COLUMN distribution_plan TEXT NOT NULL DEFAULT '{}' ")
def course_config(store,name):
 with store.conn() as c:
  ensure(c);row=c.execute('SELECT active_trips,distribution_plan FROM course_setup WHERE name=?',(name,)).fetchone()
 return {'active_trips':row[0] if row else 5,'distribution_plan':json.loads(row[1]) or plan() if row else plan()}
def course_count(store,name):return course_config(store,name)['active_trips']
def save_course(store,name,count,distribution_plan=None):
 name=name.strip();count=int(count)
 if not name or len(name)>100 or count not in range(1,6):raise ValueError('Velg kursnavn og 1–5 aktive turer.')
 value=distribution_plan if distribution_plan is not None else course_config(store,name)['distribution_plan']
 value=plan(value.get('stop_count',0),value.get('expected_minutes',0),value.get('deadlines'))
 with store.conn() as c:
  ensure(c);c.execute('INSERT OR REPLACE INTO course_setup (name,active_trips,distribution_plan) VALUES (?,?,?)',(name,count,json.dumps(value)))
def course_names(store):
 with store.conn() as c:
  ensure(c);return [r[0] for r in c.execute('SELECT name FROM course_setup ORDER BY name')]
def import_courses(store,rows):
 with store.conn() as c:
  ensure(c);c.execute('DELETE FROM course_setup')
  for row in rows:
   value=row.get('distribution_plan') or plan();value=plan(value.get('stop_count',0),value.get('expected_minutes',0),value.get('deadlines'))
   c.execute('INSERT INTO course_setup (name,active_trips,distribution_plan) VALUES (?,?,?)',(row['name'],row['active_trips'],json.dumps(value)))
