from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass(frozen=True)
class ScanFile:
    path: str           # full path
    relpath: str        # relative to input root
    name: str
    ext: str            # normalized (lower, no dot) or ""
    size_bytes: int


@dataclass(frozen=True)
class ScanSummary:
    root: str
    total_files: int
    total_dirs: int
    total_bytes: int
    extensions: Dict[str, int]          # ext -> count ("" means no extension)
    unsupported: Dict[str, int]         # ext -> count (based on allowlist)


def _normalize_ext(p: Path) -> str:
    # suffix includes dot; normalize to lower without dot. "" means no extension
    s = p.suffix.lower().lstrip(".")
    return s


def scan_folder(
    root: str,
    ignore_dirs: Optional[Set[str]] = None,
    ignore_hidden: bool = True,
    follow_symlinks: bool = False,
) -> tuple[List[ScanFile], ScanSummary]:
    """
    Recursively scan a folder and return:
      - list of files with metadata
      - summary stats
    """
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"Scan root is not a directory: {root}")

    ignore_dirs = ignore_dirs or set()
    files: List[ScanFile] = []
    total_dirs = 0
    total_bytes = 0
    ext_counts: Dict[str, int] = {}

    # Walk using os.walk for speed and easy dir filtering
    for dirpath, dirnames, filenames in os.walk(root_path, followlinks=follow_symlinks):
        total_dirs += 1

        # Filter dirnames in-place so os.walk doesn't descend
        filtered = []
        for d in dirnames:
            if d in ignore_dirs:
                continue
            if ignore_hidden and d.startswith("."):
                continue
            filtered.append(d)
        dirnames[:] = filtered

        # Skip hidden files optionally
        for fn in filenames:
            if ignore_hidden and fn.startswith("."):
                continue

            full = Path(dirpath) / fn
            try:
                stat = full.stat()
            except OSError:
                # unreadable file; still record it as size 0
                stat = None

            rel = str(full.relative_to(root_path)).replace("\\", "/")
            ext = _normalize_ext(full)
            size = int(stat.st_size) if stat else 0

            files.append(
                ScanFile(
                    path=str(full),
                    relpath=rel,
                    name=full.name,
                    ext=ext,
                    size_bytes=size,
                )
            )

            total_bytes += size
            key = ext  # "" allowed
            ext_counts[key] = ext_counts.get(key, 0) + 1

    # Basic unsupported warning group
    allow = {
        # DCC / scene
        "ma", "mb", "max", "blend",
        # common exports
        "fbx", "abc", "usd", "usda", "usdc", "obj", "gltf", "glb",
        # textures
        "png", "jpg", "jpeg", "tif", "tiff", "exr", "tga", "bmp", "hdr",
        # data / docs
        "json", "xml", "txt", "md", "pdf", "csv", "yml", "yaml",
        # misc
        "mtl", "wav",
        # archives (often not desired, but common in drops)
        "zip", "7z", "rar",
    }

    unsupported: Dict[str, int] = {}
    for ext, count in ext_counts.items():
        if ext == "":
            # files with no ext are suspicious; treat as unsupported bucket for now
            unsupported["(no_ext)"] = unsupported.get("(no_ext)", 0) + count
            continue
        if ext not in allow:
            unsupported[ext] = unsupported.get(ext, 0) + count

    summary = ScanSummary(
        root=str(root_path),
        total_files=len(files),
        total_dirs=total_dirs,
        total_bytes=total_bytes,
        extensions=dict(sorted(ext_counts.items(), key=lambda kv: (-kv[1], kv[0]))),
        unsupported=dict(sorted(unsupported.items(), key=lambda kv: (-kv[1], kv[0]))),
    )
    return files, summary
