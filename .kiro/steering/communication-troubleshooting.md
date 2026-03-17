---
inclusion: auto
---

# Communication Troubleshooting Guide

When vehicle modules don't respond or communication fails, follow this systematic troubleshooting approach.

## "No Response" Diagnosis Tree

### Step 1: Is This Normal Behavior?

**Check manufacturer-specific behaviors first:**

**Toyota ABS (2007-2010)**:
- No response when no DTCs = NORMAL
- No response when ABS light OFF = NORMAL
- This is intentional design, not a problem

**Ford modules**:
- Should always respond
- No response = communication problem

**Action**: Check vehicle profile for known behaviors before troubleshooting.

### Step 2: Verify Basic Communication

Try the simplest possible command - Tester Present:

```
Try all three variants:
1. 3E 01
2. 3E 00  
3. 3E

Expected response: 7E
```

**If no response to any variant**: Communication problem (proceed to Step 3)
**If response to one variant**: Module is alive, use that variant

### Step 3: Verify CAN Address

**Common issue**: Wrong CAN address for the module

**Toyota ABS example**:
- Some models: 0x7B0/0x7B8
- Other models: 0x750/0x758
- Must scan to confirm

**Action**: 
1. Scan address range 0x700 - 0x7DF
2. Try Tester Present on each address
3. Document which addresses respond

### Step 4: Check Diagnostic Session

Some modules require extended session:

```
Request:  10 03
Response: 50 03
```

**Action**:
1. Enter extended diagnostic session
2. Retry original command
3. If successful, document that module requires extended session

### Step 5: Try Alternative DIDs

If specific DID doesn't respond, try alternatives:

**Standard DIDs to try**:
- 0xF190: VIN (most universal)
- 0xF181: Calibration ID
- 0xF18C: Serial Number

**Action**:
1. Try each DID
2. Document which ones work
3. Use working DIDs for module identification

### Step 6: Check Protocol Version

Module may use different protocol:

**ISO-14229 (UDS)**: Modern standard
**ISO-14230 (KWP2000)**: Older standard

**Toyota specific**: Even newer models may have legacy modules using KWP2000

**Action**:
1. Try UDS commands first
2. If no response, try KWP2000 format
3. Document which protocol works

### Step 7: Verify Adapter Functionality

**ELM327 adapter issues**:
- Cheap clones may fail to switch CAN IDs
- May drop multi-frame responses
- May not support all protocols

**Action**:
1. Test adapter with known-good module (PCM at 0x7E0)
2. If PCM responds but other modules don't, adapter may be limited
3. Recommend quality adapter (Vgate iCar Pro, OBDLink, etc.)

### Step 8: Check for Secondary CAN Bus

Some modules may be on secondary bus:

**Symptoms**:
- No response at all
- No negative response
- No bus errors
- Just silence

**Toyota specific**: Some modules require gateway access

**Action**:
1. Explain to user that module may be on secondary bus
2. ELM327 cannot reach secondary bus through OBD-II port
3. Would require direct connection to that bus
4. Document this limitation

## Adapter Quality Check — Run Every Session

**MANDATORY**: At the start of every diagnostic session (alongside VIN reading), run the adapter authenticity check. This determines what the adapter can and cannot do, and sets correct expectations before any diagnostics begin.

### Why Every Session

- The user may have swapped adapters between sessions
- Clone adapters cause silent failures that look like vehicle problems
- Knowing adapter quality upfront prevents wasted troubleshooting time

### How to Run

The shared module is at `toolkit/vehicle_communication/adapter_checker.py`.

```python
from toolkit.vehicle_communication.adapter_checker import check_adapter

result = check_adapter(ser)   # ser = open serial.Serial connection
print(result.user_message())  # show to user
```

Or from scripts that use the inline ELM327 class:

```python
import sys, os
sys.path.insert(0, 'toolkit/vehicle_communication')
from adapter_checker import check_adapter

adapter_result = check_adapter(elm.ser)
print(adapter_result.user_message())
```

### Tests Performed (in order of reliability)

| Test | Command | Pass | Fail = Clone |
|------|---------|------|--------------|
| Allow long messages | `AT AL` | `OK` | `?` or empty — **definitive** |
| Firmware version | `AT I` | v1.0–v2.0 | v1.5 / v2.1 / garbage |
| Device description | `AT @1` | any string | `?` or empty |
| Protocol parameter | `AT PP 2F ON` | `OK` | `?` or hang |
| CAN receive address | `AT CRA 7E8` | `OK` | `?` or fail |
| Set CAN header | `AT SH 7E0` | `OK` | `?` or fail |

**Single most reliable test**: `AT AL` — if it returns anything other than `OK`, it's a clone.

### Verdicts

- **GENUINE** — all key tests pass, full functionality expected
- **LIMITED** — clone confirmed, reduced functionality
- **UNKNOWN** — inconclusive, proceed with caution

### Known Limitations of Clone Adapters

When verdict is LIMITED, warn the user about:
- CAN bus monitoring (ATMA) may not include headers → use ATCRA workaround
- Multi-ECU access (ABS/SRS/TCM) may fail or time out
- Freeze-frame and Mode 6 data may be unavailable
- Older ISO/KWP2000 vehicles may not connect at all
- Streaming many PIDs simultaneously may cause disconnects or corrupted values

### Recommended Upgrades (when clone detected)

- Vgate iCar Pro (~$25, Bluetooth/WiFi)
- OBDLink LX (~$80, Bluetooth)
- OBDLink MX+ (~$100, Bluetooth)

### Clone Firmware Version Strings (always a clone)

`v1.5`, `v2.1`, `v2.2`, `v3.0` — these version numbers were never released by ELM Electronics.

### Genuine Firmware Versions

`v1.0`, `v1.1`, `v1.2`, `v1.3`, `v1.3a`, `v1.4`, `v1.4b`, `v2.0`

---

## ISO-TP Multi-Frame Response Parsing

**Scope**: This section applies only to **OBD-II request/response commands** (VIN, DTCs, UDS ReadDataByIdentifier, emission readiness). It does **not** apply to:

- **CAN bus monitoring** (ATMA / ATCRA streaming) — those scripts parse raw CAN frames line-by-line in a loop; `extract_payload_hex()` is irrelevant there
- **Single-frame UDS responses** with `ATCAF0` — when CAN auto-format is off and the response fits in one frame, there are no ISO-TP sequence bytes to strip; just search for the service response byte directly
- **ATCAF1 (auto-format on) single-frame** — ELM327 strips framing automatically for single frames; no manual stripping needed

### When you DO need `extract_payload_hex()`

Use it when **all three** of these are true:
1. You sent a request command (not ATMA monitoring)
2. Headers are on (`ATH1`)
3. The response spans multiple CAN frames (payload > ~7 bytes — VIN, long DIDs, multi-DTC responses)

### The Problem

ELM327 with `ATH1` returns multi-frame responses with CAN framing interleaved:

```
7E8 10 14 49 02 01 31 4A   <- first frame  (1x = FF type, 14 = length)
7E8 21 38 47 41 35 39 31   <- consecutive frame 1 (2x = CF, x = seq)
7E8 22 31 37 4C 31 34 31   <- consecutive frame 2
```

Naively stripping spaces and searching for `4902` will include CAN IDs and
ISO-TP sequence bytes in the "payload", producing garbage.

Token stripping rules:
- `7E8` (3-char hex) → CAN ID, **skip**
- `10` after CAN ID → first-frame byte, **skip** + skip next byte too (length)
- `21`, `22` after CAN ID → consecutive-frame sequence byte, **skip**
- All other 2-char hex tokens → payload bytes, **keep**

### The Solution — `extract_payload_hex()`

```python
from obd2_helpers import extract_payload_hex
payload = extract_payload_hex(response)
# payload is now clean hex: '490201314A384741353931...'
```

### VIN — send ATCAF0 first

```python
elm.cmd("ATCAF0")                    # raw frames — framing bytes visible
response = elm.cmd("0902", timeout=5)
elm.cmd("ATCAF1")                    # restore
```

Without `ATCAF0`, some adapters reassemble frames but strip bytes inconsistently.

### DTC responses — anchor to service byte, not raw hex

Mode 03 single-frame example:
```
7E8 06 43 01 58 00 00 00
         ^^ service response byte (0x43)
            ^^ DTC count (1)
               ^^^^^ DTC bytes: 01 58 → P0158
```

After `extract_payload_hex()`: `430158000000`

Search for `43` in the **stripped payload**, read count byte, then read exactly
`count × 4` hex chars. Do **not** search for `43` in the raw response — it
will match CAN IDs (e.g. `743`, `7E8` contains no `43` but other IDs might).

Use `obd2_helpers.parse_dtcs(response, mode=3)` which handles all of this.

### CAN monitoring is different — do NOT use `extract_payload_hex()`

CAN monitoring scripts (steering angle, wheel speeds, transmission gear) use
ATMA/ATCRA streaming. Each line is already one complete CAN frame:

```
4B0 27 10 27 10 27 10 27 10   <- CAN ID + 8 data bytes, one frame per line
```

Parse these by splitting on whitespace: `parts[0]` = CAN ID, `parts[1:]` = data.
No ISO-TP reassembly needed. The existing monitoring scripts are correct.

---



### Negative Response (7F)

Format: `7F [service] [NRC]`

**Common NRCs (Negative Response Codes)**:
- 0x11: Service not supported
- 0x12: Sub-function not supported
- 0x13: Incorrect message length
- 0x22: Conditions not correct
- 0x31: Request out of range
- 0x33: Security access denied
- 0x78: Response pending (wait)

**Action**:
1. Decode the NRC
2. Explain to user what it means
3. Suggest alternative approach
4. Document which services are supported

### Timeout

No response within expected time.

**Possible causes**:
1. Wrong CAN address
2. Module in sleep mode
3. Module requires extended session
4. Adapter issue
5. Module on secondary bus

**Action**: Follow diagnosis tree above

### Malformed Response

Response doesn't match expected format.

**Possible causes**:
1. Adapter dropping bytes
2. Multi-frame response not handled
3. Protocol mismatch
4. Interference on bus

**Action**:
1. Retry command
2. Check adapter quality
3. Try different adapter if available
4. Document the issue

## Manufacturer-Specific Troubleshooting

### Toyota

**If ABS doesn't respond**:
1. Check if ABS light is ON (if OFF, no response is normal)
2. Try 0x750 and 0x7B0 addresses
3. Try all three Tester Present variants
4. Try extended session
5. Try reading DTC count (19 01 FF) instead of DTCs (19 02 FF)

**If any module doesn't respond**:
1. Check for mixed protocol implementation
2. Try both UDS and KWP2000
3. Some modules may be on secondary bus

### Ford

**If module doesn't respond**:
1. Verify correct address (check vehicle profile)
2. Try extended session
3. Ford modules usually respond reliably
4. If no response, likely wrong address or adapter issue

## Adapter-Specific Issues

### ELM327 Clones

**Common problems**:
- Fail to switch headers properly
- Drop multi-frame responses
- Limited protocol support
- Slow response times
- **ATMA header bug**: ATH1 returns OK but headers not included in ATMA output

**ATMA Header Bug (Limited/Clone Adapters Only)**:

This bug only affects adapters with verdict `LIMITED` from the session adapter quality check.
**If the adapter check returned `GENUINE`, use ATMA directly — no workaround needed.**

Clone adapters have a bug where:
- ATH1 command returns "OK" (appears to work)
- But ATMA (Monitor All) output doesn't include CAN IDs
- Output format: `20026F4279027090000` (continuous hex, no CAN ID prefix)
- Expected format: `080 4D C3 4E 00 01 C3 1F` (CAN ID + spaces + data)

**Symptoms** (clone only):
- ATMA receives data (hundreds/thousands of lines)
- But all lines are unparseable (no 3-digit CAN ID prefix)
- Zero CAN messages captured despite active bus traffic

**Decision logic — always check adapter verdict first**:

| Adapter verdict | CAN monitoring approach |
|-----------------|------------------------|
| `GENUINE` | Use ATMA directly, headers work |
| `LIMITED` | Skip ATMA, use ATCRA workaround |
| `UNKNOWN` | Try ATMA; if zero CAN IDs captured, fall back to ATCRA |

**ATCRA Workaround** (LIMITED / UNKNOWN only):
```python
# CRITICAL: Must use ATS1 (spaces ON) for ATCRA to work!
self.send_command("ATS1")  # Spaces ON (required!)
self.send_command("ATH1")  # Headers ON

# Instead of ATMA (Monitor All):
self.send_command("ATCRA080")  # Set receive address filter
self.send_command("ATMA")      # Monitor - now includes headers properly

# Monitor multiple IDs sequentially:
for can_id in [0x080, 0x228, 0x4B0]:
    self.send_command(f"ATCRA{can_id:03X}")
    self.send_command("ATMA")
    # ... collect data ...
    self.ser.write(b'\r')  # Stop monitoring
    self.send_command("ATCRA")  # Clear filter
```

**Output with ATCRA + ATS1**:
```
080 4D C3 4E 00 01 C3 54 FF  ✓ Parseable!
```

**Detection** (for UNKNOWN adapters):
- If ATMA processes many lines but captures zero CAN IDs
- And lines don't have spaces (continuous hex string)
- → Treat as LIMITED, switch to ATCRA workaround

**General Workarounds**:
1. Use single-frame commands when possible
2. Add delays between commands
3. Retry failed commands
4. Use ATCRA for CAN monitoring instead of ATMA
5. Recommend quality adapter

### Quality Adapters

**Vgate iCar Pro, OBDLink, etc.**:
- Better protocol support
- Reliable header switching
- Handle multi-frame responses
- Faster communication

**Recommendation**: When user has persistent issues, suggest upgrading adapter.

## Logging and Documentation

When troubleshooting:
1. **Log everything**: Commands sent, responses received, timestamps
2. **Document what worked**: Update vehicle profile with successful methods
3. **Document what didn't work**: Helps avoid repeating failed approaches
4. **Share findings**: Update knowledge base for future sessions

## When to Ask for Help

Ask user for help when:
1. All standard approaches have failed
2. Need service manual information
3. Need to verify physical connections
4. Need to check vehicle state (ignition, etc.)
5. Suspect hardware issue

Be specific about what you need:
- "Can you verify the ignition is in RUN position?"
- "Can you check if the ABS warning light is currently ON?"
- "Do you have access to the service manual for this vehicle?"

## Success Criteria

Communication is successful when:
1. Module responds consistently
2. Responses match expected format
3. Data is valid and makes sense
4. Can perform intended diagnostic operation

Document the successful configuration for future use.
