# Vehicle Discovery Summary - 2008 Ford Escape

**Vehicle**: 2008 Ford Escape 2.3L I4 DURATEC-HE  
**VIN**: 1FMCU03Z68KB12969  
**Odometer**: 325,588.8 km (202,330 miles)  
**Discovery Date**: February 15, 2026

---

## Quick Summary

We successfully discovered **4 accessible DIDs** via standard UDS protocol, and confirmed **13 modules** are accessible via FORScan proprietary protocol.

---

## UDS Discovery Results (Standard OBD-II/UDS)

### Accessible DIDs: 4 Total

#### Transmission/Powertrain (PCM at 0x7E0)
1. **DID 0x0100** - Transmission Fluid Temperature
   - Command: `22 0100`
   - Response: `62 01 00 XX`
   - Formula: `(XX hex - 40) = °C`
   - Status: ✓ Working, formula verified

2. **DID 0x0101** - Transmission Line Pressure
   - Command: `22 0101`
   - Response: `62 01 01 XX XX`
   - Formula: TBD (needs calibration)
   - Status: ✓ Working, formula unknown

#### ABS System (at 0x760)
3. **DID 0x0200** - Unknown ABS Parameter
   - Command: `22 0200`
   - Response: `62 02 00 00`
   - Formula: Unknown
   - Status: ✓ Working, needs investigation

4. **DID 0x0202** - Unknown ABS Parameter
   - Command: `22 0202`
   - Response: `62 02 02 00`
   - Formula: Unknown
   - Status: ✓ Working, needs investigation

### Scan Statistics
- **Total DIDs Tested**: 538
- **DIDs Found**: 4
- **Success Rate**: 0.74%
- **Ranges Scanned**:
  - 0x0100-0x01FF: Transmission (2 found)
  - 0x0200-0x02FF: ABS (2 found)
  - 0x0300-0x031A: HVAC (0 found, partial scan)
  - 0x0300-0x03FF: Transit-style (0 found)
  - 0x0400-0x041C: Transit-style (0 found, partial scan)

---

## FORScan Discovery Results (Proprietary Protocol)

### Accessible Modules: 13 Total

| # | Module | Part Number | Software Date | DTCs | Notes |
|---|--------|-------------|---------------|------|-------|
| 1 | PCM | 8L8A-12A650-AEB | 2006 | None | Engine control |
| 2 | ABS | 8L84-2C219-CH | 2006-12-11 | None | Braking system |
| 3 | IC | 8L8T-10849-HA | 2007-01-31 | B1318-20* | Instrument cluster |
| 4 | HVAC | 8L84-19980-AJ | 2007-01-08 | B1676-20* | Climate control |
| 5 | RCM | 8L84-14B321-AH | 2006-09-06 | None | Airbag control |
| 6 | PSCM | 8L84-3F964-BA | 2013-02-15 | None | Power steering |
| 7 | OCS | 8L84-14B422-AF | 2006-10-30 | None | Seat occupancy |
| 8 | FCIM | 8L8T-18A802-AK | 2007-03-14 | None | Front controls |
| 9 | FDIM | 8L8T-19C116-AK | 2007-03-09 | None | Front display |
| 10 | ACM | 8L8T-19C107-AM | 2007-03-08 | None | Audio control |
| 11 | SDARS | 8S4T-18C963-AE | 2007-05-21 | B1032-20* | Satellite radio |
| 12 | GEM/SJB | 7L1T-14B476-CH | 2006-10-27 | None | Body control/fuses |
| 13 | OBD2_PCM | - | - | None | OBD-II interface |

\* = Previously set DTC, not currently active

---

## Key Discoveries

### 1. Limited UDS Exposure
The 2008 Escape exposes very few DIDs via standard UDS:
- Only 4 DIDs found across 538 tested (0.74% success rate)
- Compare to 2018 Transit: 200+ DIDs accessible
- Ford significantly expanded UDS capabilities in newer vehicles

### 2. Proprietary Protocol Required
Most modules require Ford's proprietary protocol:
- 13 modules accessible via FORScan
- Only 2 modules partially accessible via standard UDS
- FORScan uses extended addressing and custom services

### 3. Multi-Bus Architecture
Vehicle uses two CAN buses:
- **HS-CAN** (500 kbaud): PCM, ABS, IC, RCM, PSCM, OCS
- **MS-CAN** (125 kbaud): HVAC, GEM/SJB, FCIM, FDIM, ACM, SDARS

Standard OBD-II adapters typically only access HS-CAN.

### 4. No Extended Session Support
- UDS Service 0x10 (DiagnosticSessionControl) NOT supported
- All diagnostics must work in default session
- Limits access to advanced diagnostic features

### 5. Historical DTCs
Three modules have voltage-related DTCs (now cleared):
- IC: B1318-20 (Battery voltage too low)
- HVAC: B1676-20 (Battery voltage out of range)
- SDARS: B1032-20 (Satellite antenna short)

All likely from low battery condition (11.4V measured).

---

## What We Can Access

### With Standard OBD-II/UDS (ELM327)
✓ Engine parameters (Mode 01 PIDs)  
✓ Engine DTCs (Mode 03/04)  
✓ VIN and calibration ID (Mode 09)  
✓ Transmission temperature (DID 0x0100)  
✓ Transmission pressure (DID 0x0101)  
✓ Some ABS parameters (DIDs 0x0200, 0x0202)  

### Requires FORScan
✓ HVAC diagnostics  
✓ Body control modules (GEM/SJB, FCIM, FDIM)  
✓ Safety modules (RCM, OCS)  
✓ Module part numbers and software versions  
✓ Module programming/configuration  
✓ Advanced diagnostic functions  
✓ All module DTCs  

---

## Remaining Work

### High Priority
1. **Decode ABS DIDs** (0x0200, 0x0202)
   - Test with vehicle moving
   - Test with braking
   - Compare with known ABS parameters

2. **Calibrate Transmission Pressure** (DID 0x0101)
   - Determine formula
   - Test under different conditions

3. **Complete DID Scanning**
   - Test 0x1E00-0x1EFF (Transit transmission range)
   - Test remaining system ranges
   - Test 0xF000+ (vehicle identification)

### Medium Priority
4. **Create Live Monitoring Tools**
   - Real-time display of all 4 DIDs
   - Logging capabilities
   - Alert thresholds

5. **FORScan Integration**
   - Document FORScan procedures
   - Parse FORScan output
   - Guide users when FORScan needed

### Low Priority
6. **Test Other UDS Services**
   - Service 0x2F: InputOutputControlByIdentifier
   - Service 0x31: RoutineControl
   - Service 0x19: ReadDTCInformation

7. **CAN Bus Sniffing**
   - Capture broadcast messages
   - Find parameters not accessible via UDS
   - Decode FORScan parameters (TR, TCC_RAT, etc.)

---

## Tools and Adapters

### What Works
- **ELM327 v1.5**: Basic OBD-II and UDS diagnostics
- **FORScan**: Full module access (with adapter warning)
- **Python + pyserial**: Custom diagnostic scripts

### Recommended Upgrades
- **OBDLink MX+**: Better FORScan compatibility
- **VLinker FS**: Designed for FORScan
- **CANtact/PCAN**: For CAN bus sniffing

---

## Files Generated

### Discovery Results
- `vehicle_discovery/all_systems_20260215_165055.json`
- `vehicle_discovery/all_systems_summary_20260215_165055.txt`
- `vehicle_discovery/discovered_dids_20260215_164211.json`
- `vehicle_discovery/summary_20260215_164211.txt`

### Documentation
- `COMPLETE_DID_DISCOVERY.md` - Full UDS discovery report
- `FORSCAN_MODULE_DISCOVERY.md` - FORScan module analysis
- `DISCOVERY_SUMMARY.md` - This file
- `TRANSMISSION_DATA_DISCOVERY.md` - Transmission DID details

### Scripts
- `working_discovery_scanner.py` - Proven DID scanner
- `scan_all_systems.py` - Multi-system scanner
- `scan_transit_dids.py` - Transit-style range scanner
- `read_transmission_live.py` - Live transmission monitor
- `test_basic_communication.py` - Communication test

### Knowledge Base
- `knowledge_base/Ford_Escape_2008_profile.yaml` - Updated with all findings
- `knowledge_base/Ford_Escape_2008_technical.dat` - Updated with DIDs

---

## Conclusion

The 2008 Ford Escape has limited diagnostic capabilities via standard protocols compared to newer vehicles. We successfully discovered 4 accessible DIDs and confirmed 13 modules are accessible via FORScan.

**For AI Agent Development:**
- Use standard OBD-II/UDS for basic diagnostics
- Integrate with FORScan for advanced features
- Document limitations clearly
- Provide clear guidance on when each tool is needed

**Next Steps:**
1. Decode the unknown ABS parameters
2. Complete scanning of remaining DID ranges
3. Create comprehensive monitoring tools
4. Document FORScan integration procedures
