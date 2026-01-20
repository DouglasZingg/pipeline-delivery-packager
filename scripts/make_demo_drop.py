from __future__ import annotations

from pathlib import Path

def main():
    root = Path("demo_drop/CrateA_drop")
    (root / "geo").mkdir(parents=True, exist_ok=True)
    (root / "tex").mkdir(parents=True, exist_ok=True)
    (root / "export").mkdir(parents=True, exist_ok=True)
    (root / "source" / "maya").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)

    (root / "geo" / "CrateA_v001.fbx").write_bytes(b"dummy_fbx")
    (root / "tex" / "CrateA_v001_diffuse.png").write_bytes(b"dummy_png")
    (root / "export" / "CrateA_v001.abc").write_bytes(b"dummy_abc")
    (root / "source" / "maya" / "CrateA_v001.ma").write_text("// dummy maya", encoding="utf-8")
    (root / "docs" / "readme.md").write_text("# Demo Drop\n", encoding="utf-8")

    print(f"Created demo drop at: {root.resolve()}")

if __name__ == "__main__":
    main()
