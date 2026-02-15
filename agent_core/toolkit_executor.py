"""
Toolkit Executor

Executes toolkit scripts as subprocesses and parses their JSON output.
Provides a clean interface for the agent to run diagnostic scripts.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


class ToolkitExecutionError(Exception):
    """Raised when toolkit script execution fails"""
    pass


class ToolkitExecutor:
    """
    Executes toolkit scripts and parses their output
    
    Toolkit scripts follow a standard interface:
    - Accept CLI arguments
    - Return JSON output to stdout
    - Return error details to stderr
    - Exit with code 0 on success, non-zero on failure
    """
    
    def __init__(self, toolkit_path: Optional[str] = None):
        """
        Initialize toolkit executor
        
        Args:
            toolkit_path: Path to toolkit directory (defaults to ../toolkit)
        """
        if toolkit_path:
            self.toolkit_path = Path(toolkit_path)
        else:
            # Default to toolkit directory relative to this file
            self.toolkit_path = Path(__file__).parent.parent / "toolkit"
        
        if not self.toolkit_path.exists():
            raise ToolkitExecutionError(f"Toolkit path not found: {self.toolkit_path}")
    
    def execute_script(
        self,
        script_name: str,
        args: List[str],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Execute a toolkit script with arguments
        
        Args:
            script_name: Name of script (e.g., "read_dtc.py")
            args: List of command-line arguments
            timeout: Timeout in seconds (default: 30)
            
        Returns:
            Dictionary with parsed JSON output from script
            
        Raises:
            ToolkitExecutionError: If script execution fails
        """
        # Construct script path
        script_path = self.toolkit_path / script_name
        
        if not script_path.exists():
            raise ToolkitExecutionError(f"Script not found: {script_path}")
        
        # Build command
        cmd = [sys.executable, str(script_path)] + args
        
        try:
            # Execute script
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Parse JSON output
            if result.returncode == 0:
                # Success - parse stdout
                try:
                    output = json.loads(result.stdout)
                    return output
                except json.JSONDecodeError as e:
                    raise ToolkitExecutionError(
                        f"Failed to parse script output as JSON: {e}\n"
                        f"Output: {result.stdout}"
                    )
            else:
                # Failure - try to parse stderr for error details
                try:
                    error_output = json.loads(result.stderr)
                    raise ToolkitExecutionError(
                        f"Script failed: {error_output.get('error', 'Unknown error')}"
                    )
                except json.JSONDecodeError:
                    # Stderr is not JSON, use raw text
                    raise ToolkitExecutionError(
                        f"Script failed with exit code {result.returncode}\n"
                        f"Error: {result.stderr or result.stdout}"
                    )
        
        except subprocess.TimeoutExpired:
            raise ToolkitExecutionError(
                f"Script execution timed out after {timeout} seconds"
            )
        except Exception as e:
            if isinstance(e, ToolkitExecutionError):
                raise
            raise ToolkitExecutionError(f"Unexpected error executing script: {e}")
    
    def read_dtc(
        self,
        port: str,
        module: Optional[str] = None,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute read_dtc.py toolkit script
        
        Args:
            port: Serial port (e.g., COM3)
            module: Module name (optional)
            address: CAN address in hex (optional)
            
        Returns:
            Dictionary with DTCs: {"success": bool, "dtcs": [...], "count": int}
        """
        args = ["--port", port, "--json"]
        
        if module:
            args.extend(["--module", module])
        
        if address:
            args.extend(["--address", address])
        
        return self.execute_script("vehicle_communication/read_dtc.py", args)
    
    def clear_dtc(
        self,
        port: str,
        module: Optional[str] = None,
        address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute clear_dtc.py toolkit script
        
        Args:
            port: Serial port (e.g., COM3)
            module: Module name (optional)
            address: CAN address in hex (optional)
            
        Returns:
            Dictionary with result: {"success": bool, "cleared": bool}
        """
        args = ["--port", port, "--json", "--confirm"]
        
        if module:
            args.extend(["--module", module])
        
        if address:
            args.extend(["--address", address])
        
        return self.execute_script("vehicle_communication/clear_dtc.py", args)
    
    def read_vin(self, port: str) -> Dict[str, Any]:
        """
        Execute read_vin.py toolkit script
        
        Args:
            port: Serial port (e.g., COM3)
            
        Returns:
            Dictionary with VIN: {"success": bool, "vin": str}
        """
        args = ["--port", port, "--json"]
        return self.execute_script("vehicle_communication/read_vin.py", args)
    
    def can_explore(
        self,
        port: str,
        duration: int = 10
    ) -> Dict[str, Any]:
        """
        Execute can_explore.py toolkit script
        
        Args:
            port: Serial port (e.g., COM3)
            duration: Capture duration in seconds
            
        Returns:
            Dictionary with modules: {"success": bool, "modules": [...]}
        """
        args = ["--port", port, "--duration", str(duration), "--json"]
        return self.execute_script("vehicle_communication/can_explore.py", args)


# Convenience function for quick testing
def main():
    """Test toolkit executor"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test toolkit executor')
    parser.add_argument('--port', default='COM3', help='Serial port')
    parser.add_argument('--module', help='Module name')
    parser.add_argument('--address', help='CAN address')
    parser.add_argument('--action', choices=['read', 'clear'], default='read')
    
    args = parser.parse_args()
    
    executor = ToolkitExecutor()
    
    try:
        if args.action == 'read':
            result = executor.read_dtc(args.port, args.module, args.address)
        else:
            result = executor.clear_dtc(args.port, args.module, args.address)
        
        print(json.dumps(result, indent=2))
    
    except ToolkitExecutionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
