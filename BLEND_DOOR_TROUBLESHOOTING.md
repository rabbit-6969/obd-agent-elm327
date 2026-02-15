# Blend Door Actuator — Troubleshooting Guide

Symptom
-------
- HVAC blend door actuator cannot determine position / reports sensor fault.

Quick checks
------------
- Read HVAC DTCs (Service 19 / 07) and Mode 03 stored codes. Look for codes such as `P1632`, `P1634`, `P1635` (actuator/door faults) or manufacturer/chassis codes like `C7F19`.
- Check the raw hex in logs for the DTC entry to help vendor lookups.

Electrical sanity
-----------------
- Verify vehicle battery/ignition is in RUN. Low voltage can cause module/sensor faults.
- Inspect connector at the HVAC actuator for corrosion, loose pins, or broken wires.
- With harness unplugged, check for 5V reference and ground at the connector using a multimeter.

Actuator & sensor checks
------------------------
- Command the actuator to move (if supported by your tool) and observe motion:
  - If actuator doesn't move: check power/ground, measure motor supply while commanding.
  - If actuator moves but position is incorrect: likely position sensor (potentiometer) failure or linkage problem.
- Check for mechanical binding in the blend door linkage (broken tab, worn spline, disconnected slotted shaft).

Module-level checks
-------------------
- Read live module values (position sensor or target position PID if available) and compare command vs reported.
- If module reports impossible values or constant value, suspect sensor (pot) or wiring.

Software / calibration
----------------------
- Some HVAC modules require a calibration or relearn after actuator replacement — follow Ford-specific procedures.
- Clear DTCs, cycle the ignition, and re-run self-tests to verify whether the fault returns.

Logging & diagnostics with this tool
-----------------------------------
- Use `HVACDiagnostics.read_dtc_codes()` to capture DTCs and include raw hex in logs for vendor lookup.
- Save parsed-events JSONL and attach them when asking a dealer or consulting service manuals.

Next actions (recommended order)
-------------------------------
1. Capture DTCs and the raw hex entry (for `C7F19` lookups).
2. Visually inspect actuator connector and wiring; repair any damage.
3. Measure 5V reference and ground at the actuator connector.
4. Command actuator and observe movement vs reported position.
5. Replace actuator if the position sensor is faulty; perform calibration/relearn.

References
----------
- Ford Service Manual / TSBs for model-specific actuator calibration and DTC definitions.
- `BLEND_DOOR` actuator replacement guides and HVAC module wiring diagrams.
