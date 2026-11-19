import argparse
import sys

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--submission", required=True)
    args = ap.parse_args(argv)
    try:
        run(args.submission)
    except Exception as exc:
        sys.stderr.write("failed: %s\n" % exc)
        return 1
    return 0

def run(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()

if __name__ == "__main__":
    raise SystemExit(main())
