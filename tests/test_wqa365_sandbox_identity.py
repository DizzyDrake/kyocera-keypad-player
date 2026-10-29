"""Static sandbox identity contracts; no Android build or device execution."""
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GRADLE=(ROOT/'app/build.gradle').read_text()
MANIFEST=ROOT/'app/src/main/AndroidManifest.xml'
ACTIVITY=(ROOT/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
NS='{http://schemas.android.com/apk/res/android}'

class SandboxContracts(unittest.TestCase):
    def test_updates_existing_wqa365_sandbox_id(self):
        self.assertIn("applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'",GRADLE)
        self.assertNotIn("applicationId 'org.roarin.kyocerakeypad'",GRADLE)
        self.assertEqual(len(re.findall(r"(?m)^\s*applicationId\s+['\"]",GRADLE)),1)
    def test_namespace_unchanged_for_class_resolution(self):
        self.assertIn("namespace 'org.roarin.kyocerakeypad'",GRADLE)
        self.assertTrue((ROOT/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').exists())
    def test_launcher_identity(self):
        tree=ET.parse(MANIFEST); root=tree.getroot()
        self.assertEqual(root.attrib.get('package'),'org.roarin.kyocerakeypad')
        app=root.find('application');self.assertEqual(app.attrib[NS+'label'],'Keypad Sandbox WQA365')
        acts=app.findall('activity');self.assertEqual(len(acts),1)
        self.assertEqual(acts[0].attrib[NS+'name'],'.KeypadPlayerActivity')
        self.assertEqual(acts[0].attrib[NS+'exported'],'true')
        filters=acts[0].findall('intent-filter');self.assertEqual(len(filters),1)
        self.assertEqual(filters[0].find('action').attrib[NS+'name'],'android.intent.action.MAIN')
        self.assertEqual(filters[0].find('category').attrib[NS+'name'],'android.intent.category.LAUNCHER')
    def test_private_state_and_export_paths(self):
        self.assertIn('new File(getFilesDir(), "keypad_player_state_v1.bin")',(ROOT/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlaybackService.java').read_text())
        self.assertIn('getExternalFilesDir("transfer")',ACTIVITY)
        self.assertNotIn('Environment.getExternalStorageDirectory',ACTIVITY)
    def test_permissions_not_expanded(self):
        root=ET.parse(MANIFEST).getroot(); permissions=[e.attrib[NS+'name'] for e in root.findall('uses-permission')]
        self.assertEqual(permissions,['android.permission.READ_EXTERNAL_STORAGE','android.permission.FOREGROUND_SERVICE','android.permission.WAKE_LOCK'])
        app=root.find('application');self.assertEqual(app.attrib[NS+'allowBackup'],'false')
        self.assertEqual(app.attrib[NS+'usesCleartextTraffic'],'false')
        self.assertNotIn(NS+'sharedUserId',root.attrib)
        self.assertEqual(app.findall('provider'),[])
    def test_sandbox_visible_on_phone(self):
        self.assertIn('Keypad Player · DISPOSABLE SANDBOX',ACTIVITY)
        self.assertIn('DISPOSABLE SANDBOX',ACTIVITY)
        self.assertIn('getPackageName()',ACTIVITY)
        self.assertIn('Do not uninstall, clear storage, or overwrite the owner-installed player', (ROOT/'README_WQA365_DISPOSABLE_SIDE_BY_SIDE_TRIAL.md').read_text())
    def test_build_compatibility_preserved(self):
        for v in ['compileSdk 33','minSdk 29','targetSdk 29','versionCode 7',"versionName '0.1.8-dev4-wqa365-update-source'"]:
            self.assertIn(v,GRADLE)
    def test_no_silent_telephony_or_write_permission(self):
        m=MANIFEST.read_text()
        for s in ['READ_SMS','READ_CALL_LOG','READ_PHONE_STATE','WRITE_EXTERNAL_STORAGE','INTERNET','RECORD_AUDIO']:
            self.assertNotIn('android.permission.'+s,m)

if __name__=='__main__':unittest.main(verbosity=2)
