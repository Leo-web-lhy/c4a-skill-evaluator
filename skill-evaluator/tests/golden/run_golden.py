"""Golden-set runner: asserts semantics, not just numbers.

Checks per case (see EXPECTATIONS) + a determinism check (two runs must agree
on evidence_hash, total and every dimension score).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # skill-evaluator/
sys.path.insert(0, ROOT)

import evaluator  # noqa: E402

CASES = os.path.join(HERE, "cases")
RUBRIC = os.path.join(ROOT, "rubrics", "c4a.json")
RESULTS = os.path.join(HERE, "results.json")

EXPECTATIONS = {
    "01_perfect": {"min_total": 90, "flags": [], "min_found": 4},
    "02_missing_aar": {"min_total": 60, "max_total": 90, "flags": [], "min_found": 4},
    "03_missing_report": {"flags": ["missing_artifacts"], "cap_dim": "artifactCompleteness", "cap": 5},
    "04_no_ai_log": {"flags": ["no_ai_log", "missing_artifacts"]},
    "05_no_iteration": {"flags": [], "lower_dim": "aiUsage"},
    "06_empty_report": {"flags": ["missing_artifacts"], "cap_dim": "artifactCompleteness", "cap": 5},
}


def dim(report, did):
    for d in report["dimensions"]:
        if d["id"] == did:
            return d
    return None


def flags_of(report):
    return sorted(f["id"] for f in report["red_flags"])


def check(name, report, spec, baseline):
    problems = []
    got_flags = flags_of(report)
    if "flags" in spec and got_flags != sorted(spec["flags"]):
        problems.append("flags expect=%s got=%s" % (sorted(spec["flags"]), got_flags))
    if "min_total" in spec and report["total"] < spec["min_total"]:
        problems.append("total %d < min %d" % (report["total"], spec["min_total"]))
    if "max_total" in spec and report["total"] > spec["max_total"]:
        problems.append("total %d > max %d" % (report["total"], spec["max_total"]))
    if "min_found" in spec:
        found = sum(1 for d in report["deliverables"] if d["found"])
        if found < spec["min_found"]:
            problems.append("deliverables found %d < %d" % (found, spec["min_found"]))
    if "cap_dim" in spec:
        d = dim(report, spec["cap_dim"])
        if d is None or d["score_final"] != spec["cap"]:
            problems.append("%s score %s != cap %d"
                            % (spec["cap_dim"], d["score_final"] if d else "?", spec["cap"]))
    if "lower_dim" in spec and baseline is not None:
        d = dim(report, spec["lower_dim"])
        b = dim(baseline, spec["lower_dim"])
        if d["score_final"] >= b["score_final"]:
            problems.append("%s %d not lower than baseline %d"
                            % (spec["lower_dim"], d["score_final"], b["score_final"]))
    return problems


def main():
    if not os.path.isdir(CASES):
        print("cases missing, run build_fixtures.py first")
        return 2
    names = sorted(n for n in os.listdir(CASES) if os.path.isdir(os.path.join(CASES, n)))
    if not names:
        print("no cases found")
        return 2

    reports = {}
    for name in names:
        path = os.path.join(CASES, name)
        r1 = evaluator.evaluate(path, RUBRIC)
        r2 = evaluator.evaluate(path, RUBRIC)
        if not (r1["evidence_hash"] == r2["evidence_hash"] and r1["total"] == r2["total"]):
            print("FAIL determinism %s" % name)
            return 1
        for d1, d2 in zip(r1["dimensions"], r2["dimensions"]):
            if d1["score_final"] != d2["score_final"]:
                print("FAIL determinism dim %s %s" % (name, d1["id"]))
                return 1
        reports[name] = r1

    baseline = reports.get("01_perfect")
    failures = 0
    table = []
    for name in names:
        report = reports[name]
        spec = EXPECTATIONS.get(name, {})
        problems = check(name, report, spec, baseline)
        status = "PASS" if not problems else "FAIL"
        if problems:
            failures += 1
        table.append({
            "case": name,
            "status": status,
            "total": report["total"],
            "dimensions": {d["id"]: d["score_final"] for d in report["dimensions"]},
            "flags": flags_of(report),
            "problems": problems,
            "evidence_hash": report["evidence_hash"],
        })
        print("%-4s %-20s total=%3d flags=%s"
              % (status, name, report["total"], ",".join(flags_of(report)) or "-"))
        for p in problems:
            print("     - %s" % p)

    # False-positive / false-negative summary against the intended labels.
    fp = sum(1 for t in table if t["case"] == "01_perfect" and t["flags"])
    fn = sum(1 for t in table
             if t["case"] != "01_perfect" and EXPECTATIONS.get(t["case"], {}).get("flags")
             and not all(f in t["flags"] for f in EXPECTATIONS[t["case"]]["flags"]))
    total_cases = len(table)
    summary = {
        "cases": total_cases,
        "passed": total_cases - failures,
        "failed": failures,
        "false_positive": fp,
        "false_negative": fn,
        "fp_rate": round(fp / float(total_cases), 4),
        "fn_rate": round(fn / float(total_cases), 4),
        "deterministic": True,
        "results": table,
    }
    with open(RESULTS, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, ensure_ascii=False, indent=2, sort_keys=True)
    print("cases=%d passed=%d failed=%d fp=%d fn=%d"
          % (total_cases, summary["passed"], failures, fp, fn))
    print("results=%s" % RESULTS)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
