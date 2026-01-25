# MotionKit — pipeline tools for MotionBuilder and 3ds Max

MotionKit is a practical toolset for technical artists to install and run shared pipeline utilities inside **Autodesk MotionBuilder** and **3ds Max**, with a consistent menu experience and a deploy-friendly structure.

## What problem it solves
In animation teams, pipeline tools tend to drift:
- everyone has a slightly different setup
- installs are manual and error-prone
- tools get lost across scripts, versions, and chat links

MotionKit focuses on **repeatable installation**, **discoverability (menus)**, and **room to grow** as the toolset expands.

## Who it’s for
- Technical artists supporting animators
- Animation teams using MotionBuilder and/or 3ds Max
- Studios that need a low-friction way to ship internal tools

## Goals (what “good” looks like)
- One-click install and uninstall
- Tools are discoverable from a predictable menu
- New tools can be added without rewriting the installer
- Clear separation between DCC integrations and shared core logic

## Non-goals (for now)
- Perfect cross-platform support (installer is Windows-first today)
- A monolithic “one true pipeline” (this is a tool runner and framework)

## What’s included
- **Installer / Uninstaller**
  - Auto-detects supported DCC versions
  - Configures MotionBuilder Python startup path
  - Creates 3ds Max startup script for menu integration
- **Menu system**
  - Tools grouped by category (Animation / Rigging / Pipeline / Unreal)
- **DCC-agnostic core**
  - Shared framework intended to support additional DCCs over time

## Quick start
1) Clone or download this repo
2) Run:
   - `install.bat`
3) Restart MotionBuilder / 3ds Max
4) Use the **MotionKit** menu to access tools

To remove:
- run `uninstall.bat`, then restart DCCs

More details:
- `QUICKSTART.md`
- `INSTALLER.md`
- `INSTALLER_FEATURES.md`

## Project structure
```text
MotionKit/
├── install.bat
├── uninstall.bat
├── core/                 # shared, DCC-agnostic framework
├── mobu/                 # MotionBuilder integration
├── max/                  # 3ds Max integration
├── maya/                 # Maya integration (in progress / future)
├── config/
├── resources/
└── docs/
```

## Configuration
- `config/config.json` controls menu layout, tool categories, and environment paths.

## Operational notes (team use)
- Treat MotionKit like a small internal product:
  - version it
  - define supported DCC versions
  - keep a lightweight changelog
  - document “how to install” and “how to recover”

## Roadmap (high-level)
- Improve Maya integration
- Add diagnostics (detect broken installs and offer repair)
- Add “tool manifest” metadata (owner, version, dependencies)

## License
TBD (add a license file to clarify internal vs external usage).
