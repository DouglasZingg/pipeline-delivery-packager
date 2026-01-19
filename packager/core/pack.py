from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from packager.models import PackPlanItem, ValidationResult


@dataclass(frozen=True)
class PackSummary:
    total: int
    copied: int
    skipped: int
    failed: int


def _same_file(src: str, dst: str) -> bool:
    """
    Best-effort check to see if dst already matches src (size + mtime).
    Not cryptographic; Day 7 adds hashing.
    """
    try:
        s = os.stat(src)
        d = os.stat(dst)
    except OSError:
        return False

    return (s.st_size == d.st_size) and (int(s.st_mtime) == int(d.st_mtime))


def execute_pack(
    plan: List[PackPlanItem],
    overwrite: bool = False,
    progress_cb: Optional[Callable[[int, int, PackPlanItem], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> Tuple[PackSummary, List[ValidationResult]]:
    """
    Copies files according to plan (safe-copy, never move).
    - overwrite=False: if destination exists, we SKIP (unless it appears identical, then also SKIP).
    - overwrite=True: always copy over existing destination.

    progress_cb(current_index_1based, total, item)
    is_cancelled() -> True to abort
    """
    issues: List[ValidationResult] = []
    total = len(plan)
    copied = 0
    skipped = 0
    failed = 0

    for idx, item in enumerate(plan, start=1):
        if is_cancelled and is_cancelled():
            issues.append(
                ValidationResult(
                    level="WARNING",
                    code="PACK_CANCELLED",
                    message="Packaging cancelled by user.",
                    relpath=item.relpath,
                )
            )
            break

        if progress_cb:
            progress_cb(idx, total, item)

        src = Path(item.src)
        dst = Path(item.dst)

        if not src.exists():
            failed += 1
            issues.append(
                ValidationResult(
                    "ERROR",
                    "SRC_MISSING",
                    f"Source missing: {src}",
                    item.relpath,
                )
            )
            continue

        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            failed += 1
            issues.append(
                ValidationResult(
                    "ERROR",
                    "DST_DIR_CREATE_FAILED",
                    f"Failed creating destination folder: {dst.parent} ({e})",
                    item.relpath,
                )
            )
            continue

        if dst.exists():
            if not overwrite:
                # If it's effectively the same, skip silently; otherwise warn and skip.
                if _same_file(str(src), str(dst)):
                    skipped += 1
                    continue
                skipped += 1
                issues.append(
                    ValidationResult(
                        "WARNING",
                        "DST_EXISTS_SKIPPED",
                        f"Destination exists; skipped (overwrite disabled): {dst}",
                        item.relpath,
                    )
                )
                continue

        try:
            shutil.copy2(src, dst)
            copied += 1
        except OSError as e:
            failed += 1
            issues.append(
                ValidationResult(
                    "ERROR",
                    "COPY_FAILED",
                    f"Copy failed: {src} -> {dst} ({e})",
                    item.relpath,
                )
            )

    summary = PackSummary(total=total, copied=copied, skipped=skipped, failed=failed)
    return summary, issues
