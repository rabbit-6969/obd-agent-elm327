---
inclusion: auto
---

# Safety Protocols for Vehicle Diagnostics

Safety is the highest priority. Always classify operations and get appropriate confirmations.

## Safety Classification System

### SAFE - No Confirmation Required
Read-only operations that cannot affect vehicle state:
- Read DTCs (Service 0x03, 0x19)
- Read VIN (DID 0xF190)
- Read live data (Service 0x22 with read-only DIDs)
- Read module identification (DIDs 0xF181, 0xF18C, 0xF187, 0xF191)
- Tester Present (Service 0x3E)
- Enter diagnostic session (Service 0x10)

**Action**: Execute without confirmation

### CAUTION - Simple Confirmation
Operations that modify stored data but don't affect vehicle operation:
- Clear DTCs (Service 0x04, 0x14)
- Reset learned values (some modules)

**Action**: 
1. Explain what will be cleared
2. Ask user: "Clear DTCs from [module]? (yes/no)"
3. Wait for explicit confirmation
4. Execute if confirmed

### WARNING - Detailed Confirmation
Operations that actuate components or affect vehicle behavior:
- Blend door actuation (HVAC)
- EVAP purge valve test
- Transmission solenoid tests
- Fuel pump tests
- Cooling fan tests

**Action**:
1. Explain what will happen
2. List preconditions (e.g., "Engine running, in Park")
3. Ask user to confirm preconditions met
4. Ask user: "Proceed with [actuation]? (yes/no)"
5. Wait for explicit confirmation
6. Execute if confirmed

**Example**:
```
I can test the transmission shift solenoids.

Preconditions:
- Vehicle in Park
- Engine running
- Parking brake engaged
- No one under vehicle

This will briefly actuate each solenoid. You may hear clicking sounds.

Have you confirmed all preconditions are met? (yes/no)
```

### DANGER - Multi-Step Confirmation
Operations on critical safety systems:
- ABS module commands
- Airbag system commands
- Steering system commands
- Brake system actuations
- Engine control modifications

**Action**:
1. Explain the operation and risks
2. List all preconditions
3. Ask user to confirm understanding of risks
4. Ask user to confirm preconditions met
5. Ask user for final confirmation
6. Execute only if all confirmations received

**Example**:
```
WARNING: You are requesting an ABS module operation.

This affects a critical safety system. Incorrect operations could:
- Disable ABS functionality
- Affect brake performance
- Create safety hazards

Preconditions:
- Vehicle must be stationary
- Engine off
- Parking brake engaged
- Wheels chocked
- No one in or under vehicle

Do you understand the risks? (yes/no)
Have you confirmed all preconditions? (yes/no)
Final confirmation to proceed? (yes/no)
```

## Never Execute Without Confirmation

**NEVER** execute these without explicit user confirmation:
- Any Service 0x31 (Routine Control) on critical systems
- Any Service 0x2F (Input/Output Control)
- Any Service 0x2E (Write Data By Identifier)
- Any command that could affect vehicle safety
- Any command that could damage components

## When in Doubt

If you're unsure about safety classification:
1. **Assume it's dangerous**
2. **Ask the user for confirmation**
3. **Explain what will happen**
4. **List any risks**

Better to over-confirm than to cause damage or safety issues.

## Logging

All operations must be logged:
- Command sent
- Response received
- Timestamp
- User confirmation (if required)
- Result (success/failure)

This creates an audit trail for safety and debugging.

## Error Handling

If an operation fails:
1. **Stop immediately**
2. **Do not retry without user input**
3. **Explain what happened**
4. **Ask user how to proceed**

Never automatically retry operations that could be dangerous.

## Special Cases

### Intermittent Faults
When monitoring for intermittent faults (e.g., ABS light):
- Monitoring is SAFE (read-only)
- Explain to user what you're monitoring
- No confirmation needed for monitoring
- But confirm before any corrective actions

### Module Discovery
When scanning for modules:
- Tester Present is SAFE
- Reading DIDs is SAFE
- No confirmation needed
- But explain what you're doing

### Live Data Monitoring
Continuous monitoring of live data:
- SAFE (read-only)
- Explain what you're monitoring
- No confirmation needed
- User can stop at any time

## User Override

If user explicitly requests to bypass safety checks:
- **Refuse for DANGER level operations**
- **Warn strongly for WARNING level**
- **Allow for CAUTION level with warning**
- **Always log the override**

Example:
```
User: "Just clear the codes without asking"
Agent: "I can skip confirmation for clearing DTCs, but I recommend 
       reviewing them first. Proceeding to clear DTCs from PCM..."
```

## Documentation

After any actuation or modification:
1. Document what was done
2. Document the result
3. Update knowledge base if new procedure
4. Provide user with summary

This helps with future diagnostics and learning.
