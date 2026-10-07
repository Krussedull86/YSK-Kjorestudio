"""Rebuild with JDK 17 + Android SDK platform 35 and build-tools 35.0.0."""
from pathlib import Path
import subprocess,os,shutil,zipfile
root=Path(__file__).resolve().parent
sdk=Path(os.environ.get('ANDROID_SDK_ROOT') or os.environ.get('ANDROID_HOME') or '')
platform=sdk/'platforms/android-35/android.jar';tools=sdk/'build-tools/35.0.0';build=root/'build';classes=build/'classes';dex=build/'dex'
if not platform.is_file():raise SystemExit('Sett ANDROID_SDK_ROOT til Android SDK med platform android-35.')
compiler=shutil.which('javac')
if not compiler:raise SystemExit('Installer JDK 17 og legg javac i PATH.')
for p in [classes,dex]:
 if p.exists():shutil.rmtree(p)
 p.mkdir(parents=True,exist_ok=True)
def tool(name):return str(tools/(name+('.bat' if name in ['d8','apksigner'] else '.exe') if os.name=='nt' else name))
def run(args):subprocess.run([str(x) for x in args],check=True)
run([compiler,'-source','8','-target','8','-encoding','UTF-8','-bootclasspath',str(platform)+os.pathsep+str(tools/'core-lambda-stubs.jar'),'-d',classes,*sorted((root/'src').rglob('*.java'))])
run([tool('d8'),'--lib',platform,'--min-api','26','--output',dex,*sorted(classes.rglob('*.class'))])
run([tool('aapt2'),'compile','--dir',root/'res','-o',build/'resources.zip'])
run([tool('aapt2'),'link','-o',build/'unsigned.apk','-I',platform,'--manifest',root/'AndroidManifest.xml',build/'resources.zip'])
with zipfile.ZipFile(build/'unsigned.apk','a',zipfile.ZIP_DEFLATED) as z:
 for p in dex.glob('*.dex'):z.write(p,p.name)
run([tool('zipalign'),'-f','4',build/'unsigned.apk',build/'aligned.apk'])
output=root/'YSK_Kjorestudio_Android.apk'
run([tool('apksigner'),'sign','--ks',root/'signing/ysk-release.p12','--ks-key-alias','ysk','--ks-pass','file:'+str(root/'signing/password.txt'),'--key-pass','file:'+str(root/'signing/key_password.txt'),'--out',output,build/'aligned.apk'])
run([tool('apksigner'),'verify','--verbose',output]);print(output)
