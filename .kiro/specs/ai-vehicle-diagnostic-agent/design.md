# Design Document: AI Vehicle Diagnostic Agent

## Overview

The AI Vehicle Diagnostic Agent enables autonomous vehicle diagnostics through OBD2 ports using a toolkit architecture. The system interprets natural language queries, searches for unknown procedures (with user assistance), executes diagnostics, and documents findings for continuous learning.

**Core Principle**: Start simple (no API keys), learn from user, become smarter over time.

## Architecture

### High-Level Components

```
User Query → Query Parser → Agent Core → Toolkit Scripts → Vehicle
                ↓              ↓              ↓
         Knowledge Base   Web Research   Audit Log
```

**5 Main Components**:
1. **Agent Core**: Orchestrates operations, makes decisions
2. **Query Parser**: Extracts intent from natural language
3. **Toolkit Scripts**: Discrete CLI tools for specific tasks
4. **Knowledge Manager**: Stores/retrieves procedures in compact format
5. **Web Research**: Searches for unknown procedures (AI-assisted + user help)

**See**: [architecture.md](./design/architecture.md) for detailed component interactions

## Workflow

### Typical Diagnostic Session

```
1. User: "check hvac codes on my vehicle"
   ↓
2. Agent: Parse query → action="read_dtc", module="HVAC"
   ↓
3. Agent: Check knowledge base → Not found
   ↓
4. Agent: "🔍 Please search Google for: '2008 Ford Escape HVAC read DTC OBD2'"
   ↓
5. User: [pastes search results]
   ↓
6. Agent: Extract commands → Execute → Get response "43 16 32"
   ↓
7. Agent: Parse DTC → "P1632" → Unknown code!
   ↓
8. Agent: "❓ Unknown DTC: P1632. Please search: 'Ford P1632 meaning'"
   ↓
9. User: "HVAC Mix Door Actuator Circuit - Stuck"
   ↓
10. Agent: Update knowledge base → Present results
    ↓
11. Next time: Instant! (already in knowledge base)
```

**See**: [workflows.md](./design/workflows.md) for complete workflow scenarios

## Key Design Decisions

### 1. No API Keys Required by Default

**Problem**: Users don't want to set up API keys just to try the tool.

**Solution**: 
- Default mode: AI-assisted (uses AI backend's web search if available)
- Fallback: Ask user to search manually and paste results
- Optional: User can configure Google Custom Search API later

**See**: [web-research.md](./design/web-research.md) for implementation details

### 2. Separated Knowledge Documents

**Problem**: Mixing technical data with human descriptions makes parsing slow and files bloated.

**Solution**: Split into two file types:

**Technical Data** (machine-optimized):
```
# Ford_Escape_2008_technical.dat
M:HVAC A:7A0 P:CAN B:HS
C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,}
```
- Ultra-compact format
- Parses in < 50ms
- No human descriptions

**Vehicle Profile** (human-readable):
```yaml
# Ford_Escape_2008_profile.yaml
dtc_descriptions:
  P1632:
    description: "HVAC Mix Door Actuator Circuit - Stuck"
    common_causes: ["Actuator motor failure"]
```
- Easy to read/edit
- Contains context and repair hints
- Separate from technical data

**See**: [knowledge-format.md](./design/knowledge-format.md) for format specifications

### 3. Toolkit Script Architecture

**Problem**: Monolithic code is hard to test and extend.

**Solution**: Discrete Python scripts with standard CLI interface:

```bash
# Each script: JSON in → JSON out
python toolkit/vehicle_communication/read_dtc.py --port COM3 --module HVAC
# Output: {"success": true, "dtcs": [{"code": "P1632", ...}]}
```

**Benefits**:
- Easy to test individually
- Agent can call any script
- New scripts added without modifying core

**See**: [toolkit-scripts.md](./design/toolkit-scripts.md) for script specifications

### 4. Safety-First Design

**Problem**: Sending wrong commands to vehicles can be dangerous.

**Solution**: 4-level danger classification with confirmations:

- **SAFE**: Read-only (read DTC, read VIN) → No confirmation
- **CAUTION**: Write operations (clear DTC) → Simple confirmation
- **WARNING**: Actuations (EVAP purge, blend door) → Detailed confirmation
- **DANGER**: Critical systems (ABS, airbag) → Multi-step confirmation + preconditions

**See**: [safety-mechanisms.md](./design/safety-mechanisms.md) for safety protocols

### 5. Multi-Backend AI Support

**Problem**: Users have different AI providers (OpenAI, Claude, local models).

**Solution**: Pluggable backend interface with automatic fallback:

```python
# Try primary backend, fall back if it fails
backends = [OpenAI, Claude, Ollama]
for backend in backends:
    try:
        return backend.generate_response(prompt)
    except:
        continue
```

**See**: [ai-backends.md](./design/ai-backends.md) for backend implementations

## Data Flow

### Query to Result

```
1. Natural Language Query
   ↓ [Query Parser]
2. Structured Intent (action, module, params)
   ↓ [Knowledge Lookup]
3. Procedure (commands, expected responses)
   ↓ [Toolkit Executor]
4. Vehicle Commands (OBD2/UDS)
   ↓ [ELM327 Adapter]
5. Raw Responses (hex bytes)
   ↓ [Response Parser]
6. Diagnostic Results (DTCs, live data)
   ↓ [Result Presenter]
7. Human-Readable Report
```

**See**: [data-flow.md](./design/data-flow.md) for detailed data transformations

## Learning Loop

### Closed-Loop Feedback System

```
Execute → Observe → Document → Improve
   ↑                              ↓
   └──────────────────────────────┘
```

**How it works**:
1. Agent executes diagnostic procedure
2. Observes results (success/failure, responses)
3. Documents successful procedures in knowledge base
4. Uses documented procedures in future sessions (faster!)

**Example**:
- First time: Ask user to search, takes 2 minutes
- Second time: Instant lookup from knowledge base
- Third time: Even faster (cached in memory)

**See**: [learning-system.md](./design/learning-system.md) for learning algorithms

## Error Handling

### Graceful Degradation

**Philosophy**: Never crash, always offer alternatives.

**Strategy**:
```
Primary approach fails
   ↓
Try alternative approach
   ↓
Ask user for help
   ↓
Document what worked
```

**Example**:
- Can't find procedure online → Try generic OBD2 commands
- Generic commands fail → Ask user for service manual
- User provides info → Document for next time

**See**: [error-handling.md](./design/error-handling.md) for error recovery strategies

## Testing Strategy

### Dual Approach

**Unit Tests**: Specific examples and edge cases
- Test query parsing: "check HVAC errors" → action="read_dtc"
- Test command extraction from text
- Test configuration loading

**Property-Based Tests**: Universal properties across all inputs
- Any valid diagnostic data should serialize/deserialize correctly
- Any OBD2 response should validate before parsing
- Any dangerous operation should require confirmation

**Library**: hypothesis (Python property-based testing)

**See**: [testing-strategy.md](./design/testing-strategy.md) for test specifications

## Configuration

### YAML-Based Configuration

```yaml
# agent_config.yaml

ai_backend:
  primary: "openai"
  fallback: ["claude", "ollama"]

vehicle:
  port: "COM3"
  
web_research:
  mode: "ai_assisted"  # No API keys needed
  
safety:
  require_confirmation: true
  allow_bypass: false
```

**See**: [configuration.md](./design/configuration.md) for complete config reference

## Phase 1 Scope

### Ford Escape 2008 HVAC Focus

**Included**:
- HVAC diagnostic procedures
- Basic query parsing for HVAC queries
- Knowledge base with Ford Escape HVAC data
- Safety mechanisms for HVAC actuations
- Audit logging

**Deferred**:
- Full multi-manufacturer support
- Advanced script generation
- Complex actuation sequences
- Real-time CAN monitoring

**See**: [implementation-phases.md](./design/implementation-phases.md) for roadmap

## Integration with Existing Code

### Leveraging Current Codebase

**Existing modules** (elm327_adapter.py, hvac_diagnostics.py, can_bus_explorer.py, vin_reader.py):
- Provide foundation for vehicle communication
- Will be wrapped by toolkit scripts
- Functionality extracted and modularized

**Integration approach**:
- Toolkit scripts instantiate existing classes
- Extract reusable functions into utilities
- Maintain backward compatibility

**See**: [code-integration.md](./design/code-integration.md) for integration details

## Performance Targets

- Query parsing: < 100ms
- Knowledge lookup: < 50ms
- Web search (if automated): < 5 seconds
- Command execution: < 2 seconds
- Report generation: < 500ms

**See**: [performance.md](./design/performance.md) for optimization strategies

## Security & Privacy

**Key principles**:
- API keys in environment variables only
- All operations logged for audit
- Dangerous operations require confirmation
- Web research respects robots.txt
- User can disable web research entirely

**See**: [security.md](./design/security.md) for security specifications

## Correctness Properties

**34 properties** derived from requirements covering:
- Query parsing correctness
- Web research behavior
- Knowledge management
- Safety mechanisms
- Logging completeness
- Serialization round-trip
- Error handling

**See**: [correctness-properties.md](./design/correctness-properties.md) for complete property list

## Summary

This design provides a practical, user-friendly AI diagnostic agent that:

1. **Works out of the box** - No API keys required
2. **Learns from user** - Builds knowledge base over time
3. **Stays safe** - Confirmation workflows for dangerous operations
4. **Handles errors gracefully** - Always offers alternatives
5. **Extensible** - Easy to add new vehicles, modules, procedures

The system starts simple and becomes smarter with each diagnostic session, creating a continuously improving diagnostic assistant.

## Knowledge Organization

The system maintains two distinct knowledge directories with clear separation of concerns:

### `knowledge_base/` - Vehicle-Specific Data
**What it contains**:
- Vehicle profiles (YAML): DTC descriptions, repair hints, common issues
- Technical data (DAT): Module addresses, command sequences, response patterns  
- CAN databases (KCD): Signal definitions for specific vehicles
- Captured data (JSON): Real diagnostic session logs
- Learned procedures: Documented successful workflows

**Purpose**: Store and grow vehicle-specific operational knowledge

**Agent behavior**:
- Primary lookup location for diagnostics
- Updated after successful operations
- Grows over time through learning
- Vehicle-specific (Ford_Escape_2008, etc.)

### `reference/` - Universal Protocol Documentation
**What it contains**:
- ISO 14229-1 UDS service specifications
- OBD-II protocol documentation
- CAN bus protocol standards
- Example implementations
- Industry standards

**Purpose**: Protocol-level reference material for implementing communication

**Agent behavior**:
- Consulted when implementing new services
- Referenced for protocol details
- Static documentation (rarely modified)
- Universal across all vehicles

### Search Hierarchy
1. Check `knowledge_base/` for vehicle-specific procedures (fast)
2. If not found, check `reference/` for protocol specs
3. If still not found, initiate web research
4. Document findings in `knowledge_base/` for next time

**See**: [architecture.md](./design/architecture.md) for detailed search flow examples

## Reference Documents

### Design Details
- [architecture.md](./design/architecture.md) - Component architecture, knowledge organization, and search strategy
- [workflows.md](./design/workflows.md) - Complete workflow scenarios
- [data-flow.md](./design/data-flow.md) - Data transformations and flow

### Component Specifications
- [query-parser.md](./design/query-parser.md) - Natural language parsing
- [web-research.md](./design/web-research.md) - Web search implementation
- [knowledge-format.md](./design/knowledge-format.md) - Knowledge document formats
- [toolkit-scripts.md](./design/toolkit-scripts.md) - Script specifications
- [ai-backends.md](./design/ai-backends.md) - AI backend implementations

### Implementation Guides
- [safety-mechanisms.md](./design/safety-mechanisms.md) - Safety protocols
- [error-handling.md](./design/error-handling.md) - Error recovery
- [learning-system.md](./design/learning-system.md) - Closed-loop feedback
- [testing-strategy.md](./design/testing-strategy.md) - Test specifications
- [configuration.md](./design/configuration.md) - Configuration reference

### Code Examples
- [code-examples.md](./design/code-examples.md) - Implementation examples
- [code-integration.md](./design/code-integration.md) - Existing code integration

### Additional Resources
- [correctness-properties.md](./design/correctness-properties.md) - Property specifications
- [performance.md](./design/performance.md) - Performance optimization
- [security.md](./design/security.md) - Security specifications
- [implementation-phases.md](./design/implementation-phases.md) - Development roadmap
