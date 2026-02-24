"""
Session Logger

Logs all agent operations for audit trail and debugging.
Uses JSONL format for structured logging.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


@dataclass
class LogEntry:
    """Base class for log entries"""
    timestamp: str
    event_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class QueryLogEntry(LogEntry):
    """Log entry for user queries"""
    query: str
    session_id: str
    
    def __init__(self, query: str, session_id: str):
        self.timestamp = datetime.now().isoformat()
        self.event_type = "query"
        self.query = query
        self.session_id = session_id


@dataclass
class ParsedIntentLogEntry(LogEntry):
    """Log entry for parsed intents"""
    action: str
    module: Optional[str]
    vehicle_info: Dict[str, str]
    session_id: str
    
    def __init__(self, action: str, module: Optional[str], 
                 vehicle_info: Dict[str, str], session_id: str):
        self.timestamp = datetime.now().isoformat()
        self.event_type = "parsed_intent"
        self.action = action
        self.module = module
        self.vehicle_info = vehicle_info
        self.session_id = session_id


@dataclass
class CommandLogEntry(LogEntry):
    """Log entry for commands sent to vehicle"""
    command: str
    module: str
    address: str
    session_id: str
    
    def __init__(self, command: str, module: str, address: str, session_id: str):
        self.timestamp = datetime.now().isoformat()
        self.event_type = "command"
        self.command = command
        self.module = module
        self.address = address
        self.session_id = session_id


@dataclass
class ResponseLogEntry(LogEntry):
    """Log entry for responses from vehicle"""
    response: str
    command: str
    success: bool
    session_id: str
    
    def __init__(self, response: str, command: str, success: bool, session_id: str):
        self.timestamp = datetime.now().isoformat()
        self.event_type = "response"
        self.response = response
        self.command = command
        self.success = success
        self.session_id = session_id


@dataclass
class ConfirmationLogEntry(LogEntry):
    """Log entry for user confirmations"""
    operation: str
    danger_level: str
    confirmed: bool
    session_id: str
    
    def __init__(self, operation: str, danger_level: str, 
                 confirmed: bool, session_id: str):
        self.timestamp = datetime.now().isoformat()
        self.event_type = "confirmation"
        self.operation = operation
        self.danger_level = danger_level
        self.confirmed = confirmed
        self.session_id = session_id


@dataclass
class ErrorLogEntry(LogEntry):
    """Log entry for errors"""
    error_type: str
    error_message: str
    context: Dict[str, Any]
    session_id: str
    
    def __init__(self, error_type: str, error_message: str, 
                 context: Dict[str, Any], session_id: str):
        self.timestamp = datetime.now().isoformat()
        self.event_type = "error"
        self.error_type = error_type
        self.error_message = error_message
        self.context = context
        self.session_id = session_id


class SessionLogger:
    """
    Session logger for agent operations
    
    Features:
    - JSONL format for structured logging
    - Timestamped entries
    - Session-based organization
    - Audit trail for all operations
    """
    
    def __init__(self, log_dir: str = "logs", session_id: Optional[str] = None):
        """
        Initialize session logger
        
        Args:
            log_dir: Directory for log files
            session_id: Session identifier (generated if not provided)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Generate session ID if not provided
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.session_id = session_id
        self.log_file = self.log_dir / f"session_{session_id}.jsonl"
        
        logger.info(f"Session logger initialized: {self.log_file}")
    
    def _write_entry(self, entry: LogEntry):
        """
        Write log entry to file
        
        Args:
            entry: Log entry to write
        """
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                json.dump(entry.to_dict(), f)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")
    
    def log_query(self, query: str):
        """
        Log user query
        
        Args:
            query: User query text
        """
        entry = QueryLogEntry(query=query, session_id=self.session_id)
        self._write_entry(entry)
        logger.debug(f"Logged query: {query[:50]}...")
    
    def log_parsed_intent(self, action: str, module: Optional[str], 
                         vehicle_info: Dict[str, str]):
        """
        Log parsed intent
        
        Args:
            action: Parsed action
            module: Parsed module
            vehicle_info: Vehicle information
        """
        entry = ParsedIntentLogEntry(
            action=action,
            module=module,
            vehicle_info=vehicle_info,
            session_id=self.session_id
        )
        self._write_entry(entry)
        logger.debug(f"Logged intent: action={action}, module={module}")
    
    def log_command(self, command: str, module: str, address: str):
        """
        Log command sent to vehicle
        
        Args:
            command: Command string
            module: Target module
            address: Module address
        """
        entry = CommandLogEntry(
            command=command,
            module=module,
            address=address,
            session_id=self.session_id
        )
        self._write_entry(entry)
        logger.debug(f"Logged command: {command} to {module}@{address}")
    
    def log_response(self, response: str, command: str, success: bool):
        """
        Log response from vehicle
        
        Args:
            response: Response string
            command: Original command
            success: Whether response indicates success
        """
        entry = ResponseLogEntry(
            response=response,
            command=command,
            success=success,
            session_id=self.session_id
        )
        self._write_entry(entry)
        logger.debug(f"Logged response: success={success}")
    
    def log_confirmation(self, operation: str, danger_level: str, confirmed: bool):
        """
        Log user confirmation
        
        Args:
            operation: Operation description
            danger_level: Danger level (SAFE, CAUTION, WARNING, DANGER)
            confirmed: Whether user confirmed
        """
        entry = ConfirmationLogEntry(
            operation=operation,
            danger_level=danger_level,
            confirmed=confirmed,
            session_id=self.session_id
        )
        self._write_entry(entry)
        logger.debug(f"Logged confirmation: {operation} - {confirmed}")
    
    def log_error(self, error_type: str, error_message: str, 
                  context: Optional[Dict[str, Any]] = None):
        """
        Log error
        
        Args:
            error_type: Type of error
            error_message: Error message
            context: Additional context
        """
        entry = ErrorLogEntry(
            error_type=error_type,
            error_message=error_message,
            context=context or {},
            session_id=self.session_id
        )
        self._write_entry(entry)
        logger.debug(f"Logged error: {error_type} - {error_message}")
    
    def get_session_id(self) -> str:
        """Get current session ID"""
        return self.session_id
    
    def get_log_file(self) -> Path:
        """Get log file path"""
        return self.log_file
    
    def read_session_log(self) -> list:
        """
        Read all entries from current session log
        
        Returns:
            List of log entry dicts
        """
        entries = []
        
        if not self.log_file.exists():
            return entries
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entries.append(json.loads(line))
        except Exception as e:
            logger.error(f"Failed to read session log: {e}")
        
        return entries


if __name__ == '__main__':
    # Test session logger
    print("Testing Session Logger...")
    
    # Create logger
    session_logger = SessionLogger(log_dir="logs", session_id="test_session")
    print(f"✓ Logger created: {session_logger.get_log_file()}")
    
    # Log various events
    session_logger.log_query("check hvac codes on my 2008 Ford Escape")
    session_logger.log_parsed_intent(
        action="read_dtc",
        module="HVAC",
        vehicle_info={"make": "Ford", "model": "Escape", "year": "2008"}
    )
    session_logger.log_command("03", "HVAC", "7A0")
    session_logger.log_response("43 00", "03", True)
    session_logger.log_confirmation("Clear DTCs", "CAUTION", True)
    session_logger.log_error("ConnectionError", "Failed to connect to adapter", 
                            {"port": "COM3"})
    
    # Read back log
    entries = session_logger.read_session_log()
    print(f"✓ Logged {len(entries)} entries")
    
    for entry in entries:
        print(f"  - {entry['event_type']}: {entry['timestamp']}")
    
    print("\nSession logger tests passed!")
