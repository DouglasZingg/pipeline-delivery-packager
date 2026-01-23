from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from packager.models import PackPlanItem, ValidationResult
from packager.core.hashing import hash_file


@dataclass(frozen=True)
class PackSummary:
    total: int
    copied: int
    skipped: int
    failed: int


def _same_file(src: str, dst: str) -> bool:
    """
    Best-effort check to see if dst already matches src (size + mtime).
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
    verify_hash: bool = True,
    hash_algo: str = "sha1",
) -> Tuple[PackSummary, List[ValidationResult], Dict[str, str]]:
    """
    Copies files according to plan (safe-copy, never move) and optionally verifies via hashes.

    Returns:
      (summary, issues, hashes_by_src)

    hashes_by_src maps source absolute path -> hash digest
    (used later in manifest export).
    """
    issues: List[ValidationResult] = []
    hashes_by_src: Dict[str, str] = {}

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

        # Precompute src hash (if enabled) so we can store it + compare after copy
        src_hash = None
        if verify_hash:
            try:
                src_hash = hash_file(str(src), algo=hash_algo)  # type: ignore[arg-type]
                hashes_by_src[str(src)] = src_hash
            except OSError as e:
                failed += 1
                issues.append(
                    ValidationResult(
                        "ERROR",
                        "HASH_SRC_FAILED",
                        f"Failed hashing source: {src} ({e})",
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

        if dst.exists() and not overwrite:
            # Skip if overwrite disabled
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
            continue

        # Verify after copy
        if verify_hash and src_hash is not None:
            try:
                dst_hash = hash_file(str(dst), algo=hash_algo)  # type: ignore[arg-type]
            except OSError as e:
                failed += 1
                issues.append(
                    ValidationResult(
                        "ERROR",
                        "HASH_DST_FAILED",
                        f"Failed hashing destination: {dst} ({e})",
                        item.relpath,
                    )
                )
                continue

            if dst_hash != src_hash:
                failed += 1
                issues.append(
                    ValidationResult(
                        "ERROR",
                        "HASH_MISMATCH",
                        f"Integrity check failed (src != dst) for: {dst.name}",
                        item.relpath,
                    )
                )

    summary = PackSummary(total=total, copied=copied, skipped=skipped, failed=failed)
    return summary, issues, hashes_by_src
