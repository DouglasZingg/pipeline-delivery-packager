from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from packager.models import ValidationResult, PackPlanItem


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_stat(path: str) -> Dict[str, Any]:
    try:
        st = os.stat(path)
        return {
            "size_bytes": int(st.st_size),
            "mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds"),
        }
    except OSError:
        return {"size_bytes": None, "mtime": None}


def build_manifest_dict(
    tool_name: str,
    tool_version: str,
    profile: str,
    input_root: str,
    output_root: str,
    project: str,
    asset_name: str,
    version: str,
    validation_results: List[ValidationResult],
    plan: List[PackPlanItem],
    include_file_stats: bool = True,
) -> Dict[str, Any]:
    files_out: List[Dict[str, Any]] = []
    for item in plan:
        entry: Dict[str, Any] = {
            "src": item.src,
            "dst": item.dst,
            "relpath": item.relpath,
            "category": item.category,
        }
        if include_file_stats:
            entry.update(_safe_stat(item.src))
        files_out.append(entry)

    results_out = [
        {
            "level": r.level,
            "code": r.code,
            "message": r.message,
            "relpath": r.relpath,
        }
        for r in validation_results
    ]

    manifest = {
        "tool": tool_name,
        "version": tool_version,
        "timestamp_utc": _utc_now_iso(),
        "profile": profile,
        "input_root": input_root,
        "output_root": output_root,
        "project": project,
        "asset_name": asset_name,
        "delivery_version": version,
        "results": results_out,
        "files": files_out,
    }
    return manifest


def write_manifest_json(
    manifest: Dict[str, Any],
    manifest_path: str,
) -> str:
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    return str(path)
