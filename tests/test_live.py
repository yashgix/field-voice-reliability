import json

import pytest

from live.arms import (
    RULE_QUESTION,
    UNIT_QUESTION,
    UNPLANNED_ANSWER,
    VALUE_QUESTION,
    parse_record,
    rule_question,
    run_live,
)
from live.entries import Entries, normalize, numbers, said
from live.guards import guarded
from live.model import ModelError, _parse
from live.scenario import REPLY, Turn, Visit, load, spoken, truth
from live.score import dropped, episodes, errors, hedged, lagging, recall

EQUIPMENT = [
    {"id": "E1", "type": "condenser", "location": "left", "make": "X", "model": "M1", "serial": "S1"},
    {"id": "E2", "type": "condenser", "location": "right", "make": "X", "model": "M2", "serial": "S2"},
]


def reading(equip, field, value):
    return {"op": "reading", "equip": equip, "field": field, "value": value, "uom": "A"}


def reassign(field, src, dst):
    return {"op": "reassign", "field": field, "from": src, "to": dst}


def revise(equip, field, value):
    return {"op": "revise", "equip": equip, "field": field, "value": value}


def work(equip, task, status):
    return {"op": "work", "equip": equip, "task": task, "status": status}


def visit(turns):
    return Visit("t", "mixed", EQUIPMENT, [Turn(str(i + 1), s, text, eff) for i, (s, text, eff) in enumerate(turns)])


def test_truth_applies_revisions_reassignments_and_work():
    v = visit([
        ("tech", "fan two point four", [reading("E1", "condenser_fan_amps", "2.4")]),
        ("tech", "that was the other one", [reassign("condenser_fan_amps", "E1", "E2")]),
        ("tech", "voltage two oh six", [reading("E1", "line_voltage", "206")]),
        ("tech", "no wait two oh eight", [{"op": "revise", "equip": "E1", "field": "line_voltage", "value": "208"}]),
        ("tech", "swapping the cap", [work("E1", "replace_capacitor", "in_progress")]),
    ])  # fmt: skip
    s = truth(v.turns)
    assert s.readings == {("E2", "condenser_fan_amps"): "2.4", ("E1", "line_voltage"): "208"}
    assert s.superseded[("E1", "line_voltage")] == {"206"}
    assert s.work == {("E1", "replace_capacitor"): "in_progress"}


def test_unsettled_owner_leaves_other_values_alone():
    amb = {"op": "ambiguous", "equip": ["E1", "E2"], "field": "compressor_amps", "value": "9", "uom": "A",
           "answer": "left one", "resolves_to": "E1"}  # fmt: skip
    s = truth(visit([("tech", "x", [reading("E2", "compressor_amps", "8")]), ("tech", "nine", [amb])]).turns)
    assert s.readings == {("E2", "compressor_amps"): "8"}
    assert len(s.unresolved) == 1


def test_load_rejects_unknown_fields(tmp_path):
    bad = {"id": "x", "kind": "ordinary", "equipment": EQUIPMENT,
           "turns": [{"id": 1, "speaker": "tech", "text": "t", "effects": [reading("E1", "amps", "1")]}]}  # fmt: skip
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad))
    with pytest.raises(ValueError):
        load(path)


def test_numbers_cover_trade_forms():
    assert {"1", "18", "118"} <= numbers("suction one eighteen")
    assert said("0.58", "point five one... point five eight")
    assert not said("57", "supply fifty five")
    assert said("11.2", "Compressors at 11 .2") and said("19", "so Delta T19.")


def test_guard_withholds_unsaid_values_and_holds_done():
    texts = {"1": "fan two point four", "2": "cap is in"}
    first = normalize({"readings": [{"equip": "E1", "field": "condenser_fan_amps", "value": "2.4", "evidence": ["1"]},
                                    {"equip": "E2", "field": "line_voltage", "value": "230", "evidence": ["1"]}],
                       "work": [{"equip": "E1", "task": "replace_capacitor", "status": "done", "evidence": ["2"]}]},
                      {"E1", "E2"})  # fmt: skip
    committed = guarded([first, first], [texts, texts])
    assert committed[0].readings == {("E1", "condenser_fan_amps"): "2.4"}
    assert committed[0].work == {}
    assert committed[1].work == {("E1", "replace_capacitor"): "done"}


def test_errors_name_their_cause():
    v = visit([
        ("tech", "a", [reading("E1", "compressor_amps", "12.1")]),
        ("tech", "b", [{"op": "revise", "equip": "E1", "field": "compressor_amps", "value": "12.4"}]),
        ("tech", "c", [reading("E2", "superheat", "11")]),
    ])  # fmt: skip
    state = truth(v.turns)
    rec = Entries(readings={("E1", "compressor_amps"): "12.1", ("E1", "superheat"): "11"},
                  work={("E1", "replace_filter"): "done"})  # fmt: skip
    causes = {e.key: e.cause for e in errors(rec, state, v.turns, None, {})}
    assert causes == {("E1", "compressor_amps"): "revision_status", ("E1", "superheat"): "reference",
                      ("E1", "replace_filter"): "unsupported"}  # fmt: skip
    assert recall(rec, state, {}) == (0, 2)


def test_work_behind_the_truth_is_lag_but_undone_work_kept_done_is_an_error():
    v = visit([("tech", "a", [work("E1", "replace_capacitor", "in_progress")]),
               ("tech", "b", [work("E1", "replace_capacitor", "done")]),
               ("tech", "c", [work("E1", "replace_filter", "done")]),
               ("tech", "d", [work("E1", "replace_filter", "declined")])])  # fmt: skip
    state = truth(v.turns)
    rec = Entries(work={("E1", "replace_capacitor"): "in_progress", ("E1", "replace_filter"): "done"})
    assert lagging(rec, state) == 1
    assert [e.key for e in errors(rec, state, v.turns, None, {})] == [("E1", "replace_filter")]


def test_episodes_count_a_lasting_error_once():
    rec = Entries(readings={("E1", "superheat"): "9"})
    state = truth(visit([("tech", "x", [reading("E1", "superheat", "11")])]).turns)
    one = errors(rec, state, [], None, {})
    assert len(episodes([one, one, [], one])) == 2


def test_live_run_answers_a_question_about_an_ambiguity():
    amb = {"op": "ambiguous", "equip": "E1", "field": "gas_pressure", "options": ["3.4", "3.6"],
           "answer": "three point six", "resolves_to": "3.6"}  # fmt: skip
    v = visit([("tech", "three point four, three point six", [amb]), ("tech", "done here", [])])
    replies = iter([
        {"readings": [], "ask": {"equip": "E1", "field": "gas_pressure", "question": "which?"}},
        {"readings": [{"equip": "E1", "field": "gas_pressure", "value": "3.6", "evidence": ["1a"]}], "ask": None},
        {"readings": [], "ask": {"equip": "E2", "field": "superheat", "question": "?"}},
        {"readings": [], "ask": None},
    ])  # fmt: skip
    run = run_live(v, {}, lambda system, prompt: (json.dumps(next(replies)), {}), arm="A-live")
    assert [t.id for t in run.turns] == ["1", "1q", "1a", "2", "2q", "2a"]
    assert truth(run.turns).readings == {("E1", "gas_pressure"): "3.6"}
    assert run.turns[-1].text == UNPLANNED_ANSWER


def test_parse_record_takes_json_inside_text():
    assert parse_record('here:\n```json\n{"readings": []}\n```') == {"readings": []}
    assert parse_record("no json") is None


def test_plain_text_question_is_answered_when_one_ambiguity_is_open():
    amb = {"op": "ambiguous", "equip": "E1", "field": "gas_pressure", "options": ["3.4", "3.6"],
           "answer": "three point six", "resolves_to": "3.6"}  # fmt: skip
    v = visit([("tech", "three point four, three point six", [amb])])
    replies = iter([{"ask": "was that 3.4 or 3.6?"}, {"ask": None}])
    run = run_live(v, {}, lambda system, prompt: (json.dumps(next(replies)), {}), arm="A-live")
    assert truth(run.turns).readings == {("E1", "gas_pressure"): "3.6"}


def test_dropped_counts_true_entries_that_vanish():
    state = truth(visit([("tech", "x", [reading("E1", "superheat", "11")])]).turns)
    held, empty = Entries(readings={("E1", "superheat"): "11"}), Entries()
    assert dropped(held, empty, state) == 1 and dropped(held, held, state) == 0


def test_work_error_after_changed_recognition_is_flagged():
    v = visit([("tech", "i'd clean it", [work("E1", "clean_coil", "proposed")])])
    rec = Entries(work={("E1", "clean_coil"): "in_progress"})
    [e] = errors(rec, truth(v.turns), v.turns, {"1": "I clean it."}, {})
    assert e.cause == "asr_changed"


def stream(api_key_source="none", tools=()):
    init = {"type": "system", "subtype": "init", "apiKeySource": api_key_source, "model": "m", "tools": list(tools)}
    usage = {"input_tokens": 1, "cache_read_input_tokens": 0, "cache_creation_input_tokens": 0, "output_tokens": 1}
    result = {"type": "result", "is_error": False, "result": "{}", "duration_ms": 10, "usage": usage}
    return "\n".join(json.dumps(e) for e in (init, result))


def test_model_refuses_api_key_or_tools():
    assert _parse(stream())["text"] == "{}"
    for bad in (stream(api_key_source="ANTHROPIC_API_KEY"), stream(tools=["Bash"])):
        with pytest.raises(ModelError):
            _parse(bad)


def test_reading_lost_by_recognition_is_blamed_on_asr():
    v = visit([("tech", "superheat eleven", [reading("E1", "superheat", "11")])])
    [e] = errors(Entries(readings={("E1", "superheat"): "17"}), truth(v.turns), v.turns, {"1": "superheat 17"}, {})
    assert e.cause == "asr_lost"


def test_guessing_a_candidate_of_an_open_ambiguity_is_missing_clarification():
    amb = {"op": "ambiguous", "equip": "E1", "field": "gas_pressure", "options": ["3.4", "3.6"],
           "answer": "3.6", "resolves_to": "3.6"}  # fmt: skip
    v = visit([("tech", "three point four, three point six", [amb])])
    [e] = errors(Entries(readings={("E1", "gas_pressure"): "3.6"}), truth(v.turns), v.turns, None, {})
    assert e.cause == "missing_clarification"


def test_misread_serial_kept_after_correction_is_a_final_error():
    def serial(value):
        return [{"op": "equipment", "equip": "E1", "field": "serial", "value": value}]

    v = visit([("tech", "serial s nine", serial("S9")), ("tech", "no, s one", serial("S1"))])
    rec = Entries(equipment={("E1", "serial"): "S9"})
    [e] = errors(rec, truth(v.turns), v.turns, None, {("E1", "serial"): "S1"}, final=True)
    assert e.cause == "revision_status"


def test_hedging_a_settled_value_is_counted():
    state = truth(visit([("tech", "superheat eleven", [reading("E1", "superheat", "11")])]).turns)
    assert hedged(Entries(unresolved={(("E1", "E2"), "superheat")}), state) == 1


def test_an_unrelated_question_gets_the_neutral_reply():
    amb = {"op": "ambiguous", "equip": "E1", "field": "gas_pressure", "options": ["3.4", "3.6"],
           "answer": "three point six", "resolves_to": "3.6"}  # fmt: skip
    v = visit([("tech", "three point four, three point six", [amb])])
    replies = iter([{"ask": {"question": "did you change the filter?"}}, {"ask": None}])
    run = run_live(v, {}, lambda system, prompt: (json.dumps(next(replies)), {}), arm="A-live")
    assert run.turns[-1].text == UNPLANNED_ANSWER


def test_a_question_about_a_recent_reading_gets_the_line_repeated():
    v = visit([("tech", "superheat eleven", [reading("E1", "superheat", "11")]), ("tech", "moving on", [])])
    replies = iter([{"ask": None}, {"ask": {"equip": "E1", "field": "superheat", "question": "superheat?"}}, {}])
    run = run_live(v, {}, lambda system, prompt: (json.dumps(next(replies)), {}), arm="A-live")
    assert run.turns[-1].text == "superheat eleven"


def test_rule_asks_only_for_unsure_numbers_or_missing_values():
    assert rule_question("suction ~one twenty eight") == RULE_QUESTION
    assert rule_question("superheat ~Date, subcool") == RULE_QUESTION
    assert rule_question("suction one twenty eight") is None
    assert rule_question("okay moving to the back unit") is None


def test_a_generic_repeat_request_gets_the_last_reading_line_again():
    v = visit([("tech", "superheat ~date", [reading("E1", "superheat", "8")])])
    replies = iter([{"ask": None}, {"ask": None}])
    run = run_live(v, {"1": "superheat ~date"}, lambda system, prompt: (json.dumps(next(replies)), {}), arm="R")
    assert [t.text for t in run.turns] == ["superheat ~date", RULE_QUESTION, "superheat ~date"]


def test_unhelpful_replies_answer_nothing():
    amb = {"op": "ambiguous", "equip": "E1", "field": "gas_pressure", "options": ["3.4", "3.6"],
           "answer": "three point six", "resolves_to": "3.6"}  # fmt: skip
    v = visit([("tech", "three point four, three point six", [amb])])
    replies = iter([{"ask": {"equip": "E1", "field": "gas_pressure", "question": "which?"}}, {"ask": None}])
    run = run_live(v, {}, lambda s, p: (json.dumps(next(replies)), {}), arm="A-live", policy="none")
    assert run.turns[-1].text == UNPLANNED_ANSWER


def test_rendered_replies_are_what_the_arm_hears():
    assert (
        spoken(Turn("3a", "tech", "superheat eight"), {REPLY + "superheat eight": "super heat ~ate"})
        == "super heat ~ate"
    )


def test_rule_asks_which_value_when_one_measurement_gets_two_numbers():
    assert rule_question("manifold's three point four, three point six") == VALUE_QUESTION
    assert rule_question("suction one twenty eight, head three forty two") is None


def test_rule_asks_which_unit_after_an_unnamed_switch_or_the_other_one():
    assert rule_question("suction ninety eight", previous="okay next one") == UNIT_QUESTION
    assert rule_question("voltage same as the other one, two oh eight") == UNIT_QUESTION
    assert rule_question("suction ninety eight", previous="okay over to the back condenser") is None
    assert rule_question("filters on this one are fine") is None
    assert rule_question("yeah go ahead") is None


def test_which_unit_question_gets_the_scripted_answer():
    amb = {"op": "ambiguous", "equip": ["E1", "E2"], "field": "compressor_amps", "value": "9", "uom": "A",
           "answer": "the left one", "resolves_to": "E1"}  # fmt: skip
    v = visit([("tech", "compressor nine", [amb])])
    replies = iter([{"ask": "which unit is that for?"}, {"ask": None}])
    run = run_live(v, {}, lambda s, p: (json.dumps(next(replies)), {}), arm="A-live")
    assert truth(run.turns).readings == {("E1", "compressor_amps"): "9"}


def test_retracting_an_ambiguous_reading_closes_the_ambiguity():
    amb = {"op": "ambiguous", "equip": "E1", "field": "static_pressure", "options": ["0.58", "0.68"],
           "answer": "0.58", "resolves_to": "0.58"}  # fmt: skip
    retract = {"op": "retract", "equip": "E1", "field": "static_pressure"}
    state = truth(
        visit([("tech", "point five eight or point six eight", [amb]), ("tech", "ignore that", [retract])]).turns
    )
    assert not state.unresolved and not state.readings


def test_errors_on_disputed_labels_are_set_aside():
    from live.report import _set_aside
    from live.score import Error

    kept, disputed = (
        Error(("E1", "superheat"), "reading", "9", "11", "unsupported"),
        Error(("E2", "clean_coil"), "work", "declined", "deferred", "revision_status"),
    )
    row = _set_aside({"live": [kept, disputed], "final": [disputed]}, {("E2", "clean_coil")})
    assert row["live"] == [kept] and row["final"] == [] and len(row["disputed"]) == 2


def test_a_missing_visit_or_arm_makes_the_batch_incomplete():
    from live.report import missing

    scored = {("asr", "A", "c01", 1): {}, ("asr", "B", "c01", 1): {}}
    assert missing(scored, "asr", ["c01", "c02"], ["A", "B"]) == ["c02/A", "c02/B"]


def test_a_missing_scripted_answer_is_built_from_the_equipment_list():
    from live.scenario import answer_text

    v = visit([])
    effect = {"op": "ambiguous", "equip": ["E1", "E2"], "field": "superheat", "value": "9", "resolves_to": "E2"}
    assert answer_text(v, effect) == "that was the condenser at the right"
    assert answer_text(v, {"equip": "E1", "options": ["1", "2"], "resolves_to": "2"}) == "it was 2"


def test_v2_tech_restates_a_recent_reading_asked_about_by_its_number_or_a_wrong_field():
    from live import tech

    v = visit([("tech", "fan point nine", [reading("E1", "condenser_fan_amps", "0.9")])])
    asked = lambda ask: tech.reply(v, v.turns, ask)  # noqa: E731
    assert asked({"question": "which reading is the 0.9 value?"}) == tech.restatement("condenser_fan_amps", "0.9")
    assert asked({"field": "condenser_fan_amps", "equip": "E1", "question": "fan amps?"}).endswith("point nine")
    assert asked({"question": "did you check the filter?"}) == tech.NOTHING


def test_v2_tech_gives_the_corrected_value_and_cannot_recall_old_readings():
    from live import tech

    v = visit([
        ("tech", "suction one thirty two", [reading("E1", "suction_pressure", "132")]),
        ("tech", "no wait one twenty three", [revise("E1", "suction_pressure", "123")]),
        *[("tech", "moving on", [])] * 4,
    ])  # fmt: skip
    assert tech.reply(v, v.turns[:2], {"question": "was suction 132?"}).endswith("twenty three")
    assert tech.reply(v, v.turns, {"field": "suction_pressure", "question": "suction?"}) == tech.CANNOT


def test_v2_tech_reads_the_plate_of_the_unit_asked_about():
    from live import tech

    v = visit([("tech", "model is m two", [])])
    assert tech.reply(v, v.turns, {"equip": "E2", "field": "model", "question": "model?"}).startswith(
        "the plate says model"
    )
    assert tech.reply(v, v.turns, {"question": "what's the serial?"}) == tech.NOTHING


def test_a_take_is_cut_at_its_pauses_or_lined_up_by_words():
    import numpy as np

    from live.voice import align, cut

    rate, tone = 16000, lambda s: 0.3 * np.sin(np.linspace(0, 2000 * s, int(16000 * s)))
    take = np.concatenate([tone(1.0), np.zeros(rate), tone(0.8), np.zeros(rate), tone(1.2)]).astype("float32")
    assert len(cut(take, rate, 3)) == 3
    words = [(" head", 0.0, 0.4), (" three", 0.4, 0.8), (" fan", 2.0, 2.3), (" draw", 2.3, 2.6)]
    assert align(["head three twelve", "fan draw two"], words, rate) == [
        (0, int(0.8 * rate)),
        (int(2.0 * rate), int(2.6 * rate)),
    ]
