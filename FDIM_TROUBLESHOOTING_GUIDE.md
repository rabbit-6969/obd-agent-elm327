# Ford FDIM Display Control - Troubleshooting Guide

## ⚠️ CRITICAL SAFETY WARNING ⚠️

**DO NOT attempt FDIM control via standard OBD-II connection!**

### What Happened During Testing

When attempting to control FDIM by sending CAN messages via the OBD-II port, the following occurred:

1. **ABS light started flickering**
2. **Warning sound and "check brake system" message appeared**
3. **ABS module stopped responding to diagnostic queries**
4. **CAN explorer failed to capture wheel speed data**
5. **Transmission gear data disappeared from CAN bus**

### Why This Happened

**Root Cause**: Ford Escape 2008 has TWO separate CAN buses:
- **HS-CAN (500 kbps)**: Safety-critical modules (ABS, PCM, brakes, steering)
- **MS-CAN (125 kbps)**: Comfort modules (FDIM, HVAC, audio)

**The Problem**:
- FDIM is on MS-CAN
- OBD-II port connects to HS-CAN
- Sending MS-CAN formatted messages on HS-CAN interfered with ABS communication
- Standard ELM327 CANNOT access MS-CAN via OBD-II port

### Safety Implications

**HS-CAN carries safety-critical data**:
- ABS wheel speed sensors (0x4B0)
- Brake status (0x190)
- Transmission gear (0x228)
- Engine control (PCM at 0x7E0)
- Steering angle (0x420)

**Injecting incorrect messages can**:
- Interfere with ABS operation
- Cause false warnings
- Disrupt safety system communication
- Potentially affect vehicle control systems

### Recovery Procedure

If you experience ABS issues after CAN bus testing:

1. **Immediate**: Turn off ignition, wait 30 seconds
2. **Clear fault**: Restart vehicle, check if ABS light clears
3. **Test ABS**: Run `scripts/debug/test_ford_abs_connection.py`
4. **Verify wheel speeds**: Run `scripts/debug/correlate_abs_wheel_speeds.py`
5. **If issues persist**: Disconnect battery for 5 minutes to reset all modules

### Conclusion

**FDIM control via OBD-II is NOT POSSIBLE and NOT SAFE**

**Requirements for FDIM control**:
- Direct connection to MS-CAN bus (pins 3 & 11 on OBD-II connector)
- Dual-CAN adapter (not standard ELM327)
- Professional tools (FORScan with MS-CAN license)
- Understanding of MS-CAN protocols

**For this project**:
- Focus on HS-CAN modules (PCM, ABS) with READ-ONLY operations
- Use FORScan for MS-CAN access (HVAC, FDIM)
- DO NOT attempt DIY MS-CAN control via OBD-II port

---

## Problem

The FDIM display writer script doesn't work with any combination of CAN IDs or message formats tested so far.

## Systematic Troubleshooting Approach

### Step 1: Verify FDIM Capability

**Question**: Does your Ford Escape 2008 actually have FDIM display control capability?

**Check**:
- Does your radio display track names when playing music?
- Does it show station information?
- Is the display text-based (not just icons)?

**If NO**: Your vehicle may not support FDIM text display via CAN bus. Some models only show pre-programmed text.

**If YES**: Proceed to Step 2.

---

### Step 2: Discover Actual FDIM CAN ID

The CAN IDs 0x415 and 0x417 are common, but your specific vehicle may use different IDs.

**Method**: Monitor CAN bus while radio displays text

```bash
python scripts/debug/discover_fdim_protocol.py --mode monitor --duration 60
```

**During monitoring**:
1. Play music on radio
2. Change tracks multiple times
3. Switch between radio stations
4. Watch display change

**Expected result**: Script will identify CAN IDs containing ASCII text

**If no ASCII text found**: 
- FDIM may be on MS-CAN (125kbps) instead of HS-CAN (500kbps)
- Try changing ELM327 protocol: `ATSP7` for MS-CAN
- Your vehicle may use proprietary encoding (not ASCII)

---

### Step 3: Analyze Message Format

Once you've identified the FDIM CAN ID, analyze the message structure:

**Look for**:
- **Header byte**: First byte before text (often 0x02, 0x03, 0x10)
- **Text encoding**: ASCII characters (0x41='A', 0x42='B', etc.)
- **Message length**: How many bytes total?
- **Padding**: Are messages padded to fixed length?
- **Terminator**: Is there an end-of-text marker?

**Example analysis**:
```
CAN ID: 0x415
Message: 02 48 45 4C 4C 4F 00 00
         ^  H  E  L  L  O  (padding)
         |
         Header byte
```

---

### Step 4: Test Message Transmission

Try sending messages using the discovered format:

```bash
python scripts/debug/discover_fdim_protocol.py --mode test --id 0x415 --text "HELLO"
```

**Test variations**:
1. Different header bytes (0x00, 0x01, 0x02, 0x03, 0x10)
2. Different message lengths (8 bytes, 16 bytes, variable)
3. With/without padding
4. With/without null terminator

---

### Step 5: Check CAN Bus Type

FDIM may be on a different CAN bus than you're accessing.

**Ford Escape 2008 has two CAN buses**:
- **HS-CAN**: 500 kbps (most modules, accessible via OBD-II)
- **MS-CAN**: 125 kbps (some modules, may not be accessible via OBD-II)

**From Valasek & Miller research**:
- FDIM diagnostic address: 0x7A6 on MS-CAN
- Display control may also be on MS-CAN

**Test MS-CAN**:
```python
# In your script, change protocol:
self.send_command("ATSP7")  # ISO 15765-4 CAN (125kbps)
```

**Problem**: Standard OBD-II port may not provide access to MS-CAN on all vehicles.

---

### Step 6: Alternative Approach - Capture Real Traffic

If direct writing doesn't work, capture what the radio actually sends:

**Method 1: Passive monitoring**
```bash
# Monitor while changing tracks
python scripts/debug/discover_fdim_protocol.py --mode monitor --duration 60
```

**Method 2: Active comparison**
1. Note current display text
2. Start monitoring
3. Change track/station
4. Note new display text
5. Compare CAN messages before/after

**Look for**:
- Which CAN ID changed?
- What's the message format?
- How does text map to hex bytes?

---

### Step 7: Check for Multi-Frame Messages

FDIM may use ISO-TP multi-frame messages for longer text.

**Single frame** (≤7 bytes):
```
0x415: 07 48 45 4C 4C 4F 00 00
       ^  H  E  L  L  O
       Length
```

**Multi-frame** (>7 bytes):
```
First frame:  10 0F 48 45 4C 4C 4F 20  (10 = first frame, 0F = total length)
Flow control: 30 00 00 ...              (from FDIM)
Consecutive:  21 57 4F 52 4C 44 00 00  (21 = frame 1)
```

**If multi-frame**: ELM327 may not handle this automatically. Need to implement ISO-TP manually.

---

### Step 8: Verify ELM327 Capabilities

Some cheap ELM327 clones don't support CAN message transmission properly.

**Test basic CAN send**:
```python
# Try sending to a known module (e.g., PCM at 0x7E0)
elm.send_command("ATSH7E0")
response = elm.send_command("01 00")  # Request supported PIDs
```

**If this fails**: Your ELM327 may not support CAN transmission, only reception.

**Solution**: Use a better quality ELM327 adapter or professional CAN tool.

---

### Step 9: Check for Gateway Filtering

Some vehicles have CAN gateways that filter messages from OBD-II port.

**Symptom**: You can READ from FDIM but can't WRITE to it.

**Why**: Gateway allows diagnostic reads but blocks writes to prevent unauthorized control.

**Test**: Try writing to other modules (e.g., clear DTCs) to verify write capability.

**If gateway blocks writes**: 
- FDIM control may require direct connection to MS-CAN bus
- May need professional tools (FORScan, IDS) that authenticate with gateway
- OBD-II port access may be read-only for FDIM

---

### Step 10: Alternative - Use Audio Module Instead

If FDIM doesn't work, try controlling the Audio Control Module (ACM) instead.

**From Valasek & Miller**:
- ACM address: 0x727 (MS-CAN)
- ACM may have display control capabilities

**Test ACM**:
```bash
python scripts/debug/discover_fdim_protocol.py --mode test --id 0x727 --text "TEST"
```

---

## Common Issues and Solutions

### Issue 1: "No response from ELM327"

**Cause**: ELM327 not properly initialized

**Solution**:
- Check COM port is correct
- Verify baud rate (38400 or 115200)
- Try resetting adapter (ATZ command)
- Check USB cable connection

### Issue 2: "Messages sent but display doesn't change"

**Possible causes**:
1. Wrong CAN ID
2. Wrong message format
3. Wrong CAN bus (HS vs MS)
4. Gateway filtering
5. FDIM doesn't support external control

**Solutions**:
- Run monitor mode to find correct CAN ID
- Analyze real FDIM traffic to determine format
- Try MS-CAN protocol (ATSP7)
- Check if other write operations work

### Issue 3: "Display shows garbage characters"

**Cause**: Wrong encoding or byte order

**Solutions**:
- Verify ASCII encoding (not UTF-8 or other)
- Check if header byte is required
- Verify message length requirements
- Check for byte swapping

### Issue 4: "Display changes briefly then reverts"

**Cause**: Not sending messages frequently enough

**Solution**:
- Increase update frequency (every 250-500ms)
- Verify continuous transmission loop is working
- Check for timing issues in code

### Issue 5: "Can read CAN bus but can't write"

**Cause**: ELM327 or gateway limitations

**Solutions**:
- Verify ELM327 supports CAN transmission
- Test writing to other modules (PCM, ABS)
- Check for gateway filtering
- May need professional CAN tool

---

## Diagnostic Script Usage

### Monitor Mode (Discover FDIM CAN ID)

```bash
# Monitor for 60 seconds while changing tracks
python scripts/debug/discover_fdim_protocol.py --mode monitor --duration 60
```

**What it does**:
- Captures all CAN traffic
- Identifies messages containing ASCII text
- Shows candidate FDIM CAN IDs

**When to use**: When you don't know the correct CAN ID

### Test Mode (Test Specific CAN ID)

```bash
# Test CAN ID 0x415 with text "HELLO"
python scripts/debug/discover_fdim_protocol.py --mode test --id 0x415 --text "HELLO"
```

**What it does**:
- Tests multiple message formats
- Sends messages continuously for 5 seconds each
- Asks if display changed

**When to use**: After discovering candidate CAN ID from monitor mode

### Scan Mode (Try Common IDs)

```bash
# Scan all common FDIM CAN IDs
python scripts/debug/discover_fdim_protocol.py --mode scan
```

**What it does**:
- Tests common FDIM CAN IDs (0x415, 0x416, 0x417, 0x7A6, etc.)
- Tries each ID with simple test message
- Interactive - asks if each attempt worked

**When to use**: Quick test of known common IDs

---

## Expected Outcomes

### Success Case

```
CAN ID: 0x415
Format: Header 0x02 + ASCII
Message: 02 48 45 4C 4C 4F (displays "HELLO")
Update rate: Every 500ms
Result: Display shows custom text
```

### Failure Case - Wrong CAN ID

```
Symptom: No display change
Cause: Using wrong CAN ID
Solution: Run monitor mode to find correct ID
```

### Failure Case - Wrong Format

```
Symptom: Display shows garbage or nothing
Cause: Incorrect message format
Solution: Analyze real FDIM traffic to determine format
```

### Failure Case - Not Supported

```
Symptom: Can't find any CAN ID with ASCII text
Cause: Vehicle may not support FDIM control via CAN
Solution: May require professional tools or direct module access
```

---

## Next Steps Based on Results

### If Monitor Mode Finds ASCII Text

1. Note the CAN ID(s) found
2. Analyze message format from samples
3. Test writing using discovered format
4. Document working configuration

### If Monitor Mode Finds No ASCII Text

**Possible reasons**:
1. FDIM on MS-CAN (not accessible via OBD-II)
2. Proprietary encoding (not ASCII)
3. Display doesn't show text during monitoring period
4. ELM327 not capturing all traffic

**Try**:
- Monitor for longer duration (2-3 minutes)
- Change tracks more frequently during monitoring
- Try MS-CAN protocol (ATSP7)
- Use professional CAN tool for comparison

### If Test Mode Works

1. Document exact configuration (CAN ID, header, format)
2. Update `fdim_display_writer.py` with working config
3. Create examples and use cases
4. Integrate with diagnostic agent

### If Nothing Works

**Accept limitations**:
- Your specific vehicle may not support FDIM control via OBD-II
- May require direct MS-CAN access (not available via OBD-II port)
- May require authentication/gateway bypass (not recommended)
- Professional tools (FORScan) may have special access

**Alternative approaches**:
- Focus on CAN bus monitoring (read-only)
- Use external display instead of FDIM
- Document limitation for future reference

---

## Research Resources

### Check These Sources

1. **FORScan forums**: Search for "FDIM display control Ford Escape"
2. **Mazda forums**: Mazda Tribute shares platform, may have info
3. **CAN bus databases**: Look for FDIM message definitions
4. **Service manuals**: Check for FDIM communication protocol

### Useful Search Terms

- "Ford Escape FDIM CAN control"
- "Ford FDIM display hack"
- "Mazda Tribute display control"
- "Ford MS-CAN FDIM"
- "FORScan FDIM text"

---

## Documentation

### If You Find Working Configuration

Please document:
1. Exact CAN ID that works
2. Message format (header byte, encoding, length)
3. Required update frequency
4. Any special requirements (protocol, bus type)
5. Which display modes it works in (radio, navigation, etc.)

### Update These Files

- `reference/Ford_FDIM_Display_Control.md` - Add working configuration
- `scripts/debug/fdim_display_writer.py` - Update with correct defaults
- `knowledge_base/Ford_Escape_2008_profile.yaml` - Add FDIM info

---

## Summary

FDIM display control is more complex than initially expected. The systematic approach:

1. **Discover** - Find the actual CAN ID using monitor mode
2. **Analyze** - Understand the message format from real traffic
3. **Test** - Try writing using discovered format
4. **Document** - Record working configuration
5. **Accept** - If it doesn't work, document the limitation

The discovery script will help you work through this methodically. Start with monitor mode while the radio is playing and displaying track names.
