"""Choose only the affected build platforms, or honor an explicit manual target."""
import os, subprocess
from pathlib import Path

def select(paths, target='auto'):
 if target != 'auto':
  if target not in ('windows','android','both'):raise ValueError('Unknown platform')
  return target in ('windows','both'), target in ('android','both')
 paths=list(paths)
 windows = android = False
 for path in paths:
  if path=='version.py' and any(p.startswith('android/') for p in paths):continue
  if path.startswith('android/'):
   android = True
  elif path.startswith('cloud/') or path in ('.github/workflows/dev.yml','scripts/publish_dev.py','scripts/select_platforms.py'):
   windows = android = True
  elif '/' not in path and (path.endswith('.py') or path == 'mobile.html'):
   windows = True
 return windows, android

def main():
 before=os.environ.get('BEFORE','')
 target=os.environ.get('TARGET','auto')
 if target=='auto':
  message=subprocess.check_output(['git','log','-1','--format=%s'],text=True)
  for platform in ('windows','android'):
   if f'[{platform}-only]' in message:target=platform
 if target=='auto' and (not before or set(before)=={'0'}):
  target='both';paths=[]
 else:
  paths=subprocess.check_output(['git','diff','--name-only',before or 'HEAD^','HEAD'],text=True).splitlines() if target=='auto' else []
 windows,android=select(paths,target)
 with Path(os.environ['GITHUB_OUTPUT']).open('a') as out:
  out.write(f'windows={str(windows).lower()}\nandroid={str(android).lower()}\n')
 print(f'Windows: {windows}; Android: {android}')
if __name__=='__main__':main()
