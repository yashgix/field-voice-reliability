from fvr.fields import Reading
from fvr.readings import Settings, verify

TH = Settings(min_prob=0.4)


def words(text, p=0.95):
    return [(w, p) for w in text.split()]


def reasons(text, **kw):
    return [(c.decision, c.reason) for c in verify(text, words(text), TH, **kw)]


def test_clean_reading_is_accepted():
    assert reasons("Suction pressure is 118 psi.") == [("accept", "ok")]


def test_misheard_unit_is_questioned_not_fixed():
    for text in (
        "The dual run capacitor reads 60 over 5 microtarads.",
        "Suction pressure is 131C.",
        "Suction pressure is 141 side.",
        "Line to line is 242 holes.",
    ):
        checks = verify(text, words(text), TH)
        assert [c.reason for c in checks] == ["unclear_unit"], text
        assert all(c.reading is None for c in checks)


def test_label_without_value():
    assert ("confirm", "no_value") in reasons("Superheat is, uh, I'll check again.")
    assert reasons("Checked the flame sensor and the pressure switch.") == []


def test_low_confidence_number():
    text = "Superheat is 15 degrees."
    ws = [("Superheat", 0.9), ("is", 0.9), ("15", 0.2), ("degrees.", 0.9)]
    assert [(c.decision, c.reason) for c in verify(text, ws, TH)] == [("confirm", "low_confidence")]


def test_correction_and_approximate():
    assert reasons("Suction is 120, no wait, 124 psi.")[0] == ("confirm", "correction")
    assert reasons("Return air is about 70 degrees.") == [("confirm", "approximate")]


def test_disagreement_with_second_transcript():
    checks = verify("Subcooling is 14 degrees.", words("x"), TH, other="Subcooling is 15 degrees.")
    assert {(c.decision, c.reason) for c in checks} == {("confirm", "disagreement")}
    assert Reading("14", "degrees") in {c.reading for c in checks}


def test_model_numbers_and_counts_are_not_readings():
    assert reasons("The condenser is a Carrier 24ACC636A003.") == []


def test_abandoned_value_is_not_questioned():
    checks = verify("Static water pressure is 72, sorry, 80 PSI.", words("x"), TH)
    assert [(c.reason, c.reading) for c in checks] == [("correction", Reading("80", "psi"))]


def test_resistance_without_unit_is_questioned():
    assert reasons("Ground resistance is 16.") == [("confirm", "unclear_unit")]


def test_correction_without_a_parsed_reading_still_asks():
    assert reasons("Suction is 120... No wait, 124.") == [("confirm", "correction")]


def test_dual_reading_with_misheard_unit_is_questioned():
    checks = verify("It's rated 45 over 5 MFT.", words("x"), TH)
    assert [(c.reason, c.question.split(".")[0]) for c in checks] == [("unclear_unit", "I heard 45 over 5 mft")]


def test_every_unitless_second_reading_is_questioned():
    assert reasons("Dual run cap reads 44.2 on the helm side and 4.8 on the fan side.") == [
        ("confirm", "unclear_unit"),
        ("confirm", "unclear_unit"),
    ]
    assert reasons("Expansion tank precharge is 40 PSI, house is at 60.") == [
        ("accept", "ok"),
        ("confirm", "unclear_unit"),
    ]


def test_unitless_correction_asks_once_for_the_final_value():
    checks = verify("Suction is 120, no wait, 124.", words("x"), TH)
    assert [c.reason for c in checks] == ["correction"]
    assert "124" in checks[0].question and "120" not in checks[0].question


def test_ordinal_is_not_a_reading():
    assert reasons("Superheat on 2nd circuit is 50 degrees.") == [("accept", "ok")]


def test_glued_amps_are_confirmed_in_a_measuring_line():
    checks = verify("Main is carrying 60A on L1 and 52A on L2.", words("x"), TH)
    assert [(c.decision, c.reading) for c in checks] == [
        ("confirm", Reading("60", "amps")),
        ("confirm", Reading("52", "amps")),
    ]
    merged = verify("L1 is 60A, L2 is 52A.", words("x"), TH)
    assert [c.reading for c in merged] == [Reading("60", "amps"), Reading("52", "amps")]


def test_glued_a_outside_a_measuring_line_is_left_alone():
    for text in ("Model number 636A.", "Charged with 507A.", "The condenser is a Carrier 24ACC 636A 003."):
        assert reasons(text) == [], text


def test_repeated_value_is_not_dropped():
    assert reasons("Suction 120 psi, head 120.") == [("accept", "ok"), ("confirm", "unclear_unit")]
    checks = verify("Cap 45/5 and herm 45 microfarads.", words("x"), TH)
    assert [(c.decision, c.reading) for c in checks] == [
        ("accept", Reading("45", "microfarads")),
        ("confirm", None),
    ]


def test_general_correction_question_survives_an_unrelated_question():
    checks = verify("Suction 120, no wait, and the cap reads 45 over 5 mft.", words("x"), TH)
    assert "correction" in [c.reason for c in checks]


def test_counts_and_unit_numbers_are_not_readings():
    for text in ("Unit 2, superheat is 12 degrees.", "3 ton unit, suction 120 psi.", "Step 2, suction 120 psi."):
        assert reasons(text) == [("accept", "ok")], text


def test_the_word_i_is_not_a_correction():
    checks = verify("I checked 3 things, suction 120 psi.", words("x"), TH)
    assert "correction" not in [c.reason for c in checks]


def test_am_after_a_number_may_be_amps():
    assert reasons("Breaker trips at 13 Am 1313.") == [("confirm", "unclear_unit")]


def test_a_measurement_word_beats_a_count_word():
    for text, value in (
        ("The cap reads 45 of 5 microfarads.", "45"),
        ("Superheat 12 of target 10.", "12"),
        ("Voltage at the unit 238.", "238"),
        ("Superheat on unit 12.", "12"),
        ("Static is .5 of an inch.", "0.5"),
    ):
        questions = [c.question for c in verify(text, words("x"), TH) if c.decision == "confirm"]
        assert any(f"I heard {value}" in q for q in questions), text


def test_numbers_merged_with_phase_or_terminal_names_are_asked():
    for text in ("Voltage L1 L2 240 volts.", "L1 60 L2 52.", "Compressor RLA 60A on L1.", "T1 60A T2 52A."):
        assert ("confirm", "unclear_unit") in reasons(text), text


def test_over_before_a_number_and_no_without_a_correction():
    assert reasons("Head pressure is over 400.") == [("confirm", "unclear_unit")]
    assert reasons("Suction 120 psi, head 250 no leaks.") == [("accept", "ok"), ("confirm", "unclear_unit")]


def test_glued_unit_in_a_measuring_line_is_asked():
    assert reasons("Supply air temp at the register is 55F.") == [("confirm", "unclear_unit")]


def test_approximate_is_checked_per_reading_position():
    assert reasons("Suction 120 psi, head about 120 psi.") == [("accept", "ok"), ("confirm", "approximate")]


def test_i_mean_and_no_weight_are_corrections():
    assert reasons("Outlet temperature is 123, I mean, 118 degrees.") == [("confirm", "correction")]
    assert reasons("Load current is 28, no weight, 14 amps.") == [("confirm", "correction")]
