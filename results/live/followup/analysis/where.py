import json
import sys
from collections import Counter

from live.entries import normalize, said, same
from live.scenario import Turn, load, spoken, truth

arms = sys.argv[1:]
for arm in arms:
    c, examples = Counter(), []
    for n in ["c01", "c02", "c03", "c04", "g01", "g02", "g03", "g04"]:
        v = load(f"live/scenarios/test/{n}.json")
        d = json.load(open(f"results/live/stage1/run1/asr/{n}.{arm}.json"))
        g = json.load(open(f"results/live/stage1/run1/gold/{n}.{arm}.json"))
        turns = [Turn(**t) for t in d["turns"]]
        heard = d["heard"]
        st = truth(turns)
        rec = normalize(d["steps"][-1]["record"], v.equipment_ids)
        grec = normalize(g["steps"][-1]["record"], v.equipment_ids)
        scripted = [t for t in turns if t.id.isdigit()]
        for k, val in st.readings.items():
            if k in rec.readings and same(rec.readings[k], val):
                c["reading kept"] += 1
                continue
            in_gold = k in grec.readings and same(grec.readings[k], val)
            lines = [
                t
                for t in scripted
                if any(e["op"] in ("reading", "revise") and (e["equip"], e["field"]) == k for e in t.effects)
            ]
            heard_has = any(said(val, spoken(t, heard).replace("~", "")) for t in lines)
            hedged = any(k[0] in eq and f == k[1] for eq, f in rec.unresolved)
            if k in rec.readings:
                why = "wrong value"
            elif not heard_has:
                why = "number not in recognised text"
            elif hedged:
                why = "heard, but marked unsure"
            else:
                why = "heard, but left out"
            c[why + (" (gold had it)" if in_gold else " (gold missed too)")] += 1
            if why.startswith("heard") and len(examples) < 6:
                examples.append((n, k, val, [spoken(t, heard)[:70] for t in lines][:1]))
        for k, s in st.work.items():
            c["work kept" if rec.work.get(k) == s else ("work wrong" if k in rec.work else "work left out")] += 1
        listed = {(e["id"], f): e[f] for e in v.equipment for f in ("model", "serial")}
        for k, val in st.equipment.items():
            if k in listed and same(val, listed[k]):
                continue
            c[
                "equipment kept" if k in rec.equipment and same(rec.equipment[k], val) else "equipment missing or wrong"
            ] += 1
        c[
            "open ambiguity marked"
            if all(
                any(u.field == f and set(eq) & set(u.equip) for eq, f in rec.unresolved) for u in st.unresolved.values()
            )
            else "open ambiguity not marked"
        ] += len(st.unresolved)
    print(arm, dict(sorted(c.items())))
    for e in examples:
        print("   ", e)
