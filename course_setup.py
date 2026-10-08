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
def course_count(store,name):
 with store.conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS course_setup (name TEXT PRIMARY KEY, active_trips INTEGER NOT NULL)')
  row=c.execute('SELECT active_trips FROM course_setup WHERE name=?',(name,)).fetchone()
 return row[0] if row else 5
def save_course(store,name,count):
 name=name.strip();count=int(count)
 if not name or len(name)>100 or count not in range(1,6):raise ValueError('Velg kursnavn og 1–5 aktive turer.')
 with store.conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS course_setup (name TEXT PRIMARY KEY, active_trips INTEGER NOT NULL)')
  c.execute('INSERT OR REPLACE INTO course_setup VALUES (?,?)',(name,count))
def course_names(store):
 course_count(store,'')
 with store.conn() as c:return [r[0] for r in c.execute('SELECT name FROM course_setup ORDER BY name')]
def import_courses(store,rows):
 with store.conn() as c:
  c.execute('CREATE TABLE IF NOT EXISTS course_setup (name TEXT PRIMARY KEY, active_trips INTEGER NOT NULL)')
  c.execute('DELETE FROM course_setup')
  for row in rows:c.execute('INSERT INTO course_setup VALUES (?,?)',(row['name'],row['active_trips']))
