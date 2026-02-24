# Toyota FJ Cruiser 2008 - ABS DTC Reading Guide

## Overview

This guide explains how to read Diagnostic Trouble Codes (DTCs) from the ABS module in a 2008 Toyota FJ Cruiser using UDS (Unified Diagnostic Services).

## Quick Start

```bash
python read_fj_cruiser_abs_dtcs.py
```

Select option 1 to read all DTCs.

## UDS vs OBD-II

### Can we use simple OBD-II?

**Short answer: No, not for ABS DTCs.**

**Why:**
- Standard OBD-II (Mode 03) only reads engine/emissions DTCs from the PCM
- ABS DTCs are stored in the ABS module, not the PCM
- ABS module requires direct UDS communication

### What's the difference?

| Feature | OBD-II Mode 03 | UDS Service 0x19 |
|---------|----------------|------------------|
| Target | PCM only | Any module (PCM, ABS, etc.) |
| Address | 0x7DF (broadcast) | Module-specific (0x7B0 for ABS) |
| DTCs | Engine/emissions only | Module-specific DTCs |
| Protocol | Simplified | Full diagnostic protocol |

## Toyota ABS Module Details

### Addressing
- Request: 0x7B0
- Response: 0x7B8
- Protocol: ISO 15765-4 CAN (500 kbps)

### UDS Services Used

**Service 0x19: ReadDTCInformation**
- Sub-function 0x02: reportDTCByStatusMask
- Sub-function 0x0A: reportSupportedDTC

**Service 0x14: ClearDiagnosticInformation**
- Clears all DTCs from module

## DTC Format

Toyota uses standard ISO 14229 DTC format:

### DTC Structure
```
[TYPE][DIGIT1][DIGIT2][DIGIT3][DIGIT4]
```

**Type codes:**
- P = Powertrain (P0xxx, P2xxx)
- C = Chassis (C0xxx, C2xxx) - ABS DTCs are here
- B = Body (B0xxx, B2xxx)
- U = Network (U0xxx, U2xxx)

### Common ABS DTC Examples

**C0xxx codes (Chassis - ABS/Brake system):**
- C0200-C0299: Wheel speed sensor codes
- C1200-C1299: ABS pump/motor codes
- C1400-C1499: ABS valve codes

**Example DTCs:**
- C0210: Right Front Wheel Speed Sensor Circuit
- C0215: Left Front Wheel Speed Sensor Circuit
- C0220: Right Rear Wheel Speed Sensor Circuit
- C0225: Left Rear Wheel Speed Sensor Circuit
- C1201: ECU Malfunction
- C1223: ABS Control Motor Relay Circuit

## DTC Status Byte

Each DTC has a status byte indicating its state:

| Bit | Mask | Meaning |
|-----|------|---------|
| 0 | 0x01 | testFailed |
| 1 | 0x02 | testFailedThisOperationCycle |
| 2 | 0x04 | pendingDTC |
| 3 | 0x08 | confirmedDTC |
| 4 | 0x10 | testNotCompletedSinceLastClear |
| 5 | 0x20 | testFailedSinceLastClear |
| 6 | 0x40 | testNotCompletedThisOperationCycle |
| 7 | 0x80 | warningIndicatorRequested |

### Status Masks

**Read all DTCs:**
```
Status mask: 0xFF (all bits set)
```

**Read confirmed DTCs only:**
```
Status mask: 0x08 (bit 3 only)
```

**Read pending DTCs only:**
```
Status mask: 0x04 (bit 2 only)
```

## UDS Command Details

### Read All DTCs

**Request:**
```
19 02 FF
```
- 19 = Service (ReadDTCInformation)
- 02 = Sub-function (reportDTCByStatusMask)
- FF = Status mask (all DTCs)

**Response:**
```
59 02 [MASK] [DTC1_HIGH] [DTC1_MID] [DTC1_LOW] [STATUS1] [DTC2...] ...
```
- 59 = Positive response (0x19 + 0x40)
- 02 = Sub-function echo
- MASK = Availability mask
- Each DTC = 4 bytes (3 bytes code + 1 byte status)

### Clear DTCs

**Request:**
```
14 FF FF FF
```
- 14 = Service (ClearDiagnosticInformation)
- FF FF FF = Group of DTC (all DTCs)

**Response:**
```
54
```
- 54 = Positive response (0x14 + 0x40)

## ELM327 Setup

### Initialization Sequence

```
ATZ              # Reset
ATE0             # Echo off
ATL0             # Linefeeds off
ATS0             # Spaces off
ATH1             # Headers on
ATSP6            # ISO 15765-4 CAN (11 bit, 500 kbps)
ATCAF0           # CAN Auto Formatting off
ATSH 7B0         # Set header to ABS request address
ATFCSH 7B8       # Set flow control response address
ATFCSD 30 00 00  # Flow control: continue, no delay
```

### Send DTC Read Command

```
19 02 FF
```

Wait 300ms for response.

## Troubleshooting

### No Response from ABS Module

**Possible causes:**
1. Wrong address (try 0x7B0, 0x760, or scan for modules)
2. Vehicle not ready (turn ignition on)
3. ABS module not on CAN bus
4. Protocol mismatch

**Solutions:**
- Verify ignition is ON
- Try standard OBD-II first to confirm adapter works
- Check if ABS warning light is on (indicates module is active)

### Negative Response Codes

**7F 19 11:** Service not supported
- ABS module doesn't support UDS Service 0x19
- Try OBD-II Mode 03 (won't work for ABS, but confirms communication)

**7F 19 12:** Sub-function not supported
- Try different sub-function (0x02, 0x0A, 0x01)

**7F 19 22:** Conditions not correct
- Vehicle may need to be in specific state
- Try with engine running

**7F 19 31:** Request out of range
- Invalid status mask or parameter

## Alternative Approaches

### If UDS doesn't work:

1. **Try OBD-II Mode 03 (won't get ABS DTCs, but tests communication):**
```
03  # Read DTCs from PCM
```

2. **Scan for modules:**
```
# Try different addresses
7B0, 7B8  # ABS (typical)
760, 768  # ABS (alternate)
7E0, 7E8  # PCM
```

3. **Use Toyota Techstream:**
- Official Toyota diagnostic software
- Guaranteed to work with all modules
- Requires MVCI or VCI cable

## Safety Notes

- Read-only operations are safe
- Clearing DTCs will turn off warning lights
- DTCs will return if problem persists
- Don't clear DTCs before diagnosing the issue
- Some DTCs require specific drive cycles to clear

## Output Example

```
Toyota FJ Cruiser 2008 - ABS DTC Reader
======================================================================

Connecting to ELM327...
Initializing adapter...
✓ Connected
  ABS Request:  0x7B0
  ABS Response: 0x7B8

Sending: 19 02 FF

======================================================================
FOUND 2 DTC(s)
======================================================================

1. DTC: C0210
   Status: 0x08
   Flags:
     ✓ confirmedDTC
   Raw: C02100 08

2. DTC: C1201
   Status: 0x04
   Flags:
     • pendingDTC
   Raw: C12010 04

✓ Disconnected
```

## Related Files

- `read_fj_cruiser_abs_dtcs.py` - DTC reader script
- `scan_abs_module.py` - Ford Escape ABS scanner (similar concept)
- `reference/ISO_14229-1_UDS_Service_0x19_Extract.md` - UDS Service 0x19 details

## References

- ISO 14229-1: Unified Diagnostic Services (UDS)
- ISO 15765-4: CAN diagnostic protocol
- Toyota service manuals
- SAE J2012: DTC definitions

## Summary

**To read ABS DTCs from FJ Cruiser:**
1. Cannot use simple OBD-II Mode 03 (PCM only)
2. Must use UDS Service 0x19 to ABS module (0x7B0)
3. Use the provided Python script
4. DTCs are in C0xxx format (chassis codes)
5. Status byte indicates if DTC is confirmed or pending

The script handles all UDS protocol details automatically.
