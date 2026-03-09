# Ford FDIM Display Control Reference

## ⚠️ CRITICAL SAFETY WARNING ⚠️

**DO NOT attempt FDIM control via standard OBD-II connection!**

### Why FDIM Control via OBD-II is Dangerous

**Ford Escape 2008 has TWO separate CAN buses**:
- **HS-CAN (500 kbps)**: Safety-critical modules (ABS, PCM, brakes, steering) - accessible via OBD-II
- **MS-CAN (125 kbps)**: Comfort modules (FDIM, HVAC, audio) - NOT accessible via standard OBD-II

**The Problem**:
- FDIM is on MS-CAN
- OBD-II port connects to HS-CAN
- Standard ELM327 CANNOT access MS-CAN
- Attempting to send MS-CAN messages on HS-CAN interferes with safety systems

**What Happened During Testing**:
1. ABS light flickering
2. Warning sounds and "check brake system" message
3. ABS module communication failure
4. Loss of wheel speed data
5. Transmission gear data disappeared

**Conclusion**: FDIM control requires direct MS-CAN access, which is NOT available via standard OBD-II port.

### Requirements for FDIM Control

**Hardware**:
- Direct connection to MS-CAN bus (pins 3 & 11 on OBD-II connector)
- Dual-CAN adapter (CANtact, PCAN-USB, or similar)
- NOT possible with standard ELM327 via OBD-II

**Software**:
- Professional tools (FORScan with MS-CAN license)
- Understanding of MS-CAN protocols
- Ford-specific diagnostic procedures

**For this project**: Focus on HS-CAN modules (PCM, ABS) with READ-ONLY operations. Use FORScan for MS-CAN access.

---

## Overview

The FDIM (Front Display Interface Module) in Ford vehicles acts as a "slave" device on the CAN bus. This allows external devices to write custom text to the factory display, enabling features like custom track names, diagnostic information display, or real-time vehicle parameter monitoring.

## Technical Details

### Display Identification

**Common CAN IDs**:
- `0x415` - Primary FDIM display ID (most common)
- `0x417` - Alternative FDIM display ID (some models)

**Vehicle Compatibility**:
- Ford Escape 2008 (CD2 platform)
- Ford Fusion 2008-2012
- Mercury Mariner 2008-2011
- Mazda Tribute 2008-2011
- Other Ford vehicles with FDIM displays

### Message Format

**Encoding**: ASCII text encoding

**Structure**:
```
[Header Byte] [Character 1] [Character 2] ... [Character N]
```

**Header Byte**: Typically indicates message type or display mode
- Exact value varies by vehicle model
- Common values: `0x02`, `0x03`, `0x10`
- May need experimentation to determine correct header

**Character Bytes**: Standard ASCII characters
- Alphanumeric: A-Z, a-z, 0-9
- Special characters: space, dash, underscore
- Display width typically 8-16 characters depending on model

### Message Persistence

**Critical Requirement**: Messages must be sent repeatedly or the display will timeout.

**Timing**:
- **Recommended interval**: Every 500ms (2 Hz)
- **Minimum interval**: Every 1000ms (1 Hz)
- **Maximum interval**: Every 250ms (4 Hz) - faster may cause issues

**Timeout Behavior**:
- If messages stop, display reverts to default
- Default display: "FORD ESCAPE", clock, or radio station
- Timeout period: Typically 1-2 seconds

## Use Cases

### 1. Custom Track Names
Display custom audio track information on the factory screen.

**Example**: "NOW PLAYING: My Song Title"

### 2. Diagnostic Information Display
Show real-time diagnostic data on the factory screen.

**Examples**:
- "GEAR: D3 RPM: 2500"
- "SPEED: 65 MPH"
- "COOLANT: 195F"
- "ABS: OK TRANS: OK"

### 3. Custom Dashboards
Create custom information displays for specific purposes.

**Examples**:
- Performance monitoring (0-60 times, G-forces)
- Fuel economy tracking
- Trip computer information
- Warning/alert messages

### 4. Development/Testing
Display debug information during vehicle diagnostics.

**Examples**:
- "CAN ID: 0x228"
- "DID: 0x0200"
- "TEST MODE ACTIVE"

## Implementation Considerations

### Safety

**WARNING**: Displaying information on the factory screen while driving can be distracting.

**Safety Guidelines**:
- Keep messages brief and easy to read
- Avoid rapidly changing information
- Don't display critical warnings that require immediate action
- Consider disabling display updates above certain speeds
- Test thoroughly in safe environments first

### Technical Challenges

**1. Header Byte Discovery**:
- May require experimentation to find correct header
- Different models may use different headers
- Monitor existing FDIM traffic to identify patterns

**2. Display Width**:
- Character limit varies by model
- Exceeding limit may cause truncation or errors
- Test with different message lengths

**3. Message Timing**:
- Too fast: May overwhelm CAN bus or cause display issues
- Too slow: Display will timeout and revert to default
- Optimal: 500ms interval (2 Hz)

**4. CAN Bus Load**:
- Continuous messages add to CAN bus traffic
- Monitor bus utilization to avoid overload
- Consider reducing update rate if bus is busy

### Best Practices

**1. Message Design**:
- Use clear, concise text
- Abbreviate when necessary (e.g., "TEMP" not "TEMPERATURE")
- Use consistent formatting
- Test readability at a glance

**2. Update Strategy**:
- Only update when data changes (reduce bus load)
- Use fixed-width formatting for numeric values
- Implement smooth transitions between messages

**3. Error Handling**:
- Detect if display stops responding
- Gracefully handle CAN bus errors
- Provide fallback behavior if FDIM unavailable

**4. User Control**:
- Allow users to enable/disable custom display
- Provide option to revert to factory display
- Save user preferences

## Example Implementation

### Basic Display Writer (Python)

```python
import serial
import time

class FDIMDisplay:
    """Ford FDIM Display Controller"""
    
    def __init__(self, port='COM3', display_id=0x415, header=0x02):
        self.port = port
        self.display_id = display_id
        self.header = header
        self.elm = None
        self.running = False
    
    def connect(self):
        """Connect to ELM327 adapter"""
        self.elm = serial.Serial(self.port, 38400, timeout=2)
        time.sleep(2)
        
        # Initialize ELM327
        self.send_command("ATZ")
        time.sleep(1)
        self.send_command("ATE0")
        self.send_command("ATL0")
        self.send_command("ATS0")
        self.send_command("ATH0")  # Headers off for sending
        self.send_command("ATSP6")  # CAN 500kbps
        
        # Set CAN ID for transmission
        self.send_command(f"ATSH{self.display_id:03X}")
    
    def send_command(self, cmd):
        """Send command to ELM327"""
        self.elm.write((cmd + '\r').encode())
        response = self.elm.read(1024).decode('ascii', errors='ignore')
        return response
    
    def write_text(self, text, duration=None):
        """
        Write text to FDIM display
        
        Args:
            text: Text to display (max 16 characters)
            duration: How long to display (seconds), None = continuous
        """
        # Truncate text if too long
        text = text[:16]
        
        # Convert to hex
        hex_bytes = [f"{self.header:02X}"]
        for char in text:
            hex_bytes.append(f"{ord(char):02X}")
        
        message = ' '.join(hex_bytes)
        
        # Send continuously
        self.running = True
        start_time = time.time()
        
        try:
            while self.running:
                self.send_command(message)
                time.sleep(0.5)  # 500ms interval
                
                # Check duration
                if duration and (time.time() - start_time) >= duration:
                    break
        
        except KeyboardInterrupt:
            self.running = False
    
    def stop(self):
        """Stop writing to display"""
        self.running = False
    
    def close(self):
        """Close connection"""
        if self.elm:
            self.elm.close()

# Example usage
if __name__ == "__main__":
    display = FDIMDisplay()
    display.connect()
    
    try:
        # Display custom message
        display.write_text("DIAGNOSTIC MODE", duration=10)
    finally:
        display.close()
```

### Advanced: Real-Time Data Display

```python
def display_realtime_data(display, data_source):
    """
    Display real-time vehicle data on FDIM
    
    Args:
        display: FDIMDisplay instance
        data_source: Function that returns current data
    """
    display.running = True
    
    try:
        while display.running:
            # Get current data
            data = data_source()
            
            # Format for display (16 char max)
            text = f"G:{data['gear']} {data['rpm']:4d}RPM"
            
            # Send to display
            hex_bytes = [f"{display.header:02X}"]
            for char in text:
                hex_bytes.append(f"{ord(char):02X}")
            
            message = ' '.join(hex_bytes)
            display.send_command(message)
            
            time.sleep(0.5)  # 500ms update rate
    
    except KeyboardInterrupt:
        display.running = False
```

## Testing Procedure

### Step 1: Identify Display ID

1. Monitor CAN bus traffic while radio is playing
2. Look for messages containing ASCII text
3. Common IDs: 0x415, 0x417
4. Note the CAN ID that carries track names

### Step 2: Determine Header Byte

1. Capture several FDIM messages
2. Identify the first byte (header)
3. Common values: 0x02, 0x03, 0x10
4. Test different headers if needed

### Step 3: Test Basic Display

1. Send simple message: "TEST"
2. Verify it appears on display
3. Confirm message persists with 500ms updates
4. Verify timeout behavior when updates stop

### Step 4: Test Character Set

1. Test alphanumeric characters
2. Test special characters (space, dash, etc.)
3. Identify any unsupported characters
4. Document character limitations

### Step 5: Optimize Timing

1. Test different update intervals
2. Find minimum interval before timeout
3. Find maximum interval that doesn't cause issues
4. Settle on optimal interval (typically 500ms)

## Integration with Diagnostic Agent

### Potential Features

**1. Diagnostic Status Display**:
- Show current diagnostic operation
- Display module being scanned
- Show DTC count as they're found

**2. Live Data Dashboard**:
- Real-time transmission gear
- Engine RPM and speed
- Coolant temperature
- Fuel level

**3. Warning/Alert System**:
- Display critical DTCs
- Show system status
- Alert user to issues

**4. Custom Information**:
- Trip computer data
- Performance metrics
- Fuel economy tracking

### Implementation Strategy

**Phase 1**: Basic display control
- Implement FDIM writer class
- Test with static messages
- Verify timing and persistence

**Phase 2**: Integration with CAN monitoring
- Display data from CAN bus explorer
- Show transmission gear from 0x228
- Show wheel speeds from 0x4B0

**Phase 3**: Integration with diagnostics
- Display diagnostic progress
- Show DTC results
- Display module scan status

**Phase 4**: Advanced features
- Custom dashboards
- User-configurable displays
- Data logging integration

## Known Issues and Limitations

### Display Limitations

**Character Set**:
- Limited to ASCII characters
- Some special characters may not display correctly
- No support for graphics or icons

**Display Width**:
- Typically 8-16 characters
- Varies by model and display type
- Longer messages will be truncated

**Update Rate**:
- Must maintain continuous updates
- Timeout causes revert to default
- Can't display static messages without continuous sending

### CAN Bus Considerations

**Bus Load**:
- Continuous messages add to bus traffic
- May interfere with other systems if bus is busy
- Monitor bus utilization

**Message Priority**:
- FDIM messages are low priority
- May be delayed if bus is busy
- Critical vehicle systems take precedence

### Safety Concerns

**Driver Distraction**:
- Custom displays can be distracting
- Rapidly changing information is dangerous
- Must comply with local laws regarding displays

**System Interference**:
- Incorrect messages could confuse FDIM
- May cause display errors or glitches
- Always test in safe environment first

## References

### Related Documentation

- `reference/Mazda_CAN_Bus_Reference.md` - CAN message definitions
- `reference/Valasek_Miller_Automotive_Networks_2014.md` - Ford CAN bus research
- `scripts/debug/explore_can_bus.py` - CAN bus exploration tool

### External Resources

- Ford FDIM technical specifications
- CAN bus protocol documentation
- ELM327 command reference

## Future Enhancements

### Planned Features

1. **Auto-discovery of FDIM ID**: Automatically detect correct CAN ID
2. **Header byte detection**: Automatically determine correct header
3. **Display templates**: Pre-configured display layouts
4. **User interface**: GUI for configuring custom displays
5. **Data logging**: Record displayed data for analysis

### Research Needed

1. **Multi-line displays**: Some FDIMs support multiple lines
2. **Graphics support**: Investigate if any graphics are possible
3. **Color control**: Some displays may support color changes
4. **Brightness control**: Adjust display brightness via CAN

## Disclaimer

**Safety Warning**: Modifying vehicle displays can be distracting and potentially dangerous. Always test in safe environments (parked vehicle) first. Comply with all local laws regarding vehicle modifications and driver distraction. The authors are not responsible for any accidents, injuries, or vehicle damage resulting from use of this information.

**Legal Notice**: This information is provided for educational and diagnostic purposes only. Modifying vehicle systems may void warranties or violate regulations. Always consult with qualified professionals before making modifications to vehicle systems.
