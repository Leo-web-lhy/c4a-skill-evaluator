"""Layer 1 - inventory collection.

Pure stdlib. No network, no clock, no randomness: the same directory always
produces the same inventory, which is what makes the whole evaluator
reproducible.
"""
import os

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", ".venv", "venv"}
MAX_TEXT_BYTES = 2 * 1024 * 1024


def _is_text(data):
    if b"\x00" in data[:4096]:
        return False
    return True


def collect(root):
    """Walk root and return a deterministic, sorted inventory."""
    root = os.path.abspath(root)
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            text = None
            if size <= MAX_TEXT_BYTES:
                try:
                    with open(full, "rb") as fh:
                        raw = fh.read()
                    if _is_text(raw):
                        text = raw.decode("utf-8", errors="replace")
                except OSError:
                    text = None
            files.append({
                "path": rel,
                "size": size,
                "lines": (text.count("\n") + 1) if text else 0,
                "is_text": text is not None,
                "text": text,
                "ext": os.path.splitext(name)[1].lower(),
            })
    files.sort(key=lambda f: f["path"])
    return files


def index_by_path(files):
    return {f["path"]: f for f in files}
