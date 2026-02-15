# Transmission Data Discovery - 2008 Ford Escape

**Date:** 2026-02-15  
**Vehicle:** 2008 Ford Escape  
**VIN:** 1FMCU03Z68KB12969  
**Status:** ✅ SUCCESS - Transmission parameters discovered!

---

## Summary

Successfully discovered transmission data parameters accessible via UDS Service 0x22 (ReadDataByIdentifier) on the PCM module. The 2008 Ford Escape does NOT have a separate TCM - transmission control is integrated into the PCM.

**Key Finding:** The 2008 Ford Escape PCM does NOT support extended diagnostic session (Service 0x10 03). Attempting to enter extended session returns NRC 0x11 (serviceNotSupported). This means all accessible DIDs must work in the default session.

**Scan Results:** 
- Default session scan (0x0100-0x01FF, 0x1000-0x10FF, 0xF000-0xF0FF): Found 2 DIDs
- Extended session: NOT SUPPORTED (NRC 0x11)
- Conclusion: Ford 2008 Escape uses default session only for transmission diagnostics

## Key Findings

### ✅ Working UDS Commands

#### 1. Transmission Fluid Temperature
- **Command:** `22 0100` (UDS Service 0x22, DID 0x0100)
- **Response:** `62 01 00 0C`
- **Parsing:**
  - `62` = Positive response (0x22 + 0x40)
  - `01 00` = DID echo
  - `0C` = Temperature value (hex)
- **Formula:** `(hex_value - 40) = °C`
- **Example:** `0x0C = 12 decimal → 12 - 40 = -28°C` (engine cold)
- **Status:** ✅ WORKING

#### 2. Transmission Line Pressure
- **Command:** `22 0101` (UDS Service 0x22, DID 0x0101)
- **Response:** `62 01 01 01 CD`
- **Parsing:**
  - `62` = Positive response
  - `01 01` = DID echo
  - `01 CD` = Pressure value (hex, 2 bytes)
- **Formula:** TBD (needs calibration with known pressure)
- **Example:** `0x01CD = 461 decimal` (units unknown - PSI or kPa?)
- **Status:** ✅ WORKING (needs formula)

### ❌ Not Supported (Standard OBD-II)
- PID 0xA4: Transmission Fluid Temperature - NOT SUPPORTED
- PID 0xA6: Transmission Range - NOT SUPPORTED
- PID 0xA7: Transmission Slip Ratio - NOT SUPPORTED
- PID 0xA8: Torque Converter Clutch - NOT SUPPORTED

### ❌ Not Found Yet (UDS DIDs)
- DID 0x0102: Current Gear Position
- DID 0x0103-0x0106: Shift Solenoid States
- DID 0x0107: Torque Converter Clutch Status
- DID 0x0108: Input Shaft Speed
- DID 0x0109: Output Shaft Speed

---

## Technical Details

### UDS Service 0x22: ReadDataByIdentifier

**Protocol:** ISO 14229-1 Unified Diagnostic Services  
**Service ID:** 0x22  
**Response ID:** 0x62 (0x22 + 0x40)

**Request Format:**
```
22 [DID_High] [DID_Low]
```

**Response Format:**
```
62 [DID_High] [DID_Low] [data_bytes...]
```

**Example Transaction:**
```
Request:  22 01 00
Response: 62 01 00 0C
```

### Module Information

**PCM Address:** 0x7E0 (standard OBD-II)  
**Protocol:** ISO 15765-4 CAN (11-bit ID, 500 kbaud)  
**Bus:** HS-CAN (High-Speed CAN)

---

## Next Steps

### ✅ Step 3: Document findings - COMPLETE
### ✅ Step 2: Scan for More DIDs - COMPLETE
- Scanned in default session: No additional DIDs found
- Attempted extended session: NOT SUPPORTED (NRC 0x11)
- **Conclusion:** 2008 Escape only supports default session

### ✅ Step 4: ISO Documentation - COMPLETE
- Service 0x10 (DiagnosticSessionControl): Documented
- Service 0x22 (ReadDataByIdentifier): Documented
- Learned: DID format, data types, manufacturer-specific ranges

### ⏳ Step 1: Parse Values and Next Actions
**Current Status:** We have 2 working DIDs (temperature and pressure)

**Options moving forward:**

**Option A: Focus on what we have**
- Parse temperature and pressure correctly
- Create monitoring tools
- Move to actuation (need Service 0x2F/0x31 docs)

**Option B: Find more DIDs**
- Capture FORScan commands to see what DIDs it uses
- FORScan shows: TR, TCC_RAT, TCIL, TFT_V, TR_V, TRAN_OT
- These must be accessible somehow (different DIDs? Different protocol?)

**Option C: Alternative approach**
- Monitor CAN bus directly (not diagnostic protocol)
- FORScan may be reading broadcast messages, not using Service 0x22
- Would require CAN bus sniffing tools

---

## Documentation Updates

### ✅ Updated Files

1. **`knowledge_base/Ford_Escape_2008_technical.dat`**
   - Added: `C:PCM.READ_TRANS_TEMP UDS:22 DID:0100`
   - Added: `C:PCM.READ_TRANS_PRESSURE UDS:22 DID:0101`
   - Added response parsing rules

2. **`knowledge_base/Ford_Escape_2008_profile.yaml`**
   - Updated TCM section (clarified it's integrated with PCM)
   - Added working UDS DIDs with examples
   - Added formulas and test results

3. **`TRANSMISSION_DATA_DISCOVERY.md`** (this file)
   - Complete discovery documentation

---

## Test Results

### Test Environment
- **Date:** 2026-02-15
- **Condition:** Engine off, ignition on
- **Voltage:** ~11.4V
- **Adapter:** ELM327 v1.5
- **Port:** COM3

### Commands Tested

| Command | Description | Result | Response | Notes |
|---------|-------------|--------|----------|-------|
| `01 A4` | OBD-II TFT | ❌ Not Supported | NO DATA | Standard OBD-II |
| `01 A6` | OBD-II Trans Range | ❌ Not Supported | NO DATA | Standard OBD-II |
| `01 A7` | OBD-II Slip Ratio | ❌ Not Supported | NO DATA | Standard OBD-II |
| `01 A8` | OBD-II TCC | ❌ Not Supported | NO DATA | Standard OBD-II |
| `22 0100` | UDS TFT | ✅ Working | `62 01 00 0C` | Default session |
| `22 0101` | UDS Line Pressure | ✅ Working | `62 01 01 01 CD` | Default session |
| `22 0102` | UDS Gear Position | ❌ Not Supported | NO DATA | Default session |
| `22 0103` | UDS Solenoid A | ❌ Not Supported | NO DATA | Default session |
| `22 0104` | UDS Solenoid B | ❌ Not Supported | NO DATA | Default session |
| `22 0105` | UDS Solenoid C | ❌ Not Supported | NO DATA | Default session |
| `22 0106` | UDS Solenoid D | ❌ Not Supported | NO DATA | Default session |
| `22 0107` | UDS TCC Status | ❌ Not Supported | NO DATA | Default session |
| `22 0108` | UDS Input Shaft Speed | ❌ Not Supported | NO DATA | Default session |
| `22 0109` | UDS Output Shaft Speed | ❌ Not Supported | NO DATA | Default session |

**Systematic Scan Results (2026-02-15 14:44):**
- Scanned 0x0100-0x01FF: No additional DIDs found
- Scanned 0x1000-0x10FF: No additional DIDs found
- Scanned 0xF000-0xF0FF: No additional DIDs found
- Vehicle condition: Engine running
- Conclusion: Additional DIDs require extended diagnostic session (Service 0x10)

---

## Comparison with FORScan

FORScan shows these transmission PIDs:
- TFT (Transmission Fluid Temperature) ✅ Found as DID 0x0100
- TFT_V (TFT sensor voltage) ❓ Not found yet
- TR (Transmission Range) ❓ Not found yet
- TR_V (TR voltage) ❓ Not found yet
- TCC_RAT (Slip Ratio) ❓ Not found yet
- TCIL (Trans Control Indicator Light) ❓ Not found yet
- TRAN_OT (Over Temperature) ❓ Not found yet

**Conclusion:** FORScan likely uses different DIDs or requires extended diagnostic session. Need to scan more DID ranges.

---

## References

- ISO 14229-1:2013(E) - Unified Diagnostic Services (UDS)
- `reference/ISO_14229-1_UDS_Service_0x19_Extract.md` - Service 0x19 documentation
- `reference/ISO_14229-1_UDS_INDEX.md` - Index of available UDS documentation
- `FORD_CAN_BUS_ARCHITECTURE.md` - Ford CAN bus architecture
- `TRANSMISSION_DIAGNOSTICS.md` - Transmission diagnostic notes

---

## Success Metrics

- ✅ Connected to PCM successfully
- ✅ Discovered 2 working transmission DIDs
- ✅ Documented commands in knowledge base
- ✅ Systematic DID scan completed (3 ranges)
- ✅ Created live data monitoring script
- ⏳ Need ISO 14229-1 documentation to proceed
- ⏳ Need to enter extended diagnostic session
- ⏳ Need to parse pressure formula correctly

**Overall Status:** 🟡 PARTIAL SUCCESS - Found 2 DIDs, need extended session for more parameters!
