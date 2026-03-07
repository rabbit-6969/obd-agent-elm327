---
inclusion: fileMatch
fileMatchPattern: '*Nissan*|*Infiniti*|*Datsun*'
---

# Nissan/Infiniti/Datsun Specific Diagnostic Guidance

This steering file is automatically included when working with Nissan, Infiniti, or Datsun vehicles.

## Critical: Multi-Protocol Architecture

**Early 2000s Nissan/Infiniti vehicles (2002-2005) use a COMPLEX multi-protocol architecture:**

### Protocol Mix (2002 Infiniti, 350Z, G35 Era)
These vehicles are "a mess of dissimilar modules just stuck together" with **3-4 different protocols**:

1. **ISO-9141-2** (K-Line, pins 7/15)
   - Used for: OBD-II standard diagnostics
   - Speed: VERY SLOW (10.4 kbaud)
   - Characteristics: Bare minimum OBD-II implementation
   - **CRITICAL**: Requires long timeouts and inter-request delays

2. **ISO-14230 (KWP2000)** (K-Line, pins 7/15)
   - Used for: Manufacturer-specific diagnostics
   - Speed: Faster than ISO-9141
   - Access: Requires Fast Init sequence
   - Addressing: Physical addressing mode (0x81) per module

3. **CAN Bus** (pins 6/14)
   - Used for: Broadcast data between modules
   - Not used for diagnostics on these models
   - Passive monitoring only

4. **UART Protocol** (proprietary)
   - Used for: HVAC module to instrument cluster communication
   - Not accessible via OBD-II port
   - Proprietary Nissan implementation

## ISO-9141-2 OBD-II Diagnostics

### Critical Timing Requirements

**MUST implement these delays or you'll get flakey responses:**

```python
# After sending request
response = send_command(request)
wait_for_response(response)  # Wait for complete response

# CRITICAL: Add 100ms delay before next request
time.sleep(0.1)  # Minimum 100ms between requests

# Next request
next_response = send_command(next_request)
```

### Timeout Configuration

**Set LONG timeouts for ISO-9141:**
- Minimum: 2 seconds
- Recommended: 3-5 seconds for complex requests
- The protocol is SLOW - don't rush it

### Characteristics

- **Bare minimum OBD-II implementation**
- Limited PID support compared to other manufacturers
- Slow response times
- Sensitive to timing - must respect delays
- May not respond if requests sent too quickly

### Example Implementation

```python
class NissanISO9141:
    def __init__(self):
        self.timeout = 3.0  # Long timeout
        self.inter_request_delay = 0.1  # 100ms between requests
    
    def send_request(self, command):
        response = self._send(command)
        self._wait_for_complete_response(response)
        time.sleep(self.inter_request_delay)  # CRITICAL
        return response
```

## ISO-14230 (KWP2000) Manufacturer Diagnostics

### Advantages Over ISO-9141

- **Faster communication**
- **No inter-request delay required**
- **More reliable responses**
- **Access to manufacturer-specific services**

### Disadvantages

- **Does NOT serve OBD-II requests**
- **Requires Fast Init sequence per module**
- **Must use manufacturer-specific services**
- **Module-specific addressing required**

### Fast Init Procedure

**To enter ISO-14230 diagnostic mode:**

1. **Physical Addressing Mode**: Use address 0x81
2. **Target specific module address**
3. **Perform Fast Init sequence**
4. **Module will respond if successful**

### Module Addresses (2002-2005 Era)

**ABS Module: 0x28**
- **Test indicator**: Makes clicking sounds when Fast Init succeeds
- **Good for testing**: Audible feedback confirms connection
- **Services**: Manufacturer-specific DTC reading, live data

**Other Common Modules:**
- ECM (Engine): 0x10
- TCM (Transmission): 0x18
- BCM (Body Control): 0x60
- Airbag: 0x38

*Note: Addresses may vary by model/year - always verify*

### Fast Init Sequence Example

```python
def fast_init_kwp2000(module_address):
    """
    Perform ISO-14230 Fast Init for specific module
    
    Args:
        module_address: Module address (e.g., 0x28 for ABS)
    
    Returns:
        True if successful, False otherwise
    """
    # Physical addressing mode
    addressing_mode = 0x81
    
    # Fast Init timing (ISO-14230 specific)
    # 1. Send start communication request
    request = [addressing_mode, module_address, 0x81]  # Start Diagnostic Session
    
    # 2. Wait for key bytes response
    # 3. Module responds with key bytes if successful
    
    # For ABS (0x28): Listen for clicking sounds
    # This confirms successful init
    
    return response_received
```

### Service Access

Once Fast Init succeeds:
- Use manufacturer-specific service IDs
- No standard OBD-II services available
- Refer to Nissan service manual for service definitions
- DTC format is manufacturer-specific

## Protocol Selection Strategy

### Use ISO-9141 When:
- Reading standard OBD-II PIDs
- Checking emissions readiness
- Reading standard DTCs (P-codes)
- Using generic scan tools

**Remember**: Add 100ms delays between requests!

### Use ISO-14230 (KWP2000) When:
- Need faster communication
- Accessing manufacturer-specific data
- Reading module-specific DTCs
- Performing actuator tests
- Need reliable rapid polling

**Remember**: Requires Fast Init per module!

## Common Issues and Solutions

### Issue: Flakey Responses on ISO-9141

**Symptoms:**
- Intermittent "NO DATA" responses
- Responses work sometimes, fail other times
- Communication drops after several requests

**Solution:**
```python
# Add inter-request delay
time.sleep(0.1)  # 100ms minimum

# Increase timeout
timeout = 3.0  # seconds

# Wait for complete response before next request
wait_for_response_complete()
```

### Issue: Module Not Responding

**Check:**
1. Correct protocol selected (ISO-9141 vs ISO-14230)
2. Correct module address (for KWP2000)
3. Fast Init performed successfully (for KWP2000)
4. Vehicle in correct state (ignition on, engine off/on as needed)

### Issue: ABS Module Silent During Fast Init

**Expected Behavior:**
- ABS module (0x28) should make clicking sounds during successful Fast Init
- This is NORMAL and indicates successful connection
- No clicks = Fast Init failed or wrong address

## Platform Sharing

### Nissan/Infiniti Shared Platforms (2002-2005)

**VQ Platform (350Z/G35/FX35):**
- Infiniti G35 = Nissan Skyline V35
- Nissan 350Z = Fairlady Z Z33
- Infiniti FX35 shares VQ35 engine and many modules

**All use same diagnostic protocols:**
- ISO-9141 for OBD-II
- ISO-14230 for manufacturer diagnostics
- Same module addresses
- Same timing requirements

### Related Vehicles

- **2002-2008 Infiniti G35** = Nissan Skyline V35
- **2003-2008 Nissan 350Z** = Fairlady Z Z33
- **2003-2008 Infiniti FX35/FX45**
- **2002-2006 Nissan Altima** (similar protocols)
- **2004-2008 Nissan Maxima** (similar protocols)

## ELM327 Adapter Configuration

### For ISO-9141 (OBD-II)

```
ATZ          # Reset
ATE0         # Echo off
ATSP3        # Set protocol to ISO-9141-2
ATSTFF       # Set timeout to maximum
ATST FF      # Alternative timeout command
```

### For ISO-14230 (KWP2000)

```
ATZ          # Reset
ATE0         # Echo off
ATSP4        # Set protocol to ISO-14230 (5 baud init)
ATSP5        # Or ISO-14230 (fast init)
```

**Note**: Fast Init may require direct serial control, not all ELM327 adapters support it properly.

## Diagnostic Strategy

### Initial Connection

1. **Start with ISO-9141 for basic OBD-II**
   - Set long timeout (3+ seconds)
   - Add 100ms inter-request delays
   - Test with Mode 01 PID 00 (supported PIDs)

2. **If need manufacturer diagnostics, switch to ISO-14230**
   - Perform Fast Init for target module
   - Use manufacturer-specific services
   - Faster and more reliable than ISO-9141

### Module Discovery

**ISO-9141 Method:**
- Limited to OBD-II mandated modules (PCM only)
- Slow but works with any adapter

**ISO-14230 Method:**
- Scan module addresses (0x10, 0x18, 0x28, 0x38, 0x60, etc.)
- Perform Fast Init for each
- Listen for module-specific responses (ABS clicks, etc.)
- More comprehensive but requires Fast Init support

## Documentation Requirements

When documenting Nissan/Infiniti diagnostics:

1. **Always specify protocol used**
   - ISO-9141 or ISO-14230
   - Include timing parameters

2. **Document module addresses**
   - Physical address for KWP2000
   - Response characteristics (clicks, etc.)

3. **Note timing requirements**
   - Inter-request delays for ISO-9141
   - Fast Init success indicators

4. **Record service IDs**
   - Manufacturer-specific services
   - Response formats

## Safety Notes

### ABS Module Fast Init

**Expected behavior:**
- Clicking sounds during Fast Init are NORMAL
- This is the ABS module self-test
- Does NOT indicate a problem
- Confirms successful communication

**Safety:**
- Vehicle should be stationary
- Parking brake engaged
- Transmission in Park
- No safety risk from clicking sounds

## Future Protocol Evolution

**2006+ Nissan/Infiniti:**
- Gradual transition to CAN-based diagnostics
- ISO-15765 (CAN) becomes primary protocol
- Simpler architecture (fewer protocol mix)
- Better standardization

**2010+ Models:**
- Primarily CAN-based
- Standard UDS (ISO-14229-1)
- More consistent with other manufacturers

## References

- ISO-9141-2: Road vehicles — Diagnostic systems — Part 2: CARB requirements
- ISO-14230: Road vehicles — Diagnostic systems — Keyword Protocol 2000
- Nissan Service Manual: Model-specific diagnostic procedures
- Platform sharing: Nissan Skyline V35 = Infiniti G35

## Common Nissan/Infiniti DTCs

### Format
- **P-codes**: Standard OBD-II (via ISO-9141)
- **Manufacturer codes**: Via ISO-14230 (format varies)

### Reading DTCs

**ISO-9141 Method:**
```
Request:  03
Response: 43 [count] [DTCs...]
```

**ISO-14230 Method:**
```
Request:  [Manufacturer-specific service]
Response: [Manufacturer-specific format]
```

Refer to service manual for manufacturer DTC format.

## Troubleshooting Checklist

- [ ] Protocol selected correctly (ISO-9141 vs ISO-14230)
- [ ] Timeout set to 3+ seconds (ISO-9141)
- [ ] Inter-request delay of 100ms+ (ISO-9141)
- [ ] Fast Init performed successfully (ISO-14230)
- [ ] Correct module address (ISO-14230)
- [ ] Vehicle in correct state (ignition, engine)
- [ ] Adapter supports selected protocol
- [ ] No other tools connected simultaneously

## Summary

**Nissan/Infiniti 2002-2005 era vehicles are complex:**
- Multiple protocols in use simultaneously
- ISO-9141 is slow and requires careful timing
- ISO-14230 is faster but requires Fast Init
- Choose protocol based on diagnostic needs
- Document everything - these vehicles are quirky
- Platform sharing means findings apply across models
