# OBD-II Traffic Logging & Debugging

## Overview

Comprehensive traffic logging system that captures all OBD-II communication flowing through the ELM327 adapter. This enables:

1. **Real-time Debugging** - See exactly what's being sent and received
2. **Test Case Creation** - Use captured traffic to create unit tests
3. **Protocol Analysis** - Understand OBD-II communication patterns
4. **Issue Diagnosis** - Troubleshoot communication problems
5. **Adapter Behavior Analysis** - Monitor ELM327 AT command responses

## What Gets Logged

### Every Message Logged Includes:

- **Timestamp** - Precise time to milliseconds (HH:MM:SS.ffffff)
- **Log Level** - DEBUG, INFO, WARNING, ERROR
- **Direction** - `[TX]` (transmitted) or `[RX]` (received)
- **Type** - AT COMMAND, OBD COMMAND, OBD RESPONSE, AT RESPONSE
- **Raw Data** - Hex representation showing all bytes
- **Parsed Data** - Clean, human-readable version

## Log File Location

```
logs/obd_traffic_YYYYMMDD_HHMMSS.log
```

- **Directory**: `logs/` (created automatically in project root)
- **Naming**: Each session gets unique timestamp
- **Format**: Tab-separated columns with timestamps

## Log Format Examples

### AT Command Logging
```
14:32:45.123456 | DEBUG | [TX] AT COMMAND: AT Z
14:32:45.234567 | DEBUG | [RX] [AT RESPONSE] Raw: 'OK\r>' (HEX: 4F 4B 0D 3E...)
14:32:45.234568 | DEBUG | [RX] [AT RESPONSE] Cleaned: OK
```

### OBD Command Logging
```
14:32:50.567890 | DEBUG | [TX] OBD COMMAND: 0100 (Mode: 01, PID: 00)
14:32:51.234567 | DEBUG | [RX] [OBD RESPONSE] Raw: '41 00 98 11 A0 13\r>' (HEX: 34 31 20 30 30...)
14:32:51.234568 | DEBUG | [RX] [OBD RESPONSE] Cleaned: 41 00 98 11 A0 13
14:32:51.234569 | DEBUG | [RX] OBD Response received: 41 00 98 11 A0 13
```

### Error Logging
```
14:32:55.123456 | ERROR | [ERROR] Serial error on AT command 'AT Z': Port not found
14:32:56.234567 | WARNING | [RX] Invalid OBD command: 0199
14:32:57.345678 | INFO | [RX] No data from vehicle for command 0902
```

## Accessing Traffic Logs

### From Menu (Option 10)

1. Run the diagnostic tool
2. Select **Option 10: View OBD-II Traffic Log**
3. Last 50 lines of current session displayed
4. Full log file path shown at top

### Manual Access

Logs are plain text files in the `logs/` directory:

```bash
# View last 100 lines
tail -n 100 logs/obd_traffic_20260119_143245.log

# Search for specific commands
grep "OBD COMMAND" logs/obd_traffic_20260119_143245.log

# Find all VIN requests
grep "0902" logs/obd_traffic_20260119_143245.log

# Find errors
grep "ERROR" logs/obd_traffic_20260119_143245.log
```

## Understanding Log Entries

### AT Commands (Adapter Configuration)

**Format**: `AT` followed by command code
- `AT Z` - Reset adapter
- `AT E0` - Disable echo
- `AT L0` - Disable linefeeds
- `AT SP6` - Set protocol to CAN
- `AT RV` - Read voltage
- `AT DP` - Detect protocol
- `AT DPN` - Detect protocol by number

**Example**:
```
[TX] AT COMMAND: AT SP6
[RX] [AT RESPONSE] Raw: 'OK\r>' 
[RX] [AT RESPONSE] Cleaned: OK
```

### OBD Commands (Vehicle Diagnostics)

**Format**: Hexadecimal mode + PID
- `0100` - Mode 01 (current data), PID 00 (supported PIDs)
- `0902` - Mode 09 (vehicle info), PID 02 (VIN)
- `0101` - Mode 01 (current data), PID 01 (DTC status)
- `1903` - Mode 19 (DTC codes), PID 03 (stored codes)

**Example**:
```
[TX] OBD COMMAND: 0902 (Mode: 09, PID: 02)
[RX] [OBD RESPONSE] Raw: '49 02 01 46 4F 52 44 20 45 53 43 41 50 45 20 45...'
[RX] [OBD RESPONSE] Cleaned: 49 02 01 46 4F 52 44 20 45 53 43 41 50 45 20 45...
```

### Response Data

Response hex values:
- `41` - Mode 01 response to mode 01 command
- `49` - Mode 09 response to mode 09 command
- `NO DATA` - Vehicle doesn't support this command
- `?` - Adapter doesn't recognize command format
- `UNABLE TO CONNECT` - Communication timeout

## Creating Test Cases from Logs

### Step 1: Extract Relevant Traffic

Find the commands you want to test:
```bash
grep -A 3 "OBD COMMAND: 0902" logs/obd_traffic_20260119_143245.log
```

### Step 2: Document Inputs and Outputs

Create test case:
```python
# Test case from captured traffic
test_data = {
    'command': '0902',           # VIN request
    'mode': '09',
    'pid': '02',
    'expected_response': '49 02 01 46 4F 52 44...',  # From log
    'vehicle': '2008 Ford Escape'
}
```

### Step 3: Use in Tests

```python
def test_vin_request(adapter):
    """Test VIN reading using captured traffic"""
    response = adapter.send_obd_command('0902')
    assert response.startswith('49 02')
```

## Common Log Patterns

### Successful VIN Read
```
[TX] OBD COMMAND: 0902 (Mode: 09, PID: 02)
[RX] [OBD RESPONSE] Raw: '49 02 01 46 4F 52 44...'
[RX] [OBD RESPONSE] Cleaned: 49 02 01 46 4F 52 44 20 45 53 43 41 50 45...
[RX] OBD Response received: 49 02 01 46 4F 52 44 20 45 53 43 41 50 45...
```
✓ Vehicle responded with data

### Unsupported Command
```
[TX] OBD COMMAND: 0199 (Mode: 01, PID: 99)
[RX] [OBD RESPONSE] Raw: '?\r>'
[RX] [OBD RESPONSE] Cleaned: ?
[RX] Invalid OBD command: 0199
```
✓ Adapter recognizes format but vehicle doesn't support it

### No Response (Timeout)
```
[TX] OBD COMMAND: 0902 (Mode: 09, PID: 02)
[RX] [OBD RESPONSE] Raw: 'NO DATA\r>'
[RX] [OBD RESPONSE] Cleaned: NO DATA
[RX] No data from vehicle for command 0902
```
✓ Vehicle doesn't respond or doesn't support this mode

## Debugging with Logs

### Problem: Vehicle Not Responding

**What to look for**:
- Lots of `NO DATA` responses
- `UNABLE TO CONNECT` messages
- No AT command responses after connection

**Solutions**:
1. Check CAN bus mode in logs (should see `AT SP6` commands)
2. Verify protocol detection (grep for `AT DP`)
3. Ensure vehicle is in RUN position during test

### Problem: Command Errors

**What to look for**:
- `?` responses instead of data
- Serial error messages
- Connection drops (large time gaps in log)

**Solutions**:
1. Check command format (Mode: should be 01-19)
2. Verify PID is supported (test with 0100 first)
3. Check for timing issues (too many commands too fast)

### Problem: Corrupted Responses

**What to look for**:
- Invalid hex characters in response
- Responses shorter than expected
- Partial data received

**Solutions**:
1. Increase timeout value in adapter
2. Reduce command frequency
3. Check serial connection quality

## Log Analysis Tools

### Count All Commands Sent
```bash
grep "\[TX\] OBD COMMAND" logs/obd_traffic_20260119_143245.log | wc -l
```

### Find All Errors
```bash
grep "ERROR" logs/obd_traffic_20260119_143245.log
```

### Extract Just Commands and Responses
```bash
grep "\[TX\]\|\[RX\]" logs/obd_traffic_20260119_143245.log | head -50
```

### Get Session Statistics
```bash
echo "Commands sent: $(grep '\[TX\]' logs/obd_traffic_*.log | wc -l)"
echo "Responses received: $(grep '\[RX\]' logs/obd_traffic_*.log | wc -l)"
echo "Errors: $(grep 'ERROR' logs/obd_traffic_*.log | wc -l)"
```

## Log Retention

- **Default**: All logs retained indefinitely
- **Manual Cleanup**: Delete old logs from `logs/` directory
- **Archive**: Copy logs to backup location
- **Space**: Each log ~100KB per 100 commands (varies with data size)

## Best Practices

1. **Clear Logs Regularly** - Keep only relevant sessions
2. **Name Sessions** - Copy log with meaningful name for reference
3. **Document Issues** - Note errors and commands that fail
4. **Use for Debugging** - Compare successful vs failed runs
5. **Create Test Suite** - Build unit tests from captured logs
6. **Share with Support** - Include logs when reporting issues

## Privacy Note

⚠️ **Traffic logs may contain sensitive data**:
- VINs (vehicle identification)
- Mileage
- Fault codes
- Vehicle location (if GPS via OBD)

**Be careful when sharing logs** - Review for sensitive information first.

## Related Features

- See [VEHICLE_DETECTION.md](VEHICLE_DETECTION.md) for connection diagnostics
- See [EMISSIONS_READINESS.md](EMISSIONS_READINESS.md) for emissions data
- See [COM_PORT_SELECTION.md](COM_PORT_SELECTION.md) for port management

## File Structure

```
obd/
├── logs/
│   ├── obd_traffic_20260119_143245.log    ← Current session
│   ├── obd_traffic_20260119_132100.log    ← Previous session
│   └── ...
├── elm327_diagnostic/
│   └── elm327_adapter.py                  ← Logging implementation
├── OBD_TRAFFIC_LOGGING.md                 ← This file
└── ...
```

## Troubleshooting Logging

### Logs Directory Not Created

**Solution**: Ensure project has write permissions to current directory

### Very Large Log Files

**Cause**: Running many commands for extended periods
**Solution**: Archive old logs, clean up regularly

### No Logs Appearing

**Check**: 
1. Is option 10 showing "No traffic data yet"?
2. Have you sent any OBD commands yet?
3. Check `logs/` directory exists

### Can't Open Traffic Log

**Solution**: Use text editor or `cat`/`type` commands (don't use binary viewers)

## Advanced Usage

### Convert Hex Responses to ASCII

```python
# From captured log
hex_response = "49 02 01 46 4F 52 44 20 45 53 43 41 50 45 20 45"
text = bytes.fromhex(hex_response.replace(" ", "")).decode('ascii')
print(text)  # Output: I .FORD ESCAPE E
```

### Extract Traffic for Specific Commands

```bash
# Get all emissions monitor checks
grep "0101" logs/obd_traffic_*.log

# Get all voltage readings
grep "AT RV" logs/obd_traffic_*.log
```

### Performance Analysis

```bash
# Find slowest response times
# (grep timestamps and calculate deltas)
```

## ELM327 Passive Sniffing Note

- Many ELM327 adapters (especially v1.x / common v1.5 clones) are request/response devices and do not support true passive CAN bus sniffing. That means listening for unsolicited module broadcasts (button presses, periodic module chatter) will often capture 0 frames.
- Quick checks: run `AT I` to get the adapter version and `AT DP` to verify protocol; some vendor builds may expose monitor commands (`AT MA`, `AT M`) but support is rare.
- Recommendation: for passive captures use a listen-capable interface (CANable, CANtact, Kvaser, Peak, or a Raspberry Pi + MCP2515 in listen-only mode). If you must use an ELM327, instrument the bus by sending requests that provoke responses instead of relying on passive broadcasts.

