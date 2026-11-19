"""Layer 3 - deterministic probes.

Every probe returns the same shape:
    {id, dimension, weight, hit, evidence:[{file, line, snippet}], note}

A probe never awards points without at least one evidence entry (or, for
negative probes that must NOT match, without an explicit absence reason).
"""
import re

MAX_EVIDENCE = 3


def glob_to_regex(pattern):
    p = pattern.replace("\\", "/")
    out = []
    i = 0
    while i < len(p):
        ch = p[i]
        if ch == "*":
            if p[i:i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif ch == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(ch))
        i += 1
    return re.compile("^" + "".join(out) + "$", re.IGNORECASE)


def match_paths(files, pattern):
    if "/" in pattern:
        rx = glob_to_regex(pattern)
        return [f for f in files if rx.match(f["path"]) or rx.match("/" + f["path"])]
    rx = glob_to_regex(pattern)
    return [f for f in files if rx.match(f["path"].rsplit("/", 1)[-1])]


def _text_files(files, globs):
    picked = []
    for g in globs:
        for f in match_paths(files, g):
            if f["is_text"] and f["text"] is not None and f not in picked:
                picked.append(f)
    picked.sort(key=lambda f: f["path"])
    return picked


def _line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def _snippet(text, start, end):
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end == -1:
        line_end = len(text)
    raw = text[line_start:line_end].strip()
    return raw[:160]


def probe_regex(probe, files):
    rx = re.compile(probe["pattern"], re.MULTILINE)
    min_count = int(probe.get("minCount", 1))
    evidence = []
    count = 0
    for f in _text_files(files, probe.get("glob", ["*"])):
        for m in rx.finditer(f["text"]):
            count += 1
            if len(evidence) < MAX_EVIDENCE:
                evidence.append({
                    "file": f["path"],
                    "line": _line_of(f["text"], m.start()),
                    "snippet": _snippet(f["text"], m.start(), m.end()),
                })
        if count >= min_count and len(evidence) >= MAX_EVIDENCE:
            break
    return {
        "id": probe["id"],
        "dimension": probe["dimension"],
        "weight": int(probe.get("weight", 0)),
        "hit": count >= min_count,
        "count": count,
        "evidence": evidence,
        "note": probe.get("note", ""),
    }


def probe_absent(probe, files):
    rx = re.compile(probe["pattern"], re.MULTILINE)
    hits = []
    for f in _text_files(files, probe.get("glob", ["*"])):
        m = rx.search(f["text"])
        if m:
            hits.append({
                "file": f["path"],
                "line": _line_of(f["text"], m.start()),
                "snippet": _snippet(f["text"], m.start(), m.end()),
            })
    return {
        "id": probe["id"],
        "dimension": probe["dimension"],
        "weight": int(probe.get("weight", 0)),
        "hit": len(hits) == 0,
        "count": len(hits),
        "evidence": hits[:MAX_EVIDENCE],
        "evidence_optional": True,
        "note": probe.get("note", ""),
    }


def probe_exists(probe, files):
    matched = []
    for g in probe.get("patterns", []):
        matched.extend(match_paths(files, g))
    seen = []
    for f in sorted(matched, key=lambda x: x["path"]):
        if f["path"] not in [s["path"] for s in seen]:
            seen.append(f)
    min_files = int(probe.get("minFiles", 1))
    return {
        "id": probe["id"],
        "dimension": probe["dimension"],
        "weight": int(probe.get("weight", 0)),
        "hit": len(seen) >= min_files,
        "count": len(seen),
        "evidence": [{"file": f["path"], "line": 1, "snippet": ""} for f in seen[:MAX_EVIDENCE]],
        "note": probe.get("note", ""),
    }


def probe_size(probe, files):
    best = None
    for g in probe.get("patterns", []):
        for f in match_paths(files, g):
            if best is None or f["size"] > best["size"]:
                best = f
    min_bytes = int(probe.get("minBytes", 200))
    hit = best is not None and best["size"] >= min_bytes
    return {
        "id": probe["id"],
        "dimension": probe["dimension"],
        "weight": int(probe.get("weight", 0)),
        "hit": hit,
        "count": best["size"] if best else 0,
        "evidence": ([{"file": best["path"], "line": 1,
                       "snippet": "size=%d bytes" % best["size"]}] if best else []),
        "note": probe.get("note", ""),
    }


def probe_count_files(probe, files):
    matched = []
    for g in probe.get("patterns", []):
        for f in match_paths(files, g):
            if f["path"] not in [m["path"] for m in matched]:
                matched.append(f)
    min_count = int(probe.get("minCount", 1))
    return {
        "id": probe["id"],
        "dimension": probe["dimension"],
        "weight": int(probe.get("weight", 0)),
        "hit": len(matched) >= min_count,
        "count": len(matched),
        "evidence": [{"file": f["path"], "line": 1, "snippet": ""} for f in matched[:MAX_EVIDENCE]],
        "note": probe.get("note", ""),
    }


KINDS = {
    "regex": probe_regex,
    "absent": probe_absent,
    "exists": probe_exists,
    "size": probe_size,
    "count_files": probe_count_files,
}


def run_probes(probes, files):
    out = []
    for probe in probes:
        kind = probe.get("kind", "regex")
        fn = KINDS.get(kind)
        if fn is None:
            continue
        out.append(fn(probe, files))
    return out
