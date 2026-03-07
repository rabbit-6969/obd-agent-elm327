---
inclusion: fileMatch
fileMatchPattern: '*Ford*|*Lincoln*|*Mercury*|*Mazda*Tribute*'
---

# Ford/Lincoln/Mercury/Mazda Tribute Specific Diagnostic Guidance

This steering file is automatically included when working with Ford, Lincoln, Mercury, or Mazda Tribute vehicles.

## Important: Mazda Tribute Platform Sharing

The **Mazda Tribute** is badge-engineered from the Ford Escape and shares:
- Identical platform and architecture
- Same CAN bus communication protocols (ISO 15765-4 CAN)
- Same module addresses and diagnostic protocols
- Same UDS/OBD-II implementation

**All Ford Escape diagnostic procedures apply to Mazda Tribute** (especially 2008+ models).

## Ford-Specific Behaviors

### Response Behavior
- Ford modules typically ALWAYS respond, even when healthy
- This is opposite of Toyota behavior
- "No response" usually indicates communication problem, not normal behavior

### Response ID Calculation
- Response ID = Request ID + 0x08
- Example: Request 0x7A0 → Response 0x7A8

### Protocol
- Most Ford vehicles use ISO-14229 (UDS)
- Some older modules may use ISO-14230 (KWP2000)

## Common Ford CAN Addresses

### Ford Escape 2008 (documented)
- 0x7E0/0x7E8: Powertrain Control Module (PCM)
- 0x7E1/0x7E9: Transmission Control Module (TCM)
- 0x7A0/0x7A8: HVAC Module
- 0x760/0x768: ABS Module (CONFIRMED 2026-03-05)
- 0x726/0x72E: Instrument Cluster
- 0x737/0x73F: Body Control Module (BCM)

### Ford Transit (documented)
- Similar addressing to Escape
- May have additional modules for commercial features

**Note**: Always scan to confirm addresses for specific model/year.

## ABS Module Diagnostics (Ford Escape 2008)

### Confirmed Communication Protocol (2026-03-05)

**Address**: 0x760 (request) / 0x768 (response)

**Working Tester Present**: `3E 01`
- Response: `7E` (positive response)
- This confirms module is alive and communicating

### Supported Services

**Service 0x3E (Tester Present)**: SUPPORTED
- Use variant: `3E 01`
- Response: `7E`

**Service 0x22 (Read Data By Identifier)**: PARTIALLY SUPPORTED
- Working DIDs:
  - 0x0200: Returns `62 02 00 00`
  - 0x0202: Returns `62 02 02 00`
- Standard identification DIDs NOT supported (F190, F181, F18C, F187, F191)
  - Returns: `7F 22 31` (request out of range)

### NOT Supported Services

**Service 0x10 (Diagnostic Session Control)**: NOT SUPPORTED
- Command: `10 03`
- Response: `7F 10 12` (sub-function not supported)
- Extended diagnostic session not available

**Service 0x19 (Read DTC Information)**: NOT SUPPORTED
- Command: `19 02 FF`
- Response: `7F 19 11` (service not supported)
- Standard DTC reading not available

**Standard Identification DIDs**: NOT SUPPORTED
- VIN (0xF190): `7F 22 31`
- Calibration ID (0xF181): `7F 22 31`
- Serial Number (0xF18C): `7F 22 31`
- Part Number (0xF187): `7F 22 31`
- Hardware Number (0xF191): `7F 22 31`

### Important Notes

**This is NORMAL behavior for Ford ABS modules**:
- They use manufacturer-specific protocols
- Standard UDS identification services are not implemented
- DTC reading requires Ford-specific tools (FORScan, IDS, FDRS)
- Limited DIDs available in 0x0200-0x02FF range

**When diagnosing Ford ABS**:
1. Use Tester Present (3E 01) to verify module presence
2. Explore DIDs in 0x0200-0x02FF range for parameters
3. Do NOT expect standard UDS services to work
4. Negative responses (7F) are normal, not errors
5. Use FORScan for DTC reading and advanced diagnostics

## Extended Diagnostic Session

Many Ford modules require extended session for full access:

```
Request:  10 03
Response: 50 03
```

After entering extended session:
- Access to additional DIDs
- Ability to perform actuator tests
- Access to manufacturer-specific services

Session timeout: typically 5 seconds. Send Tester Present (`3E 00`) to maintain.

## DTC Reading

### Standard Method: Service 0x03 (OBD-II)
For powertrain DTCs:
```
Request:  03
Response: 43 [count] [DTCs...]
```

### UDS Method: Service 0x19
For all modules:
```
Request:  19 02 FF
Response: 59 02 [DTCs...]
```

## Common Ford DIDs

### Standard Identification DIDs
- 0xF190: VIN
- 0xF181: Calibration ID
- 0xF18C: ECU Serial Number
- 0xF187: Spare Part Number
- 0xF191: ECU Hardware Number

### Ford-Specific DIDs (Escape 2008 documented)
Transmission:
- 0x0100: Transmission fluid temperature
- 0x0110: Transmission output shaft speed
- 0x0120: Torque converter clutch status
- 0x0130: Current gear
- 0x0140: Shift solenoid status

HVAC:
- Various DIDs for blend door position, temperature sensors, etc.

**Always check vehicle profile for complete DID list.**

## Transmission Diagnostics

Ford transmissions are well-documented in the knowledge base:

### Live Data Monitoring
- Fluid temperature
- Output shaft speed
- Current gear
- Solenoid status
- Torque converter status

### Solenoid Testing
Ford allows solenoid actuation tests via UDS Service 0x31 (Routine Control).

**Safety**: Always get user confirmation before actuating solenoids. Vehicle must be:
- In Park
- Engine running
- Parking brake engaged

## HVAC Diagnostics

Ford HVAC modules support:
- DTC reading (Service 0x03 or 0x19)
- Live data (temperature sensors, blend door position)
- Actuator tests (blend door movement)

**Safety**: Blend door actuation is safe but should be confirmed with user.

## Module Discovery

When scanning Ford vehicles:
1. Start with standard range: 0x700 - 0x7DF
2. Try all three Tester Present variants
3. Ford modules usually respond reliably
4. Document which modules respond

## FORScan Compatibility

FORScan is a popular Ford diagnostic tool. When users mention FORScan:
- They may have FORScan data to share
- FORScan uses same UDS protocol
- Can capture FORScan commands for analysis
- Scripts available in `scripts/debug/` for FORScan capture

## Common Issues

### Communication Problems
If Ford module doesn't respond:
1. Verify correct CAN address
2. Try extended diagnostic session
3. Check ELM327 adapter connection
4. Verify vehicle is in accessory or run mode

### DTC Clearing
Ford modules support DTC clearing via:
- Service 0x04 (OBD-II) for powertrain
- Service 0x14 (UDS) for all modules

Always confirm with user before clearing DTCs.

## Platform Sharing

Ford shares platforms across brands:
- **Ford Escape = Mazda Tribute = Mercury Mariner** (2001-2012)
  - Identical CAN bus architecture
  - Same module addresses (PCM: 0x7E0, ABS: 0x760, etc.)
  - Same diagnostic protocols (ISO 15765-4 CAN, UDS)
  - Same DIDs and service support
  - 2008+ models use CAN bus exclusively
- **Ford Focus = Mazda 3** (some years)
- **Lincoln models** often share with Ford (different trim)

**When working with Mazda Tribute**:
- Use Ford Escape procedures and scripts
- Reference Ford Escape knowledge base
- Module addresses are identical
- DID ranges are identical
- All documented Ford Escape findings apply

Document findings across related models.

## Documentation

Check vehicle profiles for:
- Complete DID lists
- Module addresses
- Known issues
- Repair procedures

Ford vehicles typically have extensive documentation in knowledge base.
