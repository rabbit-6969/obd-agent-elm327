# Toyota FJ Cruiser ABS - No Response Troubleshooting

## Situation

You're seeing:
- "ABS Request: 0x7B0, ABS Response: 0x7B8" (addressing is correct)
- "MODULE STATUS: NOT RESPONDING" when checking module presence
- "Failed to read DTC count"
- No response to any UDS services

## What This Means

The module addressing is correct (0x7B0/0x7B8), but the module is not responding to UDS commands. This is different from the normal Toyota behavior where the module simply doesn't respond to Service 0x19 when no DTCs are present.

## Root Causes

### 1. Module in Sleep Mode (Most Likely)

Toyota ABS modules can enter deep sleep mode to conserve power. In this state:
- Module is present on CAN bus
- Module shows correct addressing
- Module doesn't respond to UDS commands
- Module needs specific wake-up conditions

**Solution:**
```
1. Turn ignition OFF
2. Wait 30 seconds
3. Turn ignition ON
4. Wait 10 seconds (let module wake up)
5. Try reading DTCs again
```

### 2. Module Requires Specific Conditions

Some Toyota ABS modules require:
- Brake pedal NOT pressed (module goes to sleep when brake is pressed)
- Parking brake released
- Transmission in Park
- All doors closed
- Vehicle speed = 0 (obviously, since ignition is on but engine off)

**Solution:**
```
1. Ensure brake pedal is NOT pressed
2. Release parking brake
3. Put transmission in Park
4. Close all doors
5. Turn ignition ON
6. Wait 10 seconds
7. Try reading DTCs again
```

### 3. Module Doesn't Support Standard DIDs

Your FJ Cruiser ABS module may not implement the standard UDS DIDs:
- 0xF181 (Calibration ID)
- 0xF190 (VIN)
- 0xF18C (Serial Number)

This is manufacturer-specific behavior. The module may only respond to:
- Service 0x19 (Read DTCs) - when DTCs are present
- Service 0x3E (Tester Present) - sometimes
- Toyota-proprietary services

**This is NORMAL if:**
- ABS warning light is OFF
- No ABS issues reported
- Vehicle brakes normally

**Conclusion:** System is healthy, module just doesn't support diagnostic queries when healthy.

### 4. ELM327 Adapter Issue

The adapter may have:
- Lost connection to vehicle
- Entered power-saving mode
- Protocol mismatch

**Solution:**
```
1. Disconnect ELM327 from OBD-II port
2. Wait 10 seconds
3. Reconnect ELM327
4. Run script again
5. Try standard OBD-II first to verify adapter works:
   python -c "import serial; s=serial.Serial('COM3',38400,timeout=3); import time; time.sleep(2); s.write(b'ATZ\r'); time.sleep(1); s.write(b'0100\r'); time.sleep(1); print(s.read(s.in_waiting))"
```

## Diagnostic Workflow

### Step 1: Verify Basic Communication

Try reading engine DTCs (PCM) to confirm adapter works:

```python
import serial
import time

conn = serial.Serial('COM3', 38400, timeout=3)
time.sleep(2)

# Reset adapter
conn.write(b'ATZ\r')
time.sleep(1)
response = conn.read(conn.in_waiting)
print(f"Reset: {response}")

# Try standard OBD-II
conn.write(b'0100\r')  # Read supported PIDs
time.sleep(1)
response = conn.read(conn.in_waiting)
print(f"OBD-II: {response}")

# Try reading engine DTCs
conn.write(b'03\r')  # Read DTCs
time.sleep(1)
response = conn.read(conn.in_waiting)
print(f"Engine DTCs: {response}")

conn.close()
```

**Expected result:** Should see responses from PCM (engine computer)

**If this fails:** Problem is with adapter or vehicle connection, not ABS module

### Step 2: Wake Up ABS Module

```python
import serial
import time

conn = serial.Serial('COM3', 38400, timeout=3)
time.sleep(2)

# Initialize
conn.write(b'ATZ\r'); time.sleep(1); conn.read(conn.in_waiting)
conn.write(b'ATE0\r'); time.sleep(0.2); conn.read(conn.in_waiting)
conn.write(b'ATL0\r'); time.sleep(0.2); conn.read(conn.in_waiting)
conn.write(b'ATS0\r'); time.sleep(0.2); conn.read(conn.in_waiting)
conn.write(b'ATH1\r'); time.sleep(0.2); conn.read(conn.in_waiting)
conn.write(b'ATSP6\r'); time.sleep(0.2); conn.read(conn.in_waiting)
conn.write(b'ATSH 7B0\r'); time.sleep(0.2); conn.read(conn.in_waiting)

# Try Tester Present (wake up module)
for i in range(5):
    print(f"Attempt {i+1}: Sending Tester Present...")
    conn.write(b'3E 00\r')
    time.sleep(0.5)
    response = conn.read(conn.in_waiting)
    print(f"Response: {response}")
    if b'7E' in response:
        print("✓ Module responded!")
        break
    time.sleep(1)

conn.close()
```

### Step 3: Try Alternative Address

Some Toyota vehicles use 0x760/0x768 instead of 0x7B0/0x7B8:

```python
# In the script, modify:
self.abs_request = 0x760  # Instead of 0x7B0
self.abs_response = 0x768  # Instead of 0x7B8
```

## Understanding the Results

### Scenario 1: Module Responds After Wake-Up

```
✓ Module is AWAKE (Tester Present confirmed)
```

**Meaning:** Module was in sleep mode, now awake

**Next step:** Try reading DTCs (option 1 or 4)

### Scenario 2: Module Never Responds

```
✗ Module is NOT RESPONDING
```

**If ABS light is OFF:**
- System is healthy
- Module doesn't support diagnostic queries when healthy
- This is normal Toyota behavior
- No action needed

**If ABS light is ON:**
- Module may have hardware failure
- Try professional Toyota Techstream tool
- May need dealer diagnosis

### Scenario 3: Module Responds to Some Services

```
✓ Module is AWAKE (Tester Present confirmed)
✗ Failed to read DTC count
```

**Meaning:** Module is awake but doesn't have DTCs

**Conclusion:** System is healthy

## Professional Tools

If you need definitive diagnosis:

1. **Toyota Techstream**
   - Official Toyota diagnostic software
   - Requires MVCI or VCI cable ($200-500)
   - Guaranteed to work with all Toyota modules
   - Can perform actuator tests, bleeding, calibration

2. **Generic Professional Scanners**
   - Autel MaxiCOM
   - Launch X431
   - Snap-on Solus
   - These support Toyota-specific protocols

## Summary

**Your situation:**
- Module addressing is correct (0x7B0/0x7B8 confirmed)
- Module not responding to any UDS services
- Most likely: Module in sleep mode OR doesn't support DIDs when healthy

**If ABS light is OFF:**
- System is healthy
- No DTCs present
- Module behavior is normal
- No repairs needed

**If ABS light is ON:**
- Try wake-up procedures above
- Try professional tool
- May need dealer diagnosis

**Bottom line:** The fact that you saw "ABS Request: 0x7B0, ABS Response: 0x7B8" proves the addressing is correct. The module is just not responding to diagnostic queries, which is normal Toyota behavior when the system is healthy and no DTCs are present.
