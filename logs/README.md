# Logs

This directory contains agent session logs and audit trails:

- `session_*.jsonl` - Structured session logs in JSONL format
- `obd_traffic_*.log` - Raw OBD2/CAN traffic logs
- `error_*.log` - Error and exception logs

## Log Format

Session logs use JSONL (JSON Lines) format with timestamps for all events:
- User queries
- Parsed intents
- Commands executed
- Responses received
- User confirmations
- Safety checks

This enables easy parsing and analysis of agent behavior.
