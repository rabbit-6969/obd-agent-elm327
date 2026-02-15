# Mode 03 (Stored DTC) Refactor

Summary
-------
This change extracts the inline Mode-03 (stored DTC) parsing logic from
`get_emission_readiness_status()` into a public helper method
`ELM327Adapter.read_stored_dtcs()`.

Why
---
- Improves code reuse and testability.
- Makes stored-DTC reading available to other parts of the codebase.
- Simplifies `get_emission_readiness_status()` and makes unit testing easier.

What changed
------------
- Added `ELM327Adapter.read_stored_dtcs()` which:
  - Calls `send_obd_command("03")` to request stored DTCs.
  - Normalizes the response, converts hex tokens to bytes, skips the
    leading `0x43` response code when present, and parses the remaining
    bytes into standard DTC strings (e.g. `P0123`).
  - Returns a list of DTC strings or an empty list if none/error.
- Replaced the nested `read_stored_dtcs_local()` inside
  `get_emission_readiness_status()` with a call to
  `self.read_stored_dtcs()`.

Notes on parsing
----------------
- DTC bytes are parsed in 2-byte pairs (A,B). The type letter is
  derived from the top two bits of `A` using the standard mapping:
  00=P, 01=C, 10=B, 11=U. The 14-bit fault code number is assembled from
  `A & 0x3F` and `B`.

Testing
-------
- Unit tests were added in `tests/test_read_stored_dtcs.py`. They mock
  `send_obd_command()` (and related methods) to verify parsing logic and
  that `get_emission_readiness_status()` includes `stored_dtcs`.

Files changed/added
------------------
- Modified: `elm327_diagnostic/elm327_adapter.py` (added `read_stored_dtcs()` and removed inline reader)
- Added: `MODE_03_REFACTOR.md` (this file)
- Added: `tests/test_read_stored_dtcs.py` (unit tests using pytest)

If you want, I can next:
- extend `read_stored_dtcs()` to support ISO-TP multi-frame assembly, or
- export parsed-event fixtures into a test fixtures directory.
