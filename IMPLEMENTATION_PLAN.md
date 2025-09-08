# Implementation Plan

The repository currently provides scaffolding for the One‑Tap TV Launcher. The following phased roadmap describes the work required to deliver a production‑ready release.

## Phase 1 – Stabilize scaffold
- **Fix runtime errors**: import `jsonrpc` in `plugin.one_tap.play` to avoid `NameError` during playback.
- **Populate tooling**: flesh out `packaging/build_addons.py` and `pyproject.toml` so add-ons can be built and code style enforced.
- **Complete specifications**: fill `SPEC/SPEC-1-One-Tap-TV-Launcher.md` with authoritative architecture details.

## Phase 2 – Core playback flow
- Finalize `plugin.one_tap.play` by handling JSON-RPC failures and persisting playback history consistently.
- Build comprehensive unit tests for shared utilities in `script.module.one_tap` (configuration, database, selection logic).

## Phase 3 – Background randomizer service
- Expand `service.one_tap.random` to track playback state, revert history on errors, and pre-select episodes using `random_state`.
- Add integration tests that simulate playback events to verify auto-advance and error skipping.

## Phase 4 – Caregiver interface & configuration
- Enhance `script.one_tap.caregiver` with full tile management, export/import helpers, and PIN enforcement.
- Provide a graphical interface within Kodi alongside the CLI fallback.

## Phase 5 – User-facing skin
- Develop the minimal `skin.tile_only` so Kodi boots directly into a grid of tiles and hides extraneous UI.

## Phase 6 – Packaging & release
- Implement `packaging/bundle_release.sh` and build automation to generate per-add-on ZIPs and a release bundle.
- Document deployment steps for Fire TV and desktop Kodi in the README.

This phased approach ensures the codebase progresses from scaffold to a stable, accessible media launcher.
