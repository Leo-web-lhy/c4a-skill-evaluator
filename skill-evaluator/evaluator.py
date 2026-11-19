"""C4A skill-evaluator - deterministic submission reviewer.

Usage:
    python evaluator.py --submission <dir> [--rubric rubrics/c4a.json]
                        [--out <dir>] [--label <text>]

Outputs (into --out, default ./reports):
    report.json   machine readable, deterministic field order
    report.md     human readable evidence report

Design rules enforced by construction:
  * no LLM call, no network, no clock, no randomness -> byte-identical reruns
  * a probe earns points only with recorded evidence
  * the evaluator never auto-rejects: it emits deductions + review questions
"""
import argparse
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from lib.collect import collect            # noqa: E402
from lib.deliverables import check_deliverables, summary as dv_summary  # noqa: E402
from lib.signals import run_probes          # noqa: E402
from lib.scoring import score_dimensions, eval_red_flags, apply_flags, total_of  # noqa: E402
from lib.render import render_markdown      # noqa: E402

EVALUATOR_VERSION = "c4a-evaluator/1.0.0"


def evidence_hash(root, files):
    """Stable fingerprint of the evaluated tree: path + byte content."""
    h = hashlib.sha256()
    h.update(EVALUATOR_VERSION.encode("utf-8"))
    for f in files:
        h.update(f["path"].encode("utf-8", "replace"))
        h.update(b"\x00")
        h.update(str(f["size"]).encode("ascii"))
        h.update(b"\x00")
        full = os.path.join(root, f["path"].replace("/", os.sep))
        try:
            with open(full, "rb") as fh:
                ch = hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            ch = "unreadable"
        h.update(ch.encode("ascii"))
        h.update(b"\n")
    return h.hexdigest()


def build_review_hints(dims, red_flags, dv_sum):
    hints = []
    if dv_sum["missing"]:
        hints.append("必交物缺失：%s —— 请确认是否换名或未提交。" %
                     "、".join(dv_sum["missing"]))
    if dv_sum["empty"]:
        hints.append("必交物空壳：%s —— 请人工确认是否只是占位文件。" %
                     "、".join(dv_sum["empty"]))
    for flag in red_flags:
        hints.append("红线「%s」已触发（%s 封顶 %d），请复核证据后决定是否放行。"
                     % (flag["label"], flag["dimension"], flag["cap"]))
    scored = []
    for d in dims:
        for dd in d["deductions"]:
            scored.append((dd["weight"], d["label"], dd))
    scored.sort(key=lambda x: (-x[0], x[1], x[2]["probe"]))
    for weight, label, dd in scored[:5]:
        hints.append("[%s] 未得分探针 `%s`（-%d）：%s —— 请人工判断是漏交还是本就不适用。"
                     % (label, dd["probe"], weight, dd["note"]))
    if not hints:
        hints.append("未发现明显缺口；仍建议人工抽查证据片段是否与实际文件一致。")
    hints.append("本报告只做结构与证据层判定，不评价方案语义质量，也不代替打分决策。")
    return hints


def evaluate(submission, rubric_path):
    with open(rubric_path, "r", encoding="utf-8") as fh:
        rubric = json.load(fh)

    files = collect(submission)
    dv_results = check_deliverables(files, rubric["requiredDeliverables"])
    dv_sum = dv_summary(dv_results)

    probes = []
    for dim in rubric["dimensions"]:
        tagged = [dict(p, dimension=dim["id"]) for p in dim["probes"]]
        probes.extend(run_probes(tagged, files))

    dims = score_dimensions(rubric, probes, dv_sum)
    for d in dims:
        d["probes"] = [p for p in probes if p["dimension"] == d["id"]]

    flags = eval_red_flags(rubric, dv_sum, probes, files)
    dims, caps = apply_flags(dims, flags)
    total = total_of(dims)

    report = {
        "title": rubric["title"],
        "submission_dir": os.path.abspath(submission),
        "rubric_id": rubric["rubric_id"],
        "rubric_version": rubric["version"],
        "evaluator_version": EVALUATOR_VERSION,
        "evidence_hash": evidence_hash(submission, files),
        "file_count": len(files),
        "total": total,
        "max_total": sum(d["maxPoints"] for d in rubric["dimensions"]),
        "dimensions": dims,
        "red_flags": flags,
        "caps_applied": caps,
        "deliverables": dv_results,
        "review_hints": build_review_hints(dims, flags, dv_sum),
    }
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic C4A submission evaluator")
    ap.add_argument("--submission", required=True)
    ap.add_argument("--rubric", default=os.path.join(HERE, "rubrics", "c4a.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "reports"))
    ap.add_argument("--label", default="")
    args = ap.parse_args(argv)

    if not os.path.isdir(args.submission):
        sys.stderr.write("submission dir not found: %s\n" % args.submission)
        return 2

    report = evaluate(args.submission, args.rubric)
    os.makedirs(args.out, exist_ok=True)
    label = args.label or os.path.basename(os.path.abspath(args.submission))
    json_path = os.path.join(args.out, "report.json")
    md_path = os.path.join(args.out, "report.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2, sort_keys=True)
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(report))

    lines = []
    lines.append("label=%s" % label)
    lines.append("files=%d" % report["file_count"])
    lines.append("total=%d/%d" % (report["total"], report["max_total"]))
    for d in report["dimensions"]:
        lines.append("  %-22s %2d/%2d" % (d["id"], d["score_final"], d["max"]))
    lines.append("red_flags=%d" % len(report["red_flags"]))
    for f in report["red_flags"]:
        lines.append("  flag %s cap=%d" % (f["id"], f["cap"]))
    lines.append("deliverables=%d/%d" % (sum(1 for d in report["deliverables"] if d["found"]),
                                        len(report["deliverables"])))
    lines.append("evidence_hash=%s" % report["evidence_hash"][:16])
    lines.append("json=%s" % json_path)
    lines.append("md=%s" % md_path)
    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
