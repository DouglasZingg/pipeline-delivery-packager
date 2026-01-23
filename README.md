# Pipeline Delivery Packager

Standalone desktop pipeline utility that validates and packages an asset delivery into a clean “studio drop” layout, then exports a **manifest.json** and an **HTML report**.

## Features
- Input/output folder selection
- Profiles (Game / VFX / Mobile)
- Rules-based validation (INFO / WARNING / ERROR)
- Packaging plan preview (detect destination collisions)
- Package execution (safe-copy; never moves source files)
- Exports:
  - `docs/manifest.json`
  - `docs/report.html`

## Output layout (example)
```
DELIVERY_ROOT/
  ProjectName/
    AssetName/
      v001/
        source/
        export/
        textures/
        docs/
          manifest.json
          report.html
        logs/
```

## Quickstart (run the app)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Demo / Testing Walkthrough (2–3 minutes)
This repo includes a script that generates a fake “delivery drop” you can scan/package immediately.

1) Create the demo input folder:
```bash
python scripts/make_demo_drop.py
```
This creates: `demo_drop/CrateA_drop`

2) Launch the tool:
```bash
python main.py
```

3) In the UI:
- **Input Folder** → select `demo_drop/CrateA_drop`
- **Output Folder** → choose an empty folder (e.g. `C:\TEMP\delivery_out`)
- Click **Scan**
- Click **Preview Plan**
- Click **Package**

4) Verify output:
- Open the output folder and confirm `docs/manifest.json` exists
- Open `docs/report.html` in a browser

## Tests (optional)
```bash
python -m pip install pytest
pytest -q
```

## Troubleshooting
See:
- `docs/SETUP.md`
- `docs/TROUBLESHOOTING.md`
