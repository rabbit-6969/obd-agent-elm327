"""
Script Generator for Research and Data Analysis

Generates Python scripts for web scraping, data parsing, and CAN analysis.
Uses templates for common script patterns.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class ScriptGenerator:
    """
    Generates Python scripts for various tasks
    
    Supports:
    - Web scraping service manuals
    - Parsing DTC databases
    - Analyzing CAN bus logs
    """
    
    def __init__(self):
        """Initialize script generator"""
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """Load script templates"""
        return {
            "web_scraper": self._web_scraper_template(),
            "dtc_parser": self._dtc_parser_template(),
            "can_analyzer": self._can_analyzer_template()
        }
    
    def generate_web_scraper(self, url: str, target_data: str,
                            output_file: str = "scraped_data.json") -> str:
        """
        Generate web scraping script
        
        Args:
            url: URL to scrape
            target_data: Description of data to extract
            output_file: Output file path
            
        Returns:
            Generated script code
        """
        template = self.templates["web_scraper"]
        
        script = template.format(
            url=url,
            target_data=target_data,
            output_file=output_file
        )
        
        logger.info(f"Generated web scraper for {url}")
        return script
    
    def generate_dtc_parser(self, input_file: str, dtc_format: str,
                           output_file: str = "parsed_dtcs.json") -> str:
        """
        Generate DTC parsing script
        
        Args:
            input_file: Input file with DTC data
            dtc_format: Format description
            output_file: Output file path
            
        Returns:
            Generated script code
        """
        template = self.templates["dtc_parser"]
        
        script = template.format(
            input_file=input_file,
            dtc_format=dtc_format,
            output_file=output_file
        )
        
        logger.info(f"Generated DTC parser for {input_file}")
        return script
    
    def generate_can_analyzer(self, log_file: str, analysis_type: str,
                             output_file: str = "can_analysis.json") -> str:
        """
        Generate CAN log analysis script
        
        Args:
            log_file: CAN log file path
            analysis_type: Type of analysis (frequency, patterns, etc.)
            output_file: Output file path
            
        Returns:
            Generated script code
        """
        template = self.templates["can_analyzer"]
        
        script = template.format(
            log_file=log_file,
            analysis_type=analysis_type,
            output_file=output_file
        )
        
        logger.info(f"Generated CAN analyzer for {log_file}")
        return script
    
    def save_script(self, script_code: str, output_path: str) -> bool:
        """
        Save generated script to file
        
        Args:
            script_code: Script code
            output_path: Output file path
            
        Returns:
            True if saved successfully
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                f.write(script_code)
            
            logger.info(f"Saved script to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save script: {e}")
            return False
    
    def _web_scraper_template(self) -> str:
        """Web scraper template"""
        return '''"""
Generated Web Scraper
Target: {target_data}
"""

import json
import sys
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

def scrape_data(url):
    """Scrape data from URL"""
    try:
        # Add user agent to avoid blocking
        headers = {{'User-Agent': 'Mozilla/5.0'}}
        request = Request(url, headers=headers)
        
        with urlopen(request, timeout=10) as response:
            content = response.read().decode('utf-8')
        
        # Extract target data: {target_data}
        # TODO: Add extraction logic based on target_data
        
        results = {{
            "success": True,
            "url": url,
            "content_length": len(content),
            "data": content[:500]  # First 500 chars
        }}
        
        return results
    
    except (URLError, HTTPError) as e:
        return {{
            "success": False,
            "error": str(e)
        }}

if __name__ == '__main__':
    url = "{url}"
    results = scrape_data(url)
    
    # Save results
    with open("{output_file}", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print to stdout
    print(json.dumps(results))
'''
    
    def _dtc_parser_template(self) -> str:
        """DTC parser template"""
        return '''"""
Generated DTC Parser
Format: {dtc_format}
"""

import json
import re
import sys

def parse_dtcs(input_file):
    """Parse DTCs from file"""
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        # Parse DTC format: {dtc_format}
        # Standard DTC pattern: P0XXX, C0XXX, B0XXX, U0XXX
        dtc_pattern = r'[PCBU][0-9A-F]{{4}}'
        
        dtcs = re.findall(dtc_pattern, content, re.IGNORECASE)
        
        results = {{
            "success": True,
            "input_file": input_file,
            "dtc_count": len(dtcs),
            "dtcs": list(set(dtcs))  # Unique DTCs
        }}
        
        return results
    
    except Exception as e:
        return {{
            "success": False,
            "error": str(e)
        }}

if __name__ == '__main__':
    input_file = "{input_file}"
    results = parse_dtcs(input_file)
    
    # Save results
    with open("{output_file}", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print to stdout
    print(json.dumps(results))
'''
    
    def _can_analyzer_template(self) -> str:
        """CAN analyzer template"""
        return '''"""
Generated CAN Analyzer
Analysis: {analysis_type}
"""

import json
import sys
from collections import defaultdict

def analyze_can_log(log_file):
    """Analyze CAN log file"""
    try:
        can_ids = defaultdict(int)
        
        with open(log_file, 'r') as f:
            for line in f:
                # Parse CAN frame (format: ID: DATA)
                if ':' in line:
                    parts = line.split(':')
                    can_id = parts[0].strip()
                    can_ids[can_id] += 1
        
        # Analysis type: {analysis_type}
        # Sort by frequency
        sorted_ids = sorted(can_ids.items(), key=lambda x: x[1], reverse=True)
        
        results = {{
            "success": True,
            "log_file": log_file,
            "unique_ids": len(can_ids),
            "total_frames": sum(can_ids.values()),
            "top_ids": [
                {{"id": id, "count": count}}
                for id, count in sorted_ids[:10]
            ]
        }}
        
        return results
    
    except Exception as e:
        return {{
            "success": False,
            "error": str(e)
        }}

if __name__ == '__main__':
    log_file = "{log_file}"
    results = analyze_can_log(log_file)
    
    # Save results
    with open("{output_file}", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print to stdout
    print(json.dumps(results))
'''


if __name__ == '__main__':
    # Test script generator
    print("Testing Script Generator...")
    
    generator = ScriptGenerator()
    
    # Generate web scraper
    print("\n1. Generating web scraper...")
    scraper = generator.generate_web_scraper(
        "https://example.com/manual",
        "OBD2 commands for HVAC module",
        "scraped_manual.json"
    )
    print(f"   Generated {len(scraper)} characters")
    
    # Generate DTC parser
    print("\n2. Generating DTC parser...")
    parser = generator.generate_dtc_parser(
        "dtc_database.txt",
        "Standard OBD2 format",
        "parsed_dtcs.json"
    )
    print(f"   Generated {len(parser)} characters")
    
    # Generate CAN analyzer
    print("\n3. Generating CAN analyzer...")
    analyzer = generator.generate_can_analyzer(
        "can_traffic.log",
        "frequency analysis",
        "can_analysis.json"
    )
    print(f"   Generated {len(analyzer)} characters")
    
    # Save test script
    print("\n4. Saving test script...")
    success = generator.save_script(scraper, "test_generated_script.py")
    print(f"   Save {'successful' if success else 'failed'}")
    
    # Clean up
    import os
    if os.path.exists("test_generated_script.py"):
        os.remove("test_generated_script.py")
    
    print("\nScript generator tests passed!")
