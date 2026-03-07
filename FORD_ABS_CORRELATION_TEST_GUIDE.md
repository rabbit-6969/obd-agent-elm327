# Ford Escape 2008 - ABS DID Correlation Test Guide

## Purpose

This test determines what ABS DIDs 0x0200 and 0x0202 contain by comparing them with known CAN bus wheel speed data.

## Background

We know:
- **CAN message 0x4B0** contains all four wheel speeds (confirmed from CAN database)
- **ABS DID 0x0200** returns 4 bytes of data (unknown meaning)
- **ABS DID 0x0202** returns 4 bytes of data (unknown meaning)

By monitoring all three simultaneously while the vehicle moves, we can determine if the DIDs contain wheel speed data or other parameters.

## What the Script Does

The correlation test script (`scripts/debug/correlate_abs_wheel_speeds.py`) monitors three data sources simultaneously:

1. **CAN 0x4B0** - Wheel speeds broadcast on CAN bus
   - Left Front, Right Front, Left Rear, Right Rear
   - Scaling: (value - 10000) / 100 = km/h
   - Always available (passive monitoring)

2. **ABS DID 0x0200** - Unknown parameter from ABS module
   - 4 bytes of data
   - Requires active query to ABS module

3. **ABS DID 0x0202** - Unknown parameter from ABS module
   - 4 bytes of data
   - Requires active query to ABS module

## Requirements

- Vehicle: Ford Escape 2008 (or Mazda Tribute 2008+)
- Adapter: ELM327 compatible OBD-II adapter
- Connection: Vehicle ignition ON, engine OFF
- Python: 3.6+ with `pyserial` library
- Safety: Vehicle on level ground, parking brake engaged

## Usage

### Basic Test (60 seconds, 1 second intervals)

```bash
python scripts/debug/correlate_abs_wheel_speeds.py
```

### Extended Test (5 minutes)

```bash
python scripts/debug/correlate_abs_wheel_speeds.py --duration 300
```

### Fast Sampling (0.5 second intervals)

```bash
python scripts/debug/correlate_abs_wheel_speeds.py --interval 0.5
```

### Custom COM Port

```bash
python scripts/debug/correlate_abs_wheel_speeds.py --port COM4
```

## Test Procedure

### Phase 1: Baseline (Stationary)

1. Start the script
2. Keep vehicle completely stationary for 10-15 seconds
3. Record baseline values:
   - CAN wheel speeds should be 0.00 km/h (or close to it)
   - DID 0x0200 baseline value
   - DID 0x0202 baseline value

### Phase 2: Slow Roll Forward

4. Release parking brake
5. Slowly roll vehicle forward (1-2 mph / 2-3 km/h)
6. Watch for value changes:
   - CAN wheel speeds should increase
   - Check if DID 0x0200 changes
   - Check if DID 0x0202 changes

### Phase 3: Slow Roll Backward

7. Stop vehicle
8. Slowly roll vehicle backward
9. Watch for value changes again

### Phase 4: Brake Application (Optional)

10. Stop vehicle
11. Apply brake pedal (engine off, just pedal pressure)
12. Check if DID values change (might indicate brake pressure)

## Interpreting Results

### Scenario 1: DIDs Change with Wheel Speeds

**If DID 0x0200 or 0x0202 values change when wheel speeds change:**

- They likely contain wheel speed data
- Compare the hex patterns to CAN data
- Determine scaling factor by comparing values
- Document the correlation

**Example Output:**
```
Time         CAN Wheel Speeds (km/h)                                      DID 0x0200           DID 0x0202
11:23:45.123 LF:  0.00 RF:  0.00 LR:  0.00 RR:  0.00 km/h                00 00 00 00          00 00 00 00
11:23:46.234 LF:  2.50 RF:  2.50 LR:  2.50 RR:  2.50 km/h                00 FA 00 FA          00 00 00 00
11:23:47.345 LF:  5.00 RF:  5.00 LR:  5.00 RR:  5.00 km/h                01 F4 01 F4          00 00 00 00
```
→ DID 0x0200 is changing with wheel speeds (likely wheel speed data)

### Scenario 2: DIDs Stay Constant

**If DID 0x0200 and 0x0202 stay at 00 00 00 00 regardless of wheel movement:**

- They likely contain status flags, brake pressure, or other parameters
- Not wheel speed related
- May only change during ABS events or brake application

**Example Output:**
```
Time         CAN Wheel Speeds (km/h)                                      DID 0x0200           DID 0x0202
11:23:45.123 LF:  0.00 RF:  0.00 LR:  0.00 RR:  0.00 km/h                00 00 00 00          00 00 00 00
11:23:46.234 LF:  2.50 RF:  2.50 LR:  2.50 RR:  2.50 km/h                00 00 00 00          00 00 00 00
11:23:47.345 LF:  5.00 RF:  5.00 LR:  5.00 RR:  5.00 km/h                00 00 00 00          00 00 00 00
```
→ DIDs are NOT wheel speed related

### Scenario 3: Partial Correlation

**If one DID changes but the other doesn't:**

- One might be wheel speed, the other something else
- Analyze each DID separately
- Document which one correlates

## Expected Outcomes

Based on typical Ford ABS implementations:

### Likely: DIDs are NOT Wheel Speeds

Most probable outcome:
- CAN 0x4B0 shows wheel speeds changing
- DIDs 0x0200 and 0x0202 stay constant at 00 00 00 00
- **Reason**: Wheel speeds are already broadcast on CAN bus, no need to duplicate in DIDs
- **Meaning**: DIDs likely contain:
  - ABS system status flags
  - Brake pressure sensor readings
  - Valve states
  - Pump motor status
  - Sensor health indicators

### Possible: DIDs Contain Processed Wheel Speed Data

Less likely but possible:
- DIDs might contain:
  - Average wheel speed
  - Wheel speed deltas (for slip detection)
  - Filtered/processed wheel speeds
  - Wheel acceleration values

## What to Do After the Test

### If DIDs Correlate with Wheel Speeds

1. Document the correlation in `FORD_ABS_DID_SCANNER_GUIDE.md`
2. Calculate the scaling factor
3. Update `knowledge_base/Ford_Escape_2008_profile.yaml`
4. Create a live wheel speed monitoring script using the DIDs

### If DIDs Don't Correlate (Most Likely)

1. Document that DIDs 0x0200/0x0202 are NOT wheel speed related
2. Try brake application test to see if they're pressure-related
3. Scan additional DIDs in the 0x02XX range to find more parameters
4. Use CAN 0x4B0 for wheel speed monitoring instead

## Next Steps

### Expand DID Discovery

If DIDs 0x0200/0x0202 aren't wheel speeds, scan more DIDs:

```bash
# Try extended diagnostic session first
python scripts/debug/test_ford_abs_connection.py

# Then scan broader DID range
python scripts/debug/scan_ford_abs_extended.py
```

### Create Live Monitoring Script

Once you know what the DIDs contain, create a live monitoring script:

```python
# If wheel speeds: monitor DIDs
# If not: monitor CAN 0x4B0 for wheel speeds
```

## Troubleshooting

### No CAN Data

If CAN 0x4B0 shows "No data":
- Check that protocol is set to ISO 15765-4 CAN
- Verify vehicle is in correct state (ignition ON)
- Try monitoring with `ATMA` to see all CAN traffic
- CAN 0x4B0 might only transmit when vehicle is moving

### No DID Response

If DIDs return "No response":
- Verify ABS module address (0x760)
- Try Tester Present first: `AT SH 760` then `3E 01`
- Try entering extended diagnostic session: `10 03`
- Check that previous scan actually worked

### Values Don't Make Sense

If wheel speeds show strange values:
- Verify scaling formula: (value - 10000) / 100
- Check byte order (big-endian vs little-endian)
- Confirm CAN message format matches documentation

## Safety Notes

- This is a READ-ONLY test (no commands modify vehicle behavior)
- Vehicle must be on level ground with parking brake engaged
- Have someone outside the vehicle to watch for movement
- Do not perform test on public roads
- Engine should be OFF (ignition ON only)

## Related Documentation

- `FORD_ABS_DID_SCANNER_GUIDE.md` - Complete ABS DID scanner guide
- `reference/Mazda_CAN_Bus_Reference.md` - CAN bus message documentation
- `reference/Valasek_Miller_Automotive_Networks_2014.md` - Research on Ford Escape ABS
- `knowledge_base/Ford_Escape_2008_profile.yaml` - Vehicle profile with ABS module info

## Example Session

```
$ python scripts/debug/correlate_abs_wheel_speeds.py

================================================================================
Ford Escape 2008 - ABS DID and CAN Wheel Speed Correlation Test
================================================================================

This script will monitor:
  1. CAN 0x4B0 - Known wheel speeds (broadcast on CAN bus)
  2. ABS DID 0x0200 - Unknown parameter
  3. ABS DID 0x0202 - Unknown parameter

Instructions:
  - Keep vehicle stationary initially (baseline)
  - Then slowly roll vehicle forward/backward
  - Watch which values change together
  - Press Ctrl+C to stop early

Monitoring for 60 seconds with 1.0s intervals...

Connected to ELM327

Time         CAN Wheel Speeds (km/h)                                      DID 0x0200           DID 0x0202
----------------------------------------------------------------------------------------------------------------
11:23:45.123 LF:  0.00 RF:  0.00 LR:  0.00 RR:  0.00 km/h                00 00 00 00          00 00 00 00
11:23:46.234 LF:  0.00 RF:  0.00 LR:  0.00 RR:  0.00 km/h                00 00 00 00          00 00 00 00
11:23:47.345 LF:  2.50 RF:  2.50 LR:  2.50 RR:  2.50 km/h                00 00 00 00          00 00 00 00
11:23:48.456 LF:  5.00 RF:  5.00 LR:  5.00 RR:  5.00 km/h                00 00 00 00          00 00 00 00
...

================================================================================
Correlation Test Complete
================================================================================
Total samples: 60

Analysis:
  - If DID 0x0200 or 0x0202 values change when wheel speeds change:
    → They likely contain wheel speed or related ABS data
  - If DID values stay constant (all zeros):
    → They likely contain status flags, pressure, or other parameters
  - Compare the hex patterns to identify correlations
```

## Summary

This correlation test is the definitive way to determine what ABS DIDs 0x0200 and 0x0202 contain. By comparing them with known CAN wheel speed data while the vehicle moves, you'll know exactly what these DIDs represent and how to use them for diagnostics.
