#!/usr/bin/env python3
"""
Capture FORScan Commands via ELM327 Monitoring
Since we can't sniff COM3 while FORScan uses it, this script:
1. Enables ELM327 echo and headers
2. Logs all traffic to file
3. You run FORScan, then we analyze the logs
"""

from toolkit.vehicle_communication.elm327_base import ELM327Base
import time
from datetime import datetime
import json

def setup_elm327_logging(port='COM3'):
    """
    Setup ELM327 for maximum logging
    """
    print('=' * 70)
    print('FORSCAN COMMAND CAPTURE SETUP')
    print('=' * 70)
    print()
    print('This will configure ELM327 to log all traffic.')
    print('After setup, close this script and use FORScan.')
    print('All commands will be logged by the ELM327.')
    print()
    
    adapter = ELM327Base(port)
    adapter.connect()
    
    print('Configuring ELM327 for logging...')
    
    # Enable echo (see commands sent)
    adapter.send_command('AT E1')
    print('✓ Echo enabled')
    
    # Enable headers (see full CAN frames)
    adapter.send_command('AT H1')
    print('✓ Headers enabled')
    
    # Enable spaces (easier to read)
    adapter.send_command('AT S1')
    print('✓ Spaces enabled')
    
    # Show all data (not just responses)
    adapter.send_command('AT CAF1')
    print('✓ CAN Auto Formatting enabled')
    
    # Monitor all CAN traffic
    adapter.send_command('AT MA')
    print('✓ Monitor All mode enabled')
    
    print()
    print('✓ ELM327 configured for logging')
    print()
    print('IMPORTANT: ELM327 is now in monitor mode!')
    print('It will capture all CAN traffic.')
    print()
    print('To use with FORScan:')
    print('1. Close this script')
    print('2. Open FORScan')
    print('3. FORScan will reset the adapter and use it normally')
    print('4. Check FORScan logs for captured commands')
    print()
    
    adapter.disconnect()

def analyze_forscan_logs(log_path):
    """
    Analyze FORScan log files to extract HVAC commands
    """
    print('=' * 70)
    print('FORSCAN LOG ANALYZER')
    print('=' * 70)
    print(f'Analyzing: {log_path}')
    print()
    
    # This would parse FORScan log files
    # FORScan logs are typically in its installation directory
    # Look for files like: FORScan_log_YYYYMMDD.txt
    
    print('FORScan log locations:')
    print('  - C:\\Program Files (x86)\\FORScan\\Logs\\')
    print('  - C:\\Users\\[username]\\AppData\\Local\\FORScan\\Logs\\')
    print('  - FORScan installation directory\\Logs\\')
    print()
    print('Look for files containing HVAC communication')
    print()

def create_manual_capture_guide():
    """
    Create a guide for manually capturing FORScan commands
    """
    guide = """
# FORScan Command Capture Guide

## Method 1: Use FORScan's Built-in Logging

1. **Enable FORScan Logging:**
   - Open FORScan
   - Go to Settings/Options
   - Enable "Detailed Logging" or "Debug Mode"
   - Set log level to maximum

2. **Perform HVAC Diagnostics:**
   - Connect to vehicle
   - Navigate to HVAC module (usually 7A0)
   - Read DTCs
   - Read live data
   - Perform any tests

3. **Find Log Files:**
   - Check FORScan installation directory
   - Look in: `C:\\Program Files (x86)\\FORScan\\Logs\\`
   - Or: `C:\\Users\\[username]\\AppData\\Local\\FORScan\\Logs\\`
   - Files named like: `FORScan_log_YYYYMMDD.txt`

4. **Extract Commands:**
   - Open log file
   - Look for lines with "7A0" (HVAC address)
   - Copy all commands and responses
   - Save to: `logs/forscan_hvac_commands.txt`

## Method 2: Use COM Port Monitor Tool

1. **Install COM Port Monitor:**
   - Free option: Portmon (Microsoft)
   - Paid option: Device Monitoring Studio
   - Alternative: Serial Port Monitor

2. **Setup Monitoring:**
   - Start monitor tool
   - Select COM3
   - Start capture
   - Open FORScan
   - Perform HVAC diagnostics
   - Stop capture

3. **Save Capture:**
   - Export to text file
   - Save as: `logs/com3_forscan_capture.txt`

## Method 3: Manual Command Recording

1. **In FORScan:**
   - Note each command sent
   - Note each response received
   - Take screenshots if needed

2. **Record Format:**
   ```
   Command: [hex bytes]
   Response: [hex bytes]
   Description: [what it does]
   ```

3. **Focus on:**
   - Module initialization
   - DTC read commands
   - Live data requests
   - Any HVAC-specific commands

## What to Look For

### Key Commands:
- **Module Init:** Usually starts with AT commands
- **Set Header:** AT SH 7A0 (or similar)
- **Set Protocol:** AT SP [number]
- **DTC Read:** Mode 19 or proprietary
- **Live Data:** Mode 22 or proprietary
- **Clear DTCs:** Mode 14 or proprietary

### Example FORScan HVAC Session:
```
> AT Z          (reset)
< ELM327 v1.5

> AT SP 6       (set protocol ISO 15765-4 CAN)
< OK

> AT SH 7A0     (set header to HVAC)
< OK

> 19 02 AF      (read DTCs - UDS Mode 19)
< 59 02 AF ...  (response with DTCs)

> 22 F1 90      (read VIN - UDS Mode 22)
< 62 F1 90 ...  (response with VIN)
```

## After Capture

1. **Organize Data:**
   - Separate commands by function
   - Group related sequences
   - Note timing between commands

2. **Analyze Patterns:**
   - Identify command structure
   - Find response patterns
   - Determine checksums/validation

3. **Implement:**
   - Add to `elm327_base.py`
   - Create HVAC-specific functions
   - Test with vehicle

## Files to Create

- `logs/forscan_hvac_commands.txt` - Raw commands
- `logs/forscan_hvac_analysis.md` - Analysis notes
- `knowledge_base/Ford_HVAC_protocol.md` - Protocol documentation
"""
    
    with open('FORSCAN_CAPTURE_GUIDE.md', 'w') as f:
        f.write(guide)
    
    print('✓ Created: FORSCAN_CAPTURE_GUIDE.md')
    print()
    print('Read this guide for detailed instructions on capturing FORScan commands')

if __name__ == '__main__':
    print()
    print('FORScan Command Capture Tool')
    print()
    print('Options:')
    print('1. Create capture guide (recommended)')
    print('2. Setup ELM327 logging (advanced)')
    print('3. Analyze FORScan logs (if you have log files)')
    print()
    
    choice = input('Select option (1-3): ')
    
    if choice == '1':
        create_manual_capture_guide()
        print()
        print('Next steps:')
        print('1. Read FORSCAN_CAPTURE_GUIDE.md')
        print('2. Enable logging in FORScan')
        print('3. Perform HVAC diagnostics')
        print('4. Share the log files')
        
    elif choice == '2':
        setup_elm327_logging()
        
    elif choice == '3':
        log_path = input('Enter FORScan log file path: ')
        analyze_forscan_logs(log_path)
        
    else:
        print('Invalid choice')
