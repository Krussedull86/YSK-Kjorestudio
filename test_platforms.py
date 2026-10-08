import unittest
from scripts.select_platforms import select
class PlatformTests(unittest.TestCase):
 def test_windows_only(self):self.assertEqual(select(['main.py','core.py','version.py','CHANGELOG.txt']),(True,False))
 def test_android_only(self):self.assertEqual(select(['android/src/no/talappen/ysk/MainActivity.java','version.py','CHANGELOG.txt']),(False,True))
 def test_shared(self):self.assertEqual(select(['cloud/functions/ysk-admin/updates.ts']),(True,True))
 def test_docs(self):self.assertEqual(select(['README.md']),(False,False))
 def test_manual(self):
  for target,expected in [('windows',(True,False)),('android',(False,True)),('both',(True,True))]:self.assertEqual(select(['cloud/shared'],target),expected)
