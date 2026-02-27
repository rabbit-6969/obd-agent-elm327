# Toyota FJ Cruiser / 4Runner - Live ABS Monitoring Guide

## Overview

This tool continuously monitors your ABS system in real-time to catch intermittent faults as they occur. Perfect for diagnosing those annoying lights that come on and disappear.

## What It Does

The monitor reads two key data points from your ABS module:

1. **Warning Light Status (DID 0x213D)**
   - ABS warning light
   - Brake warning light
   - Slip indicator
   - ECB warning
   - Buzzer status

2. **Individual Wheel Status (DID 0x215F)**
   - Front Right wheel ABS status
   - Front Left wheel ABS status
   - Rear Right wheel ABS status
   - Rear Left wheel ABS status
   - Brake assist status

## Quick Start

```bash
python toolkit/diagnostic_procedures/monitor_fj_abs_live.py
```

The script will:
- Connect to your ABS module
- Poll status every 0.5 seconds (2 times per second)
- Display changes in real-time
- Alert you when faults are detected
- Log all faults for analysis
- Save a detailed fault log file

## Usage

### Basic Monitoring

```bash
python toolkit/diagnostic_procedures/monitor_fj_abs_live.py
```

### Custom Port

```bash
python toolkit/diagnostic_procedures/monitor_fj_abs_live.py --port COM4
```

### Faster Polling (4 times per second)

```bash
python toolkit/diagnostic_procedures/monitor_fj_abs_live.py --interval 0.25
```

### Slower Polling (once per second)

```bash
python toolkit/diagnostic_procedures/monitor_fj_abs_live.py --interval 1.0
```

## How to Use for Diagnosis

### Step 1: Start Monitoring

1. Connect ELM327 to OBD-II port
2. Turn ignition ON (engine doesn't need to run)
3. Run the monitoring script
4. Leave it running

### Step 2: Trigger the Fault

Try to reproduce the conditions when lights come on:

- **Drive the vehicle** (have passenger operate laptop)
- **Brake hard** (in safe area)
- **Make sharp turns**
- **Drive over bumps**
- **Accelerate and decelerate**
- **Different speeds** (slow, medium, highway)

### Step 3: Capture the Fault

When the fault occurs, the script will:
- Sound an alert (text-based)
- Display which wheel(s) are affected
- Log the exact time and conditions
- Continue monitoring

### Step 4: Analyze Results

After monitoring, the script shows:
- Total number of faults detected
- Which wheel(s) failed most often
- Recommended diagnosis

## Example Output

### Normal Operation

```
Timestamp           | Warnings | Wheel Status
----------------------------------------------------------------------
14:23:45.123 | OK                   | All OK
```

### Fault Detected

```
Timestamp           | Warnings | Wheel Status
----------------------------------------------------------------------
14:23:45.123 | OK                   | All OK
14:23:45.623 | ABS, BRAKE           | FR

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
⚠ FAULT DETECTED!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Time: 14:23:45.623

Warning Lights:
  ABS Warning:    ON
  Brake Warning:  ON
  Slip Indicator: OFF
  ECB Warning:    OFF
  Raw: 0x03

Wheel Status (ON = fault detected):
  Front Right: FAULT
  Front Left:  OK
  Rear Right:  OK
  Rear Left:   OK
  Raw: 0x01 0x00

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
```

### Summary After Monitoring

```
======================================================================
MONITORING STOPPED
======================================================================

⚠ 3 fault(s) detected during session

Fault Summary:
  Front Right: 3 fault(s)
  Front Left:  0 fault(s)
  Rear Right:  0 fault(s)
  Rear Left:   0 fault(s)

======================================================================
DIAGNOSIS
======================================================================

⚠ Most likely fault: Front Right wheel speed sensor

Recommended action:
  1. Inspect Front Right wheel speed sensor
  2. Check wiring and connector for damage/corrosion
  3. Clean sensor tip (remove metal shavings/debris)
  4. Check sensor air gap (should be 0.5-1.5mm)
  5. Test sensor resistance (typically 1-2 kΩ)

======================================================================

✓ Fault log saved to: abs_fault_log_20260225_142350.txt
```

## Understanding the Results

### Single Wheel Fault

If one wheel consistently shows faults:
- **Most likely:** That wheel's speed sensor is failing
- **Check:** Sensor, wiring, connector, air gap
- **Common causes:** Damaged wire, corroded connector, debris on sensor

### Multiple Wheel Faults

If multiple wheels show faults:
- **Could indicate:** ABS module issue, wiring harness problem, low battery voltage
- **Check:** Battery voltage, main ABS connector, ground connections
- **Consider:** Professional diagnosis with Toyota Techstream

### Intermittent Faults

If faults come and go:
- **Most likely:** Loose connector, damaged wire, intermittent sensor
- **Check:** Wiggle test on connectors and wires
- **Look for:** Wires rubbing on suspension, corroded pins

## Wheel Speed Sensor Locations

### Front Sensors (Most Common Failure)
- Located at each front wheel hub
- Behind brake rotor
- Most exposed to road debris, water, salt
- Wire runs along suspension to ABS module

### Rear Sensors
- Located at each rear wheel hub
- Behind brake drum/rotor
- More protected than front sensors
- Wire runs along frame rail to ABS module

## Common Wheel Speed Sensor Issues

### 1. Damaged Sensor Tip
- Metal shavings stuck to magnetic tip
- Sensor tip broken or cracked
- **Fix:** Clean or replace sensor

### 2. Incorrect Air Gap
- Sensor too far from tone ring (>1.5mm)
- Sensor too close (rubbing)
- **Fix:** Adjust sensor position

### 3. Damaged Wiring
- Wire cut or frayed
- Wire rubbing on suspension
- Connector corroded
- **Fix:** Repair or replace wiring

### 4. Tone Ring Damage
- Teeth broken on tone ring
- Rust buildup on tone ring
- **Fix:** Clean or replace tone ring

## Sensor Testing

### Visual Inspection
1. Remove wheel
2. Locate sensor at hub
3. Check for:
   - Physical damage
   - Debris on tip
   - Damaged wiring
   - Corroded connector

### Resistance Test
1. Disconnect sensor connector
2. Measure resistance across sensor pins
3. Should read: 1-2 kΩ (typical)
4. If open circuit (∞) or short (0Ω) → Replace sensor

### Air Gap Check
1. Remove sensor
2. Measure gap between sensor tip and tone ring
3. Should be: 0.5-1.5mm
4. Adjust if needed

## Fault Log File

The script saves a detailed log file: `abs_fault_log_YYYYMMDD_HHMMSS.txt`

This file contains:
- Timestamp of each fault
- Warning light status
- Wheel status
- Raw data values

Share this file with your mechanic for diagnosis.

## Tips for Best Results

### 1. Monitor While Driving
- Have passenger operate laptop
- Try different driving conditions
- Reproduce the fault conditions

### 2. Monitor for Extended Period
- Run for 10-15 minutes minimum
- Try various speeds and maneuvers
- More data = better diagnosis

### 3. Note Conditions
- When does fault occur? (braking, turning, bumps)
- What speed? (slow, medium, fast)
- Weather conditions? (wet, dry, cold)

### 4. Multiple Sessions
- Monitor on different days
- Different driving conditions
- Build pattern of failures

## Troubleshooting

### Script Can't Connect
- Check ELM327 is plugged in
- Verify COM port (Device Manager on Windows)
- Try different port: `--port COM4`
- Ensure ignition is ON

### No Data Received
- Module may not support these DIDs
- Try reading DTCs instead (original script)
- Module may be in sleep mode
- Try with engine running

### Constant Faults Shown
- This is good! Fault is active now
- Run DTC reader to get fault codes
- Inspect the failing wheel sensor immediately

## Next Steps After Diagnosis

### If Sensor Fault Identified
1. Inspect the failing sensor
2. Clean sensor tip
3. Check wiring and connector
4. Test sensor resistance
5. Replace if faulty

### If Multiple Sensors Failing
1. Check battery voltage (should be 12.5V+)
2. Inspect main ABS connector
3. Check ABS module ground
4. Consider professional diagnosis

### After Repair
1. Clear DTCs (option 7 in DTC reader script)
2. Run monitor again to verify fix
3. Test drive to confirm repair

## Related Tools

- `read_fj_cruiser_abs_dtcs.py` - Read stored DTCs
- `scan_toyota_abs_addresses.py` - Find correct CAN address
- `test_fj_abs_communication.py` - Test ABS communication

## Official Documentation

For detailed technical information, wiring diagrams, and specifications, refer to the official Toyota FJ Cruiser Repair Manual:

**Website:** https://www.purefjcruiser.com/docs/2007%20Toyota%20FJ%20Cruiser%20Repair%20Manual/

**Key documents for wheel speed sensor diagnosis:**

1. **Front Speed Sensor (02800210.pdf, 0280053.pdf)**
   - Location and removal procedures
   - Resistance specifications
   - Wiring diagrams and connector pinouts
   - Air gap specifications

2. **Rear Speed Sensor (02800310.pdf, 0280054.pdf)**
   - Location and removal procedures
   - Testing procedures
   - Replacement instructions

3. **Vehicle Stability Control System (028000.pdf through 0280052.pdf)**
   - System operation and component locations
   - DTC troubleshooting flowcharts
   - Diagnostic procedures for each DTC code
   - Wiring diagrams for entire ABS system

4. **CAN Communication System (05300.pdf through 053009.pdf)**
   - CAN bus architecture
   - Module addressing
   - Communication protocols

**What you'll find in these documents:**
- Exact sensor locations with photos
- Connector pinout diagrams
- Resistance values (typically 1-2 kΩ for speed sensors)
- Air gap specifications (0.5-1.5mm)
- Tone ring inspection procedures
- Step-by-step troubleshooting flowcharts
- Wiring harness routing diagrams

## Safety Notes

- Monitor while parked for initial testing
- Have passenger operate laptop while driving
- Don't attempt repairs while vehicle is running
- Disconnect battery before working on sensors
- ABS system is critical for safety - repair promptly

## Summary

This live monitoring tool is perfect for diagnosing intermittent ABS faults. It captures the exact moment when the fault occurs and identifies which wheel sensor is failing. Combined with the DTC reader and official repair manual, you have complete diagnostic capability for your FJ Cruiser/4Runner ABS system.

Run this monitor when your lights are acting up, and you'll quickly identify the problem!
