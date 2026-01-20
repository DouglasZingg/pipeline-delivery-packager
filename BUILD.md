# Pipeline Delivery Packager (Standalone Python Pipeline Tool)

Standalone desktop pipeline utility that validates and packages asset deliveries into a clean “studio drop” layout, then exports a **manifest.json** + **report.html**.

## What this proves (portfolio)
- Standalone pipeline application (not tied to a DCC)
- Rules-based scanning + validation
- Production-style delivery packaging (safe-copy)
- Collision detection + packaging plan preview
- Integrity checks via hashing (SHA1)
- Delivery documentation: manifest + HTML report
- Unit tests + basic UI tests

## Features (v1.0.0)
- Input/output folder selection
- Profiles: Game / VFX / Mobile (JSON save/load)
- Validation:
  - required folders
  - no spaces
  - version token (v001)
  - unsupported extensions
  - duplicate filename warning
- Preview: build a copy plan and catch destination collisions
- Package: safe-copy with progress + cancel
- Export:
  - `docs/manifest.json`
  - `docs/report.html` (validation + plan + hashes)

## Output layout
DELIVERY_ROOT/
└── ProjectName/
└── AssetName/
└── v001/
├── source/
├── export/
├── textures/
├── docs/
│ ├── manifest.json
│ └── report.html
└── logs/

## Quick start
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
