from pathlib import Path
r=Path(__file__).resolve().parents[1]
a=(r/'app/src/main/java/org/roarin/kyocerakeypad/KeypadPlayerActivity.java').read_text()
c=(r/'app/src/main/java/org/roarin/kyocerakeypad/core/HomeMenuOrder.java').read_text()
g=(r/'app/build.gradle').read_text()
m=(r/'app/src/main/AndroidManifest.xml').read_text()
checks={
 'home order stable identity': 'homeOrder.get(i)' in a and 'homeAction(id)' in a,
 'nine menu identities': c.count('"resume_music"')>=1 and '"about"' in c and 'DEFAULT=Collections.unmodifiableList' in c,
 'resume first default': c.index('"resume_music"')<c.index('"resume_audiobook"')<c.index('"music_playlists"'),
 'saved preference load': 'getString("order", "")' in a,
 'synchronous save': '.putString("order",homeDraft.serialize()).commit()' in a,
 'failed save retained': 'if(!persisted){message("Menu order not saved; retry or cancel.");return;}' in a,
 'no tenth row': 'for(int i=0;i<homeOrder.size();i++)' in a and 'item("Reorder' not in a,
 'reorder footer shortcut': '" · 1–9 opens saved menu positions · * Reorder"' in a,
 'home digit action': 'homeAction(homeOrder.get(key-KeyEvent.KEYCODE_1))' in a,
 'reorder only home': 'if("HOME".equals(screen)' in a and 'startHomeReorder()' in a,
 'reorder isolated screen': 'if("HOME_REORDER".equals(screen)' in a,
 'stale posted selection guarded': 'draft.indexOf(homeMovingId)==row' in a,
 'explicit save cancel': 'finishHomeReorder(save)' in a and 'finishHomeReorder(false)' in a,
 'edit field protection': '!(getCurrentFocus() instanceof EditText)' in a,
 'NOW preserved': 'if("NOW".equals(screen)' in a and 'nowShortcut(key)' in a,
 'playlist move preserved': 'if("MOVE".equals(screen)' in a and 'moveByKey(key)' in a,
 'app identity unchanged': "applicationId 'org.roarin.kyocerakeypad.sandboxwqa365'" in g,
 'version code bumped': 'versionCode 17' in g,
 'Dumbplayer display label': 'android:label="Dumbplayer"' in m,
 'legacy readme preserved': (r/'README_DEV8_HISTORICAL.md').exists(),
 'legacy manifest preserved': (r/'SOURCE_MANIFEST_DEV8_HISTORICAL.json').exists(),
}
for k,v in checks.items():print(('PASS' if v else 'FAIL')+' '+k)
assert all(checks.values())
print(f'{len(checks)}/{len(checks)} DEV9 wiring checks PASS')
