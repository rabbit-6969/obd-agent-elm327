"""
Diagnostic Report Generator

Generates comprehensive diagnostic reports from session data.
Supports multiple export formats (markdown, JSON).
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class DiagnosticReport:
    """
    Diagnostic report data structure
    
    Contains:
    - Vehicle information
    - Modules scanned
    - DTCs found
    - Commands executed
    - Raw responses
    - AI-generated interpretation
    - Recommendations
    """
    
    def __init__(self):
        self.timestamp = datetime.now().isoformat()
        self.vehicle_info: Dict[str, str] = {}
        self.modules_scanned: List[Dict[str, Any]] = []
        self.dtcs_found: List[Dict[str, Any]] = []
        self.commands_executed: List[Dict[str, Any]] = []
        self.raw_responses: List[Dict[str, Any]] = []
        self.interpretation: str = ""
        self.recommendations: List[str] = []
        self.web_resources: List[Dict[str, str]] = []
        self.session_id: Optional[str] = None
    
    def set_vehicle_info(self, make: str, model: str, year: str, vin: Optional[str] = None):
        """Set vehicle information"""
        self.vehicle_info = {
            "make": make,
            "model": model,
            "year": year
        }
        if vin:
            self.vehicle_info["vin"] = vin
    
    def add_module_scanned(self, module_name: str, address: str, 
                          status: str, dtc_count: int = 0):
        """Add scanned module"""
        self.modules_scanned.append({
            "name": module_name,
            "address": address,
            "status": status,
            "dtc_count": dtc_count
        })
    
    def add_dtc(self, code: str, description: str, module: str, 
                severity: str = "unknown"):
        """Add DTC found"""
        self.dtcs_found.append({
            "code": code,
            "description": description,
            "module": module,
            "severity": severity
        })
    
    def add_command(self, command: str, module: str, timestamp: str, 
                   success: bool):
        """Add executed command"""
        self.commands_executed.append({
            "command": command,
            "module": module,
            "timestamp": timestamp,
            "success": success
        })
    
    def add_raw_response(self, command: str, response: str, module: str):
        """Add raw response"""
        self.raw_responses.append({
            "command": command,
            "response": response,
            "module": module
        })
    
    def set_interpretation(self, interpretation: str):
        """Set AI-generated interpretation"""
        self.interpretation = interpretation
    
    def add_recommendation(self, recommendation: str):
        """Add recommendation"""
        self.recommendations.append(recommendation)
    
    def add_web_resource(self, title: str, url: str, description: str = ""):
        """Add web resource"""
        self.web_resources.append({
            "title": title,
            "url": url,
            "description": description
        })
    
    def set_session_id(self, session_id: str):
        """Set session ID"""
        self.session_id = session_id


class ReportGenerator:
    """
    Generates diagnostic reports in various formats
    
    Supported formats:
    - Markdown (.md)
    - JSON (.json)
    """
    
    def __init__(self):
        pass
    
    def generate_markdown(self, report: DiagnosticReport) -> str:
        """
        Generate markdown report
        
        Args:
            report: DiagnosticReport object
            
        Returns:
            Markdown formatted string
        """
        lines = []
        
        # Header
        lines.append("# Vehicle Diagnostic Report")
        lines.append("")
        lines.append(f"**Generated:** {report.timestamp}")
        if report.session_id:
            lines.append(f"**Session ID:** {report.session_id}")
        lines.append("")
        
        # Vehicle Information
        lines.append("## Vehicle Information")
        lines.append("")
        if report.vehicle_info:
            lines.append(f"- **Make:** {report.vehicle_info.get('make', 'N/A')}")
            lines.append(f"- **Model:** {report.vehicle_info.get('model', 'N/A')}")
            lines.append(f"- **Year:** {report.vehicle_info.get('year', 'N/A')}")
            if 'vin' in report.vehicle_info:
                lines.append(f"- **VIN:** {report.vehicle_info['vin']}")
        else:
            lines.append("No vehicle information available.")
        lines.append("")
        
        # Modules Scanned
        lines.append("## Modules Scanned")
        lines.append("")
        if report.modules_scanned:
            for module in report.modules_scanned:
                lines.append(f"### {module['name']}")
                lines.append(f"- **Address:** {module['address']}")
                lines.append(f"- **Status:** {module['status']}")
                lines.append(f"- **DTCs Found:** {module['dtc_count']}")
                lines.append("")
        else:
            lines.append("No modules scanned.")
            lines.append("")
        
        # DTCs Found
        lines.append("## Diagnostic Trouble Codes (DTCs)")
        lines.append("")
        if report.dtcs_found:
            for dtc in report.dtcs_found:
                lines.append(f"### {dtc['code']} - {dtc['module']}")
                lines.append(f"**Description:** {dtc['description']}")
                lines.append(f"**Severity:** {dtc['severity']}")
                lines.append("")
        else:
            lines.append("No DTCs found.")
            lines.append("")
        
        # Commands Executed
        lines.append("## Commands Executed")
        lines.append("")
        if report.commands_executed:
            lines.append("| Timestamp | Module | Command | Success |")
            lines.append("|-----------|--------|---------|---------|")
            for cmd in report.commands_executed:
                success_icon = "✓" if cmd['success'] else "✗"
                lines.append(f"| {cmd['timestamp']} | {cmd['module']} | `{cmd['command']}` | {success_icon} |")
            lines.append("")
        else:
            lines.append("No commands executed.")
            lines.append("")
        
        # Raw Responses
        lines.append("## Raw Responses")
        lines.append("")
        if report.raw_responses:
            for resp in report.raw_responses:
                lines.append(f"### {resp['module']} - Command: `{resp['command']}`")
                lines.append("```")
                lines.append(resp['response'])
                lines.append("```")
                lines.append("")
        else:
            lines.append("No raw responses recorded.")
            lines.append("")
        
        # AI Interpretation
        if report.interpretation:
            lines.append("## AI Interpretation")
            lines.append("")
            lines.append(report.interpretation)
            lines.append("")
        
        # Recommendations
        if report.recommendations:
            lines.append("## Recommendations")
            lines.append("")
            for i, rec in enumerate(report.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")
        
        # Web Resources
        if report.web_resources:
            lines.append("## Additional Resources")
            lines.append("")
            for resource in report.web_resources:
                lines.append(f"- [{resource['title']}]({resource['url']})")
                if resource.get('description'):
                    lines.append(f"  {resource['description']}")
            lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("*Report generated by AI Vehicle Diagnostic Agent*")
        
        return "\n".join(lines)
    
    def generate_json(self, report: DiagnosticReport) -> str:
        """
        Generate JSON report
        
        Args:
            report: DiagnosticReport object
            
        Returns:
            JSON formatted string
        """
        data = {
            "timestamp": report.timestamp,
            "session_id": report.session_id,
            "vehicle_info": report.vehicle_info,
            "modules_scanned": report.modules_scanned,
            "dtcs_found": report.dtcs_found,
            "commands_executed": report.commands_executed,
            "raw_responses": report.raw_responses,
            "interpretation": report.interpretation,
            "recommendations": report.recommendations,
            "web_resources": report.web_resources
        }
        
        return json.dumps(data, indent=2)
    
    def save_report(self, report: DiagnosticReport, filepath: str, 
                   format: str = "markdown"):
        """
        Save report to file
        
        Args:
            report: DiagnosticReport object
            filepath: Output file path
            format: Report format ("markdown" or "json")
        """
        filepath = Path(filepath)
        
        if format.lower() == "markdown" or filepath.suffix == ".md":
            content = self.generate_markdown(report)
        elif format.lower() == "json" or filepath.suffix == ".json":
            content = self.generate_json(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)


if __name__ == '__main__':
    # Test report generator
    print("Testing Report Generator...")
    
    # Create sample report
    report = DiagnosticReport()
    report.set_session_id("test_20260223_120000")
    report.set_vehicle_info("Ford", "Escape", "2008", "1FMCU03Z68KB12969")
    
    report.add_module_scanned("PCM", "7E0", "accessible", 0)
    report.add_module_scanned("ABS", "760", "partial", 1)
    report.add_module_scanned("HVAC", "7A0", "not_accessible", 0)
    
    report.add_dtc("C1234", "ABS Wheel Speed Sensor Circuit Malfunction", "ABS", "warning")
    
    report.add_command("03", "PCM", "2026-02-23T12:00:00", True)
    report.add_command("03", "ABS", "2026-02-23T12:00:05", True)
    
    report.add_raw_response("03", "43 00", "PCM")
    report.add_raw_response("03", "43 C1 23 4", "ABS")
    
    report.set_interpretation(
        "The vehicle shows one DTC in the ABS module related to wheel speed sensor. "
        "PCM and HVAC modules show no codes. The ABS issue should be investigated further."
    )
    
    report.add_recommendation("Inspect ABS wheel speed sensor wiring for damage")
    report.add_recommendation("Check wheel speed sensor resistance values")
    report.add_recommendation("Clear codes after repair and retest")
    
    report.add_web_resource(
        "Ford Escape ABS Diagnostics",
        "https://example.com/ford-escape-abs",
        "Comprehensive guide to ABS troubleshooting"
    )
    
    # Generate reports
    generator = ReportGenerator()
    
    # Markdown
    md_content = generator.generate_markdown(report)
    print("✓ Generated markdown report")
    print(f"  Length: {len(md_content)} characters")
    
    # JSON
    json_content = generator.generate_json(report)
    print("✓ Generated JSON report")
    print(f"  Length: {len(json_content)} characters")
    
    # Save to files
    generator.save_report(report, "logs/test_report.md", "markdown")
    generator.save_report(report, "logs/test_report.json", "json")
    print("✓ Saved reports to logs/")
    
    print("\nReport generator tests passed!")
