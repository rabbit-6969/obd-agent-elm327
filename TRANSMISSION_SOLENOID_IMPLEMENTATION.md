# Transmission Solenoid State Reading - Implementation Guide

## Overview

This guide explains how to implement transmission solenoid state reading for the 2008 Ford Escape using your HS-CAN capable adapter (ELM327 v1.5 with manual switch).

## Hardware Requirements

### Your Adapter
- ELM327 v1.5 compatible with HS-CAN/MS-CAN manual switch
- Works with FORScan (confirmed capability)
- Manual switch for HS-CAN/MS-CAN selection

### Switch Position
- **HS-CAN**: For TCM, PCM, ABS, and most powertrain modules (500 Kbps)
- **MS-CAN**: For BCM, HVAC, and body control modules (125 Kbps)

For transmission solenoid reading: **Switch must be in HS-CAN position**

## Software Requirements

```bash
pip install python-can
pip install can-isotp
pip install pyserial
```

## Implementation Approach

### Phase 1: DID Discovery (One-Time)

Since Ford doesn't publish their proprietary DIDs, we need to discover them:

1. **Enter Extended Diagnostic Session**
   - UDS Service 0x10 0x03
   - Required to access advanced DIDs

2. **Scan DID Ranges**
   - 0x1000-0x1FFF: Transmission parameters
   - 0x2000-0x2FFF: Actuator states
   - 0xF000-0xFFFF: System information

3. **Identify Solenoid DIDs**
   - Look for DIDs that return data when transmission is active
   - Compare data at different gear positions
   - Validate with FORScan if possible

### Phase 2: Data Reading

Once DIDs are discovered:

1. **Connect to TCM**
   - CAN ID 0x7E1 (request)
   - CAN ID 0x7E9 (response)
   - ISO-TP protocol

2. **Enter Extended Session**
   - Required for most solenoid DIDs

3. **Read Solenoid States**
   - Use UDS Service 0x22 (ReadDataByIdentifier)
   - Parse response bytes

4. **Keep Session Alive**
   - Send TesterPresent (0x3E) every 2-3 seconds

### Phase 3: Data Parsing

CD4E transmission solenoids:
- **SS1** (Shift Solenoid 1): Controls 1-2 and 3-4 shifts
- **SS2** (Shift Solenoid 2): Controls 2-3 shifts
- **SS3** (Shift Solenoid 3): Controls torque converter lockup
- **EPC** (Electronic Pressure Control): Line pressure control

Data format (typical):
- Bit-packed byte(s) representing ON/OFF states
- May include duty cycle percentages for PWM solenoids

## User Interaction for Switch Position

Since your adapter has a manual switch, the implementation must:

1. **Prompt user before connecting**
   ```
   ⚠ IMPORTANT: Set adapter switch to HS-CAN position
   Press Enter when ready...
   ```

2. **Verify connection**
   - Attempt to communicate with TCM
   - If no response, remind user to check switch

3. **For MS-CAN modules** (future)
   ```
   ⚠ Switching to MS-CAN modules
   Please flip adapter switch to MS-CAN position
   Press Enter when ready...
   ```

## Example Workflow

```python
# 1. User starts script
python read_transmission_solenoids.py

# 2. Script prompts for switch position
⚠ IMPORTANT: Ensure HS-CAN switch is in HS position!
Press Enter when switch is set to HS-CAN...

# 3. Script connects and enters extended session
→ Entering extended diagnostic session...
✓ Extended session active

# 4. Option A: Discover DIDs (first time)
Do you want to discover solenoid DIDs? (y/n): y
Scanning range 0x1000 - 0x1100...
  ✓ Found DID 0x1034: 0a3f
  ✓ Found DID 0x1056: 1200ff
...

# 5. Option B: Read known DIDs
Reading Solenoid Commanded State (DID 0x1034)...
  ✓ Data: 0a3f
  
Shift Solenoid 1 (SS1): ON
Shift Solenoid 2 (SS2): OFF
Shift Solenoid 3 (SS3): ON
EPC Solenoid: ON (Duty: 62%)
```

## Integration with AI Agent

The AI agent should:

1. **Detect adapter type**
   - Check if adapter has HS/MS-CAN capability
   - Determine if switch is manual or automatic

2. **Guide user through switch changes**
   - Provide clear instructions
   - Wait for user confirmation
   - Verify communication after switch

3. **Cache discovered DIDs**
   - Save to vehicle profile
   - Reuse for future sessions
   - Update when new DIDs found

4. **Interpret solenoid states**
   - Correlate with current gear
   - Detect stuck solenoids
   - Identify shift issues

## Known DIDs from FORScan Community

These are examples from FORScan forums (may vary by TCM firmware):

| DID | Description | Data Format |
|-----|-------------|-------------|
| 0x1034 | Solenoid commanded state | 2 bytes, bit-packed |
| 0x1056 | Solenoid actual state | 2 bytes, bit-packed |
| 0x1078 | EPC duty cycle | 1 byte, 0-255 (0-100%) |
| 0x109A | Shift in progress | 1 byte, boolean |
| 0x10BC | Current gear | 1 byte, 0-4 |

**Note**: These DIDs are examples and must be verified on your specific vehicle.

## Troubleshooting

### No Response from TCM

1. **Check switch position**
   - Must be in HS-CAN for TCM
   - LED indicator (if present) should show HS mode

2. **Verify ignition**
   - Ignition must be ON
   - Engine can be off or running

3. **Check CAN bus**
   - Ensure adapter is fully inserted
   - Check for other devices on bus

### Negative Response Codes

| NRC | Meaning | Solution |
|-----|---------|----------|
| 0x11 | Service not supported | DID not available in current session |
| 0x22 | Conditions not correct | Enter extended session first |
| 0x31 | Request out of range | DID doesn't exist |
| 0x33 | Security access denied | Security unlock required (rare) |

### Session Timeout

- Extended session times out after ~5 seconds of inactivity
- Send TesterPresent (0x3E 0x00) every 2-3 seconds
- Re-enter session if timeout occurs

## Next Steps

1. **Run DID discovery** on your vehicle
2. **Document found DIDs** in vehicle profile
3. **Validate with FORScan** if possible
4. **Implement parsing** for discovered data format
5. **Integrate into AI agent** toolkit

## Safety Considerations

- **Read-only operations**: This implementation only reads data, doesn't control solenoids
- **No vehicle movement**: Perform diagnostics with vehicle stationary
- **Park/Neutral**: Ensure transmission is in Park or Neutral
- **Battery voltage**: Maintain adequate voltage during diagnostics

## References

- ISO 14229-1 (UDS specification)
- ISO 15765-2 (ISO-TP over CAN)
- FORScan forums and documentation
- Ford workshop manuals (if available)
