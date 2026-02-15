# ISO 14229-1 UDS Service 0x2F: InputOutputControlByIdentifier

**Source:** ISO 14229-1:2013(E) Section 12.2 (pages 245-258)  
**Service ID:** 0x2F  
**Response ID:** 0x6F (0x2F + 0x40)

---

## Service Description

The InputOutputControlByIdentifier service is used to substitute a value for an input signal, internal server function, and/or force control to a value for an output (actuator) of an electronic system.

**Use Cases:**
- Control actuators (solenoids, relays, motors, valves)
- Substitute input values for testing
- Override normal ECU control strategy
- Test outputs directly (e.g., turn on fuel pump, cycle HVAC door, activate shift solenoid)

**Key Difference from RoutineControl:**
- Service 0x2F: Simple, static control (e.g., "set solenoid to 50%")
- Service 0x31: Complex sequences (e.g., "run transmission self-test")

---

## Request Message Format

```
2F [DID_high] [DID_low] [controlParameter] [controlState...] [controlMask...]
```

### Control Parameters (inputOutputControlParameter)

| Value | Name | Description |
|-------|------|-------------|
| 0x00 | returnControlToECU | Return control to ECU (stop override) |
| 0x01 | resetToDefault | Reset to default state |
| 0x02 | freezeCurrentState | Freeze at current value |
| 0x03 | shortTermAdjustment | Set to specific value (most common) |

### Example: Control HVAC Blend Door (DID 0x9B00) to 50%

```
Request:  2F 9B 00 03 32
Response: 6F 9B 00 03 32
```

**Breakdown:**
- `2F` = Service ID
- `9B 00` = DID (HVAC blend door position)
- `03` = shortTermAdjustment
- `32` = 50 decimal = 50%

### Example: Return Control to ECU

```
Request:  2F 9B 00 00
Response: 6F 9B 00 00
```

---

## Positive Response Format

```
6F [DID_high] [DID_low] [controlParameter] [controlState...]
```

The response echoes the DID and control parameter, and may include feedback data showing the actual state achieved.

---

## Control Enable Mask (Optional)

For DIDs that control multiple parameters (bit-mapped or packeted), a controlEnableMask may be required:

```
2F [DID] [controlParam] [controlState] [controlMask]
```

- Each bit in controlMask corresponds to a parameter in the DID
- Bit = 1: Control this parameter
- Bit = 0: Don't control this parameter

---

## Negative Response Codes

| NRC | Mnemonic | Description |
|-----|----------|-------------|
| 0x13 | IMLOIF | incorrectMessageLengthOrInvalidFormat |
| 0x22 | CNC | conditionsNotCorrect - Conditions not met (e.g., vehicle moving) |
| 0x31 | ROOR | requestOutOfRange - DID not supported or invalid control value |
| 0x33 | SAD | securityAccessDenied - DID requires security access |

---

## Usage for Transmission Diagnostics

### Control Shift Solenoid

```python
# Assuming DID 0x0103 controls shift solenoid A
# Activate solenoid to 100%
send: "2F 0103 03 FF"
receive: "6F 0103 03 FF"  # Success

# Return control to ECU
send: "2F 0103 00"
receive: "6F 0103 00"
```

### Test Sequence

1. Read current state: `22 0103` → get current value
2. Take control: `2F 0103 03 [value]` → set to test value
3. Observe behavior (listen, measure, etc.)
4. Return control: `2F 0103 00` → ECU resumes normal operation

---

## Important Notes

- **Always return control to ECU** when done testing
- Some DIDs require extended diagnostic session (Service 0x10)
- Some DIDs require security access (Service 0x27)
- Vehicle conditions may prevent control (e.g., engine must be running, vehicle stationary)
- The controlState format must match the dataRecord format from Service 0x22

---

## Safety Warnings

⚠️ **CAUTION:** This service directly controls vehicle actuators
- Can affect vehicle operation and safety
- Always ensure safe conditions before testing
- Never test while vehicle is in motion
- Always return control to ECU when finished
- Some actuations may damage components if misused

---

## References

- ISO 14229-1:2013(E) Section 12.2 (pages 245-258)
- Annex E.1: InputOutputControlParameter definitions (page 374)
- Service 0x22: ReadDataByIdentifier (to read current state)
- Service 0x31: RoutineControl (for complex control sequences)
