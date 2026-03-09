# ELM327 ATMA Header Bug

## Problem Description

Many cheap ELM327 clone adapters have a firmware bug where the ATH1 (Headers On) command appears to work but doesn't actually include headers in ATMA (Monitor All) output.

## Symptoms

1. **ATH1 returns OK** - Command appears successful
2. **ATMA receives data** - Hundreds or thousands of lines captured
3. **No CAN IDs in output** - Lines are continuous hex strings without CAN ID prefix
4. **Zero messages parsed** - Parser can't extract CAN IDs from the data

## Example Output

**Expected format (with headers)**:
```
080 4D C3 4E 00 01 C3 1F
228 12 34 56 78 9A BC DE
4B0 00 11 22 33 44 55 66 77
```

**Actual format (bug - no headers)**:
```
20026F4279027090000
20026F5279027090000
20026F4279027090000
```

The actual format is a continuous hex string with no spaces and no CAN ID prefix, making it impossible to determine which CAN ID sent each message.

## Root Cause

The ELM327 clone firmware doesn't properly implement the ATH1 command for ATMA mode. While ATH1 works correctly for normal OBD-II commands (Mode 01, UDS, etc.), it fails to include headers when in ATMA monitoring mode.

## Detection

Run the diagnostic script to confirm:
```bash
python scripts/debug/diagnose_can_monitoring.py
```

**Indicators of this bug**:
- ATMA processes many lines (hundreds/thousands)
- Zero CAN IDs captured
- Sample lines show continuous hex with no spaces
- Lines don't start with 3-digit hex CAN ID

## Workaround: ATCRA Targeted Monitoring

Use ATCRA (CAN Receive Address) filtering to monitor specific CAN IDs. With ATCRA, the adapter properly includes headers.

**CRITICAL**: Must use ATS1 (spaces ON) for ATCRA to work properly.

### Method

```python
# Initialize with spaces ON
self.send_command("ATS1")  # Spaces ON (required!)
self.send_command("ATH1")  # Headers ON

# Set receive address filter for specific CAN ID
self.send_command("ATCRA080")  # Monitor only CAN ID 0x080

# Start monitoring - now includes headers properly
self.ser.write(b'ATMA\r')

# ... collect data for duration ...

# Stop monitoring
self.ser.write(b'\r')

# Clear filter
self.send_command("ATCRA")
```

**Output format with ATCRA + ATS1**:
```
080 4D C3 4E 00 01 C3 54 FF
080 4D C3 4E 00 01 C3 55 FF
080 4D C3 4E 00 01 C3 56 FF
```
✓ CAN ID included, spaces between bytes, parseable!

### Implementation

Use the targeted monitoring script:
```bash
python scripts/debug/targeted_can_monitor.py
```

This script:
- Monitors 12 known CAN IDs sequentially
- Uses ATCRA filtering for each ID
- 5 seconds per ID (total ~60 seconds)
- Properly captures CAN traffic with headers

## Known Affected Adapters

- Generic ELM327 v1.5 clones (most common)
- Adapters without genuine ELM327 chip
- Low-cost Bluetooth/WiFi OBD-II adapters

## Known Working Adapters

These adapters properly support ATH1 in ATMA mode:
- Genuine ELM327 chips
- Vgate iCar Pro
- OBDLink MX+
- OBDLink LX
- VINT-TT5L

## Alternative Solutions

### 1. Targeted Monitoring (Recommended)
Use ATCRA filtering as described above. Works with most adapters.

### 2. Upgrade Adapter
Get a quality adapter that properly implements ELM327 protocol.

### 3. External CAN Sniffer
Use dedicated CAN tools:
- CANable (USB-CAN adapter)
- PCAN-USB
- Kvaser interfaces
- SocketCAN on Raspberry Pi

These provide full CAN bus visibility without ELM327 limitations.

## Impact on Diagnostic Agent

The agent should:

1. **Detect the issue**: If ATMA captures many lines but zero CAN IDs, suspect this bug
2. **Recommend workaround**: Suggest using targeted_can_monitor.py script
3. **Document limitation**: Note in vehicle profile that adapter has ATMA header bug
4. **Suggest upgrade**: For users doing extensive CAN work, recommend quality adapter

## Testing

To verify if an adapter has this bug:

1. Run diagnostic script:
   ```bash
   python scripts/debug/diagnose_can_monitoring.py
   ```

2. Check output:
   - If "Valid CAN messages found: 0" → Adapter has bug
   - If "Valid CAN messages found: >0" → Adapter works correctly

3. Try targeted monitoring:
   ```bash
   python scripts/debug/targeted_can_monitor.py
   ```

4. If targeted monitoring works but ATMA doesn't → Confirmed ATMA header bug

## Related Files

- `scripts/debug/explore_can_bus.py` - Original CAN exploration script (affected by bug)
- `scripts/debug/targeted_can_monitor.py` - Workaround using ATCRA
- `scripts/debug/diagnose_can_monitoring.py` - Diagnostic tool to detect issue
- `.kiro/steering/communication-troubleshooting.md` - Troubleshooting guidance

## References

- ELM327 AT Command Set documentation
- ATMA: Monitor All (should include headers when ATH1 is set)
- ATCRA: CAN Receive Address (filtering forces headers to be included)
- ATH1: Headers On (works for normal commands, fails for ATMA on clones)

## Date Discovered

March 7, 2026 - Ford Escape 2008 testing with generic ELM327 v1.5 clone
