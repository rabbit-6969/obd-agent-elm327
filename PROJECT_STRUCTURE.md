# AI Vehicle Diagnostic Agent - Project Structure

## Directory Layout

```
obd-agent-elm327/
├── agent_core/                    # Core agent logic
│   ├── __init__.py
│   ├── agent.py                   # Main agent orchestration
│   ├── query_parser.py            # Natural language query parsing
│   ├── toolkit_executor.py        # Toolkit script execution
│   ├── diagnostic_workflow.py     # Diagnostic workflow orchestration
│   ├── ai_backend.py              # AI backend interface
│   ├── safety.py                  # Safety mechanisms
│   ├── session_logger.py          # Session logging
│   ├── error_handler.py           # Error handling and recovery
│   ├── vehicle_profile.py         # Vehicle profile management
│   ├── module_registry.py         # Module discovery and registry
│   ├── script_generator.py        # Script generation
│   ├── script_executor.py         # Sandboxed script execution
│   ├── manual_consultation.py     # Manual consultation workflow
│   ├── report_generator.py        # Diagnostic report generation
│   └── backends/                  # AI backend implementations
│       ├── openai_backend.py
│       ├── claude_backend.py
│       └── ollama_backend.py
│
├── toolkit/                       # Specialized toolkit scripts
│   ├── __init__.py
│   ├── vehicle_communication/     # Vehicle communication scripts
│   │   ├── __init__.py
│   │   ├── elm327_base.py         # ELM327 adapter base (refactored)
│   │   ├── read_dtc.py            # Read diagnostic trouble codes
│   │   ├── clear_dtc.py           # Clear diagnostic trouble codes
│   │   ├── read_vin.py            # Read VIN (refactored)
│   │   ├── can_explore.py         # CAN bus exploration (refactored)
│   │   └── actuate.py             # Actuation commands
│   │
│   ├── web_research/              # Web research scripts
│   │   ├── __init__.py
│   │   ├── ai_search.py           # AI-assisted web search
│   │   └── user_fallback.py       # User fallback mode
│   │
│   ├── knowledge_management/      # Knowledge management scripts
│   │   ├── __init__.py
│   │   ├── technical_parser.py    # Technical data format parser
│   │   ├── profile_handler.py     # Vehicle profile YAML handler
│   │   ├── append_procedure.py    # Append learned procedures
│   │   └── query_knowledge.py     # Query knowledge base
│   │
│   ├── diagnostic_procedures/     # Diagnostic procedure scripts
│   │   └── __init__.py
│   │
│   └── toolkit_registry.json      # Toolkit script registry
│
├── knowledge_base/                # Vehicle knowledge documents
│   ├── README.md
│   ├── Ford_Escape_2008_technical.dat
│   ├── Ford_Escape_2008_profile.yaml
│   └── learned_procedures/
│
├── config/                        # Configuration files
│   ├── README.md
│   ├── agent_config.yaml
│   ├── config_loader.py
│   └── vehicle_profiles/
│
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── unit/                      # Unit tests
│   ├── property/                  # Property-based tests
│   └── integration/               # Integration tests
│
├── logs/                          # Session logs and audit trails
│   └── README.md
│
├── elm327_diagnostic/             # Legacy diagnostic system (separate)
│   └── ...                        # Existing code preserved
│
├── scripts/                       # Utility scripts
│   └── ...
│
├── docs/                          # Documentation
│   ├── USER_GUIDE.md
│   └── DEVELOPER_GUIDE.md
│
├── examples/                      # Example configurations
│   ├── ford_escape_2008.yaml
│   ├── agent_config_openai.yaml
│   └── agent_config_ollama.yaml
│
├── main.py                        # Main entry point
├── requirements.txt               # Python dependencies
└── README.md                      # Project overview
```

## Integration Strategy

The new agent system integrates and refactors code from `elm327_diagnostic/`:

- `elm327_adapter.py` → `toolkit/vehicle_communication/elm327_base.py`
- `vin_reader.py` → `toolkit/vehicle_communication/read_vin.py`
- `can_bus_explorer.py` → `toolkit/vehicle_communication/can_explore.py`
- `hvac_diagnostics.py` → Knowledge base + diagnostic workflows

The legacy `elm327_diagnostic/` system remains as a separate, standalone tool.

## Next Steps

1. Implement configuration system (Task 1.2)
2. Implement knowledge document format (Task 2.x)
3. Implement query parser (Task 3.x)
4. Continue with remaining tasks...
