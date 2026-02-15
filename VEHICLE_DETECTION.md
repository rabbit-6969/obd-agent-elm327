# Vehicle Detection Feature

## Overview

The diagnostic tool now includes comprehensive vehicle detection that checks if a vehicle is actually connected to the OBD-II port. This helps troubleshoot when the adapter connects but no vehicle is detected.

## What It Checks

The vehicle detection verifies:

1. **Adapter Voltage**
   - Expected: 12V from vehicle battery
   - If voltage < 2V: No power from vehicle
   - Indicates OBD-II connection issue

2. **Vehicle Communication**
   - Tests if vehicle responds to adapter queries
   - Verifies OBD protocol establishment
   - Confirms vehicle ECU communication

3. **Protocol Detection**
   - Identifies which OBD protocol is active
   - Shows adapter-vehicle handshake success

## How to Use

### From the Menu

```
1. Check ELM327 Adapter Settings
2. Test Vehicle Connection
3. Detect Vehicle (check voltage and VIN)  <-- NEW
4. Full HVAC Diagnostics (VIN, DTC codes, module info)
...
```

Select option **3** to run vehicle detection.

### Expected Output

**Scenario 1: Vehicle Properly Connected**
```
===== VEHICLE DETECTION =====

Adapter Status:
    Voltage: 12.5V
    Power: ✓ Adapter powered

Vehicle Communication:
    Protocol: Detected
    Vehicle: Responding

    ✓ Vehicle is properly connected
```

**Scenario 2: No Power from Vehicle**
```
===== VEHICLE DETECTION =====

Adapter Status:
    Voltage: 0.0V
    Power: ✗ No/Low power

Vehicle Communication:
    Protocol: Not detected
    Vehicle: Not responding

    ✗ No power from vehicle. Check OBD-II port and vehicle ignition.
```

**Scenario 3: Adapter Powered but No Vehicle Response**
```
===== VEHICLE DETECTION =====

Adapter Status:
    Voltage: 12.3V
    Power: ✓ Adapter powered

Vehicle Communication:
    Protocol: Not detected
    Vehicle: Not responding

    ⚠ Adapter has power but vehicle not responding. Check CAN bus connection.
```

## Troubleshooting Guide

### ✗ No Power from Vehicle

**Symptoms:**
- Voltage: 0.0V or very low
- Power: ✗ No/Low power

**Solutions:**
1. Ensure vehicle ignition is in RUN position (not OFF)
2. Check OBD-II port connection:
   - Fully insert adapter into port
   - Look for any bent pins
   - Try wiggling adapter gently
3. Check vehicle battery:
   - Turn on dashboard lights to confirm power
   - Battery may be dead
4. Check for blown fuses:
   - Look at OBD-II port fuse in fuse box
   - Replace if blown
5. Different vehicle port:
   - Some vehicles may have alternate ports

### ⚠ Adapter Powered but No Response

**Symptoms:**
- Voltage: 12V+ (power OK)
- Vehicle: Not responding

**Solutions:**
1. Check CAN bus configuration:
   - Verify High CAN vs Low CAN setting
   - Try both modes
2. Vehicle may not support OBD:
   - Some older vehicles or special editions don't have OBD
   - Check vehicle documentation
3. OBD protocol mismatch:
   - Try changing protocol settings
   - Some vehicles use KWP2000 instead of CAN
4. Adapter issue:
   - Try restarting adapter (disconnect and reconnect)
   - Check adapter firmware

### ✓ Vehicle Detected but Diagnostics Fail

**Symptoms:**
- Vehicle is properly connected
- But diagnostics commands fail

**Solutions:**
1. Check CAN bus mode (High/Low):
   - Use option 9 for dual-mode testing
   - Try both HIGH and LOW CAN
2. Vehicle may require special setup:
   - Some modules need specific commands first
   - Try full diagnostics to see detailed results
3. Module not responding:
   - HVAC module may be offline
   - Try basic vehicle diagnostics first

## Related Features

- **Option 2**: Quick vehicle connection test
- **Option 4**: Full HVAC diagnostics (includes VIN read)
- **Option 9**: Test both HIGH and LOW CAN modes

## Technical Details

### `get_voltage()` Method
Returns current voltage reading from adapter in volts.

```python
voltage = adapter.get_voltage()
if voltage is not None:
    print(f"Voltage: {voltage:.1f}V")
```

### `verify_vehicle_connection()` Method
Comprehensive vehicle detection returning status dictionary:

```python
result = adapter.verify_vehicle_connection()
# Returns:
# {
#     'connected': bool,
#     'voltage': float or None,
#     'has_voltage': bool,
#     'protocol_detected': bool,
#     'protocol': str or None,
#     'message': str
# }
```

### `verify_vehicle()` Method
From DiagnosticTool - displays results with formatted UI.

## Menu Updates

Menu now has 10 options (0-9):
- Option 3: NEW - Detect Vehicle
- Options 4-9: Shifted from previous (3-8)

Updated menu display reflects new numbering.

## Use Cases

1. **Troubleshooting Connection Issues**
   - Run option 3 first to verify vehicle
   - Helps identify if problem is adapter or vehicle

2. **Before Running Diagnostics**
   - Verify vehicle is connected
   - Saves time troubleshooting failed diagnostics

3. **User Support**
   - Provide diagnostic info to show customer
   - Clear voltage/communication status

4. **Testing Multiple Vehicles**
   - Quickly verify each vehicle connection
   - Useful in service shop environment

## Benefits

✅ **Comprehensive Verification** - Checks both power and communication  
✅ **Clear Diagnostics** - Shows exactly what's working or not  
✅ **Troubleshooting Guide** - Clear error messages guide resolution  
✅ **Professional** - Shows detailed status with formatted output  
✅ **Time Saving** - Quickly identify connection issues  

## Example Workflow

```
User: "Adapter connects but no data"

1. Run option 3 (Detect Vehicle)
2. Check voltage reading:
   - If 0V → Problem is power connection
   - If 12V+ but no response → Check CAN mode
3. Get specific error message
4. Follow troubleshooting guide
5. Try suggested solutions
```
