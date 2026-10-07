from core import QUAL
def seed(store):
 for i,name in enumerate(['Anne','Bjørn','Camilla','Daniel','Erik','Fatima','Geir','Hanna']):
  for n in range(1,6):
   store.save(dict(driver=name,course='Demokurs',vehicle='Lastebil C',trip=n,minutes=48+i*.9-n*.3,km=36,liters=12+i*.45-n*.65,stops=max(0,4-n+i%2),notes='Demodata – kun for å prøve visningen.',**{k:'Bra' if n>=4 or i%3==0 else 'Middel' if n>=2 else 'Svak' for k in QUAL}))
