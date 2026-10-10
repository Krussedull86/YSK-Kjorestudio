"""Printable, blank student forms generated from the selected school templates."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

CLASSIC_FIELDS=[
 ('start_time','Starttid','text',''),('minutes','Forbrukt tid','minutes','min'),
 ('km','Kjørt distanse','number','km'),('average_speed','Gjennomsnittsfart','number','km/t'),
 ('stops','Unødige stopp','integer',''),('liters','Forbruk totalt','number','liter'),
 ('fuel','Forbruk per mil','fuel','l/mil'),('score','Kjørepoeng','number',''),
 ('trafikksikkerhet','Trafikksikkerhet','rating',''),('avpassing','Fartsavpassing','rating',''),
 ('okning','Fartsøkning','rating',''),('komfort','Komfort','rating',''),('notes','Notater','text','')]

def classic_templates(store,course):
 from course_setup import NAMES,course_config
 config=course_config(store,course);result=[]
 for i,name in enumerate(NAMES[:config['active_trips']],1):
  result.append({'name':name,'parameters':[dict(id=id,label=label,type=type_,unit=unit,required=False) for id,label,type_,unit in CLASSIC_FIELDS], 'compact':True, 'stop_count':config['distribution_plan']['stop_count'] if i==4 else 0,'expected_minutes':config['distribution_plan']['expected_minutes'] if i==4 else 0})
 return result

def create_forms(path,students,course,templates,teacher='',vehicle='',date=''):
 """Blank A4 forms. Every field and stop is retained, with page breaks as needed."""
 from reportlab.pdfgen import canvas
 from reportlab.lib.pagesizes import A4
 from reportlab.lib.styles import ParagraphStyle
 from reportlab.platypus import Paragraph
 from reportlab.pdfbase import pdfmetrics
 from reportlab.pdfbase.ttfonts import TTFont
 import reportlab
 names=list(dict.fromkeys(s.strip() for s in students if s.strip()))
 if not names or not templates:raise ValueError('Velg minst én elev og én tur.')
 fontdir=Path(reportlab.__file__).parent/'fonts'
 for name,file in [('YSK','Vera.ttf'),('YSK-Bold','VeraBd.ttf')]:
  if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(fontdir/file)))
 c=canvas.Canvas(str(path),pagesize=A4);c.setTitle('YSK Kjørestudio - elevskjema');c.setAuthor('YSK Kjørestudio')
 width,height=A4;margin=36;inner=width-2*margin;page=0;y=0;student=''
 style=ParagraphStyle('field',fontName='YSK',fontSize=8,leading=10)
 def paragraph(text,x,top,w):
  p=Paragraph(escape(str(text)),style);_,h=p.wrap(w,10000);p.drawOn(c,x,top-h);return h
 def footer():
  c.setFont('YSK',8);c.setFillColorRGB(.35,.35,.35);c.drawString(margin,24,'YSK Kjørestudio - registreringsskjema');c.drawRightString(width-margin,24,f'Side {page}');c.setFillColorRGB(0,0,0)
 def new_page():
  nonlocal page,y
  if page:footer();c.showPage()
  page+=1;c.setFont('YSK-Bold',17);c.drawString(margin,height-48,'YSK Kjørestudio');y=height-68
  y-=paragraph('Elev: '+student,margin,y,inner)+5
  y-=paragraph('Kurs: '+course,margin,y,inner)+5
  y-=paragraph('Dato: '+(date or '________________')+'    Bil: '+(vehicle or '________________'),margin,y,inner)+5
  y-=paragraph('Lærer: '+(teacher or '________________'),margin,y,inner)+12
 def heading(name,continued=False):
  nonlocal y
  if y<160:new_page()
  c.setFillColorRGB(.92,.94,.95);c.rect(margin,y-24,inner,24,fill=1,stroke=0);c.setFillColorRGB(0,0,0);c.setFont('YSK-Bold',10)
  y-=5+paragraph(name+(' (forts.)' if continued else ''),margin+6,y-4,inner-12)+14
 def row(fields,name):
  nonlocal y
  cellwidth=inner/len(fields);labels=[('Gj.snittsfart' if len(fields)==8 and p.get('id')=='average_speed' else p['label'])+(' ('+p.get('unit','')+')' if p.get('unit') else '') for p in fields]
  labelheight=max(Paragraph(escape(label),style).wrap(cellwidth-12,10000)[1] for label in labels)
  choiceheights=[Paragraph(escape(' / '.join(p.get('options',[])) if p['type']=='choice' else 'Svak / Middels / Bra' if p['type']=='rating' else 'Ja / Nei' if p['type']=='boolean' else ''),style).wrap(cellwidth-12,10000)[1] for p in fields]
  writing=24 if any(p['type']=='text' for p in fields) else 18
  h=labelheight+max(choiceheights)+writing+10
  if y-h<65:new_page();heading(name,True)
  for i,p in enumerate(fields):
   x=margin+i*cellwidth;c.setLineWidth(.5);c.rect(x,y-h,cellwidth,h);paragraph(labels[i],x+6,y-6,cellwidth-12)
   if p['type'] in ('rating','boolean','choice'):
    options=p.get('options',[]) if p['type']=='choice' else ['Svak','Middels','Bra'] if p['type']=='rating' else ['Ja','Nei']
    paragraph(' / '.join(options),x+6,y-10-labelheight,cellwidth-12)
  y-=h
 for student in names:
  new_page()
  for template in templates:
   name=template['name']
   if template.get('compact') and y<310:new_page()
   heading(name);group=[]
   limit=8 if template.get('compact') else 4
   for p in template['parameters']:
    wide=p['type'] in ('text','choice') and not (template.get('compact') and p['id']=='start_time')
    category='rating' if p['type'] in ('rating','boolean') else 'numeric'
    previous='rating' if group and group[0]['type'] in ('rating','boolean') else 'numeric'
    if group and (wide or category!=previous):row(group,name);group=[]
    if wide:row([p],name)
    else:
     group.append(p)
     if len(group)==(4 if category=='rating' else limit):row(group,name);group=[]
   if group:row(group,name)
   if template.get('stop_count',0):
    expected=template.get('expected_minutes',0)
    row([dict(label='Forventet tid skole - skole',type='minutes',unit='min'),dict(label=f'Planlagt: {expected:g} minutter',type='text')],name)
    for stop in range(1,template['stop_count']+1):
     row([dict(label=f'Stopp {stop}: ankomst / samlet tid',type='minutes'),dict(label='Tid siden forrige stopp',type='minutes'),dict(label='Rygget til rampe',type='boolean'),dict(label='Stopp avbrutt',type='boolean')],name)
     row([dict(label=f'Kommentar ved rampe {stop}',type='text')],name)
    row([dict(label='Tilbake ved skolen / avsluttet',type='text'),dict(label='Retur fra siste stopp (min)',type='minutes')],name)
   if y<90:new_page();heading(name,True)
   y-=16;c.setFont('YSK',9);c.drawString(margin,y,'Signatur lærer: __________________________________________');y-=12
 footer();c.save();return page

class FormsDialog:
 def __init__(self,app,catalog,cache,runs):
  import tkinter as tk
  from tkinter import ttk,messagebox,filedialog
  self.win=win=tk.Toplevel(app.root);win.title('Lag papirskjema / PDF');win.geometry('820x760')
  from course_setup import course_names
  classic=app.store.all(include_unscored=True)
  courses=sorted(set(course_names(app.store)+[r['course'] for r in classic]+[r['payload']['course'] for r in runs]+[r['name'] for r in catalog['courses']]))
  course=tk.StringVar();ttk.Label(win,text='Kurs').pack(anchor='w',padx=12);box=ttk.Combobox(win,textvariable=course,values=courses);box.pack(fill='x',padx=12)
  mode=tk.StringVar(value='templates');toolbar=ttk.Frame(win);toolbar.pack(fill='x',padx=12,pady=6)
  ttk.Radiobutton(toolbar,text='Turmaler / egendefinerte turer',variable=mode,value='templates').pack(side='left');ttk.Radiobutton(toolbar,text='Vanlige turer 1-5',variable=mode,value='classic').pack(side='left')
  ttk.Label(win,text='Elever - ett navn per linje. Listen kan redigeres før utskrift.').pack(anchor='w',padx=12)
  names=tk.Text(win,height=8);names.pack(fill='x',padx=12)
  roster_file=Path(cache)/'paper_rosters.json';rosters={}
  try:rosters=json.loads(roster_file.read_text(encoding='utf-8'))
  except (OSError,ValueError):pass
  choices=ttk.Frame(win);choices.pack(fill='both',expand=True,padx=12,pady=8);canvas=tk.Canvas(choices,highlightthickness=0);bar=ttk.Scrollbar(choices,command=canvas.yview);canvas.configure(yscrollcommand=bar.set);bar.pack(side='right',fill='y');canvas.pack(fill='both',expand=True);inner=ttk.Frame(canvas);item=canvas.create_window(0,0,window=inner,anchor='nw');inner.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.bind('<Configure>',lambda e:canvas.itemconfigure(item,width=e.width))
  selections=[];last_course=[None]
  def refresh(*args):
   if last_course[0] is not None:rosters[last_course[0]]=[n.strip() for n in names.get('1.0','end').splitlines() if n.strip()]
   last_course[0]=course.get()
   names.delete('1.0','end');students=rosters.get(course.get(),sorted(set([r['driver'] for r in classic if r['course']==course.get()]+[r['payload']['driver'] for r in runs if r['payload']['course']==course.get()])))
   names.insert('1.0','\n'.join(students));selections.clear()
   for w in inner.winfo_children():w.destroy()
   assigned=next((r['template_ids'] for r in catalog['courses'] if r['name']==course.get()),None)
   templates=classic_templates(app.store,course.get()) if mode.get()=='classic' else [dict(t['definition'],revision=t['revision']) for t in catalog['templates'] if assigned is None or t['id'] in assigned]
   from course_setup import course_config
   plan=course_config(app.store,course.get())['distribution_plan']
   for template in templates:
    if template.get('base_trip')==4:template.update(stop_count=plan['stop_count'],expected_minutes=plan['expected_minutes'])
    selected=tk.BooleanVar(value=True);selections.append((template,selected));ttk.Checkbutton(inner,text=template['name']+(' · v'+str(template['revision']) if 'revision' in template else ''),variable=selected).pack(anchor='w',pady=3)
   ttk.Label(inner,text='Alle parametre skrives ut. Nye elever kan legges til i listen ovenfor.').pack(anchor='w',pady=8)
  box.bind('<<ComboboxSelected>>',refresh);mode.trace_add('write',refresh)
  meta=ttk.Frame(win);meta.pack(fill='x',padx=12);fields={}
  for label in ('Dato','Bil','Lærer'):
   ttk.Label(meta,text=label).pack(side='left',padx=3);value=tk.StringVar();fields[label]=value;ttk.Entry(meta,textvariable=value,width=18).pack(side='left')
  status=tk.StringVar();ttk.Label(win,textvariable=status,wraplength=780).pack(fill='x',padx=12,pady=8)
  def export():
   students=list(dict.fromkeys(n.strip() for n in names.get('1.0','end').splitlines() if n.strip()));templates=[t for t,v in selections if v.get()]
   if not students or not templates or not course.get().strip():messagebox.showerror('Velg innhold','Fyll inn kurs, minst én elev og minst én tur.',parent=win);return
   path=filedialog.asksaveasfilename(parent=win,title='Lagre elevskjema',defaultextension='.pdf',filetypes=[('PDF','*.pdf')],initialfile='YSK_elevskjema.pdf')
   if not path:return
   try:
    pages=create_forms(path,students,course.get().strip(),templates,fields['Lærer'].get(),fields['Bil'].get(),fields['Dato'].get());rosters[course.get()]=students;roster_file.write_text(json.dumps(rosters,ensure_ascii=False),encoding='utf-8');status.set(f'PDF lagret: {len(students)} elever, {len(templates)} turer per elev, {pages} sider.')
    if messagebox.askyesno('PDF klar','Åpne PDF-en for gjennomgang og utskrift?',parent=win):
     import os,sys,subprocess
     if sys.platform=='win32':os.startfile(path)
     else:subprocess.Popen(['open' if sys.platform=='darwin' else 'xdg-open',path])
   except Exception as e:messagebox.showerror('Kunne ikke lage skjema',str(e),parent=win)
  ttk.Button(win,text='Lag PDF med navn',command=export).pack(pady=12)
  if courses:course.set(courses[0])
  refresh()
