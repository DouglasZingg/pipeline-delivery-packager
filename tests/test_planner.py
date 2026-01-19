import unittest
from packager.core.planner import build_pack_plan, validate_pack_inputs
from packager.core.scanner import ScanFile


class TestPlanner(unittest.TestCase):
    def test_validate_pack_inputs(self):
        errs = validate_pack_inputs("", "", "")
        self.assertTrue(any(r.code == "PROJECT_MISSING" for r in errs))
        self.assertTrue(any(r.code == "ASSET_MISSING" for r in errs))
        self.assertTrue(any(r.code == "VERSION_MISSING" for r in errs))

        errs2 = validate_pack_inputs("Proj", "Asset", "001")
        self.assertTrue(any(r.code == "VERSION_INVALID" for r in errs2))

        ok = validate_pack_inputs("Proj", "Asset", "v001")
        self.assertFalse(any(r.level.upper() == "ERROR" for r in ok))

    def test_category_routing(self):
        files = [
            ScanFile(path="C:/in/geo/CrateA_v001.fbx", relpath="geo/CrateA_v001.fbx", name="CrateA_v001.fbx", ext="fbx", size_bytes=1),
            ScanFile(path="C:/in/tex/CrateA_v001_diffuse.png", relpath="tex/CrateA_v001_diffuse.png", name="CrateA_v001_diffuse.png", ext="png", size_bytes=1),
            ScanFile(path="C:/in/source/maya/CrateA_v001.ma", relpath="source/maya/CrateA_v001.ma", name="CrateA_v001.ma", ext="ma", size_bytes=1),
            ScanFile(path="C:/in/docs/readme.md", relpath="docs/readme.md", name="readme.md", ext="md", size_bytes=1),
        ]

        plan, issues = build_pack_plan(files, "C:/out", "Proj", "CrateA", "v001")
        self.assertEqual(len(plan), 4)
        self.assertFalse(any(i.level.upper() == "ERROR" for i in issues))

        cats = {p.relpath: p.category for p in plan}
        self.assertEqual(cats["geo/CrateA_v001.fbx"], "export/fbx")
        self.assertEqual(cats["tex/CrateA_v001_diffuse.png"], "textures")
        self.assertEqual(cats["source/maya/CrateA_v001.ma"], "source/maya")
        self.assertEqual(cats["docs/readme.md"], "docs")

    def test_destination_collision(self):
        # Two different source files but same destination file name/category
        files = [
            ScanFile(path="C:/in/geo/A_v001.fbx", relpath="geo/A_v001.fbx", name="A_v001.fbx", ext="fbx", size_bytes=1),
            ScanFile(path="C:/in/export/A_v001.fbx", relpath="export/A_v001.fbx", name="A_v001.fbx", ext="fbx", size_bytes=1),
        ]
        plan, issues = build_pack_plan(files, "C:/out", "Proj", "Asset", "v001")
        self.assertEqual(len(plan), 2)
        self.assertTrue(any(i.code == "DEST_COLLISION" for i in issues))


if __name__ == "__main__":
    unittest.main()
