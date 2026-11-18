from fvr.arms import run_arm
from fvr.metrics import safeguard_outcomes, silent_errors
from fvr.verify import Record, Thresholds, field_decisions, retrieve

RECORD = Record(["24ACC636A003"], ["Carrier", "contactor", "dual run capacitor"])
TH = Thresholds()


def words(text, p=0.9):
    return [(w, p) for w in text.split()]


def test_retrieval_selects_only_near_misses():
    assert retrieve("The condenser is a carrier 24ACC636A003, contactor fine.", RECORD, TH) == []
    assert retrieve("The condenser is a carrier 24 ACC 63 6A 003, contractor fine.", RECORD, TH) == ["contactor"]
    assert retrieve("Condenser 24ACG636A008, the contactor.", RECORD, TH) == ["24ACC636A003"]


def test_safeguard_confirms_unknown_or_disputed_ids_and_never_edits():
    text = "Unit is 24ACC636A003 and suction is 118 psi"
    assert field_decisions(text, words(text), RECORD, TH) == [
        (("id", "24acc636a003"), "accept"),
        (("reading", "118|psi"), "accept"),
    ]
    other = "Unit is 24ACC648A003 and suction is 180 psi"
    decisions = field_decisions(text, words(text), RECORD, TH, unbiased=other)
    assert [d for _, d in decisions] == ["confirm", "confirm"]
    stale = Record(["24ACC648A003"], [])
    assert field_decisions(text, words(text), stale, TH)[0] == (("id", "24acc636a003"), "confirm")


def test_low_probability_reading_is_confirmed():
    text = "suction is 118 psi"
    probs = [("suction", 0.9), ("is", 0.9), ("118", 0.1), ("psi", 0.9)]
    assert field_decisions(text, probs, RECORD, TH) == [(("reading", "118|psi"), "confirm")]


def test_outcomes_count_silent_errors():
    row = {"ids": ["24ACC636A003"], "readings": [["118", "psi"]]}
    out = safeguard_outcomes(row, [(("id", "24acc636a003"), "accept"), (("reading", "180|psi"), "accept")])
    assert out["correct_accept"] == 1 and out["wrong_accept"] == 1 and silent_errors(out) == 1
    out = safeguard_outcomes(row, [(("reading", "180|psi"), "confirm")])
    assert out["wrong_confirm"] == 1 and out["missed_silent"] == 1 and silent_errors(out) == 1


def test_hybrid_keeps_unbiased_text_when_audio_disagrees():
    none = {"text": "Unit is 24ACC636A003", "words": words("Unit is 24ACC636A003"), "seconds": 1.0}
    ctx = {"text": "Unit is 24ACC648A003", "words": words("Unit is 24ACC648A003"), "seconds": 1.0}
    evidence = {
        "lp_none": -5.0,
        "encode_seconds": 0.1,
        "stale": {
            "record": {"ids": ["24ACC648A003"], "terms": []},
            "hybrid": {"lp_context": -30.0, "score_seconds": 0.1},
            "detect": {"items": []},
        },
    }
    res = run_arm("H", {"none": none, "stale": ctx}, evidence, "stale", TH)
    assert res.text == none["text"] and not res.rewrote
    assert [d for _, d in res.decisions] == ["confirm"]


def test_glued_neighbour_word_does_not_hide_a_record_id():
    text = "Main panel is a Square D QO130L200PG060."
    record = Record(["QO130L200PG060"], [])
    assert field_decisions(text, words(text), record, TH) == [(("id", "qo130l200pg060"), "accept")]
    row = {"ids": ["QO130L200PG060"], "readings": []}
    assert safeguard_outcomes(row, field_decisions(text, words(text), record, TH))["correct_accept"] == 1


def test_unchanged_transcript_is_not_a_rewrite():
    none = {"text": "Unit is 24ACC636A003", "words": words("Unit is 24ACC636A003"), "seconds": 1.0}
    evidence = {
        "lp_none": -5.0,
        "encode_seconds": 0.1,
        "job": {
            "record": {"ids": ["24ACC636A003"], "terms": []},
            "hybrid": {"lp_context": -5.0, "score_seconds": 0},
            "detect": {"items": []},
        },
    }
    assert not run_arm("H", {"none": none, "job": dict(none)}, evidence, "job", TH).rewrote


def test_spoken_refrigerant_is_not_a_context_insertion():
    from fvr.metrics import context_insertions

    row = {"ids": ["PUZ-A024NKA7"], "readings": []}
    text = "Mitsubishi PUZ-A024NKA7, check the R-410A."
    assert context_insertions(row, text, ["PUZ-A036NKA7", "R-410A"]) == 0
    assert context_insertions(row, "Mitsubishi PUZ-A036NKA7", ["PUZ-A036NKA7"]) == 1
