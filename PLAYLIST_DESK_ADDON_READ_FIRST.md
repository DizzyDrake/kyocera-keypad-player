# Playlist Desk add-on for an existing Dumbplayer DEV17 repository

This overlay updates the desktop companion for **Windows and Linux**, its GitHub Actions source checks, and the public repository README. Your existing Android DEV17 source and workflow remain in place.

## Add to the existing repository

Extract the ZIP. Copy its contents into the top level of your existing Dumbplayer repository, preserving the paths shown here:

- `README.md` (updated public homepage)
- `tools/playlist-desk/` (complete desktop source, Windows/Linux launchers and test suite)
- `.github/workflows/playlist-desk-source-checks.yml` (desktop CI workflow)

If you use Git locally, review `git diff --stat` and `git status` before committing. Push as an ordinary commit. The optional `tools/playlist-desk/UPLOAD_DESK_ADDON.cmd` helper can clone your existing GitHub repo, show staged changes, and ask before pushing.

### Run Playlist Desk

- **Windows:** `tools\playlist-desk\src\launch_windows.cmd`
- **Linux:** `cd tools/playlist-desk/src && bash launch_linux.sh` (Python 3.9+ and Tkinter)

### GitHub Actions

The new **Playlist Desk Windows Linux source and bridge checks** workflow runs the source manifest, 249 desktop unit tests, phone/desktop schema checks, and Linux GUI smoke test on Ubuntu. Your existing **Dumbplayer DEV17 integrated unsigned candidate** Android build workflow is unchanged.

## Source and test status

Desktop source derived from the verified Linux port of the November 15 Playlist Desk integrated candidate. The Windows launcher and desktop data format are retained. Source and Linux GUI tests were performed in a Linux test environment; Windows physical launch, real ADB transfer, and real owner data remain to be tested. No audio media, passwords, signing keys, or owner data are included.

The `tools/playlist-desk/SHA256SUMS.txt` file is the Linux source manifest. `VERIFY_INTEGRATED_SOURCE.py` checks the 106 saved Linux-port files. `README.md`, this guide, the companion's bridge-test files and GitHub workflow are checked separately in the overlay validation report.
