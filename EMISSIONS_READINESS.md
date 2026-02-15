# Emissions Readiness & Smog Test Preparation

## Overview

Enhanced vehicle detection system now includes comprehensive emissions monitoring data to help determine if a vehicle is ready to pass an emissions/smog test. The feature displays:

1. **Emissions Monitor Status** - Which monitors have completed since DTC reset
2. **Time Since DTC Reset** - How long vehicle has been running since codes were cleared
3. **Pending DTC Detection** - If any diagnostic trouble codes are pending
4. **Emission Test Prediction** - Clear verdict on pass/fail likelihood

## What Are Emissions Monitors?

Emissions monitors are diagnostic tests that your vehicle's computer runs to check if the emissions control systems are working properly. Different systems have their own monitors:

- **Misfire Monitor** - Checks for engine misfires
- **Fuel System Monitor** - Checks fuel system operation
- **EVAP Monitor** - Checks for fuel vapor leaks
- **O2 Sensor Monitor** - Checks oxygen sensor function
- **O2 Heater Monitor** - Checks sensor heater operation
- **Catalyst Monitor** - Checks catalytic converter efficiency
- **NOx Absorber** - Checks NOx absorption system
- **NOx Catalyst** - Checks NOx catalyst system

## Emission Test Requirements

Most states/regions require vehicles to pass emissions tests. Requirements typically include:

### Monitor Readiness
- **Minimum:** All monitors are completed (100% ready)
- **Alternative:** No more than 1 monitor incomplete (on some vehicles)
- **Minimum Threshold:** Usually 80%+ monitors ready acceptable

### Time Since DTC Clear
- Vehicles typically need **100-200+ miles** of normal driving since last DTC clear
- Monitors take time to run as vehicle operates under different conditions
- Highway + city driving helps complete monitors faster

### Pending DTCs (Diagnostic Trouble Codes)
- **NO pending DTCs allowed** for test passage
- Vehicle with pending codes will **automatically fail** emissions test
- Stored codes (resolved issues) are typically acceptable if not current

### Running Time
- Vehicle must have engine running for sufficient time since codes were cleared
- This allows all monitors to run through their complete test cycles
- Typical requirement: 50-100 hours or 500+ miles of driving

## Emission Test Verdict System

### ✓ READY FOR TEST
```
All monitors: 100% Complete
Time since clear: 100+ hours
Pending codes: None

Result: ✓ Vehicle READY for emission test (all monitors complete)
```
**Vehicle will likely PASS emissions test**

### ✓ LIKELY READY
```
All monitors: 80%+ Complete  
Pending codes: None

Result: ✓ Vehicle LIKELY READY (80%+ monitors complete, no pending codes)
```
**Vehicle has good chance of passing** - Last 20% should complete with continued driving

### ⚠ IN PROGRESS
```
Monitors: 50-80% Complete
Pending codes: None

Result: ⚠ In Progress (65% monitors complete) - Continue driving
```
**Continue normal driving** - Vehicle needs more time for monitors to complete

### ✗ PENDING CODES
```
Any pending DTC detected

Result: ✗ Pending DTC detected - Will FAIL emission test. Clear codes and drive vehicle.
```
**Will FAIL emissions test** - Must:
1. Clear pending codes using diagnostic tool
2. Drive vehicle 100+ miles to complete monitor cycles
3. Retest only after codes are cleared

### ⚠ NOT READY
```
Monitors: <50% Complete
No pending codes

Result: ⚠ Monitors not ready - Continue normal driving (100+ miles typically needed)
```
**Not yet ready** - Continue normal driving to complete monitor cycles

## OBD-II Commands Used

### Monitor Readiness (Mode 01, PID 01)
```
Command: 0101
Response: 8 bytes with bit flags for each monitor
Indicates: Which emissions monitors have completed their test cycles
```

### Time Since DTC Clear (Mode 01, PID 4E)
```
Command: 014E
Response: 2-byte value representing seconds
Indicates: How long engine has been running since last DTC clear
```

## Usage

### From Menu
Select option **3: Detect Vehicle** which now displays:
- Voltage readings (ECU + 5V reference)
- Power status
- Vehicle communication
- **NEW: Emissions monitoring status**
- **NEW: Time since DTC reset**
- **NEW: Smog test readiness verdict**

### Sample Output

```
╔════════════════════════════════════════════════════════════════╗
║ VEHICLE DETECTION                                              ║
╚════════════════════════════════════════════════════════════════╝

  Voltage Readings:
    ✓ ECU Voltage: 12.5V
    ✓ 5V Reference: 5.0V

  Power Status:
    ✓ Power: ✓ Valid voltage detected

  Vehicle Communication:
    ✓ Protocol: Detected
    ✓ Vehicle: Responding

  Emissions Monitoring:
    ✓ Monitors: ✓ ALL READY (100%)
    Running Time: 45h 30m 22s since DTC reset
    ✓ Status: ✓ No pending codes

  Emission Test Readiness:
    ✓ Vehicle READY for emission test (all monitors complete)

  ✓ Vehicle is properly connected
```

## Programmatic Usage

### Get Monitor Status
```python
monitors = adapter.get_emissions_monitor_status()
# Returns:
# {
#     'ready': bool,              # All monitors complete
#     'pending_dtc': bool,        # Any pending codes?
#     'monitors': {
#         'misfire': bool,
#         'fuel_system': bool,
#         'evap': bool,
#         'o2_sensor': bool,
#         'o2_heater': bool,
#         'cat_monitor': bool,
#         'nox_absorber': bool,
#         'nox_catalyst': bool
#     }
# }
```

### Get Time Since Clear
```python
seconds = adapter.get_time_since_dtc_clear()
# Returns: 123456 (seconds since DTC clear)
```

### Get Complete Readiness Status
```python
readiness = adapter.get_emission_readiness_status()
# Returns:
# {
#     'monitors_ready': bool,          # All complete?
#     'time_since_clear': int,         # Seconds
#     'time_formatted': str,           # "45h 30m 22s"
#     'pending_dtc': bool,             # Any pending?
#     'completion_percent': int,       # 0-100
#     'pass_emission_test': bool,      # Will pass?
#     'message': str                   # Detailed verdict
# }
```

## Troubleshooting

### "Unable to read emissions data - vehicle not responding"
- Vehicle is connected but not responding to OBD commands
- Check: CAN bus connections, vehicle ignition state
- Try: Turning vehicle off/on, re-connecting adapter

### Monitors show 0% complete
- Vehicle may be brand new or DTCs were just cleared
- Normal - continue driving vehicle under varied conditions
- Expect 50-100 miles for monitor completion

### Pending DTC but no fault lights
- Pending codes haven't triggered warning light yet
- Clear codes and drive vehicle 100+ miles
- Monitors need to run through complete test cycles

### Time shows as "Unknown"
- Vehicle doesn't support PID 4E (Time Since Clear)
- Use: 100+ miles of driving as benchmark instead
- Still can check monitor readiness percentage

## Smog Test Preparation Checklist

- [ ] **Connect adapter** and run Vehicle Detection (Option 3)
- [ ] **Check emissions status:**
  - [ ] Monitors: 80%+ complete (ideally 100%)
  - [ ] Pending DTCs: None present
  - [ ] Running time: 50-100+ miles since clear
- [ ] **If not ready:**
  - [ ] Continue normal driving (highway + city)
  - [ ] Avoid short trips (multiple short drives = hard on emissions)
  - [ ] Check again in 50+ miles
- [ ] **If pending codes exist:**
  - [ ] Run HVAC Diagnostics (Option 1) to read codes
  - [ ] Use HVAC Diagnostics to clear codes (if applicable)
  - [ ] Drive 100+ miles to allow monitors to reset
  - [ ] Recheck readiness
- [ ] **When ready (✓ status):**
  - [ ] Schedule emissions test with state/local agency
  - [ ] Take vehicle to testing facility
  - [ ] Vehicle should pass

## Benefits

✅ **Know Before You Go** - Check readiness before scheduling test  
✅ **Save Time** - Avoid failed test and retesting costs  
✅ **Understand Status** - See which monitors are complete  
✅ **Preparation Guide** - Know what driving is needed  
✅ **Pending Code Detection** - Catch codes before test  
✅ **Historical Data** - Track time since codes were cleared  

## Files Modified

- `elm327_adapter.py`:
  - Added `get_emissions_monitor_status()` method
  - Added `get_time_since_dtc_clear()` method
  - Added `get_emission_readiness_status()` method

- `main.py`:
  - Updated `verify_vehicle()` method
  - Added emissions display section
  - Added emission test readiness verdict

## Compatibility

- ✅ All OBD-II vehicles (2008+)
- ✅ All ELM327 adapters
- ✅ Both HIGH CAN and LOW CAN modes
- ✅ Backward compatible

## Notes

- Emissions monitors run automatically during normal driving
- Different monitors run under different driving conditions
- Highway driving completes some monitors faster
- City driving helps complete others
- Best results: Mix of highway (40 mph+) and city driving
- If vehicle is brand new or codes just cleared: expect 100-200 miles before ready

## Related Features

- See [VOLTAGE_DETECTION.md](VOLTAGE_DETECTION.md) for power verification
- See [COM_PORT_SELECTION.md](COM_PORT_SELECTION.md) for port management
- See [HVAC_DIAGNOSTICS.md](HVAC_DIAGNOSTICS.md) for code reading/clearing
