"""Synthetic field-service jobs and technician utterances (clearly labelled synthetic).

Every job has a frozen record (equipment, model numbers, the dispatched complaint) and a stale record from the
customer's previous visit. Readings are generated per utterance and never appear in any record.
Model-number formats imitate common brands' styles; the strings themselves are invented.
"""

import random
from dataclasses import asdict, dataclass, field

TONS = ["024", "030", "036", "048", "060"]

# type -> (trade, [(brand, model template)], jargon)
CATALOG = {
    "condenser": (
        "hvac",
        [
            ("Carrier", "24ACC6{t}A003"),
            ("Goodman", "GSX14{t}1"),
            ("Trane", "4TTR4{t}L1000A"),
            ("Lennox", "ML14XC1-{t}"),
        ],
        [
            "contactor",
            "dual run capacitor",
            "TXV",
            "line set",
            "condenser fan motor",
            "compressor",
            "R-410A",
            "superheat",
            "subcooling",
            "disconnect",
        ],
    ),
    "furnace": (
        "hvac",
        [
            ("Goodman", "GMVC96{n}4CN"),
            ("Carrier", "59SC5A{n}E17"),
            ("Lennox", "EL296UH{n}XE36B"),
            ("Rheem", "R96VA{n}17MSA"),
        ],
        [
            "flame sensor",
            "inducer motor",
            "pressure switch",
            "hot surface igniter",
            "heat exchanger",
            "limit switch",
            "ECM blower",
            "condensate trap",
            "gas valve",
        ],
    ),
    "heat pump": (
        "hvac",
        [("Rheem", "RP14{t}AJ1NA"), ("Daikin", "DZ14SA{t}1"), ("Mitsubishi", "PUZ-A{t}NKA7")],
        [
            "reversing valve",
            "defrost board",
            "contactor",
            "dual run capacitor",
            "R-410A",
            "TXV",
            "outdoor coil",
            "superheat",
        ],
    ),
    "water heater": (
        "plumbing",
        [("Rheem", "XG50T06EC{n}U1"), ("A. O. Smith", "GCR-50{n}"), ("Bradford White", "RG250T6N{n}")],
        ["anode rod", "thermocouple", "T&P valve", "dip tube", "gas control valve", "flue baffle", "expansion tank"],
    ),
    "tankless water heater": (
        "plumbing",
        [("Rinnai", "RU199iN{n}"), ("Navien", "NPE-240A2{n}")],
        ["descaling", "flow sensor", "heat exchanger", "condensate neutralizer", "isolation valves", "venting"],
    ),
    "electrical panel": (
        "electrical",
        [("Square D", "QO130L200PG{n}"), ("Siemens", "PN2040B1200C{n}"), ("Eaton", "BR2040B200{n}")],
        ["bus bar", "neutral", "GFCI", "AFCI", "double tap", "main breaker", "grounding electrode", "torque spec"],
    ),
}

# type -> [(label spoken, unit, low, high, decimals)]; dual readings are capacitor style "45 over 5".
READINGS = {
    "condenser": [
        ("suction pressure", "psi", 100, 150, 0),
        ("head pressure", "psi", 250, 420, 0),
        ("superheat", "degrees", 5, 20, 0),
        ("subcooling", "degrees", 6, 16, 0),
        ("compressor amp draw", "amps", 8, 25, 1),
        ("line voltage", "volts", 228, 246, 0),
    ],
    "furnace": [
        ("manifold gas pressure", "inches of water column", 3, 4, 1),
        ("temperature rise", "degrees", 35, 65, 0),
        ("total external static", "inches of water column", 0.4, 0.9, 2),
        ("inducer amp draw", "amps", 1, 3, 1),
    ],
    "heat pump": [
        ("suction pressure", "psi", 100, 150, 0),
        ("superheat", "degrees", 5, 20, 0),
        ("compressor amp draw", "amps", 8, 25, 1),
    ],
    "water heater": [
        ("outlet temperature", "degrees", 118, 140, 0),
        ("gas pressure", "inches of water column", 5, 7, 1),
        ("house pressure", "psi", 45, 80, 0),
    ],
    "tankless water heater": [
        ("outlet temperature", "degrees", 118, 140, 0),
        ("inlet gas pressure", "inches of water column", 5, 7, 1),
    ],
    "electrical panel": [
        ("line to neutral", "volts", 116, 124, 0),
        ("line to line", "volts", 236, 246, 0),
        ("load on the main", "amps", 20, 140, 0),
    ],
}

GENERIC_TERMS = [
    "contactor",
    "capacitor",
    "compressor",
    "TXV",
    "superheat",
    "subcooling",
    "R-410A",
    "flame sensor",
    "inducer motor",
    "pressure switch",
    "heat exchanger",
    "igniter",
    "ECM blower",
    "condensate",
    "anode rod",
    "thermocouple",
    "T&P valve",
    "expansion tank",
    "tankless",
    "descaling",
    "GFCI",
    "AFCI",
    "bus bar",
    "neutral",
    "breaker",
    "grounding",
    "psi",
    "amps",
    "volts",
    "microfarads",
    "water column",
    "static pressure",
]

_ONES = "zero one two three four five six seven eight nine".split()
_TEENS = "ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


@dataclass
class Equipment:
    type: str
    brand: str
    model: str


@dataclass
class Job:
    job_id: str
    trade: str
    complaint: str
    equipment: list[Equipment]
    stale_equipment: list[Equipment]


@dataclass
class Utterance:
    utt_id: str
    job_id: str
    ref_text: str
    spoken_text: str
    ids: list[str] = field(default_factory=list)
    ids_in_record: list[bool] = field(default_factory=list)
    readings: list[tuple[str, str]] = field(default_factory=list)
    terms: list[str] = field(default_factory=list)


def two_digits(n: int) -> str:
    if n < 10:
        return _ONES[n]
    if n < 20:
        return _TEENS[n - 10]
    return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])


def say_number(value: float, decimals: int, rng: random.Random) -> str:
    """Technician style: 118 -> "one eighteen" or "a hundred eighteen"; 3.5 -> "three point five"."""
    whole = int(value)
    if decimals:
        frac = f"{value:.{decimals}f}".split(".")[1]
        head = "zero" if whole == 0 else say_number(whole, 0, rng)
        return head + " point " + " ".join(_ONES[int(d)] for d in frac)
    if whole < 100:
        return two_digits(whole)
    hundreds, rest = divmod(whole, 100)
    if rest == 0:
        return _ONES[hundreds] + " hundred"
    if rng.random() < 0.5:
        return _ONES[hundreds] + " " + (two_digits(rest) if rest >= 10 else "oh " + _ONES[rest])
    return _ONES[hundreds] + " hundred " + two_digits(rest)


def say_id(model: str, rng: random.Random) -> str:
    """Spell letters, read digits singly ("oh" for zero sometimes) or in pairs."""
    parts, buf = [], ""
    for c in model + " ":
        if buf and (c.isdigit() != buf[-1].isdigit() or not c.isalnum()):
            parts.append(buf)
            buf = ""
        if c.isalnum():
            buf += c
        elif c == "-" and rng.random() < 0.5:
            parts.append("dash")
    words = []
    for p in parts:
        if p == "dash":
            words.append("dash")
        elif p.isdigit():
            if len(p) % 2 == 0 and rng.random() < 0.4 and "0" not in p[::2]:
                words += [two_digits(int(p[i : i + 2])) for i in range(0, len(p), 2)]
            else:
                words += [("oh" if d == "0" and rng.random() < 0.5 else _ONES[int(d)]) for d in p]
        else:
            words += [c.upper() for c in p]
    return " ".join(words)


def _make_equipment(etype: str, rng: random.Random, avoid: str = "") -> Equipment:
    _, models, _ = CATALOG[etype]
    for _ in range(50):
        brand, tmpl = rng.choice(models)
        model = tmpl.format(t=rng.choice(TONS), n=rng.choice(["060", "080", "100", "40", "36"]))
        if model != avoid:
            return Equipment(etype, brand, model)
    raise RuntimeError("could not make distinct equipment")


def _stale_version(eq: Equipment, rng: random.Random) -> Equipment:
    """Previous visit's unit of the same type and brand, since replaced: a near-miss model number."""
    _, models, _ = CATALOG[eq.type]
    same_brand = [m for b, m in models if b == eq.brand]
    for _ in range(50):
        model = rng.choice(same_brand).format(t=rng.choice(TONS), n=rng.choice(["060", "080", "100", "40", "36"]))
        if model != eq.model:
            return Equipment(eq.type, eq.brand, model)
    return _make_equipment(eq.type, rng, avoid=eq.model)


def make_jobs(n_jobs: int, rng: random.Random) -> list[Job]:
    trades = {
        "hvac": [["condenser", "furnace"], ["heat pump"], ["condenser", "furnace"]],
        "plumbing": [["water heater"], ["tankless water heater"]],
        "electrical": [["electrical panel"]],
    }
    complaints = {
        "hvac": ["no cooling", "short cycling", "no heat", "noisy outdoor unit"],
        "plumbing": ["no hot water", "leaking water heater", "pilot keeps going out"],
        "electrical": ["breaker keeps tripping", "panel inspection", "flickering lights"],
    }
    plan = (
        ["hvac"] * (n_jobs // 2) + ["plumbing"] * (n_jobs // 4) + ["electrical"] * (n_jobs - n_jobs // 2 - n_jobs // 4)
    )
    jobs = []
    for i, trade in enumerate(plan):
        types = rng.choice(trades[trade])
        equipment = [_make_equipment(t, rng) for t in types]
        stale = [_stale_version(e, rng) for e in equipment]
        jobs.append(Job(f"job{i:02d}", trade, rng.choice(complaints[trade]), equipment, stale))
    return jobs


def _reading(etype: str, rng: random.Random) -> tuple[str, str, str, tuple[str, str]]:
    label, unit, lo, hi, dec = rng.choice(READINGS[etype])
    value = round(rng.uniform(lo, hi), dec) if dec else rng.randint(int(lo), int(hi))
    written = f"{value:.{dec}f}" if dec else str(value)
    spoken = say_number(value, dec, rng)
    unit_key = {"inches of water column": "inches_wc"}.get(unit, unit)
    return label, f"{written} {unit}", f"{spoken} {unit}", (f"{float(written):g}", unit_key)


def _capacitor(rng: random.Random) -> tuple[str, str, tuple[str, str]]:
    big = rng.choice([35, 40, 45, 50, 55, 60])
    return f"{big} over 5 microfarads", f"{two_digits(big)} over five microfarads", (f"{big}/5", "microfarads")


def make_utterances(job: Job, n_new_equipment: int, rng: random.Random) -> list[Utterance]:
    """Six utterances per job: model statements, readings, jargon, and one about equipment not on record."""
    out = []
    for k, eq in enumerate(job.equipment[:2]):
        jargon = CATALOG[eq.type][2]
        t1, t2 = rng.sample(jargon, 2)
        sid = say_id(eq.model, rng)
        out.append(
            Utterance(
                f"{job.job_id}_u{len(out)}",
                job.job_id,
                f"The {eq.type} is a {eq.brand} {eq.model}, checked the {t1} and the {t2}.",
                f"The {eq.type} is a {eq.brand}, {sid}. Checked the {t1} and the {t2}.",
                [eq.model],
                [True],
                [],
                [eq.brand, t1, t2],
            )
        )
        label, w, s, r = _reading(eq.type, rng)
        label2, w2, s2, r2 = _reading(eq.type, rng)
        if label2 == label:
            label2, w2, s2, r2 = "", "", "", None
        ref = f"{label.capitalize()} is {w}" + (f" and {label2} is {w2}." if r2 else ".")
        spoken = f"{label.capitalize()} is {s}" + (f", and {label2} is {s2}." if r2 else ".")
        out.append(
            Utterance(f"{job.job_id}_u{len(out)}", job.job_id, ref, spoken, [], [], [r] + ([r2] if r2 else []), [])
        )
        if k == 0:
            t3 = rng.choice(jargon)
            label, w, s, r = _reading(eq.type, rng)
            out.append(
                Utterance(
                    f"{job.job_id}_u{len(out)}",
                    job.job_id,
                    f"Replaced the {t3} on the {eq.brand} {eq.model}, {label} now {w}.",
                    f"Replaced the {t3} on the {eq.brand}, {say_id(eq.model, rng)}, {label} now {s}.",
                    [eq.model],
                    [True],
                    [r],
                    [eq.brand, t3],
                )
            )
    eq = job.equipment[0]
    if eq.type in ("condenser", "heat pump"):
        w, s, r = _capacitor(rng)
        out.append(
            Utterance(
                f"{job.job_id}_u{len(out)}",
                job.job_id,
                f"The dual run capacitor reads {w}.",
                f"The dual run capacitor reads {s}.",
                [],
                [],
                [r],
                ["dual run capacitor"],
            )
        )
    for _ in range(n_new_equipment):
        new = _make_equipment(eq.type, rng, avoid=eq.model)
        out.append(
            Utterance(
                f"{job.job_id}_u{len(out)}",
                job.job_id,
                f"Customer wants a quote on a {new.brand} {new.model} {new.type}.",
                f"Customer wants a quote on a {new.brand}, {say_id(new.model, rng)}, {new.type}.",
                [new.model],
                [False],
                [],
                [new.brand],
            )
        )
    return out


def job_record_terms(job: Job) -> list[str]:
    """Terminology selected automatically from the equipment types on the job record."""
    terms = []
    for eq in job.equipment:
        terms += [t for t in CATALOG[eq.type][2] if t not in terms]
    return terms


def as_dict(obj) -> dict:
    return asdict(obj)
