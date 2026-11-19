"""Markdown rendering of an evaluation report.

All human-readable labels come from the rubric JSON, so this module stays
ASCII-only and the Chinese wording lives in data.
"""


def _fmt_deduction(d):
    note = d.get("note") or ""
    return "- probe `%s` (-%d) %s" % (d["probe"], d["weight"], note)


def render_markdown(report):
    lines = []
    lines.append("# %s" % report["title"])
    lines.append("")
    lines.append("- submission: `%s`" % report["submission_dir"])
    lines.append("- rubric: `%s` v%s" % (report["rubric_id"], report["rubric_version"]))
    lines.append("- evaluator: %s" % report["evaluator_version"])
    lines.append("- evidence_hash: `%s`" % report["evidence_hash"])
    lines.append("")
    lines.append("## 总分：%d / %d" % (report["total"], report["max_total"]))
    lines.append("")
    lines.append("| 维度 | 得分 | 上限 | 命中探针 |")
    lines.append("| --- | --- | --- | --- |")
    for d in report["dimensions"]:
        lines.append("| %s | %d | %d | %d/%d |" % (
            d["label"], d["score_final"], d["max"], d["probes_hit"], d["probes_total"]))
    lines.append("")

    if report["red_flags"]:
        lines.append("## 红线")
        lines.append("")
        for f in report["red_flags"]:
            lines.append("- **%s**（%s 封顶 %d）" % (f["label"], f["dimension"], f["cap"]))
        lines.append("")
    if report["caps_applied"]:
        lines.append("## 封顶生效")
        lines.append("")
        for c in report["caps_applied"]:
            lines.append("- %s: %d -> %d (%s)" % (
                c["dimension"], c["from"], c["to"], c["reason"]))
        lines.append("")

    lines.append("## 必交物")
    lines.append("")
    lines.append("| 模式 | 命中 | 文件数 | 空壳 |")
    lines.append("| --- | --- | --- | --- |")
    for r in report["deliverables"]:
        lines.append("| `%s` | %s | %d | %s |" % (
            r["pattern"], "yes" if r["found"] else "NO",
            r["matched_count"], ", ".join(r["empty"]) or "-"))
    lines.append("")

    lines.append("## 维度明细")
    lines.append("")
    for d in report["dimensions"]:
        lines.append("### %s  %d/%d" % (d["label"], d["score_final"], d["max"]))
        lines.append("")
        for p in d["probes"]:
            mark = "PASS" if p["hit"] else "MISS"
            lines.append("- [%s] `%s` +%d %s" % (mark, p["id"], p["weight"], p["note"]))
            for ev in p["evidence"]:
                snippet = ev["snippet"] or "(file present)"
                lines.append("  - `%s:%s` %s" % (ev["file"], ev["line"], snippet))
        if d["deductions"]:
            lines.append("")
            lines.append("未得分（无证据或未命中）：")
            for dd in d["deductions"]:
                lines.append(_fmt_deduction(dd))
        lines.append("")

    lines.append("## 复核建议")
    lines.append("")
    for item in report["review_hints"]:
        lines.append("- %s" % item)
    lines.append("")
    return "\n".join(lines) + "\n"
