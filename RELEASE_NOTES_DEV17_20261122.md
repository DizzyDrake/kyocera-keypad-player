# DEV17 integrated release candidate — 2026-11-22

**Status:** Complete Android source tree and manual GitHub Actions workflow; NOT yet Android-compiled, signed, installed, published or approved as a tested release.

**Source ancestry:** DEV16 complete GitHub-ready ZIP 2026-11-15, SHA-256 `5385082fa542c6005dc6ebb8577fb7006a3479deeb35d3e9dd9d915770b1d6dd`. The original is preserved in the Library; this folder is a separate candidate.

## Implemented in actual Android source

1. Track completion / skip / currently-playing playlist removal: separate old-player release from foreground-service retirement. A new track can prepare without `stopSelf()` terminating the owner service. Preserves single MediaPlayer, playlist state, shuffle and selection guards.
2. Temporary audio-focus interruption: both music and audiobook streams pause, save position, retain foreground ownership and become eligible to resume on matching GAIN when they had been actively playing or preparing. Explicit Pause or Stop, denied requests, detected call mode or permanent focus loss remain stopped. Initial seek completion is guarded against early resume.
3. Presentation: orange Music, navy Audiobooks; neutral shared menus; explicit lane labels; owner-selected orange equilateral right-pointing triangle with white outline on navy adaptive icon.
4. Android metadata: retains `org.roarin.kyocerakeypad.sandboxwqa365`, minSdk=29, targetSdk=29, compileSdk=33, versionCode increased 19→20, updated versionName.
5. GitHub Actions manual workflow builds an unsigned release and checks package/version; independent Java and static source tests run first. Owner's permanent signing key is never in the source.

## Verified versus unverified

**Verified host-side:** pure Java policy and playlist tests, 24 DEV17 static source contracts, legacy remote-skip/library/import safety checks, XML syntax, ZIP integrity, hash manifest.

**Not verified:** Android Gradle compile, runtime API, real closed-flip shuffle, call recognition vs notifications, in-place APK update, user-data migration, foreground-service survival on hardware. This is a ready-to-compile source candidate, **not** an installable or physically accepted release.

`DEV16_TO_DEV17_SOURCE_CHANGE_LEDGER.json` and `DEV16_TO_DEV17_IMPLEMENTATION.diff` show the differences from the original DEV16 repository tree. Original historical manifests/tests remain, but should not be used as checks on intentionally modified DEV17 source.

**Safety:** Never uninstall an installed app to overcome signing errors. Match the permanent certificate SHA-256 from the build handoff. No owner-device mutations or external GitHub pushes were performed.
