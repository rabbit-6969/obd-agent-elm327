"""
OBD-II / ISO-TP Helper Utilities

Shared parsing functions for use in all diagnostic scripts.
Covers:
  - ISO-TP CAN frame stripping (ELM327 ATH1 multi-frame responses)
  - VIN reading and parsing (Mode 09 PID 02)
  - DTC decoding (Mode 03 stored, Mode 07 pending)
  - Emission readiness monitor decoding (Mode 01 PID 01)

Usage in a diagnostic script:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../toolkit/vehicle_communication'))
    from obd2_helpers import extract_payload_hex, read_vin, parse_dtcs, parse_readiness

All functions accept a raw ELM327 response string (spaces preserved or stripped — both work).
"""

import re
import time
from typing import Optional


# ---------------------------------------------------------------------------
# ISO-TP frame stripping
# ---------------------------------------------------------------------------

def extract_payload_hex(response: str) -> str:
    """
    Strip CAN/ISO-TP framing from an ELM327 ATH1 multi-frame response and
    return the concatenated payload as an uppercase hex string (no spaces).

    With ATH1 enabled, ELM327 returns lines like:
        7E8 10 14 49 02 01 31 4A   <- first frame  (1x = FF, length follows)
        7E8 21 38 47 41 35 39 31   <- consecutive frame 1 (2x = CF, x = seq)
        7E8 22 31 37 4C 31 34 31   <- consecutive frame 2

    Rules applied per token group:
      - 3-char hex token  -> CAN ID, skip
      - token after CAN ID:
          starts with '1' -> first frame; skip this byte AND the next (lower length)
          starts with '2' -> consecutive frame; skip this byte only
          anything else   -> treat as payload byte
      - all other 2-char hex tokens -> payload bytes

    Single-frame responses (no CAN ID prefix) are handled gracefully:
    the function just strips spaces and returns the hex string as-is.

    Also handles responses where frames are concatenated without spaces
    (some adapters collapse newlines into a single string).
    """
    # Normalise: collapse all whitespace to single spaces, uppercase
    normalised = ' '.join(response.upper().split())

    # If the response looks like it has no spaces between frame bytes
    # (e.g. "7E810144902013..."), try to re-tokenise by splitting on
    # known 3-char CAN ID boundaries.
    # Heuristic: if there are very few spaces relative to length, try splitting
    # on 3-char hex boundaries.
    tokens = normalised.split()
    payload = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        # CAN ID: exactly 3 hex chars (e.g. 7E8, 7EB)
        if len(tok) == 3 and all(c in '0123456789ABCDEF' for c in tok):
            i += 1
            if i >= len(tokens):
                break
            frame_tok = tokens[i]
            if not frame_tok or not all(c in '0123456789ABCDEF' for c in frame_tok):
                i += 1
                continue
            nibble = int(frame_tok[0], 16)
            if nibble == 1:
                i += 2   # skip frame-type byte + lower-length byte
            elif nibble == 2:
                i += 1   # skip sequence byte only
            else:
                i += 1   # single frame or unknown — skip frame byte
        elif len(tok) == 2 and all(c in '0123456789ABCDEF' for c in tok):
            payload.append(tok)
            i += 1
        else:
            i += 1
    return ''.join(payload)


# ---------------------------------------------------------------------------
# VIN
# ---------------------------------------------------------------------------

def parse_vin_from_payload(payload_hex: str) -> Optional[str]:
    """
    Extract a 17-character VIN from a clean payload hex string.

    Mode 09 PID 02 positive response: 49 02 [count] [17 VIN bytes as ASCII hex]
    The count byte is typically 01 but some ECUs omit it or use a different value.

    Strategy:
      1. Find '4902' marker
      2. Try skipping 1 count byte (standard: 49 02 01 [VIN])
      3. If that doesn't yield a valid VIN, try skipping 0 count bytes (49 02 [VIN])
      4. Validate: all 17 chars must be alphanumeric ASCII (VIN charset)

    Returns the VIN string or None if not found / incomplete.
    """
    p = payload_hex.upper()
    idx = p.find('4902')
    if idx == -1:
        return None

    after_marker = p[idx + 4:]  # everything after '4902'

    # Try both offsets: with count byte (offset 2) and without (offset 0)
    for skip_chars in (2, 0, 4):
        vin_hex = after_marker[skip_chars: skip_chars + 34]
        if len(vin_hex) < 34:
            continue
        vin = ''
        valid = True
        for j in range(0, 34, 2):
            try:
                val = int(vin_hex[j:j+2], 16)
                ch = chr(val)
                if ch.isalnum() and val >= 0x20:
                    vin += ch
                else:
                    valid = False
                    break
            except Exception:
                valid = False
                break
        if valid and len(vin) == 17:
            return vin

    return None


def read_vin(elm_cmd_fn, timeout: float = 5.0) -> Optional[str]:
    """
    Read VIN from vehicle using Mode 09 PID 02.

    Args:
        elm_cmd_fn: Callable(command, timeout=) -> str  (your ELM327.cmd / send_command)
        timeout:    How long to wait for the multi-frame response

    Returns:
        17-character VIN string, or None if unavailable / parse failure.

    Strategy:
      1. Send ATCAF0 (raw CAN frames) so ISO-TP framing is visible
      2. Send 0902 and collect multi-frame response
      3. Strip framing with extract_payload_hex(), find 4902 marker
      4. Fallback: regex scan for 17-char VIN pattern in raw ASCII
    """
    elm_cmd_fn("ATCAF0")  # raw frames — framing bytes visible
    time.sleep(0.1)
    response = elm_cmd_fn("0902", timeout=timeout)
    elm_cmd_fn("ATCAF1")  # restore CAN auto-format

    if not response or "NO DATA" in response.upper():
        return None

    # Strategy 1: strip ISO-TP framing
    try:
        payload = extract_payload_hex(response)
        vin = parse_vin_from_payload(payload)
        if vin:
            return vin
    except Exception:
        pass

    # Strategy 2: regex scan for 17-char VIN in raw ASCII
    m = re.search(r'[1-9A-HJ-NPR-Z][A-HJ-NPR-Z0-9]{16}', response)
    if m:
        return m.group(0)

    return None


# ---------------------------------------------------------------------------
# DTC decoding
# ---------------------------------------------------------------------------

_DTC_TYPE = {0: 'P', 1: 'C', 2: 'B', 3: 'U'}


def decode_dtc_bytes(high: int, low: int) -> str:
    """
    Decode two DTC bytes into a standard 5-character code (e.g. P0158).

    Byte layout (SAE J2012):
      bits 7-6 of high byte: system (P/C/B/U)
      bits 5-4 of high byte: first digit (0-3)
      bits 3-0 of high byte: second digit (0-F)
      bits 7-4 of low byte:  third digit  (0-F)
      bits 3-0 of low byte:  fourth digit (0-F)
    """
    dtc_type = _DTC_TYPE[(high >> 6) & 0x03]
    d1 = (high >> 4) & 0x03
    d2 =  high       & 0x0F
    d3 = (low  >> 4) & 0x0F
    d4 =  low        & 0x0F
    return f"{dtc_type}{d1}{d2:X}{d3:X}{d4:X}"


def parse_dtcs(response: str, mode: int) -> list:
    """
    Parse Mode 03 (stored) or Mode 07 (pending) DTC response.

    Args:
        response: Raw ELM327 response string (ATH1 format)
        mode:     3 for stored DTCs, 7 for pending DTCs

    Returns:
        List of DTC strings, e.g. ['P0158', 'P0420']

    Response format with ATH1:
        7E8 06 43 01 58 00 00 00   <- one DTC: P0158
        (service response byte = 0x43 for mode 03, 0x47 for mode 07)

    After stripping framing, payload looks like:
        43 01 58 00 00 00
        ^^ service response
           ^^ DTC count
              ^^^^^ DTC bytes (high, low per DTC)
    """
    if not response:
        return []

    service_byte = 0x40 + mode  # 0x43 for mode 03, 0x47 for mode 07
    marker = f"{service_byte:02X}"

    payload = extract_payload_hex(response)
    dtcs = []
    pos = 0

    while True:
        idx = payload.find(marker, pos)
        if idx == -1:
            break
        after = payload[idx + 2:]  # skip service byte
        if len(after) < 2:
            break
        try:
            num_dtcs = int(after[0:2], 16)
        except Exception:
            pos = idx + 2
            continue
        data = after[2:]  # DTC bytes start here
        for k in range(num_dtcs):
            offset = k * 4
            if offset + 4 > len(data):
                break
            try:
                high = int(data[offset:offset+2], 16)
                low  = int(data[offset+2:offset+4], 16)
                if high == 0 and low == 0:
                    continue
                dtcs.append(decode_dtc_bytes(high, low))
            except Exception:
                pass
        pos = idx + 2

    # Deduplicate, preserve order
    seen = set()
    result = []
    for d in dtcs:
        if d not in seen:
            seen.add(d)
            result.append(d)
    return result


# ---------------------------------------------------------------------------
# Emission readiness monitors (Mode 01 PID 01)
# ---------------------------------------------------------------------------

# (name, supported_mask_in_byte_b, incomplete_flag_byte)
# 'C' = byte_c (continuous monitors), 'D' = byte_d (non-continuous)
_SPARK_MONITORS = [
    # Continuous monitors — supported & incomplete flags both in byte B/C
    ("Misfire",              0x01, 'C'),
    ("Fuel System",          0x02, 'C'),
    ("Components",           0x04, 'C'),
    # Non-continuous monitors — supported in byte B, incomplete in byte D
    ("Catalyst",             0x01, 'D'),
    ("Heated Catalyst",      0x02, 'D'),
    ("Evaporative System",   0x04, 'D'),
    ("Secondary Air System", 0x08, 'D'),
    ("A/C Refrigerant",      0x10, 'D'),
    ("Oxygen Sensor",        0x20, 'D'),
    ("Oxygen Sensor Heater", 0x40, 'D'),
    ("EGR System",           0x80, 'D'),
]

_DIESEL_MONITORS = [
    ("Misfire",              0x01, 'C'),
    ("Fuel System",          0x02, 'C'),
    ("Components",           0x04, 'C'),
    ("EGR/VVT System",       0x01, 'D'),
    ("PM Filter",            0x02, 'D'),
    ("Exhaust Gas Sensor",   0x04, 'D'),
    ("Boost Pressure",       0x08, 'D'),
    ("NOx/SCR Monitor",      0x20, 'D'),
    ("NMHC Catalyst",        0x40, 'D'),
]


def parse_readiness(response: str) -> Optional[dict]:
    """
    Parse Mode 01 PID 01 emission readiness response.

    Args:
        response: Raw ELM327 response string

    Returns:
        Dict with keys:
          mil_on           (bool)
          dtc_count        (int)   — DTC count embedded in PID 01
          is_spark         (bool)  — True = gasoline, False = diesel
          monitors         (list)  — [{'name', 'supported', 'complete'}]
          incomplete_count (int)
          complete_count   (int)
        Or None if parse fails.

    Byte layout of 4101 response (SAE J1979):
      Byte A: bit7=MIL, bits6-0=DTC count, bit3=ignition type (0=spark)
      Byte B: supported flags for continuous (bits 0-2) + non-continuous (bits 0-7)
      Byte C: incomplete flags for continuous monitors
      Byte D: incomplete flags for non-continuous monitors
    """
    if not response or "NO DATA" in response.upper():
        return None

    hex_data = response.replace(' ', '').upper()
    idx = hex_data.find('4101')
    if idx == -1:
        return None

    data = hex_data[idx + 4:]
    if len(data) < 8:
        return None

    try:
        byte_a = int(data[0:2], 16)
        byte_b = int(data[2:4], 16)
        byte_c = int(data[4:6], 16)
        byte_d = int(data[6:8], 16)
    except Exception:
        return None

    mil_on    = bool(byte_a & 0x80)
    dtc_count = byte_a & 0x7F
    is_spark  = not bool(byte_a & 0x08)

    monitor_defs = _SPARK_MONITORS if is_spark else _DIESEL_MONITORS
    monitors = []
    incomplete_count = 0
    complete_count   = 0

    for name, mask, flag_byte in monitor_defs:
        supported = bool(byte_b & mask)
        if not supported:
            continue
        incomplete = bool((byte_c if flag_byte == 'C' else byte_d) & mask)
        monitors.append({
            'name':      name,
            'supported': True,
            'complete':  not incomplete,
        })
        if incomplete:
            incomplete_count += 1
        else:
            complete_count += 1

    return {
        'mil_on':           mil_on,
        'dtc_count':        dtc_count,
        'is_spark':         is_spark,
        'monitors':         monitors,
        'incomplete_count': incomplete_count,
        'complete_count':   complete_count,
    }
