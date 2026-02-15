# Architecture

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User/Technician                      │
└────────────────────────┬────────────────────────────────────┘
                         │ Natural Language Query
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                      AI Agent Core                           │
│  - Orchestration                                             │
│  - Decision Making                                           │
│  - Session Management                                        │
└─┬───────┬───────┬───────┬───────┬───────────────────────────┘
  │       │       │       │       │
  ↓       ↓       ↓       ↓       ↓
┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐
│ Q │   │ T │   │ W │   │ K │   │ A │
│ P │   │ S │   │ R │   │ M │   │ L │
└─┬─┘   └─┬─┘   └─┬─┘   └─┬─┘   └─┬─┘
  │       │       │       │       │
  │       ↓       │       ↓       ↓
  │   ┌───────┐   │   ┌───────┐ ┌───────┐
  │   │Vehicle│   │   │ Tech  │ │ Audit │
  │   │ Comm  │   │   │ Data  │ │  Log  │
  │   └───┬───┘   │   └───────┘ └───────┘
  │       │       │
  │       ↓       │
  │   ┌───────┐   │
  │   │ELM327 │   │
  │   │Adapter│   │
  │   └───┬───┘   │
  │       │       │
  │       ↓       ↓
  │   ┌───────────────┐
  │   │    Vehicle    │
  │   │   OBD2 Port   │
  │   └───────────────┘
  │
  └─→ AI Backend (OpenAI/Claude/Ollama)

Legend:
QP = Query Parser
TS = Toolkit Scripts
WR = Web Research
KM = Knowledge Manager
AL = Audit Logger
```

## Component Responsibilities

### 1. AI Agent Core
**Purpose**: Central orchestrator and decision maker

**Responsibilities**:
- Parse user queries via Query Parser
- Check Knowledge Manager for existing procedures
- Initiate Web Research if procedure not found
- Execute Toolkit Scripts to interact with vehicle
- Handle errors and provide alternatives
- Update knowledge base with new findings
- Generate diagnostic reports

**Key Methods**:
```python
process_query(query: str) -> AgentResponse
execute_diagnostic(intent: ParsedIntent) -> DiagnosticResult
handle_unknown_dtc(dtc_code: str) -> DTCDefinition
update_knowledge(procedure: Procedure) -> bool
```

### 2. Query Parser
**Purpose**: Extract structured intent from natural language

**Responsibilities**:
- Parse user queries into action, module, parameters
- Identify ambiguities and request clarification
- Extract vehicle information if mentioned
- Maintain conversation context

**Input**: "check hvac codes on my 2008 Ford Escape"
**Output**: 
```python
ParsedIntent(
    action="read_dtc",
    module="HVAC",
    vehicle=VehicleProfile(make="Ford", model="Escape", year=2008),
    confidence=0.95
)
```

### 3. Toolkit Scripts
**Purpose**: Discrete CLI tools for specific diagnostic tasks

**Categories**:
- **vehicle_communication/**: read_dtc.py, clear_dtc.py, read_vin.py, etc.
- **web_research/**: search_procedure.py, extract_commands.py, etc.
- **knowledge_management/**: store_procedure.py, retrieve_procedure.py, etc.
- **diagnostic_procedures/**: diagnose_module.py, hvac_diagnostic.py, etc.

**Interface**: JSON in → JSON out, standard exit codes

### 4. Web Research Module
**Purpose**: Find unknown procedures with user assistance

**Modes**:
1. **AI-Assisted** (default): Use AI backend's web search if available
2. **User-Assisted**: Ask user to search and paste results
3. **Google API** (optional): Automated search with user-configured API key

**Workflow**:
```
Procedure not in knowledge base
  ↓
Try AI web search
  ↓ (if fails)
Ask user to search manually
  ↓
Extract commands from user input
  ↓
Validate and execute
```

### 5. Knowledge Manager
**Purpose**: Store and retrieve diagnostic procedures

**Storage**:
- **Technical Data**: Ultra-compact format for fast parsing
- **Vehicle Profiles**: Human-readable YAML with descriptions

**Operations**:
- `get_procedure(vehicle, module, action)` - < 50ms
- `store_procedure(procedure)` - Append to technical data
- `get_dtc_description(code)` - Lookup from vehicle profile
- `list_known_procedures(vehicle)` - List all procedures

### 6. Audit Logger
**Purpose**: Log all operations for debugging and compliance

**Log Types**:
- User queries and parsed intents
- Knowledge lookups (hit/miss)
- Web searches performed
- Commands sent to vehicle
- Vehicle responses received
- User confirmations
- Errors and recovery actions

**Format**: JSONL (one JSON object per line)

## Data Flow

### Complete Diagnostic Flow

```
1. User Query
   "check hvac codes"
   ↓
2. Query Parser
   ParsedIntent(action="read_dtc", module="HVAC")
   ↓
3. Knowledge Lookup
   Check technical data for HVAC.READ_DTC procedure
   ↓
4a. If Found:
    Retrieve command sequence
    ↓
4b. If Not Found:
    Web Research → Extract commands → Validate
    ↓
5. Toolkit Executor
   Execute read_dtc.py with parameters
   ↓
6. ELM327 Adapter
   Send OBD2 command to vehicle
   ↓
7. Vehicle Response
   Raw hex bytes: "43 16 32"
   ↓
8. Response Parser
   Parse using technical data rules
   ↓
9. DTC Lookup
   Check vehicle profile for DTC descriptions
   ↓
10a. If Found:
     Present results with descriptions
     ↓
10b. If Not Found:
     Ask user to search for DTC meaning
     ↓
11. Update Knowledge
    Store new procedure/DTC in knowledge base
    ↓
12. Generate Report
    Present results to user
```

## Communication Patterns

### Agent ↔ Toolkit Scripts
**Pattern**: Command-line execution with JSON I/O

```bash
# Agent executes script
python toolkit/vehicle_communication/read_dtc.py \
  --port COM3 \
  --module HVAC \
  --format json

# Script returns JSON
{
  "success": true,
  "dtcs": [
    {"code": "P1632", "hex": "1632", "module": "HVAC"}
  ],
  "raw_response": "43 16 32"
}
```

### Agent ↔ AI Backend
**Pattern**: API calls with prompt/response

```python
# Agent sends prompt
response = ai_backend.generate_response(
    prompt="Extract OBD2 commands from this text: ...",
    context={"vehicle": "Ford Escape 2008", "module": "HVAC"}
)

# AI returns structured response
commands = parse_ai_response(response)
```

### Agent ↔ User
**Pattern**: Interactive prompts with formatted output

```
Agent: 🔍 I need to search for: "2008 Ford Escape HVAC read DTC OBD2"
       
       Please search Google and paste relevant info,
       or type 'config' to set up automatic search,
       or 'skip' to continue without.

User: [pastes search results or types command]

Agent: ✓ Found procedure! Executing...
```

## Scalability Considerations

### Performance Targets
- Query parsing: < 100ms
- Knowledge lookup: < 50ms
- Command execution: < 2 seconds
- Report generation: < 500ms

### Memory Management
- Technical data loaded on demand
- Vehicle profiles cached in memory
- Audit logs rotated daily
- Search results cached for 24 hours

### Extensibility Points
1. **New Toolkit Scripts**: Drop in new .py files
2. **New AI Backends**: Implement AIBackend interface
3. **New Vehicle Makes**: Add vehicle profile YAML
4. **New Protocols**: Add protocol handler class

## Deployment Architecture

### Single-User Desktop Application
```
User's Computer
├── Python Environment
│   ├── Agent Core
│   ├── Toolkit Scripts
│   └── Dependencies
├── Knowledge Base (local files)
│   ├── technical/
│   └── vehicles/
├── Configuration (YAML)
└── Logs (JSONL)
```

### Multi-User Server (Future)
```
Server
├── Agent Core (shared)
├── Toolkit Scripts (shared)
└── Knowledge Base (shared)

Clients
├── Web Interface
├── CLI Interface
└── API Interface
```

## Knowledge Organization

### Directory Structure

The system maintains two distinct knowledge directories:

#### `knowledge_base/` - Vehicle-Specific Operational Data
**Purpose**: Store learned information about specific vehicles

**Contents**:
- Vehicle profiles (YAML): DTC descriptions, repair hints, common issues
- Technical data (DAT): Module addresses, command sequences, response patterns
- CAN bus databases (KCD): Signal definitions for specific vehicles
- Captured vehicle data (JSON): Real diagnostic session data
- Learned procedures: Documented successful diagnostic workflows

**Examples**:
```
knowledge_base/
├── Ford_Escape_2008_profile.yaml      # DTC descriptions, repair hints
├── Ford_Escape_2008_technical.dat     # Module addresses, commands
├── Ford_Escape_2008_canbus.kcd        # CAN signal definitions
├── vehicle_data_20260214_185442.json  # Captured diagnostic data
└── learned_procedures/                # Successful workflows
    └── hvac_blend_door_diagnosis.md
```

**Characteristics**:
- Vehicle-specific (make, model, year)
- Grows over time through learning
- Modified by agent during operation
- User's proprietary diagnostic knowledge

**Agent Usage**:
- Primary lookup location for diagnostic procedures
- Updated after successful diagnostics
- Queried for DTC descriptions and repair hints
- Source of truth for vehicle-specific data

#### `reference/` - Universal Protocol Documentation
**Purpose**: Store standard protocol specifications and reference materials

**Contents**:
- ISO 14229-1 UDS service specifications
- OBD-II protocol documentation
- CAN bus protocol standards
- Example implementations from other vehicles
- Industry standard reference materials

**Examples**:
```
reference/
├── ISO_14229-1_UDS_INDEX.md                    # Index of available UDS docs
├── ISO_14229-1_UDS_Service_0x19_Extract.md     # Service 0x19 specification
├── ISO_14229-1_UDS_Service_0x22_Extract.md     # Service 0x22 specification
├── ISO_14229-1_UDS_Service_0x2F_Extract.md     # Service 0x2F specification
├── ISO_14229-1_UDS_Service_0x31_Extract.md     # Service 0x31 specification
└── mazda_skyactiv.kcd                          # Example CAN database
```

**Characteristics**:
- Protocol-level documentation
- Universal across all vehicles
- Static reference material (rarely modified)
- Industry standards and specifications

**Agent Usage**:
- Consulted when implementing new UDS services
- Referenced for protocol-level details
- Used to understand message formats
- Guides implementation of communication layer

### Search Strategy

When the agent needs information, it follows this hierarchy:

1. **Check `knowledge_base/` first** (vehicle-specific)
   - Look for exact vehicle match (Ford_Escape_2008)
   - Check for learned procedures
   - Query technical data for known commands

2. **If not found, check `reference/`** (protocol-level)
   - Consult ISO 14229-1 index for required service
   - Request missing documentation from user
   - Use protocol specs to construct commands

3. **If still not found, initiate web research**
   - Search for vehicle-specific procedures
   - Extract and validate commands
   - Document findings in `knowledge_base/`

### Example Search Flow

```
User: "Read transmission DTCs on my 2008 Ford Escape"

Agent:
1. Check knowledge_base/Ford_Escape_2008_technical.dat
   → Not found: No TCM.READ_DTC procedure

2. Check reference/ISO_14229-1_UDS_INDEX.md
   → Found: Service 0x19 (ReadDTCInformation) documented
   → Read reference/ISO_14229-1_UDS_Service_0x19_Extract.md

3. Construct UDS command using ISO spec:
   → Request: 19 02 AF (Service 0x19, sub-function 0x02, mask 0xAF)
   → Set addressing for TCM module

4. Execute command and capture response

5. Document successful procedure:
   → Append to knowledge_base/Ford_Escape_2008_technical.dat
   → Next time: Instant lookup from knowledge_base!
```

### Growth Pattern

**Initial State**:
```
knowledge_base/
└── Ford_Escape_2008_profile.yaml  (basic DTC descriptions)

reference/
└── ISO_14229-1_UDS_Service_0x19_Extract.md
```

**After First Transmission Diagnostic**:
```
knowledge_base/
├── Ford_Escape_2008_profile.yaml
├── Ford_Escape_2008_technical.dat  (NEW: TCM commands added)
└── vehicle_data_20260214_185442.json  (NEW: captured data)

reference/
├── ISO_14229-1_UDS_Service_0x19_Extract.md
└── ISO_14229-1_UDS_Service_0x22_Extract.md  (NEW: requested from user)
```

**After Multiple Diagnostics**:
```
knowledge_base/
├── Ford_Escape_2008_profile.yaml  (enriched with more DTCs)
├── Ford_Escape_2008_technical.dat  (multiple modules documented)
├── Ford_Escape_2008_canbus.kcd
├── vehicle_data_*.json  (multiple sessions)
└── learned_procedures/
    ├── hvac_blend_door_diagnosis.md
    ├── transmission_shift_solenoid_test.md
    └── abs_wheel_speed_sensor_test.md

reference/
├── ISO_14229-1_UDS_INDEX.md
├── ISO_14229-1_UDS_Service_0x19_Extract.md
├── ISO_14229-1_UDS_Service_0x22_Extract.md
├── ISO_14229-1_UDS_Service_0x2F_Extract.md
└── ISO_14229-1_UDS_Service_0x31_Extract.md
```

## Technology Stack

**Core**:
- Python 3.9+
- PySerial (ELM327 communication)
- YAML (configuration)
- JSON/JSONL (data/logs)

**AI Backends**:
- OpenAI Python SDK
- Anthropic Python SDK
- Ollama REST API

**Testing**:
- pytest (unit tests)
- hypothesis (property-based tests)

**Web Research** (optional):
- requests (HTTP)
- BeautifulSoup (HTML parsing)
- google-api-python-client (Google Custom Search)
