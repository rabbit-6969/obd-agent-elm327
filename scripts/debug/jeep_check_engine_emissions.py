#!/usr/bin/env python3
"""
2007 Jeep Wrangler JK - Check Engine Codes & Emission Readiness

Workflow:
  1. Adapter quality check (every session)
  2. Read VIN
  3. Read stored DTCs (Mode 03)
  4. Read pending DTCs (Mode 07)
  5. Read emission readiness monitors (Mode 01 PID 01)

SAFETY: READ-ONLY - no messages modify vehicle state.

Usage:
    python scripts/debug/jeep_check_engine_emissions.py --port COM3
"""

import serial
import time
import sys
import os
from datetime import datetime

_TOOLKIT = os.path.join(os.path.dirname(__file__), '..', '..', 'toolkit', 'vehicle_communication')
sys.path.insert(0, _TOOLKIT)

try:
    from adapter_checker import check_adapter
    _CHECKER_AVAILABLE = True
except ImportError:
    _CHECKER_AVAILABLE = False

from obd2_helpers import read_vin, parse_dtcs, parse_readiness, extract_payload_hex, parse_vin_from_payload


# ---------------------------------------------------------------------------
# ELM327 interface
# ---------------------------------------------------------------------------

class ELM327:
    def __init__(self, port='COM3', baudrate=38400, timeout=3):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None

    def connect(self):
        try:
            self.ser = serial.Serial(port=self.port, baudrate=self.baudrate, timeout=self.timeout)
            time.sleep(2)
            self.cmd("ATZ");  time.sleep(1)
            self.cmd("ATE0")
            self.cmd("ATL0")
            self.cmd("ATS0")
            self.cmd("ATH1")
            self.cmd("ATSP0")
            r = self.cmd("0100")
            return bool(r and "NO DATA" not in r)
        except Exception as e:
            print(f"Connection error: {e}")
            return False

    def cmd(self, command, timeout=None):
        if not self.ser:
            return None
        t = timeout if timeout is not None else self.timeout
        try:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.write((command + '\r').encode())
            buf = b''
            deadline = time.time() + t
            while time.time() < deadline:
                if self.ser.in_waiting:
                    buf += self.ser.read(self.ser.in_waiting)
                    if b'>' in buf:
                        break
                time.sleep(0.05)
            text = buf.decode('ascii', errors='ignore')
            return text.replace('\r', ' ').replace('\n', ' ').replace('>', '').strip()
        except Exception:
            return None

    def close(self):
        if self.ser:
            self.ser.close()


# ---------------------------------------------------------------------------
# Diagnostic steps
# ---------------------------------------------------------------------------

def step_vin(elm, debug=False):
    print("=" * 70)
    print("STEP 1: READ VIN")
    print("=" * 70)

    # Capture raw response for debug / fallback
    elm.cmd("ATCAF0")
    import time; time.sleep(0.1)
    raw = elm.cmd("0902", timeout=5)
    elm.cmd("ATCAF1")

    if debug and raw:
        print(f"  [DEBUG] Raw 0902 response: {raw!r}")
        payload = extract_payload_hex(raw)
        print(f"  [DEBUG] Stripped payload : {payload}")

    vin = None
    if raw and "NO DATA" not in raw.upper():
        try:
            payload = extract_payload_hex(raw)
            vin = parse_vin_from_payload(payload)
        except Exception:
            pass
        if not vin:
            import re
            m = re.search(r'[1-9A-HJ-NPR-Z][A-HJ-NPR-Z0-9]{16}', raw)
            if m:
                vin = m.group(0)

    if vin:
        print(f"  VIN: {vin}")
    else:
        print("  VIN: Not available")
        if raw and not debug:
            print(f"  [Hint] Raw response: {raw!r}")
            print("  [Hint] Run with --debug-vin for full parse trace")
    print()
    return vin


def step_stored_dtcs(elm, debug=False):
    print("=" * 70)
    print("STEP 2: STORED DTCs (Mode 03 - Check Engine Codes)")
    print("=" * 70)
    response = elm.cmd("03", timeout=5)
    if debug and response:
        print(f"  [DEBUG] Raw Mode 03 response: {response!r}")
        print(f"  [DEBUG] Stripped payload    : {extract_payload_hex(response)}")
    if not response or "NO DATA" in response or "UNABLE TO CONNECT" in response:
        print("  No stored DTCs")
        print()
        return []
    dtcs = parse_dtcs(response, mode=3)
    if not dtcs:
        print("  No stored DTCs")
    else:
        print(f"  {len(dtcs)} stored DTC(s):")
        for code in dtcs:
            print(f"    {code}")
    print()
    return dtcs


def step_pending_dtcs(elm, debug=False):
    print("=" * 70)
    print("STEP 3: PENDING DTCs (Mode 07 - Not Yet Confirmed)")
    print("=" * 70)
    response = elm.cmd("07", timeout=5)
    if debug and response:
        print(f"  [DEBUG] Raw Mode 07 response: {response!r}")
        print(f"  [DEBUG] Stripped payload    : {extract_payload_hex(response)}")
    if not response or "NO DATA" in response or "UNABLE TO CONNECT" in response:
        print("  No pending DTCs")
        print()
        return []
    dtcs = parse_dtcs(response, mode=7)
    if not dtcs:
        print("  No pending DTCs")
    else:
        print(f"  {len(dtcs)} pending DTC(s):")
        for code in dtcs:
            print(f"    {code}")
    print()
    return dtcs


def step_readiness(elm):
    print("=" * 70)
    print("STEP 4: EMISSION READINESS MONITORS (Mode 01 PID 01)")
    print("=" * 70)
    response = elm.cmd("0101", timeout=5)
    result = parse_readiness(response) if response else None
    if not result:
        print("  Readiness data not available")
        print()
        return None

    print(f"  MIL (Check Engine Light) : {'ON' if result['mil_on'] else 'OFF'}")
    print(f"  DTC count (from PID 01)  : {result['dtc_count']}")
    print(f"  Ignition type            : {'Spark (gasoline)' if result['is_spark'] else 'Compression (diesel)'}")
    print()
    print(f"  {'Monitor':<28} {'Supported':<12} {'Status'}")
    print("  " + "-" * 58)
    for m in result['monitors']:
        status = "COMPLETE   ✓" if m['complete'] else "INCOMPLETE ⚠"
        print(f"  {m['name']:<28} {'Yes':<12} {status}")
    print()
    return result


def print_summary(vin, stored_dtcs, pending_dtcs, readiness):
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Timestamp : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Vehicle   : 2007 Jeep Wrangler JK")
    if vin:
        print(f"  VIN       : {vin}")
    print()

    if readiness:
        print(f"  Check Engine Light : {'ON' if readiness['mil_on'] else 'OFF'}")

    total = len(stored_dtcs) + len(pending_dtcs)
    if total == 0:
        print("  DTCs               : None")
    else:
        if stored_dtcs:
            print(f"  Stored DTCs        : {', '.join(stored_dtcs)}")
        if pending_dtcs:
            print(f"  Pending DTCs       : {', '.join(pending_dtcs)}")

    if readiness:
        if readiness['incomplete_count'] == 0:
            print("  Emission Monitors  : All complete (ready for inspection)")
        else:
            print(f"  Emission Monitors  : {readiness['incomplete_count']} incomplete, "
                  f"{readiness['complete_count']} complete")
            print("  NOTE: Drive cycle required to complete remaining monitors")

    print()
    issues = total + (readiness['incomplete_count'] if readiness else 0)
    if issues == 0:
        print("  PASS - No issues found. Vehicle appears ready for emissions test.")
    else:
        print("  ATTENTION - Issues found. See details above.")
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(port='COM3', debug_vin=False):
    print("=" * 70)
    print("2007 Jeep Wrangler JK - Check Engine & Emission Readiness")
    print("=" * 70)
    print()

    elm = ELM327(port=port)
    if not elm.connect():
        print("Failed to connect to ELM327")
        print()
        print("Troubleshooting:")
        print("  - Verify adapter is plugged into OBD-II port")
        print("  - Check COM port (use Device Manager)")
        print("  - Ensure ignition is in RUN position")
        return False

    print(f"Connected on {port}")
    print()

    if _CHECKER_AVAILABLE:
        print("Checking adapter quality...")
        print(check_adapter(elm.ser).user_message())
        print()

    vin          = step_vin(elm, debug=debug_vin)
    stored_dtcs  = step_stored_dtcs(elm, debug=debug_vin)
    pending_dtcs = step_pending_dtcs(elm, debug=debug_vin)
    readiness    = step_readiness(elm)

    print_summary(vin, stored_dtcs, pending_dtcs, readiness)

    elm.close()
    print("Disconnected")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description='Check engine codes and emission readiness for 2007 Jeep Wrangler JK'
    )
    parser.add_argument('--port', default='COM3', help='Serial port (default: COM3)')
    parser.add_argument('--debug-vin', action='store_true', help='Show raw VIN/DTC responses for debugging')
    args = parser.parse_args()
    sys.exit(0 if main(port=args.port, debug_vin=args.debug_vin) else 1)
