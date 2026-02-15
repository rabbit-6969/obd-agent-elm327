# COM Port Selection Feature

## Overview

The diagnostic tool now automatically detects available COM ports and allows users to select from them if the default connection fails.

## How It Works

### 1. Default Connection Attempt
When you start the tool, it attempts to connect to the default port (COM3):
```
Attempting to connect to adapter on COM3...
✗ Failed to connect to ELM327 adapter

Would you like to select a different COM port? (y/n):
```

### 2. Port Selection
If you answer `y`, the tool:
- Scans your system for available COM ports
- Tests each port to ensure it's accessible
- Displays a numbered list for you to choose from

```
============= SELECT COM PORT =============

Scanning for available COM ports...
✓ Found 3 accessible port(s):

  1. COM3   - USB Serial Port
  2. COM4   - Intel ActiveKey
  3. COM5   - ProlificUSB-to-Serial Comm Port

Select port number (or 'c' to cancel):
```

### 3. Connection Attempt
After selecting a port, the tool attempts to connect:
```
Attempting to connect to COM5...
✓ Successfully connected to COM5
```

## Features

✅ **Automatic Port Detection** - Scans for all available COM ports  
✅ **Port Testing** - Only shows accessible ports  
✅ **Easy Selection** - Simple numbered menu  
✅ **Retry Option** - Can try different ports without restarting  
✅ **User Friendly** - Clean UI with clear status messages  

## Usage Examples

### Scenario 1: Default Works
```
Attempting to connect to adapter on COM3...
✓ Connected to ELM327 adapter successfully
```

### Scenario 2: Default Fails, User Selects Different Port
```
Attempting to connect to adapter on COM3...
✗ Failed to connect to ELM327 adapter

Would you like to select a different COM port? (y/n): y

============= SELECT COM PORT =============

Scanning for available COM ports...
✓ Found 2 accessible port(s):

  1. COM4   - USB Serial Port
  2. COM5   - USB Serial Port

Select port number (or 'c' to cancel): 1

Attempting to connect to COM4...
✓ Successfully connected to COM4
```

### Scenario 3: No Ports Available
```
Attempting to connect to adapter on COM3...
✗ Failed to connect to ELM327 adapter

Would you like to select a different COM port? (y/n): y

============= SELECT COM PORT =============

Scanning for available COM ports...
⚠ No accessible COM ports found

  Check that your ELM327 adapter is connected
```

## New Module

### `com_port_detector.py`

Provides the `COMPortDetector` class with three key methods:

```python
# Get all available COM ports (detected by OS)
ports = COMPortDetector.get_available_ports()
# Returns: [('COM3', 'USB Serial Port'), ('COM4', 'Intel ActiveKey')]

# Test if a specific port is accessible
is_accessible = COMPortDetector.test_port('COM3')
# Returns: True or False

# Get only accessible COM ports
accessible_ports = COMPortDetector.get_accessible_ports()
# Returns: [('COM3', 'USB Serial Port'), ('COM4', 'Intel ActiveKey')]
```

## Modified Files

### `main.py`
- Added import: `from com_port_detector import COMPortDetector`
- Updated `connect()` method to prompt user if default fails
- Added new `select_and_connect_port()` method for port selection

## Configuration

No additional configuration needed! The feature works automatically.

If you want to change the default port, edit `main.py`:

```python
def main():
    PORT = "COM3"  # Change this to your preferred default port
```

## Technical Details

### Port Detection
Uses `serial.tools.list_ports` to detect all COM ports available on the system.

### Port Testing
Creates a temporary connection to test if a port is accessible. This ensures only working ports are presented to the user.

### Error Handling
- Gracefully handles missing ports
- Validates user input
- Allows cancellation at any time
- Supports retry attempts

## Benefits

1. **Better UX** - Users don't have to manually find their COM port
2. **Automatic Discovery** - Scans system for available ports
3. **Error Recovery** - Recover from wrong port without restarting
4. **Non-Intrusive** - Only appears when needed (connection fails)
5. **Professional** - Clean, organized interface with clear options

## Troubleshooting

### "No accessible COM ports found"
- Ensure your ELM327 adapter is connected
- Check Device Manager to see if adapter appears
- Try reinstalling USB drivers
- Restart the tool and try again

### "Failed to connect" for all ports
- Verify ELM327 adapter is powered on
- Check that vehicle is in RUN position
- Verify CAN bus mode (High/Low) is correct for your vehicle
- Try different baud rates (if needed)

### Port disappears after selection
- USB connection may have been lost
- Reconnect the adapter and try again
- The tool will allow you to reselect from available ports

## Future Enhancements

Possible future improvements:
- Save user's preferred COM port
- Auto-detect ELM327 adapters specifically
- Test multiple ports in parallel
- Add port history/favorites
