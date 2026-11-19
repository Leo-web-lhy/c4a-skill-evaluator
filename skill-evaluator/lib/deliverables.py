"""Layer 2 - required deliverables check.

The platform matches requiredDeliverables by FILE NAME substring, not by file
content (learned from prepare-submission behaviour on C6). This module uses the
same convention so the evaluator agrees with the platform instead of inventing
its own idea of "present".
"""
from fnmatch import fnmatchcase

EMPTY_BYTES = 20


def split_patterns(spec):
    if isinstance(spec, list):
        parts = spec
    else:
        parts = str(spec).split(",")
    return [p.strip() for p in parts if p.strip()]


def _match_path(pattern, path):
    """Match a platform-style pattern against a relative path.

    Patterns such as '*方案设计*' or 'README.md' are name based; a pattern with a
    slash is matched against the whole relative path.
    """
    p = pattern.lower()
    low = path.lower()
    if "/" in p:
        return fnmatchcase(low, p) or fnmatchcase(low, "*/" + p)
    base = low.rsplit("/", 1)[-1]
    if any(ch in p for ch in "*?["):
        return fnmatchcase(base, p) or fnmatchcase(low, p)
    return base == p


def check_deliverables(files, spec):
    results = []
    for pattern in split_patterns(spec):
        matched = [f for f in files if _match_path(pattern, f["path"])]
        empty = [f["path"] for f in matched if f["size"] < EMPTY_BYTES]
        results.append({
            "pattern": pattern,
            "found": len(matched) > 0,
            "empty": empty,
            "matched": [f["path"] for f in matched][:20],
            "matched_count": len(matched),
        })
    return results


def summary(results):
    total = len(results)
    found = sum(1 for r in results if r["found"])
    empty = sum(1 for r in results if r["found"] and len(r["empty"]) == len(r["matched"]))
    missing = [r["pattern"] for r in results if not r["found"]]
    empty_patterns = [r["pattern"] for r in results
                      if r["found"] and len(r["empty"]) == len(r["matched"])]
    return {
        "total": total,
        "found": found,
        "missing": missing,
        "empty": empty_patterns,
        "all_found": total > 0 and found == total,
        "has_missing_or_empty": bool(missing or empty_patterns),
    }
