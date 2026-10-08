"""GitHub OIDC -> verified school publisher. No admin password or service key."""
import os,json,hashlib,urllib.request,urllib.parse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from version import VERSION,BUILD
PROJECT='https://otuemdgmymgognzghmnu.supabase.co'
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kw):raise ValueError('Unexpected redirect')
opener=urllib.request.build_opener(NoRedirect)
def oidc():
 request=urllib.request.Request(os.environ['ACTIONS_ID_TOKEN_REQUEST_URL']+'&audience=ysk-dev-publisher',headers={'Authorization':'Bearer '+os.environ['ACTIONS_ID_TOKEN_REQUEST_TOKEN']})
 with opener.open(request,timeout=30) as r:return json.load(r)['value']
def action(body):
 request=urllib.request.Request(PROJECT+'/functions/v1/ysk-publish',data=json.dumps(body).encode(),headers={'Authorization':'Bearer '+oidc(),'Content-Type':'application/json'})
 with opener.open(request,timeout=120) as r:return json.load(r)
def release_notes(text):
 notes=text.split('\n\n',1)[0].strip()
 if not notes or len(notes)>5000:raise ValueError('Current release notes must contain 1–5000 characters')
 return notes
def main():
 files={'android':ROOT/'release_output/android/YSK_Kjorestudio_Android.apk','windows':ROOT/'release_output/windows/YSK_Kjorestudio.exe'}
 files={p:f for p,f in files.items() if f.is_file()}
 if not files:raise ValueError('No platform artifacts to publish')
 assets={p:{'size':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for p,f in files.items()}
 result=action({'action':'release_prepare','version':VERSION,'build':BUILD,'notes':release_notes((ROOT/'CHANGELOG.txt').read_text(encoding='utf-8')),'assets':assets})
 for platform,upload in result['uploads'].items():
  url=urllib.parse.urlsplit(upload['url']);origin=urllib.parse.urlsplit(PROJECT)
  if url.scheme!='https' or url.hostname!=origin.hostname or not url.path.startswith('/storage/v1/object/upload/sign/'):raise ValueError('Unexpected upload URL')
  request=urllib.request.Request(upload['url'],data=files[platform].read_bytes(),method='PUT',headers={'Content-Type':'application/octet-stream','x-upsert':'false'})
  with opener.open(request,timeout=120) as r:
   if r.status not in (200,201):raise ValueError('Upload failed')
 print(action({'action':'release_commit','release_id':result['id']})['message'])
if __name__=='__main__':main()
