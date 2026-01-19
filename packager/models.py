from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ValidationResult:
    level: str  # INFO | WARNING | ERROR
    code: str   # stable short identifier (e.g. REQ_FOLDER_MISSING)
    message: str
    relpath: Optional[str] = None  # relative to input root when applicable
