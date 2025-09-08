# Implementation Notes

This document records the initial implementation work for the One‑Tap TV Launcher
MVP as described in the repository `README`.

## Summary

- Added fully fledged Python module under `script.module.one_tap` providing
  configuration loading/saving, JSON‑RPC utilities, logging helpers, playback
  history storage and episode selection logic.
- Implemented playback controller `plugin.one_tap.play` which loads the
  caregiver configuration, chooses the next episode in **Order** or **Random**
  mode and instructs Kodi to start playback via JSON‑RPC.
- Filled in `addon.xml` manifests for all add‑ons so they can be packaged by the
  `packaging/build_addons.py` script.
- Added minimal stubs for the randomizer background service and caregiver menu
  to allow future feature expansion.
- Refined episode selection to provide a list of candidates and defer history
  updates until playback succeeds, enabling error skips.
- Playback controller now retries up to three episodes before giving up,
  avoiding getting stuck on corrupt files.

## Design Choices

- **SQLite storage:** Playback history uses a lightweight SQLite database for
  durability while remaining simple to manage.
- **Kodi fallbacks:** Modules gracefully degrade when run outside Kodi by
  avoiding hard dependencies on `xbmc`/`xbmcvfs` modules, easing desktop testing.
- **Explicit logging:** A tiny wrapper normalises logging both inside Kodi and
  during development, keeping messages consistent across environments.

## Next Steps

- Flesh out caregiver UI and PIN handling.
- Extend randomiser service to support comfort weighting and exclude‑last logic
  without relying solely on the playback controller.
- Implement auto-advance and smarter error handling based on player events.
- Remove legacy JSON progress files once migration to SQLite completes to avoid
  stale data lingering alongside the new database.
- Allow caregivers to configure the maximum retained history instead of relying
  on the built-in default.
- Harden the SQLite layer with basic error handling and provide maintenance
  tooling such as a history purge command.
