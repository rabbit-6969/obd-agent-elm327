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

## Common Error Responses

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

**Workarounds**:
1. Use single-frame commands when possible
2. Add delays between commands
3. Retry failed commands
4. Recommend quality adapter

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
