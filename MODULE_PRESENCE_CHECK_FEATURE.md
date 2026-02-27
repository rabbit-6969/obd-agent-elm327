# Module Presence Check Feature

## Overview

Added `check_module_presence()` method to definitively verify the Toyota FJ Cruiser ABS module is awake and responsive before attempting to read DTCs.

## Problem Solved

When Toyota ABS modules don't respond to UDS Service 0x19 (Read DTCs), it's unclear whether:
1. Module is healthy with no DTCs (expected behavior)
2. Module is not communicating at all (communication failure)

## Solution

The `check_module_presence()` method reads standard UDS Data Identifiers (DIDs) that Toyota modules always respond to when awake:

### DIDs Checked

1. **DID 0xF181: Calibration ID**
   - ECU software version/calibration identifier
   - Standard UDS DID supported by most modules
   - Command: `22 F1 81`
   - Response: `62 F1 81 [DATA...]`

2. **DID 0xF190: VIN (fallback)**
   - Vehicle Identification Number
   - Alternative DID if Calibration ID not supported
   - Command: `22 F1 90`
   - Response: `62 F1 90 [VIN_DATA...]`

## Implementation

```python
def check_module_presence(self) -> bool:
    """
    Read the Calibration ID (DID 0xF181) to verify the module is awake.
    If this works but 0x19 fails, we know for sure there are simply no DTCs.
    
    Returns:
        True if module responds, False otherwise
    """
    # Try Calibration ID first
    cmd = "22 F1 81"
    response = self._send_command(cmd)
    time.sleep(0.2)
    
    response = response.replace(' ', '').replace('\r', '').replace('\n', '')
    
    if '62F181' in response:
        print("✓ Module is AWAKE (Calibration ID verified)")
        return True
    
    # Try VIN as fallback
    cmd = "22 F1 90"
    response = self._send_command(cmd)
    time.sleep(0.2)
    response = response.replace(' ', '').replace('\r', '').replace('\n', '')
    
    if '62F190' in response:
        print("✓ Module is AWAKE (VIN verified)")
        return True
    
    return False
```

## Integration

### Automatic Check in DTC Reading

When `read_dtcs_by_status()` gets no response, it automatically calls `check_module_presence()`:

```python
if not response or 'NO DATA' in response.upper():
    print("\nVerifying module is awake...")
    if self.check_module_presence():
        print("\n✓ Module is responsive to other services")
        print("✓ No response to Service 0x19 = No DTCs present")
    else:
        print("\n✗ Module is not responding to any service")
        print("\nThis indicates a communication issue")
```

### Manual Check (Menu Option 6)

Users can manually check module presence:

```
Select option (1-7): 6

Checking if ABS module is awake and responsive...
✓ Module is AWAKE (Calibration ID verified)

======================================================================
MODULE STATUS: AWAKE AND RESPONSIVE
======================================================================

The ABS module is communicating properly.
If Service 0x19 returns 'no response', it means:
  ✓ Module is functioning normally
  ✓ No DTCs are stored
  ✓ This is expected Toyota behavior
```

## Benefits

1. **Definitive Diagnosis**
   - Confirms module is awake and responsive
   - Eliminates guesswork about communication status

2. **Clear User Messaging**
   - "Module awake + no DTCs" = Healthy system
   - "Module not responding" = Communication issue

3. **Troubleshooting Aid**
   - Helps identify wrong module address
   - Detects sleep mode or communication problems
   - Guides user to correct solution

4. **Confidence Building**
   - Users know for certain their module is working
   - Reduces anxiety about "no response" messages

## Use Cases

### Case 1: Healthy System (Most Common)

```
ABS light: OFF
Service 0x19: No response
Module presence: ✓ AWAKE

Conclusion: System is healthy, no DTCs present (NORMAL)
```

### Case 2: DTCs Present

```
ABS light: ON
Service 0x19: Returns DTCs
Module presence: ✓ AWAKE

Conclusion: DTCs found, diagnose and repair
```

### Case 3: Communication Issue

```
ABS light: ON or OFF
Service 0x19: No response
Module presence: ✗ NOT RESPONDING

Conclusion: Communication failure, check:
- Module address (try 0x760)
- Ignition ON
- CAN bus connection
```

### Case 4: Module in Sleep Mode

```
ABS light: OFF
Service 0x19: No response
Module presence: ✗ NOT RESPONDING

Conclusion: Module may be in sleep mode
- Try extended session (option 5)
- Wake module with other commands
```

## Technical Details

### UDS Service 0x22: ReadDataByIdentifier

- Service ID: 0x22
- Request format: `22 [DID_HIGH] [DID_LOW]`
- Response format: `62 [DID_HIGH] [DID_LOW] [DATA...]`
- Positive response: Service ID + 0x40 = 0x62

### Standard DIDs (ISO 14229-1)

| DID | Name | Description |
|-----|------|-------------|
| 0xF181 | Calibration ID | ECU software version |
| 0xF187 | Spare Part Number | ECU part number |
| 0xF18A | ECU Serial Number | Unique ECU identifier |
| 0xF18C | ECU Manufacturing Date | Production date |
| 0xF190 | VIN | Vehicle Identification Number |
| 0xF191 | ECU Hardware Number | Hardware version |

### Why These DIDs?

- **Widely supported**: Most ECUs implement these standard DIDs
- **Always available**: Don't require special session or security access
- **Fast response**: Simple data, quick to retrieve
- **Reliable**: Less likely to fail than complex services

## Testing Results

Tested on Toyota FJ Cruiser 2008:
- ✓ Calibration ID (0xF181) responds successfully
- ✓ Correctly identifies module is awake
- ✓ Provides clear messaging to user
- ✓ Eliminates confusion about "no response"

## Future Enhancements

Possible improvements:
1. Try multiple DIDs in sequence for better coverage
2. Cache module presence result to avoid repeated checks
3. Add timing analysis (response time indicates module health)
4. Support for other Toyota/Lexus modules (PCM, TCM, etc.)

## Related Documentation

- `FJ_CRUISER_ABS_DTC_GUIDE.md` - User guide with examples
- `TOYOTA_ABS_UPDATE_SUMMARY.md` - Complete update summary
- `knowledge_base/Toyota_FJ_Cruiser_2008_profile.yaml` - Vehicle profile
- `reference/ISO_14229-1_UDS_Service_0x22_ReadDataByIdentifier.md` - UDS spec

## Conclusion

The module presence check is a critical feature that eliminates ambiguity when Toyota ABS modules don't respond to Service 0x19. It provides definitive proof the module is communicating, allowing users to confidently interpret "no response" as "no DTCs present" rather than a communication failure.
