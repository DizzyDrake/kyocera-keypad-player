# Keypad Player v0.1.7 — WQA365 disposable side-by-side Android source trial

**Source only; NOT an APK, installed update, Android-compiled release, or owner acceptance.** Frozen parent: WQA359 optional rollback-guard ZIP, SHA-256 `4d711d6c3c92dc6acd1f96a9837bb4adcadaac848da93141cb9833839a52981a`.

## Why this variant exists

The owner-tested v0.1.4 app may have a signing certificate different from a newly generated GitHub Actions debug APK. Because the original app has `android:allowBackup=false`, uninstalling it to bypass an update signature mismatch could erase playlists, bookmarks and listening progress. **Do not uninstall, clear storage, or overwrite the owner-installed player.**

This trial changes **only** the Android Gradle `applicationId` to `org.roarin.kyocerakeypad.sandboxwqa365`, the launcher label to `Keypad Sandbox WQA365`, and a few visible warning/help strings. The Java namespace remains `org.roarin.kyocerakeypad` so existing classes and relative manifest Activity resolve normally. The original package ID is `org.roarin.kyocerakeypad` **in frozen source**, but the actual owner-installed APK identity remains to be checked by the owner before any device work.

Android isolates app-private `getFilesDir()` by installed package identity. Therefore a correctly built and installed WQA365 trial should have independent `keypad_player_state_v1.bin`, playlists and bookmarks. The `getExternalFilesDir("transfer")` metadata export is also application-specific. **This is a platform-based expectation, not physical-device verification.**

## Limits and safe owner trial

- The trial still requests `READ_EXTERNAL_STORAGE` on Android 10. If granted, it can list/read the same phone-wide MediaStore audio as the original app. It does not duplicate or isolate the audio library. Use disposable sample audio, not valuable private media; do not export metadata unless you intend to.
- The candidate preserves the parent `targetSdk=29`, `minSdk=29`, `compileSdk=33`, Android Java source and all media/playback logic. No new permissions, network, SMS, call-log or telephony access are added. It does **not** resolve untested physical keypad focus, audio focus/call interruption, APK signing or lifecycle behavior.
- The build project has **no Gradle wrapper**. It requires an owner-controlled Android build environment compatible with AGP 7.4.2, Android SDK 33 and JDK 17. Do not treat a successful Java 8 host-core compile as an Android build. If using an existing GitHub Actions build, explicitly check the artifact package name/manifest before owner-supervised installation.
- Before any phone installation, inspect the generated APK package with `aapt dump badging app-debug.apk` (or Android Studio APK Analyzer) and confirm `package: name='org.roarin.kyocerakeypad.sandboxwqa365'` and launcher `Keypad Sandbox WQA365`. Also verify APK signing, target Android 10 and no unintended permissions. If those checks fail, **do not install**.
- If installed after owner approval, verify two distinct launcher entries and separate playlists using disposable data. Never test upgrade/uninstall of the existing v0.1.4 as part of this sandbox trial. Trial removal must target **only** `org.roarin.kyocerakeypad.sandboxwqa365`, after checking its exact identity.

## Source and test boundaries

All inherited offline host tests and `tests/test_wqa365_sandbox_identity.py` are runnable without Android SDK. They test Java core behavior and static source contracts, not Android package-manager isolation or physical phone behavior. The trial changes no original WQA359 ZIP bytes and is not intended to merge automatically into the production branch.
