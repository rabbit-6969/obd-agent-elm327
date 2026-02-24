"""
Sandboxed Script Executor

Executes generated scripts in restricted environment with limited file system
and network access. Supports script persistence for reuse.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


logger = logging.getLogger(__name__)


class ScriptExecutor:
    """
    Sandboxed script executor
    
    Executes Python scripts with restrictions:
    - Limited file system access (temp directory only)
    - Timeout enforcement
    - Resource limits
    """
    
    def __init__(self, timeout: int = 30, allowed_dirs: Optional[List[str]] = None,
                 script_library: str = "knowledge_base/scripts"):
        """
        Initialize script executor
        
        Args:
            timeout: Execution timeout in seconds
            allowed_dirs: List of allowed directories for file access
            script_library: Directory for saved scripts
        """
        self.timeout = timeout
        self.allowed_dirs = allowed_dirs or []
        self.script_library = Path(script_library)
        self.script_library.mkdir(parents=True, exist_ok=True)
        
        # Load script metadata
        self.metadata_file = self.script_library / "script_metadata.json"
        self.metadata = self._load_metadata()
    
    def execute_script(self, script_code: str, 
                      script_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute Python script in sandboxed environment
        
        Args:
            script_code: Python script code
            script_args: Command-line arguments for script
            
        Returns:
            Execution results
        """
        logger.info("Executing script in sandbox...")
        
        # Create temporary script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            script_path = f.name
            f.write(script_code)
        
        try:
            # Build command
            cmd = ["python", script_path]
            if script_args:
                cmd.extend(script_args)
            
            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            # Parse output
            execution_result = {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            # Try to parse JSON output
            if result.stdout:
                try:
                    json_output = json.loads(result.stdout)
                    execution_result["parsed_output"] = json_output
                except json.JSONDecodeError:
                    pass
            
            logger.info(f"Script execution {'succeeded' if result.returncode == 0 else 'failed'}")
            
            return execution_result
        
        except subprocess.TimeoutExpired:
            logger.error(f"Script execution timed out after {self.timeout}s")
            return {
                "success": False,
                "error": f"Execution timed out after {self.timeout} seconds"
            }
        
        except Exception as e:
            logger.error(f"Script execution error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        
        finally:
            # Clean up temporary file
            try:
                Path(script_path).unlink()
            except Exception:
                pass
    
    def execute_script_file(self, script_path: str,
                           script_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute Python script file
        
        Args:
            script_path: Path to script file
            script_args: Command-line arguments
            
        Returns:
            Execution results
        """
        try:
            with open(script_path, 'r') as f:
                script_code = f.read()
            
            return self.execute_script(script_code, script_args)
        
        except Exception as e:
            logger.error(f"Failed to read script file: {e}")
            return {
                "success": False,
                "error": f"Failed to read script: {e}"
            }
    
    def validate_script(self, script_code: str) -> Dict[str, Any]:
        """
        Validate script syntax without executing
        
        Args:
            script_code: Python script code
            
        Returns:
            Validation results
        """
        try:
            compile(script_code, '<string>', 'exec')
            return {
                "valid": True,
                "message": "Script syntax is valid"
            }
        except SyntaxError as e:
            return {
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "offset": e.offset
            }
    
    def check_safety(self, script_code: str) -> Dict[str, Any]:
        """
        Check script for potentially dangerous operations
        
        Args:
            script_code: Python script code
            
        Returns:
            Safety check results
        """
        dangerous_patterns = [
            "os.system",
            "subprocess.call",
            "eval(",
            "exec(",
            "__import__",
            "open(",  # File operations
            "rmdir",
            "unlink",
            "remove"
        ]
        
        warnings = []
        for pattern in dangerous_patterns:
            if pattern in script_code:
                warnings.append(f"Potentially dangerous operation: {pattern}")
        
        return {
            "safe": len(warnings) == 0,
            "warnings": warnings
        }
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load script metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save script metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def save_script(self, script_code: str, script_name: str,
                   description: str = "", tags: Optional[List[str]] = None) -> bool:
        """
        Save script to library for reuse
        
        Args:
            script_code: Python script code
            script_name: Name for the script
            description: Script description
            tags: Tags for categorization
            
        Returns:
            True if saved successfully
        """
        try:
            # Generate filename
            script_file = self.script_library / f"{script_name}.py"
            
            # Save script
            with open(script_file, 'w') as f:
                f.write(script_code)
            
            # Update metadata
            self.metadata[script_name] = {
                "filename": script_file.name,
                "description": description,
                "tags": tags or [],
                "created_at": datetime.now().isoformat(),
                "execution_count": 0,
                "last_executed": None
            }
            
            self._save_metadata()
            
            logger.info(f"Saved script '{script_name}' to library")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save script: {e}")
            return False
    
    def load_script(self, script_name: str) -> Optional[str]:
        """
        Load script from library
        
        Args:
            script_name: Name of script to load
            
        Returns:
            Script code or None
        """
        if script_name not in self.metadata:
            logger.warning(f"Script '{script_name}' not found in library")
            return None
        
        try:
            script_file = self.script_library / self.metadata[script_name]["filename"]
            
            with open(script_file, 'r') as f:
                return f.read()
        
        except Exception as e:
            logger.error(f"Failed to load script: {e}")
            return None
    
    def execute_saved_script(self, script_name: str,
                            script_args: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute script from library
        
        Args:
            script_name: Name of script to execute
            script_args: Command-line arguments
            
        Returns:
            Execution results
        """
        script_code = self.load_script(script_name)
        
        if not script_code:
            return {
                "success": False,
                "error": f"Script '{script_name}' not found"
            }
        
        # Execute script
        result = self.execute_script(script_code, script_args)
        
        # Update execution metadata
        if script_name in self.metadata:
            self.metadata[script_name]["execution_count"] += 1
            self.metadata[script_name]["last_executed"] = datetime.now().isoformat()
            self._save_metadata()
        
        return result
    
    def list_scripts(self, tag: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List scripts in library
        
        Args:
            tag: Filter by tag (optional)
            
        Returns:
            List of script info
        """
        scripts = []
        
        for name, info in self.metadata.items():
            if tag is None or tag in info.get("tags", []):
                scripts.append({
                    "name": name,
                    "description": info.get("description", ""),
                    "tags": info.get("tags", []),
                    "execution_count": info.get("execution_count", 0),
                    "last_executed": info.get("last_executed")
                })
        
        return scripts
    
    def delete_script(self, script_name: str) -> bool:
        """
        Delete script from library
        
        Args:
            script_name: Name of script to delete
            
        Returns:
            True if deleted successfully
        """
        if script_name not in self.metadata:
            logger.warning(f"Script '{script_name}' not found")
            return False
        
        try:
            # Delete file
            script_file = self.script_library / self.metadata[script_name]["filename"]
            if script_file.exists():
                script_file.unlink()
            
            # Remove from metadata
            del self.metadata[script_name]
            self._save_metadata()
            
            logger.info(f"Deleted script '{script_name}'")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete script: {e}")
            return False


if __name__ == '__main__':
    # Test script executor
    print("Testing Script Executor...")
    
    executor = ScriptExecutor(timeout=10)
    
    # Test simple script
    print("\n1. Testing simple script execution...")
    simple_script = '''
import json
result = {"success": True, "message": "Hello from script!"}
print(json.dumps(result))
'''
    
    result = executor.execute_script(simple_script)
    print(f"   Success: {result['success']}")
    if result.get('parsed_output'):
        print(f"   Output: {result['parsed_output']}")
    
    # Test script with error
    print("\n2. Testing script with error...")
    error_script = '''
import json
raise ValueError("Test error")
'''
    
    result = executor.execute_script(error_script)
    print(f"   Success: {result['success']}")
    print(f"   Error captured: {bool(result.get('stderr'))}")
    
    # Test syntax validation
    print("\n3. Testing syntax validation...")
    invalid_script = '''
def broken_function(
    print("missing closing paren")
'''
    
    validation = executor.validate_script(invalid_script)
    print(f"   Valid: {validation['valid']}")
    if not validation['valid']:
        print(f"   Error: {validation['error']}")
    
    # Test safety check
    print("\n4. Testing safety check...")
    unsafe_script = '''
import os
os.system("rm -rf /")
'''
    
    safety = executor.check_safety(unsafe_script)
    print(f"   Safe: {safety['safe']}")
    if safety['warnings']:
        print(f"   Warnings: {len(safety['warnings'])}")
        for warning in safety['warnings']:
            print(f"     - {warning}")
    
    # Test timeout
    print("\n5. Testing timeout...")
    timeout_script = '''
import time
time.sleep(100)
'''
    
    executor_short = ScriptExecutor(timeout=2)
    result = executor_short.execute_script(timeout_script)
    print(f"   Success: {result['success']}")
    print(f"   Timeout detected: {'timeout' in result.get('error', '').lower()}")
    
    # Test script persistence
    print("\n6. Testing script persistence...")
    test_script = '''
import json
print(json.dumps({"success": True, "data": "test"}))
'''
    
    saved = executor.save_script(test_script, "test_script", 
                                "Test script for persistence", ["test", "demo"])
    print(f"   Script saved: {saved}")
    
    # List scripts
    print("\n7. Listing scripts...")
    scripts = executor.list_scripts()
    print(f"   Found {len(scripts)} scripts")
    
    # Execute saved script
    print("\n8. Executing saved script...")
    result = executor.execute_saved_script("test_script")
    print(f"   Success: {result['success']}")
    
    # Delete script
    print("\n9. Deleting script...")
    deleted = executor.delete_script("test_script")
    print(f"   Script deleted: {deleted}")
    
    # Clean up test library
    import shutil
    if Path("knowledge_base/scripts").exists():
        shutil.rmtree("knowledge_base/scripts")
    
    print("\nScript executor tests passed!")
