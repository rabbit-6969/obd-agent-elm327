# Using Discovered Vehicle Capabilities - Quick Reference

**Purpose:** How to use DIDs, routines, and actuations discovered by the scanner

---

## Reading DIDs (Service 0x22)

### Basic Command Format

```python
import serial
import time

ser = serial.Serial('COM3', 38400, timeout=1)
time.sleep(2)

# Initialize
ser.write(b"ATZ\r")
time.sleep(1)
ser.write(b"ATE0\r")
ser.write(b"ATSP0\r")

# Set target module (e.g., PCM at 0x7E0)
ser.write(b"ATSH7E0\r")

# Read DID 0x0100 (Transmission Fluid Temperature)
ser.write(b"220100\r")
time.sleep(0.2)
response = ser.read(ser.in_waiting).decode()
print(response)  # Should see: 62 01 00 XX

ser.close()
```

### Parsing DID Responses

```python
def parse_did_response(response, did):
    """Parse UDS DID response"""
    clean = response.replace(' ', '').replace('>', '').strip()
    
    # Check for positive response (62 = 0x22 + 0x40)
    if clean.startswith('62'):
        # Extract DID echo
        did_echo = clean[2:6]
        # Extract data bytes
        data = clean[6:]
        return {
            'success': True,
            'did': did_echo,
            'data': data,
            'raw': response
        }
    
    # Check for negative response (7F 22 XX)
    elif clean.startswith('7F22'):
        nrc = clean[4:6]
        return {
            'success': False,
            'nrc': nrc,
            'raw': response
        }
    
    return {'success': False, 'error': 'Invalid response'}

# Example usage
response = "62 01 00 0C"
result = parse_did_response(response, 0x0100)
if result['success']:
    temp_hex = int(result['data'], 16)
    temp_celsius = temp_hex - 40
    print(f"Temperature: {temp_celsius}°C")
```

---

## Running Routines (Service 0x31)

### Basic Routine Execution

```python
def run_routine(ser, rid, wait_time=5):
    """Execute a routine and get results"""
    
    # 1. Start routine
    cmd = f"3101{rid:04X}\r"
    ser.write(cmd.encode())
    time.sleep(0.2)
    start_response = ser.read(ser.in_waiting).decode()
    print(f"Start: {start_response}")
    
    # Check if started successfully (71 01 = positive response)
    if '71 01' not in start_response:
        return {'success': False, 'error': 'Failed to start routine'}
    
    # 2. Wait for routine to complete
    print(f"Waiting {wait_time} seconds for routine to complete...")
    time.sleep(wait_time)
    
    # 3. Request results
    cmd = f"3103{rid:04X}\r"
    ser.write(cmd.encode())
    time.sleep(0.2)
    results_response = ser.read(ser.in_waiting).decode()
    print(f"Results: {results_response}")
    
    # 4. Stop routine (if needed)
    cmd = f"3102{rid:04X}\r"
    ser.write(cmd.encode())
    time.sleep(0.2)
    stop_response = ser.read(ser.in_waiting).decode()
    print(f"Stop: {stop_response}")
    
    return {
        'success': True,
        'start': start_response,
        'results': results_response,
        'stop': stop_response
    }

# Example: Run transmission self-test (RID 0x0201)
result = run_routine(ser, 0x0201, wait_time=10)
```

### Routine Sub-Functions

| Sub-function | Value | Command Format | Description |
|--------------|-------|----------------|-------------|
| startRoutine | 0x01 | `31 01 [RID]` | Start the routine |
| stopRoutine | 0x02 | `31 02 [RID]` | Stop the routine |
| requestRoutineResults | 0x03 | `31 03 [RID]` | Get results |

---

## Controlling Actuations (Service 0x2F)

### ⚠️ SAFETY WARNING

**CAUTION:** Service 0x2F directly controls vehicle actuators!

- Always ensure safe conditions
- Never actuate while vehicle is in motion
- Always return control to ECU when finished
- Some actuations may damage components if misused

### Basic Actuation Control

```python
def control_actuator(ser, did, value=None):
    """Control an actuator via Service 0x2F"""
    
    if value is None:
        # Return control to ECU (safe)
        cmd = f"2F{did:04X}00\r"
        action = "Returning control to ECU"
    else:
        # Set to specific value
        cmd = f"2F{did:04X}03{value:02X}\r"
        action = f"Setting to {value}"
    
    print(f"{action}...")
    ser.write(cmd.encode())
    time.sleep(0.2)
    response = ser.read(ser.in_waiting).decode()
    print(f"Response: {response}")
    
    # Check for positive response (6F = 0x2F + 0x40)
    if '6F' in response:
        return {'success': True, 'response': response}
    else:
        return {'success': False, 'response': response}

# Example: Control shift solenoid (DID 0x0103)
# CAUTION: Only do this in safe conditions!

# 1. Read current state
ser.write(b"220103\r")
time.sleep(0.2)
current = ser.read(ser.in_waiting).decode()
print(f"Current state: {current}")

# 2. Take control and set to 50%
result = control_actuator(ser, 0x0103, value=0x32)  # 0x32 = 50 decimal = 50%

# 3. Wait and observe
time.sleep(2)

# 4. ALWAYS return control to ECU
result = control_actuator(ser, 0x0103)  # No value = return control
```

### Control Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| returnControlToECU | 0x00 | Return control to ECU (ALWAYS use when done) |
| resetToDefault | 0x01 | Reset to default state |
| freezeCurrentState | 0x02 | Freeze at current value |
| shortTermAdjustment | 0x03 | Set to specific value |

---

## Complete Example: Transmission Diagnostics

```python
import serial
import time

class TransmissionDiagnostics:
    def __init__(self, port='COM3'):
        self.ser = serial.Serial(port, 38400, timeout=1)
        time.sleep(2)
        self.initialize()
    
    def initialize(self):
        """Initialize ELM327"""
        self.ser.write(b"ATZ\r")
        time.sleep(1)
        self.ser.write(b"ATE0\r")
        self.ser.write(b"ATSP0\r")
        self.ser.write(b"ATSH7E0\r")  # Target PCM
    
    def read_fluid_temp(self):
        """Read transmission fluid temperature (DID 0x0100)"""
        self.ser.write(b"220100\r")
        time.sleep(0.2)
        response = self.ser.read(self.ser.in_waiting).decode()
        
        # Parse: 62 01 00 XX
        if '62 01 00' in response:
            hex_val = response.split()[-1]
            temp_c = int(hex_val, 16) - 40
            return temp_c
        return None
    
    def read_line_pressure(self):
        """Read transmission line pressure (DID 0x0101)"""
        self.ser.write(b"220101\r")
        time.sleep(0.2)
        response = self.ser.read(self.ser.in_waiting).decode()
        
        # Parse: 62 01 01 XX XX
        if '62 01 01' in response:
            parts = response.split()
            if len(parts) >= 5:
                pressure_hex = parts[3] + parts[4]
                pressure_raw = int(pressure_hex, 16)
                return pressure_raw  # Formula TBD
        return None
    
    def run_self_test(self):
        """Run transmission self-test (RID 0x0201)"""
        # Start test
        self.ser.write(b"31010201\r")
        time.sleep(0.2)
        start = self.ser.read(self.ser.in_waiting).decode()
        print(f"Test started: {start}")
        
        # Wait for completion
        time.sleep(10)
        
        # Get results
        self.ser.write(b"31030201\r")
        time.sleep(0.2)
        results = self.ser.read(self.ser.in_waiting).decode()
        print(f"Test results: {results}")
        
        return results
    
    def close(self):
        self.ser.close()

# Usage
diag = TransmissionDiagnostics()

print("Reading transmission parameters...")
temp = diag.read_fluid_temp()
pressure = diag.read_line_pressure()

print(f"Fluid Temperature: {temp}°C")
print(f"Line Pressure: {pressure} (raw)")

print("\nRunning self-test...")
results = diag.run_self_test()

diag.close()
```

---

## Error Handling

### Negative Response Codes (NRC)

Common NRCs you'll encounter:

| NRC | Mnemonic | Description | Solution |
|-----|----------|-------------|----------|
| 0x11 | SNS | serviceNotSupported | Service not available on this module |
| 0x12 | SFNS | sub-functionNotSupported | Sub-function not supported |
| 0x13 | IMLOIF | incorrectMessageLength | Check command format |
| 0x22 | CNC | conditionsNotCorrect | Check vehicle conditions (park, engine running, etc.) |
| 0x31 | ROOR | requestOutOfRange | DID/RID not supported or invalid value |
| 0x33 | SAD | securityAccessDenied | Requires security access (Service 0x27) |

### Example Error Handler

```python
def handle_negative_response(response):
    """Parse and explain negative response"""
    clean = response.replace(' ', '')
    
    if clean.startswith('7F'):
        service = clean[2:4]
        nrc = clean[4:6]
        
        nrc_meanings = {
            '11': 'Service not supported',
            '12': 'Sub-function not supported',
            '13': 'Incorrect message length',
            '22': 'Conditions not correct',
            '31': 'Request out of range',
            '33': 'Security access denied',
        }
        
        meaning = nrc_meanings.get(nrc, 'Unknown error')
        print(f"Error: Service 0x{service}, NRC 0x{nrc} - {meaning}")
        return False
    
    return True
```

---

## Best Practices

### 1. Always Initialize Properly

```python
# Full initialization sequence
commands = [
    "ATZ",      # Reset
    "ATE0",     # Echo off
    "ATL0",     # Linefeeds off
    "ATSP0",    # Auto protocol
    "ATST32",   # Timeout 32ms
    "ATH1",     # Headers on (to see addresses)
]

for cmd in commands:
    ser.write((cmd + "\r").encode())
    time.sleep(0.1)
```

### 2. Set Target Module

```python
# Always set target module before sending diagnostic commands
ser.write(b"ATSH7E0\r")  # PCM
time.sleep(0.1)
```

### 3. Handle Timeouts

```python
def send_with_retry(ser, cmd, max_retries=3):
    """Send command with retry logic"""
    for attempt in range(max_retries):
        ser.write((cmd + "\r").encode())
        time.sleep(0.2)
        response = ser.read(ser.in_waiting).decode()
        
        if response and "NO DATA" not in response:
            return response
        
        print(f"Retry {attempt + 1}/{max_retries}...")
        time.sleep(0.5)
    
    return None
```

### 4. Always Return Control

```python
try:
    # Control actuator
    control_actuator(ser, 0x0103, value=0x50)
    time.sleep(2)
finally:
    # ALWAYS return control, even if error occurs
    control_actuator(ser, 0x0103)  # Return to ECU
```

---

## References

- `discover_vehicle_capabilities.py` - Scanner tool
- `VEHICLE_CAPABILITY_DISCOVERY.md` - Discovery guide
- `reference/ISO_14229-1_UDS_Service_0x22_ReadDataByIdentifier.md`
- `reference/ISO_14229-1_UDS_Service_0x31_RoutineControl.md`
- `reference/ISO_14229-1_UDS_Service_0x2F_InputOutputControlByIdentifier.md`

---

**Last Updated:** 2026-02-15
