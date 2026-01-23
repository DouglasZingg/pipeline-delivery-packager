from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from packager.core.scanner import ScanFile
from packager.models import PackPlanItem, ValidationResult

_VERSION_ONLY_RE = re.compile(r"^v\d{3,4}$", re.IGNORECASE)

DOC_EXTS = {"md", "txt", "pdf", "csv", "json", "xml", "yml", "yaml"}
TEX_EXTS = {"png", "jpg", "jpeg", "tga", "tif", "tiff", "exr", "hdr", "bmp"}
MAYA_EXTS = {"ma", "mb"}
MAX_EXTS = {"max"}
EXPORT_MAP = {
    "fbx": "export/fbx",
    "abc": "export/abc",
    "usd": "export/usd",
    "usda": "export/usd",
    "usdc": "export/usd",
    "obj": "export/obj",
    "gltf": "export/gltf",
    "glb": "export/gltf",
}


def validate_pack_inputs(project: str, asset: str, version: str) -> List[ValidationResult]:
    results: List[ValidationResult] = []

    if not project.strip():
        results.append(ValidationResult("ERROR", "PROJECT_MISSING", "Project name is required.", None))
    if not asset.strip():
        results.append(ValidationResult("ERROR", "ASSET_MISSING", "Asset name is required.", None))
    if not version.strip():
        results.append(ValidationResult("ERROR", "VERSION_MISSING", "Version is required (e.g. v001).", None))
    else:
        v = version.strip()
        if not _VERSION_ONLY_RE.match(v):
            results.append(
                ValidationResult(
                    "ERROR",
                    "VERSION_INVALID",
                    "Version must look like v001 (or v0001).",
                    None,
                )
            )

    return results


def _category_for_file(f: ScanFile) -> str:
    ext = (f.ext or "").lower()

    # Heuristic: if the relpath already indicates a bucket, respect it.
    rel_lower = f.relpath.lower().replace("\\", "/")
    parts = rel_lower.split("/")

    # Explicit folder hints
    if "tex" in parts or "textures" in parts:
        return "textures"
    if "docs" in parts or "doc" in parts:
        return "docs"
    if "source" in parts:
        # Try to keep DCC under source
        if ext in MAYA_EXTS or "maya" in parts:
            return "source/maya"
        if ext in MAX_EXTS or "max" in parts:
            return "source/max"
        return "source/other"

    # By extension
    if ext in TEX_EXTS:
        return "textures"
    if ext in DOC_EXTS:
        return "docs"
    if ext in MAYA_EXTS:
        return "source/maya"
    if ext in MAX_EXTS:
        return "source/max"
    if ext in EXPORT_MAP:
        return EXPORT_MAP[ext]

    return "other"


def build_pack_plan(
    files: List[ScanFile],
    output_root: str,
    project: str,
    asset: str,
    version: str,
) -> Tuple[List[PackPlanItem], List[ValidationResult]]:
    """
    Dry-run packaging plan:
      - decides destination path for every file
      - detects destination collisions
    """
    issues: List[ValidationResult] = []
    issues.extend(validate_pack_inputs(project, asset, version))
    if any(r.level.upper() == "ERROR" for r in issues):
        return [], issues

    out_root = Path(output_root).resolve()
    project = project.strip()
    asset = asset.strip()
    version = version.strip()

    base = out_root / project / asset / version
    plan: List[PackPlanItem] = []

    # Build plan items
    for f in files:
        cat = _category_for_file(f)

        # Keep original filename; later we can add rename/sanitize options
        filename = Path(f.path).name

        dst = base / cat / filename

        plan.append(
            PackPlanItem(
                src=f.path,
                relpath=f.relpath,
                dst=str(dst),
                category=cat,
            )
        )

    # Collision detection: exact same destination path
    dst_map: Dict[str, List[PackPlanItem]] = defaultdict(list)
    for item in plan:
        # Normalize case for Windows collisions
        key = os.path.normcase(os.path.normpath(item.dst))
        dst_map[key].append(item)

    collisions = [(k, v) for k, v in dst_map.items() if len(v) > 1]
    if collisions:
        for _, items in collisions[:25]:
            sample = items[0]
            issues.append(
                ValidationResult(
                    "ERROR",
                    "DEST_COLLISION",
                    f"Multiple files map to the same destination: {sample.dst}",
                    sample.relpath,
                )
            )
        if len(collisions) > 25:
            issues.append(
                ValidationResult(
                    "ERROR",
                    "DEST_COLLISION_MORE",
                    f"{len(collisions) - 25} more destination collisions not shown.",
                    None,
                )
            )

    return plan, issues
