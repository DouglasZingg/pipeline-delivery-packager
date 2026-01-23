# Troubleshooting

## App launches but nothing happens
Run from a terminal to see exceptions:
```bash
python main.py
```

## PySide6 install issues
Make sure you're using the venv and up-to-date pip:
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Demo drop already exists
Delete the folder and re-run:
- `demo_drop/`

## Tests fail on a machine without a GUI
Some UI tests may require a desktop session. You can skip UI tests by running:
```bash
pytest -q -k "not ui"
```
