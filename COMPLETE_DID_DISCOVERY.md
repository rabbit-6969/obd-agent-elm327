# Complete DID Discovery Report - 2008 Ford Escape

**Vehicle**: 2008 Ford Escape (VIN: 1FMCU03Z68KB12969)  
**Discovery Date**: February 15, 2026  
**Method**: UDS Service 0x22 (ReadDataByIdentifier) via ELM327 adapter

---

## Summary

**Total DIDs Discovered**: 4  
**Success Rate**: 0.74% (4 out of 538 tested)

The 2008 Ford Escape exposes very limited diagnostic data via UDS compared to newer Ford vehicles (e.g., 2018 Transit has 200+ DIDs). All discovered DIDs are in the low ranges (0x0100-0x0202).

---

## Discovered DIDs

### Transmission/Powertrain (0x0100-0x01FF)

#### DID 0x0100 - Transmission Fluid Temperature
- **Response**: `62 01 00 0C`
- **Data Bytes**: `0C` (12 decimal)
- **Formula**: `hex_value - 40 = °C`
- **Example**: `0x0C = 12`, `12 - 40 = -28°C` (cold engine)
- **Status**: ✓ Verified and documented

#### DID 0x0101 - Transmission Line Pressure
- **Response**: `62 01 01 01 CE`
- **Data Bytes**: `01 CE` (462 decimal)
- **Formula**: Unknown (needs calibration)
- **Status**: ✓ Verified, formula TBD

### ABS/Braking System (0x0200-0x02FF)

#### DID 0x0200 - ABS Parameter (Unknown)
- **Response**: `62 02 00 00`
- **Data Bytes**: `00` (0 decimal)
- **Formula**: Unknown
- **Status**: ✓ Discovered, needs investigation

#### DID 0x0202 - ABS Parameter (Unknown)
- **Response**: `62 02 02 00`
- **Data Bytes**: `00` (0 decimal)
- **Formula**: Unknown
- **Status**: ✓ Discovered, needs investigation

---

## Scan Coverage

### Ranges Tested

| Range | Description | DIDs Tested | DIDs Found | Success Rate |
|-------|-------------|-------------|------------|--------------|
| 0x0100-0x01FF | Transmission/Powertrain | 256 | 2 | 0.78% |
| 0x0200-0x02FF | ABS/Braking System | 256 | 2 | 0.78% |
| 0x0300-0x031A | HVAC/Climate Control | 26 | 0 | 0% |
| 0x0300-0x03FF | Engine/Powertrain (Transit) | 256 | 0 | 0% |
| 0x0400-0x041C | Sensors (Transit) | 29 | 0 | 0% |

**Total Tested**: 538 DIDs  
**Total Found**: 4 DIDs

### Ranges NOT Tested Yet

The following Transit-style ranges were not fully tested:
- 0x0400-0x04FF: Sensors (Transit style) - partially tested (11%)
- 0x0500-0x05FF: Electrical (Transit style)
- 0x0600-0x06FF: Learned values (Transit style)
- 0x0700-0x07FF: Fault status (Transit style)
- 0x0900-0x09FF: Control outputs (Transit style)
- 0x1100-0x11FF: EVAP/Emissions (Transit style)
- 0x1200-0x12FF: Sensors 2 (Transit style)
- 0x1500-0x15FF: Vehicle speed (Transit style)
- 0x1600-0x16FF: Misfire data (Transit style)
- 0x1E00-0x1EFF: Transmission (Transit style) - HIGH PRIORITY
- 0x3000-0x30FF: Switches (Transit style)
- 0xA400-0xA4FF: Key/Security (Transit style)
- 0xC100-0xC1FF: Security 2 (Transit style)
- 0xD000-0xD0FF: Module info (Transit style)
- 0xD100-0xD1FF: Module info 2 (Transit style)
- 0xDD00-0xDDFF: Distance/time (Transit style)
- 0xF400-0xF4FF: Standard OBD (Transit style)
- 0xFD00-0xFDFF: Manufacturer specific (Transit style)

---

## Key Findings

### 1. Limited UDS Exposure
The 2008 Ford Escape exposes far fewer DIDs than newer Ford vehicles:
- **2008 Escape**: 4 DIDs found
- **2018 Transit**: 200+ DIDs accessible

This suggests Ford significantly expanded UDS diagnostic capabilities in newer vehicles.

### 2. No Transit-Style Ranges
Initial testing of Transit-style ranges (0x0300+, 0x0400+) found no DIDs. The 2008 Escape appears to use a different DID organization scheme than newer Fords.

### 3. ABS System Accessible
The discovery of ABS DIDs (0x0200, 0x0202) confirms that multiple vehicle systems are accessible via UDS, not just the powertrain.

### 4. No Extended Session Support
The vehicle does NOT support UDS Service 0x10 (DiagnosticSessionControl), meaning all diagnostics must work in the default session. This limits access to advanced diagnostic features.

---

## Next Steps

### High Priority
1. **Decode ABS DIDs**: Determine what parameters 0x0200 and 0x0202 represent
   - Test with vehicle moving vs stationary
   - Test with ABS activation (safe environment)
   - Compare with known ABS parameters

2. **Complete Transit Range Scan**: Test 0x1E00-0x1EFF range
   - This is the transmission range in newer Fords
   - May reveal additional transmission parameters

3. **Test Remaining Systems**: Continue scanning other ranges
   - 0x0400-0x04FF: Body/Comfort Systems
   - 0x0500-0x05FF: Chassis/Suspension
   - 0xF000-0xF0FF: Vehicle Identification
   - 0xF100-0xF1FF: Manufacturer Specific

### Medium Priority
4. **Calibrate Transmission Pressure**: Determine formula for DID 0x0101
   - Compare with known transmission pressure values
   - Test under different driving conditions

5. **CAN Bus Sniffing**: Capture broadcast messages
   - Many parameters may be broadcast on CAN bus
   - Not accessible via UDS but visible via passive monitoring
   - FORScan shows additional parameters (TR, TCC_RAT, TCIL, etc.)

### Low Priority
6. **Test Other UDS Services**:
   - Service 0x2F: InputOutputControlByIdentifier (actuator tests)
   - Service 0x31: RoutineControl (self-tests)
   - Service 0x19: ReadDTCInformation (detailed fault data)

---

## Comparison: 2008 Escape vs 2018 Transit

| Feature | 2008 Escape | 2018 Transit |
|---------|-------------|--------------|
| Total DIDs | 4 (so far) | 200+ |
| Transmission Range | 0x0100-0x01FF | 0x1E00-0x1EFF |
| Extended Session | ✗ Not supported | ✓ Supported |
| DID Organization | Low ranges only | Multiple high ranges |
| UDS Maturity | Basic/Limited | Advanced/Comprehensive |

---

## Technical Notes

### Communication Pattern
- **Adapter**: ELM327 v1.5 on COM3
- **Baudrate**: 38400
- **Protocol**: Auto (ATSP0)
- **Timeout**: 0.5s per DID
- **Initialization**: ATZ → ATE0 → ATSP0

### Response Format
UDS positive response format: `62 [DID_HIGH] [DID_LOW] [DATA...]`

Example:
```
Request:  22 01 00        (Read DID 0x0100)
Response: 62 01 00 0C     (Positive response, data = 0x0C)
```

### Negative Response Codes (NRC)
Common NRCs encountered:
- `7F 22 11`: serviceNotSupported
- `7F 22 31`: requestOutOfRange
- No response: DID not implemented

---

## Files Generated

- `vehicle_discovery/all_systems_20260215_165055.json` - Full scan results
- `vehicle_discovery/all_systems_summary_20260215_165055.txt` - Summary report
- `vehicle_discovery/discovered_dids_20260215_164211.json` - Previous scan results
- `logs/did_scan_20260215_*.txt` - Detailed scan logs

---

## Conclusion

The 2008 Ford Escape has limited UDS diagnostic capabilities compared to newer vehicles. Only 4 DIDs have been discovered so far, with 2 for transmission and 2 for ABS. Further investigation is needed to:

1. Decode the ABS parameters
2. Complete scanning of Transit-style ranges
3. Explore CAN bus monitoring for additional data

The vehicle's diagnostic architecture appears to be from an earlier generation of Ford's UDS implementation, before the extensive diagnostic capabilities seen in vehicles like the 2018 Transit.
