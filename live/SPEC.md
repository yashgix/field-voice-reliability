# Visit script specification

Scripts of realistic HVAC service visits, used to test software that keeps a job record from what a technician says
during a visit. A script states what is said, line by line, and what each line means for the true record. The script
is the ground truth. It must be possible to replay it line by line and know the true record at every moment.

Write as a field technician would really talk while working: short, unplanned, with fillers, half sentences and
background talk. Most visits are ordinary. Do not try to trick any particular software. Write what plausibly happens.

## File format
One JSON object per visit.

```json
{
  "id": "v01",
  "kind": "ordinary",
  "equipment": [
    {"id": "E1", "type": "condenser", "location": "back yard, left", "make": "Carrier", "model": "24ACC636", "serial": "2416E12345"}
  ],
  "turns": [
    {"id": 1, "speaker": "tech", "text": "okay starting on the condenser out back", "effects": []},
    {"id": 2, "speaker": "tech", "text": "suction's sitting at one eighteen", "effects": [
      {"op": "reading", "equip": "E1", "field": "suction_pressure", "value": "118", "uom": "psi"}]}
  ]
}
```

- `kind`: `ordinary` (a normal visit, few or no tricky moments), `mixed` (a normal visit with two or three tricky
  moments) or `hard` (a busy visit with many).
- `equipment`: 2 to 4 pieces of equipment on site, each with a short `id` (E1, E2...). Invented model and serial
  strings are fine.
- `turns`: 25 to 40 lines in order. `speaker` is `tech`, `customer` or `device` (the voice assistant on the
  technician's headset). The software under test will not see speaker labels.
- `text`: what was said, in lower case, with numbers written as words the way they are spoken ("two forty five",
  "point five eight", "twelve point four"). Model numbers spelled as spoken ("g s x one six zero three six one").
- `effects`: what the line changes in the true record, from the list below. Most lines have none.

## Device lines
The headset speaks only in these scripted ways, and they change nothing by themselves:
- a read-back: `"reading back, compressor amps twelve point four on the north condenser"`
- a prompt: `"you haven't logged a filter check yet"`

A tech may cut a device line off. Show this with `--` at the cut, and put what the tech says next in the following
line. A read-back that was cut off confirms nothing.

## Effects
Keys: `equip` is an equipment id, `field` a reading field, `task` a work task, `uom` the unit of measure.

| op | Keys | Meaning |
|---|---|---|
| `reading` | equip, field, value, uom | A reading was taken. A later `reading` on the same equip and field replaces it (a new measurement) |
| `revise` | equip, field, value | The earlier value was wrong (misread, wrong probe, misspoke) and this is the right one |
| `reassign` | field, from, to | A reading already given for one piece of equipment really belongs to another |
| `retract` | equip, field | A reading is withdrawn with no replacement |
| `work` | equip, task, status | Work status changes. Status is one of `proposed`, `approved`, `declined`, `in_progress`, `done`, `deferred` |
| `equipment` | equip, field, value | A fact about the equipment itself: `model`, `serial` or `refrigerant` |
| `ambiguous` | equip, field, options, answer, resolves_to | The words cannot settle a value (for example two numbers with no sign of which is meant). `options` lists the candidates. `answer` is what the tech would say if asked about it right then. `resolves_to` is the value that answer gives |

An `ambiguous` effect may instead leave the equipment unsettled: then `equip` is a list of candidate ids, `value` and
`uom` give the reading, `options` is left out, and `resolves_to` is the right equipment id.

Rules:
- The true record at any moment is the result of applying every effect up to that line, in order.
- Status means what has actually happened. "I'd recommend a coil cleaning" is `proposed`. "Customer said go ahead"
  is `approved`. "Old one's out, new one's going in" is `in_progress`. "New cap is in" is `done`. A part that is
  removed but whose replacement is not installed is not `done`.
- A number that is not a reading of this equipment (a thermostat setpoint, a figure the customer quotes, a price) has
  no effect.
- If a line could reasonably mean two things, use `ambiguous`. Do not pick one silently.

## Reading fields (use only these)
`suction_pressure` psi, `head_pressure` psi, `superheat` F, `subcooling` F, `supply_air_temp` F, `return_air_temp`
F, `delta_t` F, `temp_rise` F, `compressor_amps` A, `condenser_fan_amps` A, `blower_amps` A, `capacitor_uf` uF,
`line_voltage` V, `static_pressure` in_wc, `gas_pressure` in_wc, `flame_sensor_ua` uA, `insulation_resistance` Mohm.
Add `_after` to a field for a re-measurement after a repair (`capacitor_uf_after`).

## Work tasks (use only these)
`replace_capacitor`, `replace_contactor`, `replace_compressor`, `replace_fan_motor`, `replace_blower_motor`,
`replace_filter`, `clean_coil`, `clean_flame_sensor`, `add_refrigerant`, `leak_search`, `replace_thermostat`,
`clear_drain`.

## What visits contain
Across a set of visits, include these naturally and in proportion to how often they would really happen. Ordinary
visits have none or one. Hard visits have several.
- moving to another piece of equipment without naming it, or naming it only by place ("okay, the one by the fence")
- a reading given and later corrected, with a cue ("no wait") or without one
- a reading later said to belong to other equipment
- "same on the other one" and similar references
- work proposed, approved, declined, deferred, started but not finished, or finished and then undone
- a device read-back the tech cuts off, or answers only in part
- customer talk with numbers in it
- a reference to an earlier photo, observation or repair
- a model or serial misread and corrected

Keep the visit physically plausible: readings in normal ranges for the equipment, repairs that fit the readings.
