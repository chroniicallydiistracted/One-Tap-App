# One-Tap TV Launcher (Fire Stick + Kodi)

A TV-native, remote-first launcher that lets a cognitively impaired user start familiar TV shows with one button press. Presents a single grid of tiles; each tile immediately starts playback in **Order** (next unwatched) or **Random** mode. Caregiver settings are PIN-protected. Designed for **Amazon Fire TV Stick** running **Kodi**.

> Status: Repo scaffold (spec + stubs). Use this as the foundation for coding the add-ons and skin.

---

## Features (MVP)

- Appliance feel: boots directly into Kodi and shows a tile grid
- Remote-only: Fire TV remote or TV remote via HDMI-CEC
- One-tap playback: tile press → immediate episode start
- Modes: **Order** (next unwatched, wrap) and **Random** (exclude last N, optional comfort weights)
- Auto-advance, error-skip (3 consecutive failures → return Home silently)
- PIN-protected caregiver menu (tile curation, mode toggle, export/import config)
- Offline operation from USB or NAS (SMB/NFS)

---

## Architecture (high level)

```
Fire Stick (Android/Fire OS)
└─ Kodi
   ├─ Custom Skin (Tile-only Home)
   ├─ plugin.one_tap.play        # Playback Controller
   ├─ service.one_tap.random     # Randomizer service
   ├─ script.one_tap.caregiver   # Caregiver UI (PIN-gated)
   └─ script.module.one_tap      # Shared utils (DB, JSON-RPC, config)
```

---

## Repository Structure

```
one-tap-tv-launcher/
├─ SPEC/                                   # Architecture spec (source of truth)
│  └─ SPEC-1-One-Tap-TV-Launcher.md
├─ addons/                                  # Kodi add-ons (code lives here)
│  ├─ plugin.one_tap.play/                  # Playback Controller (tile press entry)
│  │  ├─ addon.xml
│  │  ├─ default.py
│  │  └─ resources/
│  │     └─ settings.xml
│  ├─ service.one_tap.random/               # Randomizer background service
│  │  ├─ addon.xml
│  │  ├─ service.py
│  │  └─ resources/settings.xml
│  ├─ script.one_tap.caregiver/             # Caregiver menu + PIN UI
│  │  ├─ addon.xml
│  │  ├─ default.py
│  │  └─ resources/...
│  └─ script.module.one_tap/                # Shared utilities (module)
│     ├─ addon.xml
│     └─ lib/one_tap/
│        ├─ __init__.py
│        ├─ config.py
│        ├─ db.py
│        ├─ jsonrpc.py
│        ├─ selection.py
│        └─ logging.py
├─ skin.tile_only/                          # Minimal tile-only skin fork (Estuary-derived)
│  └─ (skin files: addon.xml, xml/Home.xml, etc.)
├─ packaging/
│  ├─ build_addons.py                       # Packs each addon into a ZIP
│  ├─ bundle_release.sh                     # Creates release bundle for sideload
│  └─ repo/                                 # (Optional) Static addon repository metadata
├─ tools/
│  ├─ adb/                                  # ADB helper scripts for Fire TV
│  │  ├─ install_apk.sh
│  │  ├─ push_addons.sh
│  │  └─ tail_logcat.sh
│  ├─ kodi/
│  │  └─ dev_profile/                       # Optional: local Kodi profile for desktop testing
│  └─ lint/                                 # pre-commit, flake8, mypy configs
├─ .editorconfig
├─ .gitignore
├─ pyproject.toml                           # Black/Flake8/Mypy config if using Python tooling
├─ CONTRIBUTING.md
├─ LICENSE
└─ README.md
```

---

## Quick Start (Developers)

### 1) Prereqs

- **Kodi** on a desktop (Windows/macOS/Linux) for quick iteration
- **Python 3.10+** (for tooling, not required on device)
- **ADB** (Android Debug Bridge) for Fire TV sideloading and logs
- **VS Code** (recommended), with Python extension
- Optional: **pre-commit**, **black**, **flake8**, **mypy**, **pytest**

### 2) Clone & bootstrap

```bash
git clone https://github.com/<you>/one-tap-tv-launcher.git
cd one-tap-tv-launcher

# Optional: install dev tooling
pip install -r requirements-dev.txt  # if you add one
pre-commit install                   # if using pre-commit
```

### 3) Build add-on ZIPs

```bash
python packaging/build_addons.py    # outputs ./dist/*.zip
```

Each add-on will be zipped as `plugin.one_tap.play-1.0.0.zip`, etc.

### 4) Test on desktop Kodi (fast loop)

1. Launch Kodi on your computer.
2. Settings → Add-ons → Install from ZIP file → select each ZIP from `./dist`.
3. Switch to the **tile-only** skin (if you have it ready) or temporarily invoke the controller with:
   - `RunScript(plugin.one_tap.play, show_id=<tvshowid>)` via Kodi’s keymap or JSON-RPC Console add-on.
4. Point Kodi to a local `Shows/` folder with proper `SxxEyy` naming.

### 5) Deploy to Fire Stick

1. Enable **ADB Debugging** on Fire TV (Developer options).
2. Find device IP (Network settings).
3. Connect ADB from your dev machine:
   ```bash
   adb connect <FIRE_TV_IP>
   ```
4. Push add-ons:
   ```bash
   ./tools/adb/push_addons.sh <FIRE_TV_IP> ./dist/*.zip
   ```
   Or install via Kodi → Add-ons → Install from ZIP (using a USB or network share).
5. Set Kodi to auto-launch on boot (via a launcher helper app) and disable screensaver/sleep.

---

## Configuration

- Caregiver config JSON (default path):

  ```
  special://profile/addon_data/plugin.one_tap.play/config.json
  ```

- Example:
  ```json
  {
    "tiles": [
      {"show_id": "123", "label": "Golden Girls", "path": "smb://nas/Shows/Golden Girls"}
    ],
    "mode": "order",
    "random": {"exclude_last_n": 5, "use_comfort_weights": true},
    "ui": {"audible_cue": true, "tile_order": ["123"]},
    "pin": "1234"
  }
  ```

---

## Testing & Logs

- **Kodi log (device):**
  - File path (typical): `Android/data/org.xbmc.kodi/files/.kodi/temp/kodi.log`
  - Live via ADB: `adb logcat | grep -i kodi`
- **App behavior checks:**
  - One-tap success rate (tile → playback within 3s)
  - Error-skip: corrupt/missing → automatic next candidate
  - 3 consecutive failures → silent return to Home
- **Unit tests (optional):**
  - Place pure-Python logic (e.g., selection/weighting) under `script.module.one_tap/lib/one_tap/` and test with `pytest`.

---

## Packaging & Release

- `packaging/build_addons.py` → creates per-addon ZIPs in `dist/`.
- `packaging/bundle_release.sh` → bundles add-ons + skin + default config into a single `release/one-tap-bundle.zip`.
- Tag releases as `vX.Y.Z` and attach ZIPs.

---

## Roadmap (MVP → Nice-to-have)

- MVP:
  - Tile-only skin
  - Playback Controller (order/random, auto-advance, error-skip)
  - Randomizer (exclude last N, optional comfort weights)
  - Caregiver Menu (PIN, tile curation, export/import)
- Nice-to-have:
  - Audible TTS cue
  - Analytics (anonymous local counters)
  - On-device setup wizard for SMB credentials

---

## License

MIT (see `LICENSE`)

---

## Security Notes

- PIN is not high-security; it’s to prevent accidental changes. Keep the device offline if possible.
- Prefer LAN-only SMB with read-only credentials for the media share.

---

## Credits

Built for Alzheimer’s accessibility with Kodi on Fire TV. ❤️
