import uuid

import pytest
from conftest import wav

from fvr.readings import Settings
from mvp.engine import ActionError
from mvp.record import build_record
from mvp.visit import Slot, judge_reading, next_check


def talk(engine, asr, vid, slot, text):
    return engine.audio(vid, uuid.uuid4().hex, slot, asr.clip(text))


def slot(engine, vid, key):
    return engine.visit(vid).slots[key]


def kinds(engine, vid):
    return [e.kind for e in engine.log.events(vid)]


def check_all(engine, vid):
    """Confirm every remaining read-back value, one at a time, as the technician would."""
    while (v := engine.visit(vid)).stage == "readback":
        engine.tap(vid, "confirm", next_check(v)["slot"])
    return engine.visit(vid)


def confirm_until(engine, vid, key):
    while next_check(engine.visit(vid))["slot"] != key:
        engine.tap(vid, "confirm", next_check(engine.visit(vid))["slot"])


def assert_every_value_was_said_or_typed(engine, vid):
    """No value in the record that the technician did not say, confirm or type."""
    record = build_record(engine.log, engine.clips, vid)
    assert record["audit"]["untraceable_values"] == [], record["readings"]


def test_clean_reading_is_accepted(engine, asr, hvac):
    vid = engine.start(hvac)
    p = talk(engine, asr, vid, "suction", "Suction pressure is 118 psi.")
    s = slot(engine, vid, "suction")
    assert (s.status, s.value, s.unit, s.by) == ("accepted", "118", "psi", "checker")
    assert p == {"expect": "reading", "slot": "head", "say": "Head pressure."}
    assert asr.calls[0][1].startswith("Service call: HVAC, no cooling. Carrier condenser 24ACC636A003")


def test_glued_amps_needs_a_yes(engine, asr, hvac):
    vid = engine.start(hvac)
    p = talk(engine, asr, vid, "compressor_amps", "Compressor is pulling 18A.")
    assert p["expect"] == "yesno" and "18 amps" in p["say"]
    assert slot(engine, vid, "compressor_amps").value is None
    talk(engine, asr, vid, "compressor_amps", "Yes.")
    s = slot(engine, vid, "compressor_amps")
    assert (s.status, s.value, s.by) == ("confirmed", "18", "technician_voice")
    assert asr.calls[-1][1] is None  # yes or no answers are decoded without the job prompt


def test_no_then_a_new_value_is_a_correction(engine, asr, hvac):
    vid = engine.start(hvac)
    talk(engine, asr, vid, "compressor_amps", "Compressor is pulling 18A.")
    engine.tap(vid, "no")
    p = engine.visit(vid).slots["compressor_amps"].pending
    assert p.kind == "value" and p.failed == 0  # a clear no is not a failed answer
    talk(engine, asr, vid, "compressor_amps", "Twenty one amps.")
    s = slot(engine, vid, "compressor_amps")
    assert (s.status, s.value) == ("corrected", "21")


def test_ambiguous_answers_end_unconfirmed_with_audio_kept(engine, asr, hvac):
    vid = engine.start(hvac)
    talk(engine, asr, vid, "compressor_amps", "Compressor is pulling 18A.")
    talk(engine, asr, vid, "compressor_amps", "Yeah, no.")
    assert slot(engine, vid, "compressor_amps").pending.text.startswith("Please answer yes or no")
    talk(engine, asr, vid, "compressor_amps", "Hmm, maybe.")
    s = slot(engine, vid, "compressor_amps")
    assert (s.status, s.value) == ("unconfirmed", None)
    last = engine.log.events(vid)[-1]
    assert last.kind == "unconfirmed" and len(last.data["clips"]) == 3
    assert all(engine.clips.intact(c) for c in last.data["clips"])


def test_failed_recognition_retries_then_unconfirmed(engine, asr, hvac):
    vid = engine.start(hvac)
    p = engine.audio(vid, uuid.uuid4().hex, "suction", wav(amplitude=0.0))
    assert p["expect"] == "value" and p["say"].startswith("I didn't catch that")
    assert asr.calls == []  # silence never reaches the recogniser
    talk(engine, asr, vid, "suction", "")
    talk(engine, asr, vid, "suction", "Uh.")
    assert slot(engine, vid, "suction").status == "unconfirmed"
    problems = [e.data["problem"] for e in engine.log.events(vid) if e.kind == "utterance"]
    assert problems == ["silent", None, None]


def test_wrong_unit_and_two_values_are_asked(engine, asr, hvac):
    vid = engine.start(hvac)
    p = talk(engine, asr, vid, "suction", "Suction is 118 volts.")
    assert p["expect"] == "value" and "is in psi" in p["say"]
    vid = engine.start(hvac)
    p = talk(engine, asr, vid, "suction", "Suction is 118 psi, head 342 psi.")
    assert p["say"].startswith("I heard 118 psi and 342 psi. Say only the suction pressure")


def test_bare_number_is_proposed_with_the_slot_unit_never_stored_without_yes(engine, asr, hvac):
    vid = engine.start(hvac)
    p = talk(engine, asr, vid, "superheat", "Superheat is 9.")
    assert p == {"expect": "yesno", "slot": "superheat", "say": "I heard 9. Is that 9 degrees?"}
    assert slot(engine, vid, "superheat").value is None
    engine.tap(vid, "yes")
    s = slot(engine, vid, "superheat")
    assert (s.status, s.value, s.unit, s.by) == ("confirmed", "9", "degrees", "technician_tap")


def test_unitless_correction_asks_for_the_final_value(engine, asr, hvac):
    vid = engine.start(hvac)
    p = talk(engine, asr, vid, "suction", "Suction is 120, no wait, 124.")
    assert p["expect"] == "value" and p["say"].startswith("You corrected yourself. I heard 124.")
    talk(engine, asr, vid, "suction", "124 psi.")
    assert slot(engine, vid, "suction").value == "124"


def test_wrong_value_with_no_trace_is_accepted_and_only_read_back_can_catch_it(engine, asr, electrical):
    # Said "fifty one ... fifty eight", recognised as one clean wrong value: the text gives no reason to ask.
    vid = engine.start(electrical)
    talk(engine, asr, vid, "line_voltage", "Line voltage is 240 volts.")
    talk(engine, asr, vid, "l1_amps", "L1 is 60 amps.")
    talk(engine, asr, vid, "l2_amps", "L2 is 52 amps.")
    p = talk(engine, asr, vid, "ground", "Ground rod is 25 ohms.")
    assert slot(engine, vid, "l2_amps").status == "accepted"
    assert p["expect"] == "readback" and p["item"]["slot"] == "line_voltage" and (p["position"], p["total"]) == (1, 4)
    engine.tap(vid, "confirm", "line_voltage")
    p = engine.tap(vid, "confirm", "l1_amps")
    assert p["say"] == "L2 current: 52 amps." and p["clips"] == slot(engine, vid, "l2_amps").clips
    engine.tap(vid, "fix", "l2_amps")
    p = talk(engine, asr, vid, "l2_amps", "L2 is 58 amps.")
    s = slot(engine, vid, "l2_amps")
    assert (s.status, s.value, s.by) == ("corrected", "58", "technician_voice")
    assert p["item"] == {
        "slot": "l2_amps",
        "label": "L2 current",
        "value": "58",
        "unit": "amps",
        "status": "corrected",
        "by": "technician_voice",
    }
    assert check_all(engine, vid).stage == "closed"
    record = build_record(engine.log, engine.clips, vid)
    decisions = [(d["slot"], d["shown"], d["decision"]) for d in record["readback"]["decisions"]]
    assert decisions == [
        ("line_voltage", "240", "confirmed"),
        ("l1_amps", "60", "confirmed"),
        ("l2_amps", "52", "corrected"),
        ("l2_amps", "58", "confirmed"),
        ("ground", "25", "confirmed"),
    ]
    assert [r["origin"] for r in record["readings"]] == ["automatic", "automatic", "clarified", "automatic"]
    assert [r["corrected_at_readback"] for r in record["readings"]] == [False, False, True, False]
    assert all(r["checked_at_readback"] for r in record["readings"])
    assert_every_value_was_said_or_typed(engine, vid)


def test_typed_value_needs_a_number_and_a_listed_unit(engine, asr, hvac):
    vid = engine.start(hvac)
    talk(engine, asr, vid, "compressor_amps", "Compressor is pulling 18A.")
    with pytest.raises(ActionError):
        engine.tap(vid, "typed", "compressor_amps", "about 18", "amps")
    with pytest.raises(ActionError):
        engine.tap(vid, "typed", "compressor_amps", "18", "volts")
    engine.tap(vid, "typed", "compressor_amps", "18", "amps")
    s = slot(engine, vid, "compressor_amps")
    assert (s.status, s.value, s.by) == ("confirmed", "18", "technician_typed")


def test_missing_readings_are_asked_once_then_skipped(engine, asr, hvac):
    vid = engine.start(hvac)
    talk(engine, asr, vid, "suction", "Suction pressure is 118 psi.")
    p = engine.tap(vid, "finish")
    assert p["expect"] == "missing" and p["missing"] == ["head", "superheat", "compressor_amps", "capacitor"]
    talk(engine, asr, vid, "capacitor", "Cap reads 45 over 5 microfarads.")
    p = engine.tap(vid, "skip_missing")
    assert p["expect"] == "readback"
    statuses = {i["slot"]: i["status"] for i in engine.visit(vid).readback["items"]}
    assert statuses == {"suction": "accepted", "head": "skipped", "superheat": "skipped",
                        "compressor_amps": "skipped", "capacitor": "accepted"}  # fmt: skip
    engine.tap(vid, "confirm", "suction")
    assert engine.visit(vid).stage == "readback" and next_check(engine.visit(vid))["slot"] == "head"


PLAN = {"schedule": [{"slot": "l2_amps", "shown": "53", "type": "last_digit"}]}


def test_scheduled_error_is_shown_only_on_a_different_stored_value(engine, asr, electrical):
    plan = {"schedule": [{"slot": "l1_amps", "shown": "60"}, {"slot": "ground", "shown": "5"}]}
    vid = engine.start(electrical, plan)
    talk(engine, asr, vid, "line_voltage", "Line voltage is 240 volts.")
    talk(engine, asr, vid, "l1_amps", "L1 is 60 amps.")  # already the scheduled value: nothing to plant
    talk(engine, asr, vid, "l2_amps", "L2 is 58 amps.")
    engine.tap(vid, "skip", "ground")  # no value: nothing to plant
    assert engine.visit(vid).readback["seeded"] == []


def test_seeded_read_back_error_is_logged_and_never_stored(engine, asr, electrical):
    vid = engine.start(electrical, PLAN)
    for key, text in [("line_voltage", "Line voltage is 240 volts."), ("l1_amps", "L1 is 60 amps."),
                      ("l2_amps", "L2 is 58 amps."), ("ground", "Ground rod is 25 ohms.")]:  # fmt: skip
        talk(engine, asr, vid, key, text)
    seeded = engine.visit(vid).readback["seeded"]
    assert len(seeded) == 1 and seeded[0]["shown"] != seeded[0]["actual"]
    shown = next(i for i in engine.visit(vid).readback["items"] if i["slot"] == seeded[0]["slot"])
    assert shown["value"] == seeded[0]["shown"]
    check_all(engine, vid)  # the technician missed it
    record = build_record(engine.log, engine.clips, vid)
    assert record["readback"]["seeded"] == [dict(seeded[0], caught=False)]
    stored = next(r for r in record["readings"] if r["key"] == seeded[0]["slot"])
    assert stored["value"] == seeded[0]["actual"]


def test_seeded_error_fixed_at_read_back_counts_as_caught(engine, asr, electrical):
    vid = engine.start(electrical, PLAN)
    for key, text in [("line_voltage", "Line voltage is 240 volts."), ("l1_amps", "L1 is 60 amps."),
                      ("l2_amps", "L2 is 58 amps."), ("ground", "Ground rod is 25 ohms.")]:  # fmt: skip
        talk(engine, asr, vid, key, text)
    seed = engine.visit(vid).readback["seeded"][0]
    confirm_until(engine, vid, seed["slot"])
    engine.tap(vid, "fix", seed["slot"])
    actual_text = {"line_voltage": "240 volts.", "l1_amps": "60 amps.", "l2_amps": "58 amps.", "ground": "25 ohms."}
    talk(engine, asr, vid, seed["slot"], actual_text[seed["slot"]])
    assert slot(engine, vid, seed["slot"]).status == "confirmed"  # same value as before the fix
    assert engine.visit(vid).readback["seeded"] == []  # only the first read-back is seeded
    check_all(engine, vid)
    assert build_record(engine.log, engine.clips, vid)["readback"]["seeded"][0]["caught"] is True


def test_retried_upload_is_handled_once(engine, asr, hvac):
    vid = engine.start(hvac)
    audio, utt = asr.clip("Suction pressure is 118 psi."), uuid.uuid4().hex
    engine.audio(vid, utt, "suction", audio)
    engine.audio(vid, utt, "suction", audio)
    assert kinds(engine, vid).count("utterance") == 1 and len(asr.calls) == 1


def test_interruption_is_logged_without_changing_the_visit(engine, asr, hvac):
    vid = engine.start(hvac)
    engine.tap(vid, "interrupted", "suction", "touch cancelled")
    assert kinds(engine, vid) == ["visit_started", "capture_interrupted"]
    assert engine.visit(vid).slots["suction"].status == "open"


def test_actions_out_of_turn_are_refused(engine, asr, hvac):
    vid = engine.start(hvac)
    with pytest.raises(ActionError):
        engine.tap(vid, "yes")
    with pytest.raises(ActionError):
        engine.tap(vid, "confirm")
    talk(engine, asr, vid, "suction", "Suction pressure is 118 psi.")
    with pytest.raises(ActionError):
        talk(engine, asr, vid, "suction", "Suction pressure is 120 psi.")  # already recorded; use read-back fix


def test_glued_amps_answer_to_a_reading_request_is_confirmed(engine, asr, electrical):
    vid = engine.start(electrical)
    talk(engine, asr, vid, "line_voltage", "Line voltage is 240 volts.")
    p = talk(engine, asr, vid, "l1_amps", "58A.")
    assert p == {"expect": "yesno", "slot": "l1_amps", "say": "I heard 58 A. Is that 58 amps?"}


def test_record_flags_a_value_no_recording_contains(engine, asr, hvac):
    vid = engine.start(hvac)
    talk(engine, asr, vid, "suction", "Suction pressure is 118 psi.")
    engine.log.append(vid, "value_set", {"slot": "head", "value": "342", "unit": "psi", "status": "accepted",
                                         "by": "checker"})  # fmt: skip
    assert build_record(engine.log, engine.clips, vid)["audit"]["untraceable_values"] == ["head"]


def test_a_spoken_no_never_stores_the_rejected_value(engine, asr, hvac):
    for answer in ("No, not 9 degrees.", "No. 9 is wrong.", "I heard 9. Is that 9 degrees? No."):
        vid = engine.start(hvac)
        talk(engine, asr, vid, "superheat", "Superheat is 9.")
        p = talk(engine, asr, vid, "superheat", answer)
        assert slot(engine, vid, "superheat").value is None, answer
        assert p["expect"] == "value" and p["say"].startswith("OK. What is the superheat"), answer


def test_yes_with_the_same_number_confirms_and_no_with_a_new_value_corrects(engine, asr, hvac):
    vid = engine.start(hvac)
    talk(engine, asr, vid, "superheat", "Superheat is 9.")
    talk(engine, asr, vid, "superheat", "Yes, nine.")
    assert slot(engine, vid, "superheat").status == "confirmed"
    vid = engine.start(hvac)
    talk(engine, asr, vid, "compressor_amps", "Compressor is pulling 18A.")
    talk(engine, asr, vid, "compressor_amps", "No, 21 amps.")
    s = slot(engine, vid, "compressor_amps")
    assert (s.status, s.value) == ("corrected", "21")
    vid = engine.start(hvac)
    talk(engine, asr, vid, "compressor_amps", "Compressor is pulling 18A.")
    p = talk(engine, asr, vid, "compressor_amps", "Yes, 21 amps.")  # contradicts itself
    assert p["say"].startswith("Please answer yes or no") and slot(engine, vid, "compressor_amps").value is None


def test_audio_for_another_slot_cannot_answer_an_open_question(engine, asr, hvac):
    vid = engine.start(hvac)
    talk(engine, asr, vid, "superheat", "Superheat is 9.")
    with pytest.raises(ActionError, match="open question about Superheat"):
        talk(engine, asr, vid, "head", "Head pressure is 250 psi.")
    assert slot(engine, vid, "superheat").value is None and slot(engine, vid, "head").value is None


def test_typed_values_are_stored_in_the_parsers_exact_form(engine, asr, hvac):
    vid = engine.start(hvac)
    engine.tap(vid, "typed", "superheat", "11.0", "degrees")
    engine.tap(vid, "typed", "capacitor", "45.0/5", "microfarads")
    assert (slot(engine, vid, "superheat").value, slot(engine, vid, "capacitor").value) == ("11", "45/5")


def test_a_closed_visit_takes_no_more_actions(engine, asr, electrical):
    vid = engine.start(electrical)
    for key in ("line_voltage", "l1_amps", "l2_amps", "ground"):
        engine.tap(vid, "skip", key)
    assert next_check(engine.visit(vid))["value"] is None  # empty values are checked too ("Leave empty")
    check_all(engine, vid)
    for action in ("interrupted", "finish", "skip", "confirm", "fix"):
        with pytest.raises(ActionError):
            engine.tap(vid, action, "ground")


def test_planted_value_survives_fixing_another_reading(engine, asr, electrical):
    vid = engine.start(electrical, PLAN)
    said = {"line_voltage": "240 volts.", "l1_amps": "60 amps.", "l2_amps": "58 amps.", "ground": "25 ohms."}
    for key, text in said.items():
        talk(engine, asr, vid, key, text)
    seed = engine.visit(vid).readback["seeded"][0]
    other = next(k for k in said if k != seed["slot"])
    confirm_until(engine, vid, other)
    engine.tap(vid, "fix", other)
    talk(engine, asr, vid, other, said[other])
    shown = next(i for i in engine.visit(vid).readback["items"] if i["slot"] == seed["slot"])
    assert shown["value"] == seed["shown"]  # still planted on the second read-back
    check_all(engine, vid)
    record = build_record(engine.log, engine.clips, vid)
    assert record["readback"]["seeded"] == [dict(seed, caught=False)]
    assert next(r for r in record["readings"] if r["key"] == seed["slot"])["value"] == seed["actual"]


def test_a_dual_reading_is_never_proposed_as_one_number(engine, asr, hvac):
    # Held-out visit 1: "35 over 5MFT" was asked as "Is that 35 microfarads?"; a yes would have stored 35.
    vid = engine.start(hvac)
    p = talk(engine, asr, vid, "capacitor", "Run cap is 35 over 5MFT.")
    assert p["expect"] == "value" and "35 over 5" in p["say"]
    assert slot(engine, vid, "capacitor").pending.proposed is None
    with pytest.raises(ActionError):
        engine.tap(vid, "yes")
    talk(engine, asr, vid, "capacitor", "35 over 5 MFD.")
    assert (slot(engine, vid, "capacitor").value, slot(engine, vid, "capacitor").unit) == ("35/5", "microfarads")


def test_a_bare_number_is_proposed_only_when_it_is_the_only_number(hvac):
    cap = Slot("capacitor", "Run capacitor", ["microfarads"])
    for text in ("Run cap is 35 over 5MFT.", "Cap is 45, 5.", "Cap 45 and 5mf."):
        outcome = judge_reading(text, [], cap, Settings())
        assert outcome.kind == "value" and outcome.proposed is None, text
    assert judge_reading("Cap is 45.", [], cap, Settings()).proposed.value == "45"


def test_a_clear_answer_that_needs_a_yes_is_not_a_failed_answer(engine, asr, electrical):
    # Held-out visit 3: after one unusable answer, a clear "L2 is 39A." ended the reading as unconfirmed.
    vid = engine.start(electrical)
    talk(engine, asr, vid, "line_voltage", "Line voltage is 240 volts.")
    talk(engine, asr, vid, "l1_amps", "L1 is 42 amps.")
    talk(engine, asr, vid, "l2_amps", "Wi salf salf.")
    talk(engine, asr, vid, "l2_amps", "Alex Tu is 37, 39 arms.")
    assert slot(engine, vid, "l2_amps").pending.failed == 1
    p = talk(engine, asr, vid, "l2_amps", "L2 is 39A.")
    assert p == {"expect": "yesno", "slot": "l2_amps", "say": "I heard 39 A. Is that 39 amps?"}
    engine.tap(vid, "yes")
    s = slot(engine, vid, "l2_amps")
    assert (s.status, s.value) == ("confirmed", "39")


def test_spaced_megohms_are_accepted_in_a_megohm_slot():
    insulation = Slot("insulation", "Insulation resistance", ["megohms"])
    outcome = judge_reading("Insulation came back as 200M Ohms.", [("200M", 0.9)], insulation, Settings())
    assert outcome.reading.value == "200" and outcome.reading.unit == "megohms"


def test_read_back_takes_one_value_at_a_time_and_never_in_bulk(engine, asr, electrical):
    vid = engine.start(electrical)
    for key, text in [("line_voltage", "Line voltage is 240 volts."), ("l1_amps", "L1 is 60 amps."),
                      ("l2_amps", "L2 is 58 amps."), ("ground", "Ground rod is 25 ohms.")]:  # fmt: skip
        talk(engine, asr, vid, key, text)
    for action, key in (("confirm", ""), ("confirm", "l1_amps"), ("fix", "ground"), ("played", "ground")):
        with pytest.raises(ActionError, match="check Line voltage first"):
            engine.tap(vid, action, key)
    engine.tap(vid, "confirm", "line_voltage")
    with pytest.raises(ActionError):
        engine.tap(vid, "confirm", "line_voltage")  # a repeated tap does not confirm the next value
    engine.tap(vid, "played", "l1_amps")
    for key in ("l1_amps", "l2_amps"):
        engine.tap(vid, "confirm", key)
    assert engine.visit(vid).stage == "readback"  # not saved until the last value is checked
    assert engine.tap(vid, "confirm", "ground")["expect"] == "done"
    decisions = build_record(engine.log, engine.clips, vid)["readback"]["decisions"]
    assert [d["listened"] for d in decisions] == [False, True, False, False]
    assert all(d["seconds"] >= 0 for d in decisions)


def test_record_keeps_how_each_value_was_obtained(engine, asr, hvac):
    vid = engine.start(hvac)
    talk(engine, asr, vid, "suction", "Suction pressure is 118 psi.")
    talk(engine, asr, vid, "head", "Head pressure is 250.")
    engine.tap(vid, "yes")
    engine.tap(vid, "typed", "superheat", "11", "degrees")
    engine.tap(vid, "skip", "compressor_amps")
    talk(engine, asr, vid, "capacitor", "Uh.")
    engine.tap(vid, "skip", "capacitor")
    check_all(engine, vid)
    record = build_record(engine.log, engine.clips, vid)
    got = {r["key"]: (r["status"], r["origin"]) for r in record["readings"]}
    assert got == {"suction": ("accepted", "automatic"), "head": ("confirmed", "clarified"),
                   "superheat": ("confirmed", "typed"), "compressor_amps": ("skipped", None),
                   "capacitor": ("unconfirmed", None)}  # fmt: skip


def test_a_unit_fragment_that_did_not_parse_is_never_dropped_from_a_proposal(hvac):
    # A lowercase m could mean milli: "Is that 5 ohms?" would store a value off by a factor of 1000.
    ground = Slot("ground", "Ground resistance", ["ohms"])
    insulation = Slot("insulation", "Insulation resistance", ["megohms"])
    for slot_, text in [(ground, "Ground is 5 m ohms."), (insulation, "Insulation is 200 mOhms."),
                        (insulation, "Insulation is 200 m ohms."), (ground, "Ground is 5 k.")]:  # fmt: skip
        outcome = judge_reading(text, [], slot_, Settings())
        assert outcome.kind == "value" and outcome.proposed is None, text


def test_repeating_the_proposed_number_counts_toward_the_retry_limit(engine, asr, electrical):
    vid = engine.start(electrical)
    talk(engine, asr, vid, "line_voltage", "Line voltage is 240 volts.")
    talk(engine, asr, vid, "l1_amps", "L1 is 39A.")
    talk(engine, asr, vid, "l1_amps", "39.")  # asked the same question again: no progress
    assert slot(engine, vid, "l1_amps").pending.failed == 1
    talk(engine, asr, vid, "l1_amps", "39.")
    s = slot(engine, vid, "l1_amps")
    assert (s.status, s.value) == ("unconfirmed", None)


def test_records_written_before_the_per_value_read_back_still_build(engine, asr, electrical):
    vid = engine.start(electrical)
    for key in ("line_voltage", "l1_amps", "l2_amps", "ground"):
        engine.tap(vid, "skip", key)
    engine.log.append(
        vid, "reopened", {"slot": "ground", "from": "readback", "previous": {"value": None, "unit": None}}
    )
    record = build_record(engine.log, engine.clips, vid)
    assert record["readback"]["decisions"][0]["shown"] is None


def test_switching_numbers_at_a_yes_or_no_question_still_ends(engine, asr, electrical):
    vid = engine.start(electrical)
    talk(engine, asr, vid, "line_voltage", "Line voltage is 240 volts.")
    talk(engine, asr, vid, "l1_amps", "L1 is 39A.")
    talk(engine, asr, vid, "l1_amps", "38.")
    talk(engine, asr, vid, "l1_amps", "39.")
    s = slot(engine, vid, "l1_amps")
    assert (s.status, s.value) == ("unconfirmed", None)
