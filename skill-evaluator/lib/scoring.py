"""Layer 4 - scoring and red flags.

Rules that matter for trust:
  * a probe only contributes points when it has evidence (or is an explicit
    absence check that passed);
  * dimension score is capped at its declared maxPoints;
  * every red flag is evaluated from the same inventory, never from the score.
"""


def score_dimensions(rubric, probe_results, deliverable_summary):
    dims = []
    by_dim = {}
    for probe in probe_results:
        by_dim.setdefault(probe["dimension"], []).append(probe)

    for d in rubric["dimensions"]:
        probes = by_dim.get(d["id"], [])
        raw = 0
        hits = 0
        deductions = []
        for p in probes:
            if p["hit"] and (p["evidence"] or p["weight"] == 0 or p.get("evidence_optional")):
                raw += p["weight"]
                hits += 1
            else:
                deductions.append({
                    "probe": p["id"],
                    "weight": p["weight"],
                    "note": p["note"],
                })
        score = min(raw, d["maxPoints"])
        dims.append({
            "id": d["id"],
            "label": d["label"],
            "max": d["maxPoints"],
            "score": score,
            "raw": raw,
            "capped": raw > d["maxPoints"],
            "probes_hit": hits,
            "probes_total": len(probes),
            "deductions": deductions,
        })
    return dims


def eval_red_flags(rubric, deliverable_summary, probe_results, files):
    flags = []
    specs = {f["id"]: f for f in rubric.get("redFlags", [])}
    by_id = {p["id"]: p for p in probe_results}

    def cap(flag_id, capped_score):
        spec = specs.get(flag_id, {})
        return {
            "id": flag_id,
            "label": spec.get("label", flag_id),
            "dimension": spec.get("dimension"),
            "cap": capped_score,
            "triggered": True,
        }

    if deliverable_summary["has_missing_or_empty"]:
        spec = specs.get("missing_artifacts", {})
        flags.append(cap("missing_artifacts", int(spec.get("cap", 5))))
        flags[-1]["evidence"] = {
            "missing": deliverable_summary["missing"],
            "empty": deliverable_summary["empty"],
        }

    ai_log = by_id.get("ai.log_scale")
    if ai_log is not None and not ai_log["hit"]:
        spec = specs.get("no_ai_log", {})
        flags.append(cap("no_ai_log", int(spec.get("cap", 5))))
        flags[-1]["evidence"] = {"ai_log_scale": ai_log["count"]}

    one_shot = by_id.get("ai.iteration_rounds")
    scale = by_id.get("ai.log_scale")
    # one_shot_ai only makes sense when a log file actually exists but is too
    # thin; a completely absent log is already covered by no_ai_log.
    if (one_shot is not None and not one_shot["hit"]
            and scale is not None and scale["count"] > 0 and not scale["hit"]):
        spec = specs.get("one_shot_ai", {})
        flags.append(cap("one_shot_ai", int(spec.get("cap", 5))))
        flags[-1]["evidence"] = {
            "iteration_rounds": one_shot["count"],
            "log_bytes": scale["count"],
        }
    return flags


def apply_flags(dims, flags):
    capped = []
    for d in dims:
        score = d["score"]
        for flag in flags:
            if flag["dimension"] == d["id"] and score > flag["cap"]:
                capped.append({
                    "dimension": d["id"],
                    "from": score,
                    "to": flag["cap"],
                    "reason": flag["id"],
                })
                score = flag["cap"]
        d["score_final"] = score
    return dims, capped


def total_of(dims):
    return sum(d["score_final"] for d in dims)
