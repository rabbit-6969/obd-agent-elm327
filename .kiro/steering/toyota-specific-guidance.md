---
inclusion: fileMatch
fileMatchPattern: '*Toyota*|*Lexus*|*Scion*'
---

# Toyota/Lexus/Scion Specific Diagnostic Guidance

This steering file is automatically included when working with Toyota, Lexus, or Scion vehicles.

## Critical Toyota Behaviors

### "No Response" is Often Normal

**Toyota 2007-2010 ABS Modules** (FJ Cruiser, 4Runner, Tacoma, Tundra, Sequoia, Lexus GX470):
- **Do NOT respond to UDS Service 0x19 when no DTCs are stored**
- This is INTENTIONAL design, not a communication failure
- "No response" when ABS light is OFF = system is healthy (NORMAL)
- "No response" when ABS light is ON = try workarounds or module in fault mode

### Response ID Calculation
- Response ID = Request ID + 0x08
- Example: Request 0x7B0 → Response 0x7B8

### Protocol Versions
- **Newer models (2010+)**: ISO-14229 (UDS)
- **Older models (pre-2010)**: ISO-14230 (KWP2000)
- **Mixed implementations**: Even newer models may have some modules using ISO-14230
- Always try both protocols when discovering modules

## Common CAN Addresses

Based on documented Toyota vehicles:

### Scion FR-S / Toyota 86 / Subaru BRZ (2012-2016)
- 0x727/0x72F: Transmission
- 0x750/0x758: Main Body
- 0x780/0x788: Airbag
- 0x781/0x789: Precrash
- 0x790/0x798: Distance/Radar
- 0x791/0x799: Precrash2
- 0x7A1/0x7A9: Steering Assist/Power Steering
- 0x7A2/0x7AA: Park Assist/APGS
- 0x7B0/0x7B8: ABS Brake
- 0x7C0/0x7C8: Instrument Cluster
- 0x7C4/0x7CC: Air Conditioner
- 0x7D0/0x7D8: Navigation
- 0x7E0/0x7E8: Engine Control (ECM/ECT)
- 0x7E1/0x7E9: Transmission (Auto only)
- 0x7E2/0x7EA: Hybrid System/Cruise Control

### FJ Cruiser / 4Runner (2007-2010)
- 0x7B0/0x7B8: ABS Brake (may also be 0x750/0x758 on some models)
- 0x7E0/0x7E8: Engine Control (PCM)

**Note**: Some Toyota models use 0x750/0x758 for ABS instead of 0x7B0/0x7B8. Always scan to confirm.

## ABS Module Diagnostics

### When ABS Module Doesn't Respond

**If ABS warning light is OFF**:
- Module is likely healthy and intentionally not responding
- This is NORMAL Toyota behavior
- No action needed

**If ABS warning light is ON** (or intermittent):
1. Try module presence check using alternative DIDs:
   - 0xF181 (Calibration ID)
   - 0xF190 (VIN)
   - 0xF18C (Serial Number)
2. Try entering extended diagnostic session: `10 03`
3. Try reading DTC count: `19 01 FF`
4. Try all three Tester Present variants: `3E 01`, `3E 00`, `3E`

### Intermittent ABS Lights

**Symptoms**: ABS light comes on and disappears, parking brake light on (with brake released), VSC OFF light on

**Most Common Cause**: Wheel speed sensor issue
- Front sensors more common than rear
- Connector corrosion or damaged wiring
- Sensor itself failing

**Diagnostic Approach**:
1. Use live monitoring to catch fault when it occurs
2. Monitor DID 0x213D (ABS warning light status)
3. Monitor DID 0x215F (individual wheel ABS status)
4. Log data to identify which wheel sensor is failing

## Extended Diagnostic Session

Some Toyota modules require extended session for full access:

```
Request:  10 03
Response: 50 03
```

After entering extended session, you can:
- Read additional DIDs
- Access more diagnostic services
- Perform actuator tests

Session typically times out after 5 seconds of inactivity. Send Tester Present (`3E 00`) to keep alive.

## DTC Reading Strategies

### Primary Method: Service 0x19 Sub-function 0x02
```
Request:  19 02 FF
Response: 59 02 [DTCs...]
```

### Alternative Method: Service 0x19 Sub-function 0x01 (DTC Count)
More reliable on some Toyota modules:
```
Request:  19 01 FF
Response: 59 01 [count]
```

### Fallback: Check Module Presence First
If no response to Service 0x19:
1. Verify module is awake (try DIDs)
2. Enter extended session
3. Try DTC count first
4. Then try reading DTCs

## Common Toyota DIDs

- 0xF190: VIN (most reliable)
- 0xF181: Calibration ID
- 0xF18C: ECU Serial Number
- 0xF187: Spare Part Number
- 0xF191: ECU Hardware Number
- 0x213D: ABS warning light status (4Runner/FJ Cruiser)
- 0x215F: Individual wheel ABS status (4Runner/FJ Cruiser)

## Troubleshooting "No Response"

When Toyota module doesn't respond:

1. **Check if it's normal behavior** (ABS with no faults)
2. **Try different CAN address** (0x750 vs 0x7B0 for ABS)
3. **Try all Tester Present variants** (`3E 01`, `3E 00`, `3E`)
4. **Check if module is on secondary CAN bus** (ELM327 cannot reach)
5. **Verify ELM327 adapter quality** (cheap clones fail to switch CAN IDs properly)
6. **Try extended diagnostic session** (`10 03`)

## Platform Sharing

Toyota shares platforms across models:
- **FJ Cruiser = 4Runner** (J120/J150 platform, identical ABS hardware)
- **Lexus GX470 = 4Runner** (luxury version, same ABS system)
- **Scion FR-S = Toyota 86 = Subaru BRZ** (same platform, same modules)

When you discover something on one model, document it for related models too.

## Documentation References

When working with Toyota vehicles, check for official repair manual links in the vehicle profile. Example:
- FJ Cruiser: https://www.purefjcruiser.com/docs/2007%20Toyota%20FJ%20Cruiser%20Repair%20Manual/

Look for these sections:
- Brake System (BR)
- CAN Communication System (BE)
- Speed Sensors (SP)
- ABS/VSC/TRAC System (AB)
