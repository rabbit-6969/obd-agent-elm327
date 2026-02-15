# FORScan Module Discovery - 2008 Ford Escape

**Date**: February 15, 2026  
**Vehicle**: 2008 Ford Escape (VIN: 1FMCU03Z68KB12969)  
**Tool**: FORScan  
**Adapter**: ELM327 v1.5 on COM3

---

## Summary

FORScan successfully connected to **13 modules** in the vehicle, far more than what we discovered via standard UDS scanning. This confirms that Ford uses proprietary protocols and addressing schemes that require manufacturer-specific tools.

---

## Accessible Modules

### 1. OBD2_PCM - On Board Diagnostic II (PCM)
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Standard OBD-II interface to PCM

### 2. PCM - Powertrain Control Module
- **Part Number**: 8L8A-12A650-AEB
- **Calibration**: 8L8A-12A650-AEB (latest: 8U7A-12A650-XA)
- **Strategy**: QIEF1A6
- **Hardware**: LBO-C15
- **Copyright**: Ford Motor Co. 2006
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Main engine control module

### 3. OCS - Occupant Classification System Module
- **Part Number**: 8L84-14B422-AF
- **Calibration**: 8L84-14B422-AF
- **Strategy**: 8L84-14D224-AB
- **Software**: v15 2006-10-30
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Airbag seat sensor system

### 4. ABS - Antilock Braking System
- **Part Number**: 8L84-2C219-CH
- **Calibration**: 8L84-2C219-CH
- **Strategy**: 8L84-2D053-CF
- **Software**: 2006-12-11
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: We discovered DIDs 0x0200 and 0x0202 via UDS

### 5. RCM - Restraint Control Module
- **Part Number**: 8L84-14B321-AH
- **Calibration**: 8L84-14B321-AH
- **Strategy**: 8L84-14C028-AB
- **Software**: v9 2006-09-06
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Airbag control module

### 6. PSCM - Power Steering Control Module
- **Part Number**: 8L84-3F964-BA
- **Calibration**: 8L84-3F964-BA
- **Strategy**: AL84-14D003-AE
- **Software**: 2013-02-15
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Electric power steering control

### 7. IC - Instrument Cluster
- **Part Number**: 8L8T-10849-HA
- **Calibration**: 8L8T-10849-HA (latest: 8L8T-10849-KE)
- **Strategy**: 8E6T-14C026-BA
- **Software**: 2007-01-31
- **Odometer**: 325,588.8 km (202,330 miles)
- **Status**: ✓ Accessible
- **DTCs**: B1318-20 (Battery voltage too low - previously set, not current)
- **Notes**: Dashboard instrument panel

### 8. FCIM - Front Controls Interface Module
- **Part Number**: 8L8T-18A802-AK
- **Calibration**: 8L8T-18A802-AK
- **Strategy**: 8L8T-14D017-AF
- **Software**: v1 2007-03-14
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Front panel controls (HVAC, radio buttons)

### 9. FDIM - Front Display Interface Module
- **Part Number**: 8L8T-19C116-AK
- **Calibration**: 8L8T-19C116-AK
- **Strategy**: 8L8T-14D010-AF
- **Software**: v1 2007-03-09
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Front display screen

### 10. SDARS - Satellite Digital Audio Receiver System
- **Part Number**: 8S4T-18C963-AE
- **Calibration**: 8S4T-18C963-AE (latest: 8S4T-18C963-AJ)
- **Strategy**: 8S4T-14C341-AE
- **Software**: 2007-05-21
- **Status**: ✓ Accessible
- **DTCs**: B1032-20 (Satellite antenna short - previously set, not current)
- **Notes**: Sirius/XM satellite radio receiver

### 11. HVAC - Heating Ventilation Air Conditioning
- **Part Number**: 8L84-19980-AJ
- **Calibration**: 8L84-19980-AJ
- **Strategy**: 8L84-14C178-BD
- **Software**: 2007-01-08
- **Status**: ✓ Accessible
- **DTCs**: B1676-20 (Battery voltage out of range - previously set, not current)
- **Notes**: Climate control module - NOT accessible via standard OBD-II

### 12. ACM - Audio Control Module
- **Part Number**: 8L8T-19C107-AM
- **Calibration**: 8L8T-19C107-AM
- **Strategy**: 8L8T-14D099-AH
- **Software**: v2 2007-03-08
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Radio/audio system control

### 13. GEM/SJB - Generic Electronic Module / Smart Junction Box
- **Part Number**: 7L1T-14B476-CH
- **Calibration**: 7L1T-14B476-CH (latest: 7L1T-14B476-CL)
- **Strategy**: 7L1T-14C184-AG
- **Software**: v8 2006-10-27
- **Status**: ✓ Accessible
- **DTCs**: None
- **Notes**: Body control module, fuse box controller

---

## Key Findings

### 1. FORScan vs Standard UDS
- **FORScan**: 13 modules accessible
- **Standard UDS**: Only 2 modules partially accessible (PCM, ABS)
- **Conclusion**: Ford uses proprietary protocols that require manufacturer tools

### 2. Module Addressing
FORScan uses different addressing than standard OBD-II:
- Standard OBD-II uses addresses like 0x7E0 (PCM), 0x760 (ABS)
- FORScan likely uses extended addressing or different CAN IDs
- Some modules are on MS-CAN (125 kbaud) not HS-CAN (500 kbaud)

### 3. Historical DTCs
Three modules have previously set DTCs (now cleared):
- **IC**: B1318-20 (Battery voltage too low)
- **SDARS**: B1032-20 (Satellite antenna short)
- **HVAC**: B1676-20 (Battery voltage out of range)

All are voltage-related, likely from when battery was low (11.4V measured).

### 4. Software Versions
Most modules have software from 2006-2007 timeframe:
- **Exception**: PSCM has 2013 software (likely updated/replaced)
- Several modules have newer calibrations available

### 5. Odometer Reading
- **Current**: 325,588.8 km (202,330 miles)
- **Source**: Instrument Cluster module
- This is the official vehicle mileage

---

## Comparison: FORScan vs Our UDS Discovery

| Module | FORScan Access | Our UDS Access | DIDs Found |
|--------|----------------|----------------|------------|
| PCM | ✓ Full | ✓ Partial | 2 (0x0100, 0x0101) |
| ABS | ✓ Full | ✓ Partial | 2 (0x0200, 0x0202) |
| HVAC | ✓ Full | ✗ None | 0 |
| IC | ✓ Full | ✗ None | 0 |
| RCM | ✓ Full | ✗ None | 0 |
| PSCM | ✓ Full | ✗ None | 0 |
| OCS | ✓ Full | ✗ None | 0 |
| FCIM | ✓ Full | ✗ None | 0 |
| FDIM | ✓ Full | ✗ None | 0 |
| SDARS | ✓ Full | ✗ None | 0 |
| ACM | ✓ Full | ✗ None | 0 |
| GEM/SJB | ✓ Full | ✗ None | 0 |

---

## Why FORScan Can Access More Modules

### 1. Proprietary Protocol Knowledge
FORScan has reverse-engineered Ford's proprietary diagnostic protocols:
- Extended addressing schemes
- Custom service IDs
- Manufacturer-specific message formats
- Security/authentication sequences

### 2. Multi-Bus Access
FORScan can communicate on both:
- **HS-CAN** (500 kbaud): PCM, ABS, IC
- **MS-CAN** (125 kbaud): HVAC, BCM, FCIM, FDIM, ACM

Standard OBD-II adapters typically only access HS-CAN.

### 3. Module-Specific Commands
Each module may require:
- Specific initialization sequences
- Custom diagnostic session modes
- Module-specific service IDs
- Timing requirements

### 4. Database of Module Definitions
FORScan has a database of:
- Module addresses for each vehicle
- Supported services per module
- DID definitions and formulas
- DTC descriptions

---

## Implications for Our Project

### What We Can Do with Standard Tools
- Read basic engine parameters (PCM via OBD-II)
- Read transmission temp/pressure (PCM via UDS DIDs 0x0100, 0x0101)
- Read some ABS parameters (via UDS DIDs 0x0200, 0x0202)
- Read/clear engine DTCs (Mode 03/04)

### What Requires FORScan
- Access HVAC module
- Access body control modules (GEM/SJB, FCIM, FDIM)
- Access safety modules (RCM, OCS)
- Read module part numbers and software versions
- Perform module programming/configuration
- Access advanced diagnostic functions

### Our AI Agent Strategy
1. **Use standard OBD-II/UDS** for basic diagnostics
2. **Integrate with FORScan** for advanced diagnostics:
   - Launch FORScan for specific tasks
   - Parse FORScan logs/output
   - Guide user through FORScan procedures
3. **Document limitations** clearly to users
4. **Provide FORScan instructions** when needed

---

## Next Steps

### 1. Document FORScan Integration
Create guides for:
- When to use FORScan vs standard tools
- How to capture FORScan data
- Parsing FORScan output files
- Common FORScan procedures

### 2. Complete UDS DID Discovery
Continue scanning for more DIDs in:
- Remaining PCM ranges (0x0102-0x01FF)
- Remaining ABS ranges (0x0201, 0x0203-0x02FF)
- Other system ranges (0x0300+)

### 3. Decode Discovered DIDs
Figure out what our 4 DIDs represent:
- 0x0100: Transmission temp (✓ known)
- 0x0101: Transmission pressure (needs calibration)
- 0x0200: ABS parameter (unknown)
- 0x0202: ABS parameter (unknown)

### 4. Update Knowledge Base
Add FORScan module information to:
- `knowledge_base/Ford_Escape_2008_profile.yaml`
- `knowledge_base/Ford_Escape_2008_technical.dat`

---

## Connection Log Analysis

The log shows FORScan's connection process:
1. Checked Bluetooth adapter (failed)
2. Checked FTDI adapter (cancelled)
3. Connected to COM3 successfully
4. First two connection attempts failed (vehicle not ready)
5. Third attempt succeeded
6. Discovered all 13 modules
7. Read DTCs from all modules

This confirms the communication pattern we observed:
- Vehicle needs time to initialize after adapter connection
- Multiple connection attempts may be needed
- Once connected, all modules respond reliably

---

## Adapter Compatibility Note

FORScan warned: "The adapter is NOT recommended for this car - some FORScan functions may not be available or not work properly"

This is because:
- ELM327 v1.5 is a generic adapter
- FORScan recommends OBDLink or VLinker adapters
- Some advanced functions may not work
- Basic diagnostics work fine (as we've seen)

For our AI agent:
- Standard diagnostics work with ELM327
- Advanced features may require better adapter
- Document adapter requirements clearly
