# AI Vehicle Diagnostic Agent - Developer Guide

## Architecture Overview

The AI Vehicle Diagnostic Agent uses a modular toolkit architecture with five main components:

```
┌─────────────────────────────────────────────────────────┐
│                     User Query                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  Query Parser                           │
│  (Extract action, module, vehicle info)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   Agent Core                            │
│  (Orchestrate operations, make decisions)               │
└─────┬──────────┬──────────┬──────────┬─────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Toolkit  │ │Knowledge │ │   Web    │ │   AI     │
│ Scripts  │ │  Base    │ │ Research │ │ Backend  │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│                      Vehicle                            │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Agent Core (`agent_core/`)

Central orchestration and decision-making.

**Key Modules:**

- `agent.py` - Main agent loop and orchestration
- `query_parser.py` - Natural language query parsing
- `diagnostic_workflow.py` - Diagnostic workflow execution
- `toolkit_executor.py` - Execute toolkit scripts
- `feedback_system.py` - Closed-loop learning
- `ai_backend.py` - AI backend interface
- `backend_manager.py` - Backend fallback logic
- `session_logger.py` - Session audit logging
- `report_generator.py` - Diagnostic report generation
- `error_handler.py` - Error recovery strategies
- `vehicle_profile.py` - Vehicle profile management
- `protocol_handlers.py` - Multi-manufacturer protocols
- `module_registry.py` - Module discovery and tracking
- `event_capture.py` - Event-driven CAN capture
- `script_generator.py` - Generate research scripts
- `script_executor.py` - Execute scripts in sandbox
- `manual_consultation.py` - Manual consultation workflow
- `command_confirmation.py` - Command confirmation workflow

### 2. Toolkit Scripts (`toolkit/`)

Standalone CLI tools for specific tasks.

**Categories:**

- `vehicle_communication/` - ELM327 communication
- `web_research/` - Online procedure research
- `knowledge_management/` - Knowledge base operations

**Standard Interface:**
- Input: CLI arguments + optional JSON stdin
- Output: JSON stdout
- Error: Non-zero exit code + error in JSON

### 3. Knowledge Base (`knowledge_base/`)

Persistent storage of learned procedures.

**File Types:**

- `.dat` - Technical data (compact format)
- `.yaml` - Vehicle profiles (human-readable)
- `.json` - Module registry
- `.kcd` - CAN database (optional)

### 4. Configuration (`config/`)

YAML-based configuration system.

**Files:**

- `agent_config.yaml` - Main configuration
- `config_loader.py` - Configuration loader

### 5. Web Research

AI-assisted and user fallback modes.

**Modes:**

- AI-assisted: Automatic search using AI backend
- User fallback: Manual search with user input

## Adding New Features

### Adding a New Toolkit Script

1. **Create Script File:**

```python
# toolkit/vehicle_communication/my_script.py
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', required=True)
    parser.add_argument('--param', required=False)
    args = parser.parse_args()
    
    try:
        # Your logic here
        result = {
            "success": True,
            "data": "result"
        }
    except Exception as e:
        result = {
            "success": False,
            "error": str(e)
        }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()
```

2. **Register in `toolkit_registry.json`:**

```json
{
  "my_script": {
    "path": "toolkit/vehicle_communication/my_script.py",
    "category": "vehicle_communication",
    "description": "Description of what it does",
    "inputs": {
      "port": {"type": "string", "required": true}
    },
    "outputs": {
      "success": {"type": "boolean"},
      "data": {"type": "string"}
    }
  }
}
```

3. **Update Documentation:**

Add usage examples to `toolkit/README.md`.

### Adding a New Vehicle

1. **Create Vehicle Profile:**

```yaml
# knowledge_base/Make_Model_Year_profile.yaml
vehicle:
  make: "Toyota"
  model: "Camry"
  year: 2015
  
dtc_descriptions:
  P0420:
    description: "Catalyst System Efficiency Below Threshold"
    common_causes:
      - "Catalytic converter failure"
      - "Oxygen sensor malfunction"
    repair_hints:
      - "Check oxygen sensors first"
      - "Inspect exhaust for leaks"
```

2. **Create Technical Data File:**

```
# knowledge_base/Make_Model_Year_technical.dat
M:PCM A:7E0 P:CAN B:HS
C:PCM.READ_DTC M:03 R:43[0-9A-F]{4,}
C:PCM.CLEAR_DTC M:04 R:44
```

3. **Add Protocol Handler (if needed):**

```python
# agent_core/protocol_handlers.py
class ToyotaProtocolHandler(ProtocolHandler):
    def __init__(self):
        super().__init__(Manufacturer.TOYOTA)
        self.module_addresses = {
            "PCM": "7E0",
            "ABS": "7B0"
        }
```

### Adding a New AI Backend

1. **Create Backend Class:**

```python
# agent_core/backends/my_backend.py
from agent_core.ai_backend import AIBackend

class MyBackend(AIBackend):
    def __init__(self, api_key: str):
        super().__init__("my_backend")
        self.api_key = api_key
    
    def generate_response(self, prompt: str) -> str:
        # Your API call here
        pass
    
    def web_search(self, query: str) -> List[Dict]:
        # Your search implementation
        pass
```

2. **Register in Backend Manager:**

```python
# agent_core/backend_manager.py
from agent_core.backends.my_backend import MyBackend

# Add to backend initialization
backends = {
    "my_backend": MyBackend(api_key)
}
```

### Adding a New Module Type

1. **Update Protocol Handler:**

```python
# agent_core/protocol_handlers.py
self.module_addresses = {
    "PCM": "7E0",
    "NEW_MODULE": "7XX"  # Add new module
}
```

2. **Add to Query Parser:**

```python
# agent_core/query_parser.py
self.module_keywords = {
    "new_module": ["new", "module", "keywords"]
}
```

3. **Document in Knowledge Base:**

Add module information to vehicle profiles.

## Testing

### Unit Tests

Run unit tests for individual components:

```bash
# Test specific module
python -m pytest tests/test_query_parser.py

# Test all
python -m pytest tests/
```

### Integration Tests

Test end-to-end workflows:

```bash
# Test with mock vehicle
python tests/integration/test_diagnostic_workflow.py

# Test with real vehicle (requires hardware)
python tests/integration/test_real_vehicle.py --port COM3
```

### Testing Toolkit Scripts

Each script includes test mode:

```bash
# Test with mock data
python toolkit/vehicle_communication/read_dtc.py --test

# Validate without executing
python toolkit/vehicle_communication/read_dtc.py --validate
```

## Code Style

### Python Style Guide

Follow PEP 8 with these conventions:

- **Indentation:** 4 spaces
- **Line Length:** 100 characters max
- **Docstrings:** Google style
- **Type Hints:** Use for function signatures

### Example:

```python
def process_query(self, query: str, vehicle_info: Optional[Dict[str, Any]] = None) -> str:
    """
    Process natural language query
    
    Args:
        query: User's natural language query
        vehicle_info: Optional vehicle information
        
    Returns:
        Formatted response string
        
    Raises:
        ValueError: If query is invalid
    """
    pass
```

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Processing query: {query}")
logger.warning(f"Module {module} not found")
logger.error(f"Failed to connect: {error}", exc_info=True)
```

## Knowledge Base Format

### Technical Data Format (.dat)

Compact format for fast parsing:

```
# Module definition
M:MODULE_NAME A:ADDRESS P:PROTOCOL B:BUS

# Command definition
C:MODULE.ACTION M:COMMAND R:RESPONSE_PATTERN

# Example
M:HVAC A:7A0 P:CAN B:HS
C:HVAC.READ_DTC M:03 R:43[0-9A-F]{4,}
```

**Format Specification:**

- `M:` - Module definition
- `A:` - Address (hex)
- `P:` - Protocol (CAN, KWP, etc.)
- `B:` - Bus type (HS/MS/LS)
- `C:` - Command definition
- `M:` - Command bytes (hex)
- `R:` - Response pattern (regex)

### Vehicle Profile Format (.yaml)

Human-readable format:

```yaml
vehicle:
  make: "Ford"
  model: "Escape"
  year: 2008

dtc_descriptions:
  P1632:
    description: "HVAC Mix Door Actuator Circuit - Stuck"
    common_causes:
      - "Actuator motor failure"
      - "Wiring issue"
    repair_hints:
      - "Check actuator operation"
      - "Inspect wiring harness"
```

## Debugging

### Enable Debug Logging

```bash
python main.py --port COM3 --log-level DEBUG
```

### Check Session Logs

```bash
# View agent log
tail -f logs/agent.log

# View session audit trail
cat logs/session_20260223_120000.jsonl | jq
```

### Test Individual Components

```python
# Test query parser
from agent_core.query_parser import QueryParser

parser = QueryParser()
result = parser.parse("check HVAC codes")
print(result)
```

### Mock ELM327 for Testing

```python
# tests/mocks/mock_elm327.py
class MockELM327:
    def send_command(self, cmd):
        # Return mock responses
        if cmd == "03":
            return "43 16 32"
        return "NO DATA"
```

## Performance Optimization

### Knowledge Base Caching

Cache frequently accessed data:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def load_vehicle_profile(vehicle_id: str):
    # Load and cache profile
    pass
```

### Parallel Script Execution

Execute independent scripts in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(run_script, script) for script in scripts]
    results = [f.result() for f in futures]
```

### Optimize Parsing

Use compiled regex for repeated patterns:

```python
import re

DTC_PATTERN = re.compile(r'[PCBU][0-9A-F]{4}')

def parse_dtcs(response):
    return DTC_PATTERN.findall(response)
```

## Security Considerations

### Sandboxed Script Execution

Scripts run with limited permissions:

```python
# agent_core/script_executor.py
- Timeout enforcement
- No file system access outside temp
- No network access (optional)
- Resource limits
```

### API Key Management

Store API keys securely:

```bash
# Environment variables only
export ANTHROPIC_API_KEY=your_key

# Never commit to git
echo ".env" >> .gitignore
```

### Command Validation

Validate commands before sending:

```python
def validate_command(cmd: str) -> bool:
    # Check format
    if not re.match(r'^[0-9A-F\s]+$', cmd):
        return False
    
    # Check length
    if len(cmd) > 100:
        return False
    
    return True
```

## Contributing

### Development Workflow

1. Fork repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit pull request

### Commit Messages

Use conventional commits:

```
feat: Add Toyota protocol handler
fix: Correct DTC parsing for GM vehicles
docs: Update developer guide
test: Add unit tests for query parser
```

### Pull Request Checklist

- [ ] Tests pass
- [ ] Documentation updated
- [ ] Code follows style guide
- [ ] Commit messages are clear
- [ ] No breaking changes (or documented)

## Troubleshooting Development Issues

### Import Errors

```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Module Not Found

```bash
# Install in development mode
pip install -e .
```

### Test Failures

```bash
# Run with verbose output
python -m pytest -v tests/

# Run specific test
python -m pytest tests/test_query_parser.py::test_parse_action
```

## Resources

### Documentation

- [User Guide](USER_GUIDE.md) - End-user documentation
- [Toolkit README](../toolkit/README.md) - Toolkit script reference
- [Knowledge Base README](../knowledge_base/README.md) - Data format reference

### External Resources

- [OBD-II PIDs](https://en.wikipedia.org/wiki/OBD-II_PIDs)
- [ISO 14229 (UDS)](https://www.iso.org/standard/55283.html)
- [ELM327 Documentation](https://www.elmelectronics.com/wp-content/uploads/2017/01/ELM327DS.pdf)

### Community

- GitHub Issues - Bug reports and feature requests
- Discussions - Questions and community support
- Wiki - Additional guides and examples

## Future Enhancements

### Planned Features

- Real-time CAN monitoring
- Advanced actuation sequences
- Multi-vehicle session support
- Cloud knowledge base sync
- Mobile app integration

### Extension Points

- Custom protocol handlers
- Additional AI backends
- New toolkit script categories
- Alternative knowledge formats
- Plugin system

## License

See LICENSE file for details.
