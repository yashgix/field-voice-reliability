from fvr.fields import Reading, extract_ids, extract_readings
from fvr.normalize import canonical_text, words_to_number


def test_words_to_number():
    assert words_to_number("forty five over".split()) == ("45", 2)
    assert words_to_number("one hundred eighteen psi".split()) == ("118", 3)
    assert words_to_number("seven point two amps".split()) == ("7.2", 3)
    assert words_to_number("two four".split()) == ("2", 1)
    assert words_to_number("psi".split()) is None


def test_spoken_id_shapes_merge_to_one_token():
    assert canonical_text("Carrier 2-4 ACC 636.") == "carrier 24acc636"
    assert canonical_text("Carrier 24ACC636,") == "carrier 24acc636"
    assert canonical_text("a Lennox ML14XC1-036 unit") == "a lennox ml14xc1036 unit"


def test_units_and_articles_do_not_merge():
    assert canonical_text("Suction pressure 118 PSI. The") == "suction pressure 118 psi the"
    assert canonical_text("is a Carrier") == "is a carrier"


def test_extract_ids_skips_refrigerant():
    assert extract_ids("Carrier 24ACC636 charged with R-410A") == ["24acc636"]


def test_extract_readings():
    text = "Suction 118 PSI, capacitor reads 45 over 5 microfarads, 7.2 amps, gas at 3.5 inches of water column"
    assert extract_readings(text) == [
        Reading("118", "psi"),
        Reading("45/5", "microfarads"),
        Reading("7.2", "amps"),
        Reading("3.5", "inches_wc"),
    ]


def test_extract_readings_from_words():
    assert extract_readings("superheat is twelve degrees") == [Reading("12", "degrees")]
    assert extract_readings("forty five over five microfarads") == [Reading("45/5", "microfarads")]


def test_unit_glued_to_number_is_a_reading():
    assert extract_readings("line voltage now 229V, suction 118psi") == [Reading("229", "volts"), Reading("118", "psi")]
    assert extract_ids("model GSX140241V") == ["gsx140241v"]


def test_spoken_dash_inside_codes():
    assert extract_ids("item ITM dash BOX dash 537 and S-K-U-DASH-I-N-K-DASH-2639") == ["itmbox537", "skuink2639"]


def test_decimal_amps_and_whole_token_id_match():
    from fvr.normalize import contains_id

    assert extract_readings("Compressor amp draw is 24.6A.") == [Reading("24.6", "amps")]
    assert contains_id("a good one, GMVC96404CN", "GMVC96404CN")
    assert contains_id("ticket DEV-ORION-22 open", "DEV-ORION-22")
    assert not contains_id("24ACC636A0035", "24ACC636A003")


def test_spelled_units_and_new_units():
    assert extract_readings("Suction is 118 P.S.I. and the cap is 45 over 5 MFD") == [
        Reading("118", "psi"),
        Reading("45/5", "microfarads"),
    ]
    assert extract_readings("flame sensor 2.8 micro amps, thermocouple 22 millivolts, flow 2.5 gallons a minute") == [
        Reading("2.8", "microamps"),
        Reading("22", "millivolts"),
        Reading("2.5", "gpm"),
    ]


def test_adjacent_numbers_and_slashes_never_merge_into_a_new_value():
    assert extract_readings("It's rated 45/5 MFD.") == [Reading("45/5", "microfarads")]
    assert extract_readings("hose bib is 60, 62 PSI.") == [Reading("62", "psi")]
    assert extract_readings("240... 242 volts.") == [Reading("242", "volts")]


def test_leading_decimals_and_hundreds():
    assert extract_readings("static is .72 inches") == [Reading("0.72", "inches_wc")]
    assert extract_readings("point nine amps") == [Reading("0.9", "amps")]
    assert extract_readings("a hundred and fifty degrees") == [Reading("150", "degrees")]
    assert extract_readings("23mV and 50 megaohms") == [Reading("23", "millivolts"), Reading("50", "megohms")]


def test_glued_ohms_and_greek_mu():
    assert extract_readings("Insulation came back at 50Mohms, ground 30Ω, coil 2 MOhm.") == [
        Reading("50", "megohms"),
        Reading("30", "ohms"),
        Reading("2", "megohms"),
    ]
    assert extract_readings("Flame sensor reading 2.8μA.") == [Reading("2.8", "microamps")]


def test_spaced_mega_and_kilo_ohms_keep_their_prefix():
    assert extract_readings("Insulation came back as 200M Ohms.") == [Reading("200", "megohms")]
    assert extract_readings("Coil is 2.5M ohm, sensor 10k ohms.") == [
        Reading("2.5", "megohms"),
        Reading("10", "kilohms"),
    ]
    assert extract_readings("Bond is 3 m ohms.") == []  # lowercase m could be milliohms: not guessed


def test_integer_glued_to_a_is_never_parsed_as_amps():
    # "60A" can be a reading, a model-number part, a breaker rating or a refrigerant; the checker confirms it instead.
    for text in ("Main is carrying 60A on L1.", "Model number 636A", "Charged with 507A", "15A breaker"):
        assert extract_readings(text) == [], text
