"""Text normalisation shared by scoring and field extraction.

Spoken identifiers come back from ASR in many shapes ("2-4 ACC 636", "24ACC636"), so runs of identifier parts
are merged into one canonical token before comparing anything.
"""

import re

UNITS = {
    "psi": "psi",
    "psig": "psi",
    "microamps": "microamps",
    "microamp": "microamps",
    "millivolts": "millivolts",
    "millivolt": "millivolts",
    "megohms": "megohms",
    "megohm": "megohms",
    "megaohms": "megohms",
    "kilohms": "kilohms",
    "mv": "millivolts",
    "ua": "microamps",
    "µa": "microamps",
    "vac": "volts",
    "inch_pounds": "inch_pounds",
    "gpm": "gpm",
    "degrees": "degrees",
    "degree": "degrees",
    "°": "degrees",
    "°f": "degrees",
    "volts": "volts",
    "volt": "volts",
    "v": "volts",
    "amps": "amps",
    "amp": "amps",
    "amperes": "amps",
    "microfarads": "microfarads",
    "microfarad": "microfarads",
    "mfd": "microfarads",
    "uf": "microfarads",
    "µf": "microfarads",
    "ohms": "ohms",
    "ohm": "ohms",
    "percent": "percent",
    "%": "percent",
    "inches": "inches_wc",
    "inch": "inches_wc",
}

_SMALL = {
    w: i
    for i, w in enumerate(
        "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
        "seventeen eighteen nineteen".split()
    )
}
_SMALL["oh"] = 0
_TENS = {w: 10 * i for i, w in enumerate("_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()) if i > 1}
_REFRIGERANT = re.compile(r"^r\d{2,3}[a-z]?$")


def words_to_number(words: list[str]) -> tuple[str, int] | None:
    """Parse a standard English number at the start of `words`. Returns (digits, words used) or None."""
    total, current, used, decimal, after_tens = 0, 0, 0, None, False
    for i, w in enumerate(words):
        if w == "a" and not used and i + 1 < len(words) and words[i + 1] == "hundred":
            current, used = 1, i + 1  # "a hundred and fifty"
            continue
        if w == "and" and used and i > 0 and words[i - 1] in ("hundred", "thousand"):
            continue
        fresh = current % 100 == 0
        if w in _SMALL and decimal is None and (fresh or (after_tens and _SMALL[w] < 10)):
            current += _SMALL[w]
            if not used and w in ("zero", "oh"):
                used = i + 1
                break  # a leading zero is a digit string, not a number
        elif w in _TENS and decimal is None and fresh:
            current += _TENS[w]
            after_tens = True
            used = i + 1
            continue
        elif w == "hundred" and used:
            current *= 100
        elif w == "thousand" and used:
            total, current = (total + current) * 1000, 0
        elif w == "point" and decimal is None and (used or (i + 1 < len(words) and words[i + 1] in _SMALL)):
            decimal = ""  # "point seven two" is 0.72
        elif decimal is not None and w in _SMALL and _SMALL[w] < 10:
            decimal += str(_SMALL[w])
        else:
            break
        used = i + 1
    if not used or decimal == "":
        return None
    value = str(total + current)
    return (f"{value}.{decimal}" if decimal else value), used


def _raw_tokens(text: str) -> list[str]:
    text = text.replace("°F", " degrees ").replace("°", " degrees ").replace("%", " percent ")
    text = text.replace("μ", "µ")  # Whisper writes Greek mu; units use the micro sign
    # "50Mohms", "200M Ohms": capital M only, since a lowercase m could mean milliohms
    text = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)\s?(MΩ|M\s?[oO]hms?)(?!\w)", r"\1 megohms", text)
    text = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)\s?(kΩ|k\s?[oO]hms?)(?!\w)", r"\1 kilohms", text)
    text = re.sub(r"(?<![\w.])(\d+(?:\.\d+)?)\s?(Ω|ohms?)(?!\w)", r"\1 ohms", text)
    text = re.sub(r"\bP\.?[\s-]?S\.?[\s-]?I\b\.?", " psi ", text, flags=re.IGNORECASE)  # before ID merging
    text = re.sub(r"\bM\.?[\s-]?F\.?[\s-]?D\b\.?", " mfd ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bin[.-]?\s?lbs?\b\.?", " inch_pounds ", text, flags=re.IGNORECASE)
    text = re.sub(r"(?<=[A-Za-z0-9])[\s-]+dash[\s-]+(?=[A-Za-z0-9])", "-", text, flags=re.IGNORECASE)  # spoken "dash"
    text = re.sub(r"(?<=\d)-(?=\d)", " ", text)  # "2-4" is two spoken digits, not a range here
    text = re.sub(r"(?<=[A-Za-z0-9])-(?=[A-Za-z0-9])", " ", text)
    text = re.sub(r"(?<=\d),(?=\d{3})", "", text)
    text = re.sub(r"\b(\d+) 1/2\b", r"\1.5", text)
    text = re.sub(r"\b(\d+) ([13])/4\b", lambda m: f"{m.group(1)}.{'25' if m.group(2) == '1' else '75'}", text)
    text = re.sub(r"(?<=\d)/(?=\d)", " over ", text)  # "45/5 MFD" is a dual reading, never 455
    text = re.sub(r"(?<![\d.])\.(?=\d)", "0.", text)  # ".72 inches" is 0.72
    text = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", text)
    text = re.sub(r"\b(\d+(?:\.\d+)?)(V|VAC|psi|PSI|uF|µF|mfd|MFD|mV|uA|µA)\b", r"\1 \2", text)  # "229V"
    text = re.sub(r"\b(\d+\.\d+)A\b", r"\1 amps", text)  # "24.6A"; "60A" may be a code, see readings.py
    return re.findall(r"[A-Za-z0-9.µ]+", text)


def _is_id_part(token: str) -> bool:
    return any(c.isdigit() for c in token) or (token.isalpha() and token.isupper() and len(token) <= 4)


def _id_runs(tokens: list[str]) -> list[list[str]]:
    """Group tokens: each run of identifier parts with a digit becomes one group, every other token its own."""
    out, run = [], []

    def flush():
        has_digit = any(any(c.isdigit() for c in t) for t in run)
        has_alpha = any(any(c.isalpha() for c in t) for t in run)
        if len(run) > 1 and has_digit and has_alpha:  # "60, 62" stays two numbers; only codes merge
            out.append(list(run))
        else:
            out.extend([t] for t in run)
        run.clear()

    for i, t in enumerate(tokens):
        pronoun = t == "I" and tokens[i + 1 : i + 2] != [] and tokens[i + 1].islower()  # "123, I mean", not "I N K"
        if _is_id_part(t) and t.lower() not in UNITS and "." not in t and not pronoun:
            run.append(t)
        else:
            flush()
            out.append([t])
    flush()
    return out


def _numbers_from_words(tokens: list[str]) -> list[str]:
    out, i = [], 0
    while i < len(tokens):
        parsed = words_to_number(tokens[i:])
        if parsed and not (parsed[1] == 1 and tokens[i] == "oh"):
            out.append(parsed[0])
            i += parsed[1]
        else:
            out.append(tokens[i])
            i += 1
    return out


def token_groups(text: str) -> list[list[str]]:
    """The pieces behind each canonical token, in the same order."""
    raw = _raw_tokens(text)
    lowered = [t if _is_id_part(t) else t.lower() for t in raw]
    return [[t.lower() for t in g] for g in _id_runs(_numbers_from_words(lowered))]


def canonical_tokens(text: str) -> list[str]:
    """Lower-cased tokens with number words as digits and identifier runs merged."""
    return ["".join(g) for g in token_groups(text)]


def id_runs(text: str) -> list[list[str]]:
    """The token pieces of each merged identifier run (and single tokens that are identifiers)."""
    return [g for g in token_groups(text) if any(c.isdigit() for c in "".join(g))]


def contains_id(text: str, identifier: str) -> bool:
    """True if some contiguous run of whole tokens in `text` spells `identifier` (ignoring case and separators).

    Whole tokens only, so a neighbouring word glued into a merged run ("Square D QO130...") does not hide a correct
    identifier, and a partial token never counts.
    """
    target = canonical_id(identifier)
    tokens = [t for g in token_groups(text) for t in g]
    for i in range(len(tokens)):
        joined = ""
        for t in tokens[i:]:
            joined += t
            if joined == target:
                return True
            if len(joined) >= len(target):
                break
    return False


def canonical_text(text: str) -> str:
    return " ".join(canonical_tokens(text))


def canonical_id(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def is_refrigerant(token: str) -> bool:
    return bool(_REFRIGERANT.match(token))
