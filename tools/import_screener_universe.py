# -*- coding: utf-8 -*-
"""Tool (a): import a real HK_UNIVERSE from an existing screener project.

The original HK screener stored ~84 hand-picked large caps in `HK_UNIVERSE`
inside `screener.py`. When that project is reachable again (e.g. on your PC once
the Eastmoney feed is back), run this to extract the list into
`data/universe_hk.json`, which the scanner will then prefer automatically.

Usage:
    python tools/import_screener_universe.py [--path /path/to/screener.py]

It uses AST (no code execution) to pull the HK_UNIVERSE assignment safely.
"""
import os, sys, argparse, ast, json

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
DEFAULT_PATH = r"C:\Users\lauki\WorkBuddy\2026-08-19-09-19-48\hk_screener\screener.py"


def extract(path):
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "HK_UNIVERSE":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        out = []
                        for el in node.value.elts:
                            if isinstance(el, ast.Tuple) and len(el.elts) == 2:
                                a = ast.literal_eval(el.elts[0])
                                b = ast.literal_eval(el.elts[1])
                                out.append([a, b])
                        return out
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=DEFAULT_PATH)
    args = ap.parse_args()
    if not os.path.exists(args.path):
        print("HK_UNIVERSE source not found at:", args.path)
        print("When the old screener is available, re-run with --path <screener.py>.")
        sys.exit(1)
    univ = extract(args.path)
    if not univ:
        print("Could not find HK_UNIVERSE in", args.path)
        sys.exit(1)
    os.makedirs(DATA, exist_ok=True)
    out = os.path.join(DATA, "universe_hk.json")
    json.dump(univ, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Imported {len(univ)} HK names -> {out}")


if __name__ == "__main__":
    main()
