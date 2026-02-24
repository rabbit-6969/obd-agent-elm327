"""
Closed-Loop Feedback System

Tracks diagnostic procedure success/failure rates and documents
successful procedures back to the knowledge base for continuous learning.

After successful diagnostics:
1. Document procedure in knowledge base
2. Track success/failure rates
3. Prioritize high-success procedures in future sessions
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProcedureExecution:
    """Record of a single procedure execution"""
    timestamp: float
    module: str
    action: str
    protocol: str
    success: bool
    duration: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat(),
            'module': self.module,
            'action': self.action,
            'protocol': self.protocol,
            'success': self.success,
            'duration': self.duration,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class ProcedureStats:
    """Statistics for a specific procedure"""
    module: str
    action: str
    protocol: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_duration: float = 0.0
    success_rate: float = 0.0
    last_execution: Optional[float] = None
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    
    def update(self, execution: ProcedureExecution):
        """Update statistics with new execution"""
        self.total_executions += 1
        self.last_execution = execution.timestamp
        
        if execution.success:
            self.successful_executions += 1
            self.last_success = execution.timestamp
        else:
            self.failed_executions += 1
            self.last_failure = execution.timestamp
        
        # Update success rate
        self.success_rate = (
            self.successful_executions / self.total_executions
            if self.total_executions > 0 else 0.0
        )
        
        # Update average duration
        if execution.duration > 0:
            total_duration = self.average_duration * (self.total_executions - 1)
            self.average_duration = (total_duration + execution.duration) / self.total_executions
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'module': self.module,
            'action': self.action,
            'protocol': self.protocol,
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': round(self.success_rate, 3),
            'average_duration': round(self.average_duration, 3),
            'last_execution': self.last_execution,
            'last_success': self.last_success,
            'last_failure': self.last_failure
        }


class FeedbackSystem:
    """
    Closed-loop feedback system for diagnostic procedures
    
    Tracks procedure execution history and statistics to:
    - Learn which procedures work best
    - Prioritize successful procedures
    - Document new procedures
    - Identify failing procedures
    """
    
    def __init__(self, feedback_dir: Optional[str] = None):
        """
        Initialize feedback system
        
        Args:
            feedback_dir: Directory for feedback data (default: ./feedback)
        """
        if feedback_dir:
            self.feedback_dir = Path(feedback_dir)
        else:
            self.feedback_dir = Path(__file__).parent.parent / "feedback"
        
        # Create feedback directory if it doesn't exist
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        
        # Paths for feedback files
        self.history_file = self.feedback_dir / "execution_history.jsonl"
        self.stats_file = self.feedback_dir / "procedure_stats.json"
        
        # Load existing statistics
        self.stats: Dict[str, ProcedureStats] = self._load_stats()
    
    def record_execution(
        self,
        module: str,
        action: str,
        protocol: str,
        success: bool,
        duration: float = 0.0,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ProcedureExecution:
        """
        Record a procedure execution
        
        Args:
            module: Module name (e.g., "PCM")
            action: Action performed (e.g., "READ_DTC")
            protocol: Protocol used (e.g., "standard_obd")
            success: Whether execution succeeded
            duration: Execution duration in seconds
            error: Error message if failed
            metadata: Additional metadata
            
        Returns:
            ProcedureExecution record
        """
        # Create execution record
        execution = ProcedureExecution(
            timestamp=time.time(),
            module=module,
            action=action,
            protocol=protocol,
            success=success,
            duration=duration,
            error=error,
            metadata=metadata or {}
        )
        
        # Append to history file (JSONL format)
        self._append_to_history(execution)
        
        # Update statistics
        self._update_stats(execution)
        
        return execution
    
    def get_procedure_stats(
        self,
        module: str,
        action: str,
        protocol: Optional[str] = None
    ) -> Optional[ProcedureStats]:
        """
        Get statistics for a specific procedure
        
        Args:
            module: Module name
            action: Action name
            protocol: Protocol (optional, returns best if not specified)
            
        Returns:
            ProcedureStats or None if not found
        """
        if protocol:
            key = self._make_stats_key(module, action, protocol)
            return self.stats.get(key)
        
        # Find best protocol for this module/action
        best_stats = None
        best_success_rate = 0.0
        
        for key, stats in self.stats.items():
            if stats.module == module and stats.action == action:
                if stats.success_rate > best_success_rate:
                    best_success_rate = stats.success_rate
                    best_stats = stats
        
        return best_stats
    
    def get_recommended_protocol(
        self,
        module: str,
        action: str
    ) -> Optional[str]:
        """
        Get recommended protocol based on success rates
        
        Args:
            module: Module name
            action: Action name
            
        Returns:
            Protocol name with highest success rate, or None
        """
        stats = self.get_procedure_stats(module, action)
        return stats.protocol if stats else None
    
    def get_top_procedures(
        self,
        limit: int = 10,
        min_executions: int = 3
    ) -> List[ProcedureStats]:
        """
        Get top-performing procedures by success rate
        
        Args:
            limit: Maximum number of procedures to return
            min_executions: Minimum executions required
            
        Returns:
            List of ProcedureStats sorted by success rate
        """
        # Filter procedures with minimum executions
        qualified = [
            stats for stats in self.stats.values()
            if stats.total_executions >= min_executions
        ]
        
        # Sort by success rate (descending)
        sorted_stats = sorted(
            qualified,
            key=lambda s: (s.success_rate, s.total_executions),
            reverse=True
        )
        
        return sorted_stats[:limit]
    
    def get_failing_procedures(
        self,
        threshold: float = 0.5,
        min_executions: int = 3
    ) -> List[ProcedureStats]:
        """
        Get procedures with low success rates
        
        Args:
            threshold: Success rate threshold (default: 0.5)
            min_executions: Minimum executions required
            
        Returns:
            List of ProcedureStats with low success rates
        """
        failing = [
            stats for stats in self.stats.values()
            if stats.total_executions >= min_executions
            and stats.success_rate < threshold
        ]
        
        # Sort by success rate (ascending)
        return sorted(failing, key=lambda s: s.success_rate)
    
    def export_stats(self, filepath: Optional[str] = None) -> str:
        """
        Export statistics to JSON file
        
        Args:
            filepath: Output file path (optional)
            
        Returns:
            Path to exported file
        """
        if not filepath:
            filepath = self.feedback_dir / f"stats_export_{int(time.time())}.json"
        else:
            filepath = Path(filepath)
        
        # Prepare export data
        export_data = {
            'exported_at': datetime.now().isoformat(),
            'total_procedures': len(self.stats),
            'procedures': [stats.to_dict() for stats in self.stats.values()]
        }
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        return str(filepath)
    
    def _make_stats_key(self, module: str, action: str, protocol: str) -> str:
        """Create unique key for procedure statistics"""
        return f"{module}:{action}:{protocol}"
    
    def _append_to_history(self, execution: ProcedureExecution):
        """Append execution to history file (JSONL format)"""
        with open(self.history_file, 'a') as f:
            f.write(json.dumps(execution.to_dict()) + '\n')
    
    def _update_stats(self, execution: ProcedureExecution):
        """Update statistics with new execution"""
        key = self._make_stats_key(
            execution.module,
            execution.action,
            execution.protocol
        )
        
        # Get or create stats
        if key not in self.stats:
            self.stats[key] = ProcedureStats(
                module=execution.module,
                action=execution.action,
                protocol=execution.protocol
            )
        
        # Update stats
        self.stats[key].update(execution)
        
        # Save updated stats
        self._save_stats()
    
    def _load_stats(self) -> Dict[str, ProcedureStats]:
        """Load statistics from file"""
        if not self.stats_file.exists():
            return {}
        
        try:
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
            
            stats = {}
            for item in data.get('procedures', []):
                key = self._make_stats_key(
                    item['module'],
                    item['action'],
                    item['protocol']
                )
                stats[key] = ProcedureStats(**item)
            
            return stats
        
        except Exception as e:
            print(f"Warning: Failed to load stats: {e}")
            return {}
    
    def _save_stats(self):
        """Save statistics to file"""
        try:
            data = {
                'updated_at': datetime.now().isoformat(),
                'total_procedures': len(self.stats),
                'procedures': [stats.to_dict() for stats in self.stats.values()]
            }
            
            with open(self.stats_file, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            print(f"Warning: Failed to save stats: {e}")


def main():
    """Test feedback system"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test feedback system')
    parser.add_argument('--action', choices=['record', 'stats', 'top', 'failing', 'export'])
    parser.add_argument('--module', help='Module name')
    parser.add_argument('--operation', help='Operation name')
    parser.add_argument('--protocol', help='Protocol name')
    parser.add_argument('--success', action='store_true', help='Mark as successful')
    
    args = parser.parse_args()
    
    feedback = FeedbackSystem()
    
    if args.action == 'record':
        if not all([args.module, args.operation, args.protocol]):
            print("Error: --module, --operation, and --protocol required for record")
            return
        
        execution = feedback.record_execution(
            module=args.module,
            action=args.operation,
            protocol=args.protocol,
            success=args.success,
            duration=1.5
        )
        print(f"Recorded: {execution.module}.{execution.action} ({execution.protocol})")
        print(f"Success: {execution.success}")
    
    elif args.action == 'stats':
        if not all([args.module, args.operation]):
            print("Error: --module and --operation required for stats")
            return
        
        stats = feedback.get_procedure_stats(args.module, args.operation, args.protocol)
        if stats:
            print(json.dumps(stats.to_dict(), indent=2))
        else:
            print("No statistics found")
    
    elif args.action == 'top':
        top = feedback.get_top_procedures()
        print(f"Top {len(top)} procedures:")
        for stats in top:
            print(f"  {stats.module}.{stats.action} ({stats.protocol}): "
                  f"{stats.success_rate:.1%} success ({stats.total_executions} executions)")
    
    elif args.action == 'failing':
        failing = feedback.get_failing_procedures()
        print(f"Failing procedures ({len(failing)}):")
        for stats in failing:
            print(f"  {stats.module}.{stats.action} ({stats.protocol}): "
                  f"{stats.success_rate:.1%} success ({stats.total_executions} executions)")
    
    elif args.action == 'export':
        filepath = feedback.export_stats()
        print(f"Exported to: {filepath}")


if __name__ == '__main__':
    main()
