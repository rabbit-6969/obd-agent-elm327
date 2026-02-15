# Vehicle Data Collection Report

**Date:** February 14, 2026, 18:54:42  
**Vehicle:** 2008 Ford Escape  
**VIN:** 1FMCU03Z68KB12969  
**Adapter:** ELM327 v1.5  
**Voltage:** 11.4V  
**Condition:** Engine off, ignition on

---

## Executive Summary

Comprehensive data collection completed successfully from 2008 Ford Escape. The vehicle's PCM (Powertrain Control Module) is fully accessible via standard OBD-II protocols, providing access to 20 live data PIDs, diagnostic trouble codes, monitor status, and vehicle information. Other modules (HVAC, ABS, BCM, IPC, TCM) are not accessible via standard OBD-II and require proprietary Ford diagnostic tools (FORScan, IDS, FDRS).

### Key Findings

- **Accessible Modules:** 1 (PCM only)
- **Partially Accessible:** 1 (ABS responds but limited)
- **Not Accessible:** 4 (HVAC, BCM, IPC, TCM)
- **Live Data Points:** 20 PIDs successfully read
- **Supported PID Ranges:** 3 ranges (01-20, 21-40, 41-60)
- **DTCs Present:** 0 (vehicle in good condition)
- **OBD Standard:** OBD-II as defined by EPA

---

## Module Accessibility

### ✅ Fully Accessible: PCM (7E0)

The Powertrain Control Module is fully accessible via standard OBD-II Mode 01 (live data), Mode 03 (DTCs), Mode 07 (pending DTCs), and Mode 09 (vehicle info).

**Capabilities:**
- Read/clear diagnostic trouble codes
- Read 20+ live data parameters
- Read VIN and calibration information
- Monitor readiness status
- Freeze frame data (when DTCs present)

**Test Response:** `43 00` (no DTCs)

### ⚠️ Partially Accessible: ABS (760)

The ABS module responds to queries but returns "service not supported" (7F 03 11) for DTC reading. This is common for non-powertrain modules in this vehicle generation.

**Test Response:** `7F 03 11` (service not supported)

### ❌ Not Accessible via Standard OBD-II

The following modules do not respond to standard OBD-II queries:

1. **HVAC (7A0)** - Requires FORScan with MS-CAN protocol
2. **BCM (726)** - Body Control Module
3. **IPC (733)** - Instrument Panel Cluster  
4. **TCM (7E1)** - Transmission Control Module

These modules require proprietary Ford diagnostic protocols not available through standard ELM327 adapters.

---

## Supported PIDs

### Range 01-20 (0x00-0x20)
**Response:** `41 00 BE 3F B8 13`

Supported PIDs in this range:
- 01: Monitor status
- 03: Fuel system status
- 04: Calculated engine load ✓
- 05: Engine coolant temperature ✓
- 06: Short term fuel trim - Bank 1 ✓
- 07: Long term fuel trim - Bank 1 ✓
- 0C: Engine RPM ✓
- 0D: Vehicle speed ✓
- 0E: Timing advance ✓
- 0F: Intake air temperature ✓
- 10: MAF air flow rate ✓
- 11: Throttle position ✓
- 13: Oxygen sensors present ✓
- 1C: OBD standards ✓
- 1F: Run time since engine start ✓

### Range 21-40 (0x21-0x40)
**Response:** `41 20 C0 17 E0 11`

Supported PIDs in this range:
- 21: Distance traveled with MIL on ✓
- 2F: Fuel tank level input ✓
- 33: Absolute barometric pressure ✓

### Range 41-60 (0x41-0x60)
**Response:** `41 40 FC 00 00 00`

Supported PIDs in this range:
- 42: Control module voltage ✓
- 43: Absolute load value ✓
- 45: Relative throttle position ✓
- 46: Ambient air temperature ✓

---

## Live Data Snapshot

All values captured with engine off, ignition on:

| PID | Parameter | Value | Raw Response |
|-----|-----------|-------|--------------|
| 04 | Calculated Engine Load | 0% | 41 04 00 |
| 05 | Engine Coolant Temperature | 14°C | 41 05 36 |
| 06 | Short Term Fuel Trim Bank 1 | 0% | 41 06 80 |
| 07 | Long Term Fuel Trim Bank 1 | 0% | 41 07 80 |
| 0C | Engine RPM | 0 RPM | 41 0C 00 00 |
| 0D | Vehicle Speed | 0 km/h | 41 0D 00 |
| 0E | Timing Advance | 68° before TDC | 41 0E 94 |
| 0F | Intake Air Temperature | 28°C | 41 0F 44 |
| 10 | MAF Air Flow Rate | 0 g/s | 41 10 00 00 |
| 11 | Throttle Position | 16.5% | 41 11 2A |
| 13 | Oxygen Sensors Present | Bank 1: 1,2 | 41 13 03 |
| 1C | OBD Standards | OBD-II (EPA) | 41 1C 02 |
| 1F | Run Time Since Engine Start | 0 seconds | 41 1F 00 00 |
| 21 | Distance with MIL On | 0 km | 41 21 00 00 |
| 2F | Fuel Tank Level | 99.2% | 41 2F FC |
| 33 | Barometric Pressure | 98 kPa | 41 33 62 |
| 42 | Control Module Voltage | 11.662V | 41 42 2D CE |
| 43 | Absolute Load Value | 0% | 41 43 00 00 |
| 45 | Relative Throttle Position | 0% | 41 45 00 |
| 46 | Ambient Air Temperature | 14°C | 41 46 36 |

---

## Diagnostic Trouble Codes

### Mode 03: Stored DTCs
**Response:** `43 00`  
**Result:** No DTCs present

### Mode 07: Pending DTCs
**Response:** `47 00`  
**Result:** No pending DTCs

### Mode 0A: Permanent DTCs
**Response:** `7F 0A 11`  
**Result:** Service not supported (normal for this vehicle)

---

## Monitor Status

**Response:** `41 01 00 07 E5 00`

**Interpretation:**
- MIL Status: OFF
- DTC Count: 0
- Misfire Monitor: Complete
- Fuel System Monitor: Complete
- Components Monitor: Complete

All emission-related monitors are complete and passing.

---

## Vehicle Information

### VIN (Mode 09 PID 02)
**Raw Response:**
```
0: 49 02 01 31 46 4D
1: 43 55 30 33 5A 36 38
2: 4B 42 31 32 39 36 39
```
**Decoded:** 1FMCU03Z68KB12969

### Calibration ID (Mode 09 PID 04)
**Raw Response:**
```
0: 49 04 01 51 49 45
1: 46 31 41 36 2E 48 45
2: 58 00 00 00 00 00 00
```
**Decoded:** QIEF1A6.HEX

### Calibration Verification Numbers (Mode 09 PID 06)
**Response:** `49 06 01 33 13 B7 13`

---

## Test Fixtures Created

All collected data has been saved to test fixtures for future testing:

### Files Created:
1. **`knowledge_base/vehicle_data_20260214_185442.json`**
   - Complete raw data collection
   - All responses in original format
   - Metadata and timestamps

2. **`tests/fixtures/ford_escape_2008_responses.json`**
   - Organized test fixtures
   - Categorized by command type
   - Includes decoded values
   - Test scenarios defined

3. **`knowledge_base/Ford_Escape_2008_technical.dat`**
   - Updated with real vehicle data
   - Module accessibility status
   - Supported PID ranges
   - Real response patterns

---

## Recommendations for Testing

### Unit Tests
Use the collected fixtures to create unit tests for:

1. **DTC Parsing**
   - Test "no DTCs" response: `43 00`
   - Test "service not supported": `7F 0A 11`

2. **Live Data Parsing**
   - Temperature conversion (PID 05, 0F, 46)
   - Voltage calculation (PID 42)
   - Percentage calculations (PID 04, 2F)

3. **VIN Decoding**
   - Multi-line response parsing
   - Hex to ASCII conversion

4. **Module Detection**
   - Accessible vs not accessible
   - Error response handling

### Integration Tests
1. Test agent workflow with "no DTCs" scenario
2. Test module accessibility detection
3. Test graceful handling of unsupported modules

### Property-Based Tests
1. Any valid OBD-II response should parse without errors
2. Temperature values should be within reasonable range (-40°C to 215°C)
3. Voltage should be within automotive range (9V to 16V)

---

## Limitations and Notes

1. **Engine Off Data:** All data collected with engine off, ignition on. Some PIDs (RPM, speed, MAF) show zero values.

2. **No DTCs Present:** Vehicle is in good condition with no diagnostic codes. Cannot test DTC parsing with real codes.

3. **Module Access:** Only PCM accessible. Other modules require proprietary tools.

4. **Freeze Frame:** No freeze frame data available (only present when DTCs exist).

5. **Low Voltage:** Battery voltage at 11.4V indicates vehicle not running. Normal operating voltage is 13.5-14.5V.

---

## Next Steps

1. ✅ Data collection complete
2. ✅ Test fixtures created
3. ✅ Knowledge base updated
4. ⏭️ Create unit tests using fixtures
5. ⏭️ Create integration tests
6. ⏭️ Implement property-based tests
7. ⏭️ Document test strategy

---

## Conclusion

Comprehensive vehicle data collection successful. The 2008 Ford Escape's PCM is fully accessible via standard OBD-II, providing rich diagnostic data. All collected responses have been documented and organized into test fixtures for future development. The data confirms that standard OBD-II access is limited to the powertrain module, with other modules requiring proprietary Ford diagnostic protocols.

**Data Quality:** Excellent  
**Coverage:** Complete for accessible modules  
**Usability:** Ready for test development  
**Documentation:** Comprehensive
