# Dumbplayer DEV9 v0.2.3 — WQD152 offline source candidate

**Not an APK, installed app, signed build, or phone-tested release.** This independent derivative preserves the exact original corrected DEV8 source ZIP (SHA-256 `75d7f040bf6caa2f6853a0bad283bfa4967deffe4184d354872fd246fc278eea`). All earlier DEV8 functionality is retained in source, not independently retested on hardware.

## Owner-requested behavior implemented in source

- Main menu defaults to **Resume music**, **Resume audiobook**, then the existing seven choices.
- **Reorder** is a home-screen shortcut, **not a tenth row**. Its exact key has not been chosen by the owner. This experimental source assigns `*` and displays `* Reorder` in the Home footer. Highlight any entry, press `*`, use Up/Down to move it, 1/9 for top/bottom, Center to save, or CLR/Back to cancel. To move another entry, return Home, highlight it, press `*` again.
- Digits **1–9 on Home** open whichever nine entries currently occupy those saved positions. Now Playing, playlist Move Mode, library and edit-field keys retain their separate mappings.
- Order persists in a separate app-private SharedPreferences file. Saving uses synchronous `commit()`; failure leaves the draft onscreen and the previous saved order intact. Invalid or obsolete saved data falls back to the nine default IDs without silently overwriting the saved preference.
- Android package ID remains `org.roarin.kyocerakeypad.sandboxwqa365` to support owner-preferred **replace in place** rather than a side-by-side install. Version metadata increments to code 12 / `0.2.3-dev9-wqd152-home-menu-source`. App display label changes to Dumbplayer. An installed APK update still requires a matching signing certificate and the owner's explicit build/install decision. Never uninstall or clear app data automatically to fix signature conflicts.

## Bounded owner review (only when ready)

Use a disposable Android emulator or the owner's authorized GitHub build workflow to inspect the proposed `*` key before compiling for the phone. On a test install, move Help to first place, save, relaunch and press 1 to open Help. Then move Resume music to first, cancel, and verify the saved order is unchanged. Check Now Playing 1/3/4/5/6 and playlist Move Mode 1/9 independently. **Do not install or replace the owner's current working app without approval.**

## Tests and limits

`sh tests/run_dev9_feature_smoke.sh` runs the inherited DEV8 pure-Java and source wiring checks plus new order model/wiring tests. Android Activity and Service compilation, APK signing, real E4831 key delivery, lifecycle/reboot persistence and hardware audio behavior are **not proven**. No owner devices, credentials, repositories, protected drives, installed apps or schedules were touched. No media files are moved or deleted by the new feature.

The `README_DEV8_HISTORICAL.md` and `SOURCE_MANIFEST_DEV8_HISTORICAL.json` are preserved source history, not current DEV9 manifests.
