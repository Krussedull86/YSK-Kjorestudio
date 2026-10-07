"""Prepare dated binaries and checksums. Signing material is never copied."""
import argparse,datetime,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--version',required=True);p.add_argument('--apk',type=Path);p.add_argument('--exe',type=Path);p.add_argument('--output',type=Path,default=Path('release_output'));a=p.parse_args()
if not a.apk and not a.exe:p.error('Oppgi --apk og/eller --exe.')
if not all(c.isalnum() or c in '.-' for c in a.version):p.error('Ugyldig versjonsnummer.')
a.output.mkdir(parents=True,exist_ok=True);date=datetime.datetime.now(datetime.timezone.utc);result={'version':a.version,'published_at':date.isoformat(),'files':{}}
for platform,path,suffix in [('android',a.apk,'.apk'),('windows',a.exe,'.exe')]:
 if path is None:continue
 if not path.is_file() or path.suffix.lower()!=suffix:p.error('Fil finnes ikke eller har feil filtype: '+str(path))
 target=a.output/f'YSK_Kjorestudio_{platform}_{a.version}_{date:%Y-%m-%d}{suffix}';shutil.copyfile(path,target)
 with target.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
 result['files'][platform]={'name':target.name,'size':target.stat().st_size,'sha256':digest}
(a.output/'release-manifest.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print('Releasefiler klargjort:',a.output.resolve())
