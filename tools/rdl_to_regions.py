"""
Convert the original Habitat region description sources (*.rdl, text) into
JSON that backend/seed_data-style loaders can consume.

The compiled .reg files (3,299 in the original tree, 512-byte binary records)
are NOT parsed. The *.rdl sources under habitat/Realms/*/ are the text form of
503 regions (1,042 .rdl files in the whole tree, many are duplicates/tests).

Usage:
    python3 tools/rdl_to_regions.py <habitat-tree-root> <out.json>

Output JSON:
    {"regions":[{"region_id","name","neighbors":{west,east,north,south},
                 "orientation","objects":[{"class_id","class_name","x","y",
                 "orientation","style","gr_state","slots":{n:v},
                 "attrs":{...},"children":[...]}]}],
     "report":{...verification counts...}}
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.models import ClassID  # noqa: E402

ALIASES = {
    "TELEPORT_BOOTH": "TELEPORT",
    "WIND_UP_TOY": "WINDUP_TOY",
    "ESCAPE_DEVICE": "ESCAPE_DEV",
    "SECURITY_DEVICE": "SECURITY_DEV",
}

TOKEN = re.compile(r"@(\w+)\s*(?:\$\s*(\w+)\s*)?\{|\}|\[|\]|([\w.]+)\s*:\s*([^;]*);")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"//[^\n]*", "", text)


def class_id_for(name: str):
    key = ALIASES.get(name.upper(), name.upper())
    return ClassID.__members__.get(key)


def parse(text: str):
    """Yield region dicts. Grammar: @region $ name { attr:v; ... [ objs ] }"""
    toks = list(TOKEN.finditer(strip_comments(text)))
    i = 0
    regions = []

    def parse_object(i):
        m = toks[i]
        node = {"cls": m.group(1), "attrs": {}, "children": []}
        i += 1
        while i < len(toks):
            t = toks[i]
            s = t.group(0)
            if s == "}":
                return node, i + 1
            if s in "[]":
                i += 1
                continue
            if t.group(1):
                child, i = parse_object(i)
                node["children"].append(child)
                continue
            node["attrs"][t.group(3)] = t.group(4).strip()
            i += 1
        return node, i

    while i < len(toks):
        if toks[i].group(1) == "region":
            name = toks[i].group(2) or ""
            node, i = parse_object(i)
            node["name"] = name
            regions.append(node)
        else:
            i += 1
    return regions


def num(v, default=0):
    try:
        return int(str(v).split(",")[0].strip())
    except (TypeError, ValueError):
        return default


def convert_object(node, unknown: Counter):
    cid = class_id_for(node["cls"])
    if cid is None:
        unknown[node["cls"]] += 1
    a = node["attrs"]
    slots = {k: num(v) for k, v in a.items() if k.isdigit()}
    attrs = {k: v for k, v in a.items()
             if not k.isdigit() and k not in ("x", "y", "or", "style", "gr_state")}
    return {
        "class_id": int(cid) if cid is not None else None,
        "class_name": node["cls"],
        "x": num(a.get("x")), "y": num(a.get("y")),
        "orientation": num(a.get("or")), "style": num(a.get("style")),
        "gr_state": num(a.get("gr_state")),
        "slots": slots, "attrs": attrs,
        "children": [convert_object(c, unknown) for c in node["children"]],
    }


def main(root: str, out: str):
    files = sorted(Path(root).rglob("*.rdl"))
    by_name = {}
    dup = 0
    for f in files:
        try:
            text = f.read_text(encoding="latin-1")
        except OSError as e:
            print(f"skip {f}: {e}")
            continue
        for r in parse(text):
            if r["name"] in by_name:
                dup += 1
                continue
            by_name[r["name"]] = r
    ids = {name: n for n, name in enumerate(sorted(by_name), start=1)}
    unknown = Counter()
    unresolved = Counter()
    regions = []
    for name, r in by_name.items():
        nb = {}
        for d in ("west", "east", "north", "south"):
            ref = r["attrs"].get(d)
            if ref:
                ref = ref.split(".")[0].strip()
                if ref in ids:
                    nb[d] = ids[ref]
                else:
                    nb[d] = 0
                    unresolved[ref] += 1
            else:
                nb[d] = 0
        regions.append({
            "region_id": ids[name], "name": name, "neighbors": nb,
            "orientation": r["attrs"].get("region_orientation", ""),
            "objects": [convert_object(c, unknown) for c in r["children"]],
        })

    def count(objs):
        return sum(1 + count(o["children"]) for o in objs)

    total = sum(count(r["objects"]) for r in regions)
    report = {
        "rdl_files": len(files), "regions": len(regions),
        "duplicate_region_names_skipped": dup, "objects": total,
        "unknown_classes": dict(unknown),
        "unresolved_neighbor_refs": len(unresolved),
        "unresolved_neighbor_examples": list(unresolved)[:10],
    }
    Path(out).write_text(json.dumps({"regions": regions, "report": report}),
                         encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
