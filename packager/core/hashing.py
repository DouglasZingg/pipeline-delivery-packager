from __future__ import annotations

import hashlib
from typing import Literal

Algo = Literal["sha1", "md5"]


def hash_file(path: str, algo: Algo = "sha1", chunk_size: int = 1024 * 1024) -> str:
    """
    Streaming file hash (safe for large files).
    Returns hex digest.
    """
    if algo not in ("sha1", "md5"):
        raise ValueError(f"Unsupported hash algo: {algo}")

    h = hashlib.new(algo)
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()
