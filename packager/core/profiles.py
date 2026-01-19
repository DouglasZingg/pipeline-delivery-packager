from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Set, Dict, Any


@dataclass(frozen=True)
class ProfileRules:
    enforce_no_spaces: bool = True
    warn_missing_version_token: bool = True
    warn_unsupported_extensions: bool = True
    error_missing_required_folders: bool = True


@dataclass(frozen=True)
class ProfileConfig:
    name: str
    required_folders: List[str]
    allowed_extensions: Set[str]  # lower, no dot
    rules: ProfileRules


def default_profiles() -> Dict[str, ProfileConfig]:
    return {
        "Game": ProfileConfig(
            name="Game",
            required_folders=["geo", "tex", "export", "source"],
            allowed_extensions={
                "fbx", "obj", "gltf", "glb", "usd", "usda", "usdc",
                "png", "jpg", "jpeg", "tga", "tif", "tiff", "exr",
                "json", "txt", "md", "pdf",
                "zip", "7z",
            },
            rules=ProfileRules(
                enforce_no_spaces=True,
                warn_missing_version_token=True,
                warn_unsupported_extensions=True,
                error_missing_required_folders=True,
            ),
        ),
        "VFX": ProfileConfig(
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
            rules=ProfileRules(
                enforce_no_spaces=True,
                warn_missing_version_token=True,
                warn_unsupported_extensions=True,
                error_missing_required_folders=True,
            ),
        ),
        "Mobile": ProfileConfig(
            name="Mobile",
            required_folders=["geo", "tex", "export", "docs"],
            allowed_extensions={
                "fbx", "gltf", "glb",
                "png", "jpg", "jpeg",
                "json", "txt", "md", "pdf",
                "zip",
            },
            rules=ProfileRules(
                enforce_no_spaces=True,
                warn_missing_version_token=True,
                warn_unsupported_extensions=True,
                error_missing_required_folders=True,
            ),
        ),
    }


def profiles_dir(repo_root: str) -> Path:
    return Path(repo_root).resolve() / "packager" / "profiles"


def profile_path(repo_root: str, profile_name: str) -> Path:
    safe = "".join(c for c in profile_name if c.isalnum() or c in ("_", "-", " "))
    return profiles_dir(repo_root) / f"{safe}.json"


def to_json_dict(profile: ProfileConfig) -> Dict[str, Any]:
    d = asdict(profile)
    d["allowed_extensions"] = sorted(list(profile.allowed_extensions))
    return d


def from_json_dict(d: Dict[str, Any]) -> ProfileConfig:
    rules_in = d.get("rules", {}) or {}
    rules = ProfileRules(
        enforce_no_spaces=bool(rules_in.get("enforce_no_spaces", True)),
        warn_missing_version_token=bool(rules_in.get("warn_missing_version_token", True)),
        warn_unsupported_extensions=bool(rules_in.get("warn_unsupported_extensions", True)),
        error_missing_required_folders=bool(rules_in.get("error_missing_required_folders", True)),
    )

    allowed = set((d.get("allowed_extensions") or []))
    allowed = {str(x).lower().lstrip(".") for x in allowed if str(x).strip()}

    required = [str(x).strip().strip("/\\") for x in (d.get("required_folders") or []) if str(x).strip()]

    return ProfileConfig(
        name=str(d.get("name") or "Custom"),
        required_folders=required,
        allowed_extensions=allowed,
        rules=rules,
    )


def ensure_default_profiles_on_disk(repo_root: str) -> None:
    pdir = profiles_dir(repo_root)
    pdir.mkdir(parents=True, exist_ok=True)

    defaults = default_profiles()
    for name, prof in defaults.items():
        path = profile_path(repo_root, name)
        if not path.exists():
            path.write_text(json.dumps(to_json_dict(prof), indent=2), encoding="utf-8")


def load_profile(repo_root: str, name: str) -> ProfileConfig:
    path = profile_path(repo_root, name)
    d = json.loads(path.read_text(encoding="utf-8"))
    return from_json_dict(d)


def save_profile(repo_root: str, profile: ProfileConfig) -> Path:
    pdir = profiles_dir(repo_root)
    pdir.mkdir(parents=True, exist_ok=True)
    path = profile_path(repo_root, profile.name)
    path.write_text(json.dumps(to_json_dict(profile), indent=2), encoding="utf-8")
    return path
