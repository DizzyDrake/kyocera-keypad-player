# Playlist Desk — comma-combined library filter source candidate

**Date:** November 10, 2026 · **Status:** offline source candidate, uninstalled, Windows trial outstanding.
**Parent work:** `WQ-20261030-012` · manual Q, `execution_mode=manual_owner_invocation`, `automation_id=null`.
**Exact source parent:** `KYOCERA_PLAYLIST_DESK_STRICT_ARTIST_CREDIT_SOURCE_20261110.zip`, SHA-256 `b2475cbf6d52cc25f0197c02fa4011f84fd303d50a9637b839a3ed919098bc3c`. All older candidates preserved unchanged.

## The new filter

In the **Library filter**, commas combine multiple phrases:

| Search | Meaning |
| --- | --- |
| `jazz, blues` | Include tracks containing **either** phrase |
| `NOT live, NOT remix` | Exclude tracks containing **either** unwanted phrase (both exclusions apply) |
| `jazz, blues, NOT live, NOT remix` | Jazz **or** blues, except any track containing live **or** remix |
| `jazz NOT live` | Existing single-query syntax is unchanged |
| `blue jazz` | Existing single literal phrase remains supported |

Search applies case-insensitively across the existing title, artist, album, genre and path fields. For comma expressions, all positive terms form an OR group; every NOT phrase filters the entire resulting group. `jazz NOT live, blues NOT remix` thus means `(jazz OR blues) AND NOT live AND NOT remix`, not two separate independent branches. Comma separators inside a literal phrase are interpreted as separators. Empty comma slots are ignored during editing; a bare incomplete `NOT` is treated as literal text, preventing a surprising broad match. This grammar is an agent-selected implementation for Aurora's existing comma-combination request; owner approval of exact syntax remains open.

**Changed production code:** `app.py` only. The GUI label now reads `Filter (comma OR; NOT excludes):`. No playlist file/audio file changes and no new background operations. The full-credit exact artist behavior from the direct parent remains unchanged, as do the optional local model and review-before-Apply workflow. Distinguish the separate *Library filter* from `Optional local Gemma` proposal requests; commas here do not change Gemma's natural-language syntax.

## Testing

- `PYTHONPATH=. python -m unittest discover -s tests -p 'test*.py' -q` — **236/236 PASS** (222 inherited + 14 new cases).
- `python -m compileall -q -f app.py integrated_app.py proposal_ui.py tests` — PASS.
- `PYTHONPATH=. xvfb-run -a python tests/gui_comma_filter_wqmanual.py` — PASS: four filter paths via actual Tk widgets, original fictional playlist orders unchanged.
- 18 GUI scripts under Linux Xvfb: **17 PASS, 1 FAIL**. Inherited `tests/gui_smoke.py` line 62 expects `edits retained` in a UI status label. The *same* failure was reproduced on the untouched direct parent ZIP, confirming baseline behavior.
- ZIP CRC and per-file SHA-256 manifest are checked after assembly. See `TEST_RESULTS_20261110_COMMA.md` and `CURRENT_MANIFEST_20261110_COMMA.json` in this archive.

## Suggested first Windows trial

Extract the new source ZIP to a **separate folder** and run `launch_windows.cmd` (Python 3.9+ and Tkinter). Load `sample/fictional_phone_snapshot.json`. In the Library filter, try `Imaginary, Chapter` to see music plus the fictional chapter, then `Imaginary, Chapter, NOT Beta` to exclude fictional Beta; clear the field to return to the full library. Optionally use your real catalog only after this offline smoke test, comparing the results against expected track names. This source is offered for testing; preserve the working Playlist Desk version.

Other owner wishes still open: easier playlist selection than the saved-playlist dropdown, duplicate-song detection across different files, and button/workflow simplification. Actual Ollama, Windows 10 UI, phone, ADB, owner media, installation and release have **not** been tested here.
