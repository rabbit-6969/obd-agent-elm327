# OBD-II Voltage Detection Enhancement

## Overview

Updated vehicle detection to properly check both ECU voltage and 5V reference signals, as the OBD-II port reads voltage from the vehicle's ECU through the protocol rather than providing direct 12V power from the port.

## What Changed

### Previous Behavior
- Only checked single "adapter voltage"
- Assumed 12V would indicate vehicle presence
- Didn't distinguish between different voltage sources

### New Behavior
- Checks **ECU Voltage** (from OBD protocol read)
- Checks **5V Reference** (adapter diagnostics)
- Provides clear distinction between voltage types
- Better troubleshooting information

## Vehicle Detection Display

### Before
```
Adapter Status:
    Voltage: 12.5V
    Power: ✓ Adapter powered
```

### After
```
Voltage Readings:
    ECU Voltage: 12.5V
    5V Reference: 5.0V

Power Status:
    Power: ✓ Valid voltage detected
```

## OBD-II Voltage Reference

### ECU Voltage
- **Source**: Vehicle ECU through OBD protocol
- **Expected**: 9-16V (typically 12V)
- **Threshold**: > 2.0V for valid detection
- **Command**: `AT RV` (Read Voltage)

### 5V Reference
- **Source**: Adapter internal 5V reference
- **Expected**: ~5.0V
- **Threshold**: > 1.0V for valid detection
- **Command**: `AT CV` (5V Reference)
- **Note**: May not be available on all adapters

## Implementation

### New Method: `get_5v_reference()`
```python
ref_5v = adapter.get_5v_reference()
# Returns float (e.g., 5.0) or None
```

### Updated Method: `verify_vehicle_connection()`
Now returns:
```python
{
    'connected': bool,
    'ecu_voltage': float or None,
    'ref_5v': float or None,
    'has_voltage': bool,
    'protocol_detected': bool,
    'protocol': str or None,
    'message': str
}
```

## Troubleshooting Examples

### Scenario 1: Vehicle Properly Connected
```
Voltage Readings:
    ECU Voltage: 12.5V
    5V Reference: 5.0V

Power Status:
    Power: ✓ Valid voltage detected

Vehicle Communication:
    Protocol: Detected
    Vehicle: Responding

    ✓ Vehicle is properly connected
```

### Scenario 2: ECU Power Present but 5V Not Available
```
Voltage Readings:
    ECU Voltage: 12.4V
    5V Reference: Not available

Power Status:
    Power: ✓ Valid voltage detected
```
Status: Vehicle is powered ✓

### Scenario 3: No ECU Voltage, 5V Reference Available
```
Voltage Readings:
    ECU Voltage: Unable to read
    5V Reference: 5.0V

Power Status:
    Power: ✗ No/Low voltage
```
Status: Adapter has power but ECU voltage not detected
→ Check OBD-II connection to vehicle

### Scenario 4: No Voltages Detected
```
Voltage Readings:
    ECU Voltage: Unable to read
    5V Reference: Not available

Power Status:
    Power: ✗ No/Low voltage

✗ No voltage detected from vehicle. Check OBD-II connection and vehicle power.
```
Status: No power detected
→ Check vehicle ignition, battery, and port connection

## Usage

### From Menu
Select option **3: Detect Vehicle** to see:
- Both voltage readings
- Power status
- Communication status
- Clear diagnostic message

### Programmatic Usage
```python
# Get individual readings
ecu_voltage = adapter.get_voltage()      # Returns float or None
ref_5v = adapter.get_5v_reference()      # Returns float or None

# Get complete verification
result = adapter.verify_vehicle_connection()
if result['has_voltage']:
    print(f"ECU: {result['ecu_voltage']:.1f}V, 5V Ref: {result['ref_5v']}")
    if result['connected']:
        print("Vehicle responding!")
```

## Voltage Interpretation

### Valid Vehicle Connection
- ECU Voltage: 8V - 16V (typically 12-13V)
- 5V Reference: 4.5V - 5.5V (if available)

### Weak Connection
- ECU Voltage: 2V - 8V
- Action: Check OBD-II port connections, may work but unreliable

### No Connection
- ECU Voltage: < 2V or unable to read
- 5V Reference: < 1V or not available
- Action: Check vehicle power, battery, and OBD-II port

## Technical Details

### OBD-II Port Pins
- **Pin 4**: Chassis Ground
- **Pin 16**: Battery Power (12V) - Optional on some vehicles
- **Pin 6, 14**: CAN High/Low
- **Pins 3, 11**: K-line/L-line (for KWP)

### Adapter Commands
- `AT RV` - Reports voltage as read from OBD protocol
- `AT CV` - Reports internal 5V reference voltage (ELM327 specific)
- `AT DP` - Reports detected protocol

## Benefits

✅ **More Accurate** - Distinguishes between ECU and reference voltages  
✅ **Better Diagnostics** - Clearer indication of connection status  
✅ **Improved Troubleshooting** - Separate readings help identify issues  
✅ **More Reliable** - Checks multiple indicators instead of just one  
✅ **Adapter Agnostic** - Works even if 5V reference not available  

## Files Modified

- `elm327_adapter.py`:
  - Added `get_5v_reference()` method
  - Updated `verify_vehicle_connection()` return format
  - Added dual-voltage checking logic

- `main.py`:
  - Updated `verify_vehicle()` display method
  - Shows both ECU voltage and 5V reference
  - Improved voltage status messages

## Compatibility

- ✅ ELM327 adapters with 5V output
- ✅ ELM327 adapters without 5V output (just uses ECU voltage)
- ✅ All OBD-II vehicle types
- ✅ Backward compatible with existing code

## Notes

- If adapter doesn't support `AT CV`, 5V reference will show "Not available"
- Vehicle must be in RUN position for ECU voltage
- ECU voltage reading is through OBD protocol, not direct 12V from port
- Most modern vehicles support this feature
