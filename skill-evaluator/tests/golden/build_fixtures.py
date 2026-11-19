"""Materialize the golden-set fixtures from fixtures.json.

Source stays ASCII-only on purpose: on this machine a Python source file with
non-ASCII literals can kill the process (0xC0000005). All Chinese text lives in
fixtures.json and is written with explicit UTF-8 encoding.
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures.json")
OUT = os.path.join(HERE, "cases")


def write_tree(root, files):
    for rel, content in files.items():
        full = os.path.join(root, rel.replace("/", os.sep))
        parent = os.path.dirname(full)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with open(full, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)


def main():
    with open(FIXTURES, "r", encoding="utf-8") as fh:
        spec = json.load(fh)
    base = spec["base"]["files"]
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    built = []
    for name, ops in spec["cases"].items():
        files = dict(base)
        for rel in ops.get("remove", []):
            files.pop(rel, None)
        files.update(ops.get("add", {}))
        root = os.path.join(OUT, name)
        write_tree(root, files)
        built.append((name, len(files)))
    for name, count in built:
        print("built %s files=%d" % (name, count))
    print("out=%s" % OUT)


if __name__ == "__main__":
    main()
