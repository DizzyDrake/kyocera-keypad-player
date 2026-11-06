# Dumbplayer DEV9 REV2 — Apache-2.0 licensed source candidate (WQB033)

This is an additive license overlay on the existing 2026-10-31 WQD152 DEV9 REV2 source-only ZIP. **It is not a built APK, owner-installed version, GitHub release, or a new port.** The app logic and all historical source bytes are unchanged.

## Contents and verification

- 96 original members retained with identical payload hashes.
- Official, unmodified Apache License 2.0 at `LICENSE`.
- `LICENSE_SCOPE.md` explains copyright/third-party boundaries and historical provenance.
- `VERIFY_WQB033.py` checks ZIP integrity, all payload hashes, manifest, original source identity (when supplied), and official LICENSE SHA-256.
- `WQB033_PACKAGE_MANIFEST.json` records all 100 non-manifest payload hashes and source/archive identities.

Run: `python VERIFY_WQB033.py WQB033_DUMBPLAYER_DEV9_REV2_APACHE2_SOURCE_ONLY.zip --source WQD152_DEV9_DUMBPLAYER_HOME_REORDER_SOURCE_ONLY_REV2.zip` (source argument optional; if absent, source-member hashes are checked against the manifest only).

The original `SOURCE_MANIFEST.json` describes the *historical source ZIP* and intentionally does not list this overlay. Its old fixed-file-count tests may need to run on an extracted original-source subset rather than the additive package root. No native Android SDK, GitHub, signing, phone, media or Bluetooth trial is claimed. Owner approval of Apache-2.0 does not grant rights over external dependencies or historical third-party content.
