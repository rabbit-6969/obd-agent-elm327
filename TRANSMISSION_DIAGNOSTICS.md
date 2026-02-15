# Transmission Diagnostics - Ford Escape 2008

## Overview
The Transmission Control Module (TCM) in the 2008 Ford Escape uses UDS (ISO 14229) protocol but requires extended diagnostic sessions or security access to read most data identifiers.

## Known Data Identifiers (DIDs)

### 1E1C - Raw Transmission Fluid Temperature (TFT)

**Description:** Raw sensor input value before any FMEM (Failure Mode Effects Management) substitution

**Specifications:**
- Size: 2 bytes (16-bit signed integer)
- Resolution: 0.0625°C per bit (1/16°C)
- Units: Degrees Celsius
- Range: -2048°C to +2047.9375°C (theoretical)

**Conversion Formula:**
```
Temperature (°C) = (raw_value * 0.0625)
Temperature (°F) = (raw_value * 0.0625 * 1.8) + 32
```

**Test Results (2026-02-14):**
- Environment: 10°F garage (~-12°C)
- Addresses tested:
  - `7E0` (PCM): NO DATA
  - `7E1` (TCM): NO DATA  
  - `C410F1` (Extended diagnostic): NO DATA

**Commands Attempted:**
```
txd: C410F1221E1C
rxd: NO DATA

txd: 07E0221E1C
rxd: NO DATA

txd: 07E1221E1C
rxd: NO DATA
```

**Analysis:**
The TCM is not responding to standard ReadDataByIdentifier (0x22) requests. This suggests:
1. Extended diagnostic session required (Service 0x10, Session 0x03)
2. Security access may be needed (Service 0x27)
3. TCM may only respond when engine is running
4. May require specific tool protocol (FORScan, IDS, FDRS)

## Next Steps

### Try Extended Diagnostic Session
```
1. Send: 10 03 (Start Extended Diagnostic Session)
2. Wait for positive response: 50 03
3. Then send: 22 1E 1C (Read TFT)
```

### Try with Engine Running
The TCM may only respond when:
- Engine is running
- Transmission is in gear
- Vehicle speed > 0

### Alternative Approaches
1. Use FORScan to capture the working command sequence
2. Monitor CAN bus while FORScan reads the value
3. Check if data is broadcast on CAN (passive monitoring)

## Related Information

**Old Output Format:**
- Previous tool showed temperature in Fahrenheit
- This suggests Ford's internal tools convert from Celsius
- Verify conversion formula with known good values

**Safety Notes:**
- Do not attempt extended diagnostic sessions while driving
- Some commands may affect transmission operation
- Always have a way to reset the TCM if needed

## References
- ISO 14229-1: Unified Diagnostic Services (UDS)
- Ford Service Manual: Transmission Control Module
- FORScan documentation
