from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from packager.core.scanner import ScanFile, ScanSummary
from packager.core.profiles import ProfileConfig
from packager.models import ValidationResult


_VERSION_RE = re.compile(r"(^|[_\-.])v(\d{3,4})($|[_\-.])", re.IGNORECASE)


def validate_delivery(
    input_root: str,
    files: List[ScanFile],
    summary: ScanSummary,
    profile: ProfileConfig,
) -> List[ValidationResult]:
    results: List[ValidationResult] = []
    root_path = Path(input_root)

    # -------------------------
    # Rule: Required folders
    # -------------------------
    existing_top: Set[str] = set()
    try:
        for p in root_path.iterdir():
            if p.is_dir():
                existing_top.add(p.name)
    except OSError:
        # If we can't read root, scanner would likely have failed earlier,
        # but keep this defensive.
        results.append(
            ValidationResult(
                level="ERROR",
                code="ROOT_UNREADABLE",
                message="Input root cannot be read.",
                relpath=None,
            )
        )
        return results

    for req in profile.required_folders:
        if req not in existing_top:
            results.append(
                ValidationResult(
                    level="ERROR",
                    code="REQ_FOLDER_MISSING",
                    message=f"Required folder missing for {profile.name}: '{req}/'",
                    relpath=req + "/",
                )
            )

    # -------------------------
    # Rule: No spaces in names (folders + files)
    # -------------------------
    # Check top-level folders too
    for d in existing_top:
        if " " in d:
            results.append(
                ValidationResult(
                    level="ERROR",
                    code="SPACE_IN_DIRNAME",
                    message=f"Folder name contains spaces: '{d}'",
                    relpath=d + "/",
                )
            )

    for f in files:
        if " " in f.name:
            results.append(
                ValidationResult(
                    level="ERROR",
                    code="SPACE_IN_FILENAME",
                    message=f"File name contains spaces: '{f.name}'",
                    relpath=f.relpath,
                )
            )

        # Also catch spaces in intermediate folders via relpath
        # (cheap check; avoids full per-dir enumeration)
        if " " in f.relpath:
            # If filename already reported, don't spam; only warn once per file
            if " " not in f.name:
                results.append(
                    ValidationResult(
                        level="ERROR",
                        code="SPACE_IN_PATH",
                        message="Path contains spaces (folder name).",
                        relpath=f.relpath,
                    )
                )

    # -------------------------
    # Rule: Version token present (v001 / _v001 / -v001)
    # -------------------------
    # We keep it as WARNING (assets sometimes include non-versioned docs).
    for f in files:
        # Skip obvious docs and logs from version enforcement
        if f.ext in {"md", "txt", "pdf", "csv", "log"}:
            continue
        if not _VERSION_RE.search(f.name):
            results.append(
                ValidationResult(
                    level="WARNING",
                    code="VERSION_TOKEN_MISSING",
                    message="Filename missing version token (e.g. v001 or _v001).",
                    relpath=f.relpath,
                )
            )

    # -------------------------
    # Rule: Unsupported extensions (profile allowlist)
    # -------------------------
    # Files with no extension are suspicious.
    for ext, count in summary.extensions.items():
        if ext == "":
            results.append(
                ValidationResult(
                    level="WARNING",
                    code="NO_EXTENSION_FILES",
                    message=f"{count} file(s) have no extension.",
                    relpath=None,
                )
            )
            continue

        if ext not in profile.allowed_extensions:
            results.append(
                ValidationResult(
                    level="WARNING",
                    code="UNSUPPORTED_EXTENSION",
                    message=f"Extension '.{ext}' not in {profile.name} allowlist ({count} file(s)).",
                    relpath=None,
                )
            )

    # -------------------------
    # Rule: Potential collisions (duplicate file names, case-insensitive)
    # -------------------------
    # Later packaging will put files into buckets (textures/export/etc),
    # but collisions are still valuable to flag early.
    name_map: Dict[str, List[str]] = defaultdict(list)
    for f in files:
        key = f.name.lower()
        name_map[key].append(f.relpath)

    for key, relpaths in name_map.items():
        if len(relpaths) > 1:
            # Error or warning? We'll use WARNING for now.
            # In Day 4 packaging preview, collisions can become ERROR if they collide in same dest.
            results.append(
                ValidationResult(
                    level="WARNING",
                    code="DUPLICATE_FILENAME",
                    message=f"Duplicate filename appears {len(relpaths)} times: '{key}'",
                    relpath=relpaths[0],
                )
            )

    # -------------------------
    # Summary info (nice to include)
    # -------------------------
    results.append(
        ValidationResult(
            level="INFO",
            code="PROFILE_ACTIVE",
            message=f"Validation profile active: {profile.name}",
            relpath=None,
        )
    )

    return results
