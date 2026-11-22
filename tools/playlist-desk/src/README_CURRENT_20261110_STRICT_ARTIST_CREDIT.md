# Playlist Desk — strict full-credit local artist candidate (November 10, 2026)

**STATUS: offline source candidate, not installed, Windows-tested or owner-accepted.**

Parent: `WQ-20261030-012` (PC Playlist Desk + Bridge). Base archive is the preserved 2026-11-08 Gemma4 artist-first candidate, SHA-256 `c2438c62524c465e5f5aa426ab48a6e22dbe177aca8c7e36e8f52730c21bfad1`. This source-only continuation integrates the existing WQC006 strict full-credit patch once. WQB268's alternative patch is **not** included. Existing 2026-11-08 README and older source manifests are retained as historical descriptions; this file takes precedence for the matching change.

## Precisely what changed

The `Optional local Gemma` **exact local artist** path now compares complete normalized artist credits, including `The`. Thus `songs by The` matches only artist `The`, while `songs by The The` matches only `The The`. `songs by The Beatles` matches `The Beatles`, and `songs by Beatles` with *only* `The Beatles` in the catalog reports no exact match, clears the previous proposal, and never sends an Ollama request. A non-explicit open-ended request such as `something energetic` remains eligible for an opt-in model proposal. Article aliases can be considered separately if desired, with explicit disambiguation; none are silently inferred here.

This corrects the 2026-11-08 README statement that a leading `The` is tolerated; **that sentence describes the prior candidate, not this one**. Existing local artist-first behavior otherwise remains: only actual local track IDs are previewed, model responses require review before Apply, and Save As remains a separate step. Model-only proposal size bounds remain as in the base candidate.

## Reproducible checks and status

- `python -m unittest discover -s tests -p 'test*.py' -q` — synthetic unit suite.
- `python -m compileall -q gemma_local.py proposal_ui.py integrated_app.py tests` — compile/syntax check.
- `PYTHONPATH=. xvfb-run -a python tests/gui_wqmanual_full_credit.py` — real Tk on virtual Linux display; no actual model request.
- `PYTHONPATH=. xvfb-run -a python tests/gui_artist_first_guard.py` — inherited integration smoke.

Extract into a **separate** directory. On Windows, `launch_windows.cmd` starts the existing application (Python 3.9+ with Tkinter). Test first with `sample/fictional_phone_snapshot.json`: the existing `Imaginary Group` exact local query should preview the two fictional tracks without contacting Ollama; an explicitly missing artist should clear the preview. Test additional full-credit artist examples only with data you choose to load into this isolated candidate. Preserve the currently working installation.

Observed local checks: **222/222 Python unittests PASS**, Python compileall PASS, **16/17 real-Tk Xvfb GUI scripts PASS** (including seven new strict-credit paths). The sole inherited `tests/gui_smoke.py` failure on an `edits retained` status assertion was reproduced separately on the unmodified November 8 base. The first version of the new GUI test used an incorrect fixture key and failed; that test-only error was corrected and the complete suite rerun.

Current scope is synthetic source/Tk GUI verification only. No local owner media, Windows 10 GUI run, model HTTP, phone, installation, release, or physical test. The saved ZIP includes source, fictional test fixtures, regression tests, and a current integrity manifest.
