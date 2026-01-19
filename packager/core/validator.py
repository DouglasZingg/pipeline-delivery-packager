from __future__ import annotations

import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

from packager.core.scanner import ScanFile, ScanSummary
from packager.core.profiles import ProfileConfig
from packager.models import ValidationResult


# Matches v001 / _v001 / -v001 / .v001 etc.
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
    # Rule: Required folders exist (profile-based)
    # -------------------------
    existing_top: Set[str] = set()
    try:
        for p in root_path.iterdir():
            if p.is_dir():
                existing_top.add(p.name)
    except OSError:
        results.append(
            ValidationResult(
                level="ERROR",
                code="ROOT_UNREADABLE",
                message="Input root cannot be read.",
                relpath=None,
            )
        )
        return results

    # Missing required folders can be ERROR or WARNING depending on profile rules
    missing_level = "ERROR" if profile.rules.error_missing_required_folders else "WARNING"
    for req in profile.required_folders:
        if req not in existing_top:
            results.append(
                ValidationResult(
                    level=missing_level,
                    code="REQ_FOLDER_MISSING",
                    message=f"Required folder missing for {profile.name}: '{req}/'",
                    relpath=req + "/",
                )
            )

    # -------------------------
    # Rule: No spaces in folder/file names
    # -------------------------
    if profile.rules.enforce_no_spaces:
        # Top-level folder names
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

        # File names + paths
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

            # Spaces in any parent folder component
            if " " in f.relpath and " " not in f.name:
                results.append(
                    ValidationResult(
                        level="ERROR",
                        code="SPACE_IN_PATH",
                        message="Path contains spaces (folder name).",
                        relpath=f.relpath,
                    )
                )

    # -------------------------
    # Rule: Version token present (WARNING)
    # -------------------------
    if profile.rules.warn_missing_version_token:
        # Skip obvious docs/logs from version enforcement
        skip_exts = {"md", "txt", "pdf", "csv", "log"}
        for f in files:
            if f.ext in skip_exts:
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
    # Rule: Unsupported extensions (WARNING)
    # -------------------------
    if profile.rules.warn_unsupported_extensions:
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
    # Rule: Duplicate filename (case-insensitive) warning
    # -------------------------
    name_map: Dict[str, List[str]] = defaultdict(list)
    for f in files:
        key = f.name.lower()
        name_map[key].append(f.relpath)

    for key, relpaths in name_map.items():
        if len(relpaths) > 1:
            results.append(
                ValidationResult(
                    level="WARNING",
                    code="DUPLICATE_FILENAME",
                    message=f"Duplicate filename appears {len(relpaths)} times: '{key}'",
                    relpath=relpaths[0],
                )
            )

    # -------------------------
    # Summary info
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
