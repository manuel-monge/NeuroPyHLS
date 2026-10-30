#!/usr/bin/env python3
"""Export a code-db SQLite into compact JSON and inject it into the explorer HTML template.

Usage: python3 -I build_explorer.py <db.sqlite> <template.html> <out.html>
"""
import json
import sqlite3
import sys

db, tpl, out = sys.argv[1:4]
con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
q = lambda sql: [dict(r) for r in con.execute(sql)]

meta = {r["key"]: json.loads(r["value"]) for r in q("SELECT * FROM meta")}
algos = q("SELECT * FROM algorithms ORDER BY algorithm_type, name")
glob = q("SELECT algorithm_id, element_type, element_id, min_depth, n_uses, n_via_functions FROM global_dataset")
af = {(r["algorithm_id"], r["function_id"]): r["reached_from"] for r in q("SELECT * FROM algorithm_functions")}

used = {t: set() for t in ("function", "library", "library_api", "primitive", "object_method")}
for g in glob:
    used[g["element_type"]].add(g["element_id"])

P = meta["package"] + "."
short = lambda s: s[len(P):] if s.startswith(P) else s
funcs = {f["function_id"]: f for f in q("SELECT * FROM functions")}
libs = {l["library_id"]: l for l in q("SELECT * FROM libraries")}
apis = {a["api_id"]: a for a in q("SELECT * FROM library_api")}
prims = {p["primitive_id"]: p for p in q("SELECT * FROM primitives")}

# element tables: index -> compact record
E = {"function": sorted(used["function"]), "library": sorted(used["library"]),
     "library_api": sorted(used["library_api"]), "primitive": sorted(used["primitive"]),
     "object_method": sorted(used["object_method"])}
idx = {t: {e: i for i, e in enumerate(v)} for t, v in E.items()}
elements = {
    "function": [[short(f), funcs[f]["kind"], funcs[f]["subpackage"], funcs[f]["n_lines"], funcs[f]["cyclomatic_complexity"],
                  funcs[f]["is_numba_jit"], funcs[f]["docstring"][:140]] if f in funcs else [short(f), "", "", 0, 0, 0, ""]
                 for f in E["function"]],
    "library": [[l, libs.get(l, {}).get("category", ""), libs.get(l, {}).get("is_stdlib", 0)] for l in E["library"]],
    "library_api": [[a, apis.get(a, {}).get("category", "")] for a in E["library_api"]],
    "primitive": [[p, prims[p]["category"], prims[p]["description"]] for p in E["primitive"]],
    "object_method": [[m] for m in E["object_method"]],
}
types = ["function", "library", "library_api", "primitive", "object_method"]
rows = {}
for g in glob:
    t = g["element_type"]
    i = idx[t][g["element_id"]]
    extra = ""
    if t == "function":
        rf = af.get((g["algorithm_id"], g["element_id"]), "")
        extra = idx["function"].get(rf, -1) if rf else -1
    rows.setdefault(g["algorithm_id"], []).append([types.index(t), i, g["min_depth"], g["n_uses"], extra])

data = {
    "meta": meta,
    "types": types,
    "elements": elements,
    "algorithms": [{
        "id": a["algorithm_id"], "name": a["name"], "type": a["algorithm_type"], "subtype": a["subtype"],
        "entry": short(a["entry_point"]), "kind": a["entry_kind"], "found": a["discovered_by"], "doc": a["docstring"],
        "notes": a["notes"], "lines": a["own_lines"], "reach": a["n_functions_reachable"], "numba": a["uses_numba"],
        "torch": a["uses_torch"], "rows": rows.get(a["algorithm_id"], []),
    } for a in algos],
    "relations": [[r["algorithm_id"], r["related_algorithm_id"], r["relation"]] for r in q("SELECT * FROM algorithm_relations")],
    "totals": {k: v for k, v in meta["counts"].items()},
}
html = open(tpl, encoding="utf-8").read().replace("/*__DATA__*/null", json.dumps(data, separators=(",", ":")))
open(out, "w", encoding="utf-8").write(html)
print(f"wrote {out}: {len(html)/1e6:.2f} MB")
