---
inclusion: fileMatch
fileMatchPattern: '*Ford*|*Lincoln*|*Mercury*'
---

# Ford/Lincoln/Mercury Specific Diagnostic Guidance

This steering file is automatically included when working with Ford, Lincoln, or Mercury vehicles.

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
- 0x760/0x768: ABS Module
- 0x726/0x72E: Instrument Cluster
- 0x737/0x73F: Body Control Module (BCM)

### Ford Transit (documented)
- Similar addressing to Escape
- May have additional modules for commercial features

**Note**: Always scan to confirm addresses for specific model/year.

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
- **Ford Escape = Mazda Tribute = Mercury Mariner**
- **Ford Focus = Mazda 3** (some years)
- **Lincoln models** often share with Ford (different trim)

Document findings across related models.

## Documentation

Check vehicle profiles for:
- Complete DID lists
- Module addresses
- Known issues
- Repair procedures

Ford vehicles typically have extensive documentation in knowledge base.
