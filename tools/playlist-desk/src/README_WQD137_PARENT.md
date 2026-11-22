# Kyocera PC Playlist Desk + Bridge v0.4 — WQD137 offline source trial

**October 30, 2026 owner request:** Drag-and-drop playlist reordering and selecting several PC audio files in one action. This is a continuation of the existing WQB434 v0.3 single-window PC application, **not** a new separate player. WQB434's original source ZIP is preserved unchanged. The owner reports the Playlist Bridge project is working well, but did not identify the installed/running version. This candidate is **source only**; not an installer, APK, phone sync or final release.

## Try on Windows 10 with fictional data

Extract this source candidate into an ordinary disposable local folder on a drive other than F:, preferably without network/junction links. Python 3.9+ with Tkinter is required; no third-party packages. Double-click `launch_windows.cmd` or run `py -3 integrated_app.py` from the extracted folder. Do not choose real private metadata or actual audio for the first trial.

1. Click **Load fictional phone snapshot** and choose `sample/fictional_phone_snapshot.json`. Choose **My order**. Drag one playlist row onto another; the manual order should change. The existing **↑ Move up / ↓ Move down** buttons still work. **Save As JSON** to a *new* file to preserve the changed order. The original snapshot remains unchanged.
2. Click **Add PC audio files…**. The Windows file chooser supports selecting several audio files together (Ctrl/Shift). If you want a disposable trial without real music, create two empty files named `trial_one.mp3` and `trial_two.flac` in a temporary C: folder; no audio is read, so the files need not contain sound. Select both in one chooser action. The playlist now shows **[PC ONLY — NOT ON PHONE]** beside each new entry. Save the edited JSON to a new local file. The JSON records the selected PC paths; treat it as personal data and do not upload it publicly.
3. With pending PC files present, **Save proposed changes**, **Save simulated result** and **Export M3U8** for that playlist intentionally refuse to pretend the files are on the phone. Select a pending entry and **Remove** it to remove that staged reference; when the last pending file is removed, provisional phone planning can work again. No files are copied or deleted by these actions.

**Why the bridge refusal matters:** The existing WQB434 phone contract has no verified mechanism to copy local audio or map it to persistent phone track identities. A PC-selected file is **not** a phone metadata row. This v0.4 candidate records it as a `pc_status=pending-local-not-on-phone` editor entry and a `pc_local_file` path, plus a synthetic editor-only `pc-pending/...` identifier. That identifier must never be treated as an actual phone path. The current bridge validates exact track inventory and rejects additions until a future authorized importer exists.

**Other boundaries:** No ADB, no phone or Android operation, no audio-file read/copy/delete, no network calls. F:, device and UNC paths are rejected before any selected-file access. The chooser itself is a normal Windows file dialog; do not browse/select F:. This candidate does not prove Windows 10/Tk behavior, actual file importing, phone transfer, player playlist order, NTFS/junction safety or compatibility with the owner's working installed version. All owner trials are voluntary and disposable. Keep the working app as fallback.

## Offline tests and provenance

Run `py -3 -m unittest discover -s tests -q` for 94 Python unit cases. The two GUI scripts in `tests/` require a display (`PYTHONPATH=. python tests/gui_smoke.py` and `PYTHONPATH=. python tests/gui_wqd137.py` on Linux). Both passed under Linux Xvfb. Source compilation with `python -m compileall -q .` passed. New tests cover one-operation multi-file selection, pending/duplicate/protected-path handling, manual-order moves, save and bridge refusal/recovery. The inherited 82 cases passed.

Parent source ZIP SHA-256: `c878d10d372610a66daf30331fca7a8f6223ff67c3858132ce17522e2bac6843`.

**Rollback:** close the app and delete only this extracted candidate folder and explicitly created disposable trial JSON/files. Do not delete the older working app or original music.
