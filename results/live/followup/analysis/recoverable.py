import json
import re
import sys
from collections import Counter

from live.entries import normalize, said, same
from live.scenario import Turn, load, spoken, truth
from live.tech import PATTERNS

run_dir, label, arm = sys.argv[1:4]
c, ex = Counter(), []
for n in ["c01", "c02", "c03", "c04", "g01", "g02", "g03", "g04"]:
    v = load(f"live/scenarios/test/{n}.json")
    d = json.load(open(f"{run_dir}/run1/{label}/{n}.{arm}.json"))
    turns = [Turn(**t) for t in d["turns"]]
    heard = d["heard"]
    st = truth(turns)
    rec = normalize(d["steps"][-1]["record"], v.equipment_ids)
    for k, val in st.readings.items():
        if k in rec.readings and same(rec.readings[k], val):
            c["kept"] += 1
            continue
        pat = re.compile(PATTERNS[k[1].removesuffix("_after")], re.I)
        lines = [
            t
            for t in turns
            if any(
                e["op"] in ("reading", "revise", "resolve")
                and (e.get("equip"), e["field"]) == k
                or (e["op"] == "resolve" and e["field"] == k[1])
                for e in t.effects
            )
        ]
        lines += [
            t for t in turns if t.id.endswith("a") and said(val, t.text) and pat.search(t.text)
        ]  # restated replies
        clear = [t for t in lines if said(val, spoken(t, heard).replace("~", "")) and pat.search(spoken(t, heard))]
        if clear:
            c["missed though number and word were heard"] += 1
            if len(ex) < 8:
                ex.append(
                    (
                        n,
                        k,
                        val,
                        spoken(clear[0], heard)[:70],
                        "unsure"
                        if any(k[0] in eq and f == k[1] for eq, f in rec.unresolved)
                        else ("wrong" if k in rec.readings else "left out"),
                    )
                )
        else:
            c["not clearly heard"] += 1
print(arm, label, dict(c))
for e in ex:
    print("   ", e)
