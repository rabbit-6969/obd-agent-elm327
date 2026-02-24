"""
Event-Driven CAN Capture

Captures CAN traffic during user-described actions to identify relevant CAN IDs.
"""

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import defaultdict


logger = logging.getLogger(__name__)


class EventCapture:
    """
    Event-driven CAN traffic capture
    
    Captures CAN traffic before, during, and after user actions
    to identify which CAN IDs are relevant to specific events.
    """
    
    def __init__(self, port: str, capture_script: str = "toolkit/vehicle_communication/can_explore.py"):
        """
        Initialize event capture
        
        Args:
            port: COM port for ELM327
            capture_script: Path to CAN capture script
        """
        self.port = port
        self.capture_script = Path(capture_script)
        
        if not self.capture_script.exists():
            logger.warning(f"Capture script not found: {capture_script}")
    
    def capture_event(self, event_description: str, 
                     duration: int = 10,
                     baseline_duration: int = 5) -> Dict[str, Any]:
        """
        Capture CAN traffic during an event
        
        Args:
            event_description: User description of action (e.g., "press brake pedal")
            duration: Duration to capture during event (seconds)
            baseline_duration: Duration to capture baseline before event (seconds)
            
        Returns:
            Capture results with identified CAN IDs
        """
        logger.info(f"Starting event capture: {event_description}")
        
        # Capture baseline
        print(f"\n📊 Capturing baseline CAN traffic for {baseline_duration} seconds...")
        print("   (Vehicle should be idle)")
        baseline_ids = self._capture_can_traffic(baseline_duration)
        
        # Prompt user to perform action
        print(f"\n🎬 Now perform the action: {event_description}")
        print(f"   Capturing for {duration} seconds...")
        input("   Press ENTER when ready to start capture...")
        
        # Capture during event
        event_ids = self._capture_can_traffic(duration)
        
        # Analyze differences
        results = self._analyze_capture(baseline_ids, event_ids, event_description)
        
        return results
    
    def _capture_can_traffic(self, duration: int) -> Dict[str, int]:
        """
        Capture CAN traffic for specified duration
        
        Args:
            duration: Capture duration in seconds
            
        Returns:
            Dictionary of CAN IDs and frame counts
        """
        can_ids = defaultdict(int)
        
        try:
            # Run CAN capture script
            cmd = [
                "python",
                str(self.capture_script),
                "--port", self.port,
                "--duration", str(duration)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=duration + 10)
            
            if result.returncode == 0:
                # Parse JSON output
                output = json.loads(result.stdout)
                
                if output.get("success"):
                    modules = output.get("modules", [])
                    for module in modules:
                        can_id = module.get("id")
                        frame_count = module.get("frames", 0)
                        can_ids[can_id] = frame_count
                    
                    logger.info(f"Captured {len(can_ids)} unique CAN IDs")
                else:
                    logger.error(f"Capture failed: {output.get('error')}")
            else:
                logger.error(f"Capture script failed: {result.stderr}")
        
        except subprocess.TimeoutExpired:
            logger.error("Capture timed out")
        except Exception as e:
            logger.error(f"Capture error: {e}")
        
        return dict(can_ids)
    
    def _analyze_capture(self, baseline: Dict[str, int], 
                        event: Dict[str, int],
                        event_description: str) -> Dict[str, Any]:
        """
        Analyze capture to identify relevant CAN IDs
        
        Args:
            baseline: Baseline CAN IDs and counts
            event: Event CAN IDs and counts
            event_description: Description of event
            
        Returns:
            Analysis results
        """
        # Find new CAN IDs (appeared during event)
        new_ids = set(event.keys()) - set(baseline.keys())
        
        # Find increased activity (>50% increase in frame count)
        increased_ids = []
        for can_id in event.keys():
            if can_id in baseline:
                baseline_count = baseline[can_id]
                event_count = event[can_id]
                
                if event_count > baseline_count * 1.5:
                    increase_pct = ((event_count - baseline_count) / baseline_count) * 100
                    increased_ids.append({
                        "can_id": can_id,
                        "baseline_frames": baseline_count,
                        "event_frames": event_count,
                        "increase_percent": round(increase_pct, 1)
                    })
        
        # Sort by increase percentage
        increased_ids.sort(key=lambda x: x["increase_percent"], reverse=True)
        
        results = {
            "event_description": event_description,
            "timestamp": datetime.now().isoformat(),
            "baseline_can_ids": len(baseline),
            "event_can_ids": len(event),
            "new_can_ids": list(new_ids),
            "increased_activity": increased_ids,
            "summary": self._generate_summary(new_ids, increased_ids, event_description)
        }
        
        logger.info(f"Analysis complete: {len(new_ids)} new IDs, {len(increased_ids)} increased activity")
        
        return results
    
    def _generate_summary(self, new_ids: set, increased_ids: List[Dict],
                         event_description: str) -> str:
        """
        Generate human-readable summary
        
        Args:
            new_ids: New CAN IDs
            increased_ids: IDs with increased activity
            event_description: Event description
            
        Returns:
            Summary text
        """
        summary_parts = []
        
        summary_parts.append(f"Event: {event_description}")
        
        if new_ids:
            summary_parts.append(f"\nNew CAN IDs appeared: {', '.join(new_ids)}")
        
        if increased_ids:
            summary_parts.append(f"\nCAN IDs with increased activity:")
            for item in increased_ids[:5]:  # Top 5
                summary_parts.append(
                    f"  - {item['can_id']}: +{item['increase_percent']}% "
                    f"({item['baseline_frames']} → {item['event_frames']} frames)"
                )
        
        if not new_ids and not increased_ids:
            summary_parts.append("\nNo significant CAN activity changes detected.")
        
        return "\n".join(summary_parts)
    
    def save_capture(self, results: Dict[str, Any], output_path: str):
        """
        Save capture results to file
        
        Args:
            results: Capture results
            output_path: Output file path
        """
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Saved capture results to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save capture: {e}")


if __name__ == '__main__':
    # Test event capture
    print("Testing Event Capture...")
    print("\nNote: This test requires a connected ELM327 adapter")
    print("      and will prompt for user actions.")
    
    # Create event capture
    port = input("\nEnter COM port (e.g., COM3): ").strip()
    
    if port:
        capture = EventCapture(port)
        
        # Capture brake pedal event
        print("\n1. Testing brake pedal event capture...")
        results = capture.capture_event("press brake pedal", duration=5, baseline_duration=3)
        
        # Display results
        print("\n" + "="*60)
        print("CAPTURE RESULTS")
        print("="*60)
        print(results["summary"])
        print("="*60)
        
        # Save results
        capture.save_capture(results, "logs/event_capture_test.json")
        print("\nResults saved to logs/event_capture_test.json")
    else:
        print("No port specified, skipping test")
    
    print("\nEvent capture test complete!")
