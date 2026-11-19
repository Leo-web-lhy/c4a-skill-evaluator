import json, io, sys

fx = json.load(open("tests/golden/fixtures.json", encoding="utf-8"))
patch = json.load(open(".scratch_r/patch_zh.json", encoding="utf-8"))

log_key = "\u0041\u0049\u65e5\u5fd7\u002e\u006d\u0064"  # AI??.md
base = fx["base"]["files"]
base[log_key] = base[log_key].rstrip() + "\n" + patch["base_append"]
fx["cases"]["05_no_iteration"]["add"][log_key] = patch["case05_log"]

out = json.dumps(fx, ensure_ascii=False, indent=2)
open("tests/golden/fixtures.json", "w", encoding="utf-8", newline="\n").write(out)

print("base_log_bytes=%d" % len(base[log_key].encode("utf-8")))
print("case05_log_bytes=%d" % len(patch["case05_log"].encode("utf-8")))
print("OK")
