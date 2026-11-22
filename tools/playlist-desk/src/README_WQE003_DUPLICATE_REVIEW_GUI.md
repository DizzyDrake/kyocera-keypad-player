# WQE003 — Possible duplicate songs review window (offline candidate)

Derived from WQB322 source ZIP. Adds one top-row **Review possible duplicates** button to Playlist Desk. After metadata JSON is loaded, it opens a read-only, scrollable table of candidate pairs with normalized artist/title, duration difference, and both source paths. It uses the existing WQB322 deterministic candidate_groups() function. No automatic deletion, renaming, fingerprinting, audio reads, playlist edits, or owner data access. Closing the dialog leaves the editor's unsaved-change state unchanged.

The list is a **shortlist**, not proof of duplicate audio. Equal title/artist and durations within 2 seconds can include different performances, albums, edits, and re-encodes; some true duplicates will not match. This candidate does not implement an owner keep/delete workflow yet.

Verification: 242 Python unit tests PASS; compileall PASS; synthetic xvfb Tk smoke PASS for one candidate pair, empty results, and unchanged edit flag. Not tested on native Windows 10, owner data, audio files, or installed application.
