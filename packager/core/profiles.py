from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set


@dataclass(frozen=True)
class ProfileConfig:
    name: str
    required_folders: List[str]
    allowed_extensions: Set[str]  # lower, no dot


def get_profile(name: str) -> ProfileConfig:
    n = (name or "").strip().lower()

    # Keep these v1-simple; you can tune later.
    if n == "game":
        return ProfileConfig(
            name="Game",
            required_folders=["geo", "tex", "export", "source"],
            allowed_extensions={
                "fbx", "obj", "gltf", "glb", "usd", "usda", "usdc",
                "png", "jpg", "jpeg", "tga", "tif", "tiff", "exr",
                "json", "txt", "md", "pdf",
                "zip", "7z",
            },
        )

    if n == "mobile":
        return ProfileConfig(
            name="Mobile",
            required_folders=["geo", "tex", "export", "docs"],
            allowed_extensions={
                "fbx", "gltf", "glb",
                "png", "jpg", "jpeg",
                "json", "txt", "md", "pdf",
                "zip",
            },
        )

    # Default: VFX
    return ProfileConfig(
        name="VFX",
        required_folders=["geo", "tex", "rig", "cache", "export", "source", "docs"],
        allowed_extensions={
            "ma", "mb", "max", "blend",
            "abc", "fbx", "usd", "usda", "usdc", "obj",
            "png", "jpg", "jpeg", "tga", "tif", "tiff", "exr", "hdr",
            "json", "xml", "txt", "md", "pdf", "csv",
            "mtl",
            "zip", "7z", "rar",
        },
    )
