"""
CAN Bus Explorer and Data Sniffer
Captures and analyzes all CAN bus traffic for module discovery and exploration
"""

import logging
import re
from typing import List, Dict, Optional
from elm327_adapter import ELM327Adapter
import time

# Configure logging to suppress module name prefixes
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class CANBusFrame:
    """Represents a single CAN bus frame"""
    
    def __init__(self, frame_id: str, data: str, timestamp: float = None):
        """
        Initialize CAN frame
        
        Args:
            frame_id: CAN frame ID (hex string)
            data: Frame data (hex string)
            timestamp: Capture timestamp
        """
        self.frame_id = frame_id
        self.data = data
        self.timestamp = timestamp or time.time()
    
    def __repr__(self):
        return f"Frame(ID: {self.frame_id}, Data: {self.data})"


class EventCapture:
    """Represents a captured vehicle event with associated CAN frames"""
    
    def __init__(self, event_description: str, start_time: float = None):
        """
        Initialize event capture
        
        Args:
            event_description: Description of what user is doing (e.g., "AC on", "Fan speed high")
            start_time: When capture started
        """
        self.description = event_description
        self.start_time = start_time or time.time()
        self.end_time = None
        self.frames: List[CANBusFrame] = []
    
    def add_frame(self, frame: CANBusFrame):
        """Add frame to this event"""
        self.frames.append(frame)
    
    def finish(self):
        """Mark event as finished"""
        self.end_time = time.time()
    
    def get_duration(self) -> float:
        """Get event duration in seconds"""
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def __repr__(self):
        return f"Event('{self.description}', {len(self.frames)} frames, {self.get_duration():.1f}s)"


class CANBusExplorer:
    """Explores and captures CAN bus traffic for module discovery"""
    
    # Common Ford module identifiers on CAN bus
    MODULE_IDS = {
        "0x100": "HVAC Module",
        "0x101": "Instrument Cluster",
        "0x102": "Body Control Module",
        "0x103": "Engine Control Module",
        "0x104": "Transmission Control Module",
        "0x105": "Airbag Module",
        "0x106": "Anti-Lock Brake Module",
        "0x107": "Steering Column Control",
        "0x108": "Door Lock Module",
        "0x109": "Window Control Module",
        "0x10A": "Lighting Control Module",
        "0x10B": "Audio System",
        "0x10C": "Navigation System",
        "0x10D": "Seat Control Module",
        "0x10E": "Climate Control Module",
        "0x200": "Gateway Module",
    }
    
    def __init__(self, adapter: ELM327Adapter):
        """
        Initialize CAN bus explorer
        
        Args:
            adapter: ELM327Adapter instance
        """
        self.adapter = adapter
        self.captured_frames: List[CANBusFrame] = []
        self.module_data: Dict[str, List[Dict]] = {}
        self.is_monitoring = False
        self.captured_events: List[EventCapture] = []  # For event-driven capture
    
    def start_monitoring(self, duration: int = 30, filter_id: Optional[str] = None) -> List[CANBusFrame]:
        """
        Start capturing CAN bus frames
        
        Args:
            duration: Capture duration in seconds
            filter_id: Optional CAN ID to filter (e.g., "0x100")
            
        Returns:
            List of captured frames
        """
        try:
            # Check adapter capability for passive sniffing based on adapter version
            try:
                version_info = self.adapter._send_command("AT I")
            except Exception:
                version_info = None

            if version_info:
                # extract version number like 'ELM327 v1.5' or '1.5'
                m = re.search(r"(\d+\.\d+)", version_info)
                if m:
                    try:
                        ver = float(m.group(1))
                        # ELM327 v1.x devices are typically request/response only
                        if ver <= 1.5:
                            logger.warning("Adapter probably cannot do passive sniffing - use listen-capable hardware")
                            return []
                    except Exception:
                        pass
            logger.info(f"Starting CAN bus monitoring for {duration} seconds...")
            if filter_id:
                logger.info(f"Filtering for CAN ID: {filter_id}")
            
            self.is_monitoring = True
            self.captured_frames = []
            start_time = time.time()
            
            # Set CAN bus to monitor mode
            self.adapter._send_command("AT CAF0")  # Clear filters
            
            if filter_id:
                # Set filter for specific CAN ID
                self.adapter._send_command(f"AT CF {filter_id}")
                self.adapter._send_command("AT CE")  # Enable CAN reception
            else:
                # Listen to all frames
                self.adapter._send_command("AT CAF1")  # Allow all frames
            
            # Start monitoring loop
            while time.time() - start_time < duration and self.is_monitoring:
                frame = self._read_can_frame()
                if frame:
                    self.captured_frames.append(frame)
                    logger.info(f"Captured: {frame}")
                else:
                    time.sleep(0.1)
            
            self.is_monitoring = False
            logger.info(f"Monitoring complete. Captured {len(self.captured_frames)} frames")
            return self.captured_frames
            
        except Exception as e:
            logger.error(f"Error during CAN bus monitoring: {e}")
            self.is_monitoring = False
            return []
    
    def stop_monitoring(self):
        """Stop monitoring CAN bus"""
        self.is_monitoring = False
        logger.info("CAN bus monitoring stopped")
    
    def _read_can_frame(self) -> Optional[CANBusFrame]:
        """
        Read single CAN frame from adapter
        
        Returns:
            CANBusFrame or None
        """
        try:
            # Read raw data from serial
            if self.adapter.serial_conn and self.adapter.serial_conn.in_waiting > 0:
                response = self.adapter._read_response()
                
                if response and len(response) > 0:
                    # Parse CAN frame format: ID DATA
                    parts = response.split()
                    
                    if len(parts) >= 2:
                        frame_id = parts[0]
                        frame_data = " ".join(parts[1:])
                        
                        return CANBusFrame(frame_id, frame_data)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error reading frame: {e}")
            return None
    
    def analyze_captured_frames(self) -> Dict:
        """
        Analyze captured frames for patterns and module identification
        
        Returns:
            Analysis dictionary with statistics and module data
        """
        try:
            logger.info("Analyzing captured frames...")
            
            analysis = {
                'total_frames': len(self.captured_frames),
                'unique_ids': set(),
                'frame_count_by_id': {},
                'data_patterns': {},
                'identified_modules': [],
                'raw_frames': []
            }
            
            for frame in self.captured_frames:
                # Count unique IDs
                analysis['unique_ids'].add(frame.frame_id)
                
                # Count frames per ID
                if frame.frame_id not in analysis['frame_count_by_id']:
                    analysis['frame_count_by_id'][frame.frame_id] = 0
                analysis['frame_count_by_id'][frame.frame_id] += 1
                
                # Identify modules
                module_name = self.MODULE_IDS.get(frame.frame_id, "Unknown Module")
                if frame.frame_id not in [m['id'] for m in analysis['identified_modules']]:
                    analysis['identified_modules'].append({
                        'id': frame.frame_id,
                        'name': module_name,
                        'sample_data': frame.data
                    })
                
                # Store raw frame
                analysis['raw_frames'].append({
                    'id': frame.frame_id,
                    'data': frame.data,
                    'timestamp': frame.timestamp
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing frames: {e}")
            return {}
    
    def get_module_parameters(self, module_id: str) -> Optional[List[Dict]]:
        """
        Extract and list parameters from specific module
        
        Args:
            module_id: CAN module ID (e.g., "0x100")
            
        Returns:
            List of parameter dictionaries
        """
        try:
            logger.info(f"Extracting parameters from module {module_id}...")
            
            module_frames = [f for f in self.captured_frames if f.frame_id == module_id]
            
            if not module_frames:
                logger.warning(f"No frames found for module {module_id}")
                return []
            
            parameters = []
            
            for i, frame in enumerate(module_frames):
                data_bytes = frame.data.replace(" ", "").split()
                
                for byte_idx, byte_val in enumerate(data_bytes):
                    try:
                        value = int(byte_val, 16)
                        
                        parameters.append({
                            'frame_number': i,
                            'byte_position': byte_idx,
                            'hex_value': byte_val,
                            'decimal_value': value,
                            'binary_value': bin(value)[2:].zfill(8),
                            'timestamp': frame.timestamp
                        })
                    except ValueError:
                        continue
            
            logger.info(f"Extracted {len(parameters)} parameter values from {module_id}")
            return parameters
            
        except Exception as e:
            logger.error(f"Error extracting module parameters: {e}")
            return []
    
    def discover_modules(self) -> List[Dict]:
        """
        Discover all active modules on CAN bus
        
        Returns:
            List of discovered module dictionaries
        """
        try:
            logger.info("Discovering modules on CAN bus...")
            
            discovered = []
            
            for frame in self.captured_frames:
                frame_id = frame.frame_id
                
                # Check if module already in list
                existing = next((m for m in discovered if m['id'] == frame_id), None)
                
                if not existing:
                    module_name = self.MODULE_IDS.get(frame_id, "Unknown Module")
                    discovered.append({
                        'id': frame_id,
                        'name': module_name,
                        'first_seen': frame.timestamp,
                        'sample_data': frame.data
                    })
            
            logger.info(f"Discovered {len(discovered)} modules")
            return discovered
            
        except Exception as e:
            logger.error(f"Error discovering modules: {e}")
            return []
    
    def export_frames_to_text(self, filename: str = "can_capture.txt") -> bool:
        """
        Export captured frames to text file
        
        Args:
            filename: Output filename
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Exporting frames to {filename}...")
            
            with open(filename, 'w') as f:
                f.write("CAN Bus Frame Capture\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Total Frames: {len(self.captured_frames)}\n")
                f.write(f"Capture Duration: {self.captured_frames[-1].timestamp - self.captured_frames[0].timestamp:.2f}s\n\n")
                
                f.write("FRAME DATA:\n")
                f.write("-" * 80 + "\n")
                
                for i, frame in enumerate(self.captured_frames, 1):
                    f.write(f"{i}. ID: {frame.frame_id} | Data: {frame.data}\n")
                
                # Add module analysis
                f.write("\n" + "=" * 80 + "\n")
                f.write("MODULE ANALYSIS:\n")
                f.write("-" * 80 + "\n")
                
                modules = self.discover_modules()
                for module in modules:
                    f.write(f"Module: {module['name']}\n")
                    f.write(f"  ID: {module['id']}\n")
                    f.write(f"  First Seen: {module['first_seen']}\n")
                    f.write(f"  Sample Data: {module['sample_data']}\n\n")
            
            logger.info(f"Export complete: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting frames: {e}")
            return False
    
    def print_summary(self):
        """Print captured data summary"""
        logger.info("\n" + "=" * 60)
        logger.info("CAN BUS CAPTURE SUMMARY")
        logger.info("=" * 60)
        
        if not self.captured_frames:
            logger.info("No frames captured")
            return
        
        logger.info(f"Total Frames: {len(self.captured_frames)}")
        
        unique_ids = set(f.frame_id for f in self.captured_frames)
        logger.info(f"Unique Module IDs: {len(unique_ids)}")
        
        logger.info("\nDiscovered Modules:")
        modules = self.discover_modules()
        for module in modules:
            logger.info(f"  {module['id']}: {module['name']}")
        
        logger.info("\nFrame Count by Module:")
        frame_counts = {}
        for frame in self.captured_frames:
            frame_counts[frame.frame_id] = frame_counts.get(frame.frame_id, 0) + 1
        
        for frame_id in sorted(frame_counts.keys()):
            module_name = self.MODULE_IDS.get(frame_id, "Unknown")
            logger.info(f"  {frame_id} ({module_name}): {frame_counts[frame_id]} frames")
        
        logger.info("=" * 60)
    
    def start_event_capture(self) -> bool:
        """
        Start interactive proactive event-driven capture mode
        
        User describes actions and program immediately starts capturing CAN bus events
        No delay between description and capture start
        
        Returns:
            True if capture completed
        """
        try:
            # Check adapter capability for passive sniffing before entering event capture
            try:
                version_info = self.adapter._send_command("AT I")
            except Exception:
                version_info = None

            if version_info:
                m = re.search(r"(\d+\.\d+)", version_info)
                if m:
                    try:
                        ver = float(m.group(1))
                        if ver <= 1.5:
                            logger.warning("Adapter probably cannot do passive sniffing - use listen-capable hardware")
                            return False
                    except Exception:
                        pass
            logger.info("\n" + "=" * 60)
            logger.info("PROACTIVE EVENT CAPTURE - MAP ACTIONS TO CAN MESSAGES")
            logger.info("=" * 60)
            logger.info("Describe what you're about to do, then perform the action.")
            logger.info("Capture starts IMMEDIATELY after description.")
            logger.info("Press Ctrl+C to stop capturing for that event.")
            logger.info("=" * 60)
            
            self.captured_events = []
            
            while True:
                logger.info("\nProactive Capture Options:")
                logger.info("1. Capture new event")
                logger.info("2. View captured events")
                logger.info("3. Export all events to file")
                logger.info("4. Done capturing")
                
                choice = input("\nSelect option (1-4): ").strip()
                
                if choice == "1":
                    event_description = input("\nDescribe the action you're about to perform: ").strip()
                    
                    if not event_description:
                        logger.warning("Event description cannot be empty")
                        continue
                    
                    logger.warning("\n⚠️  CAPTURE STARTING NOW - PERFORM YOUR ACTION!")
                    time.sleep(0.5)  # Brief pause to let user see message
                    
                    if self._capture_single_event(event_description):
                        logger.info(f"✓ Event '{event_description}' captured successfully")
                    else:
                        logger.error("Event capture failed")
                
                elif choice == "2":
                    self._display_captured_events()
                
                elif choice == "3":
                    self._export_events_to_file()
                
                elif choice == "4":
                    logger.info("Exiting event capture mode")
                    break
                
                else:
                    logger.error("Invalid option")
            
            return len(self.captured_events) > 0
            
        except Exception as e:
            logger.error(f"Error during event capture: {e}")
            return False
    
    def _capture_single_event(self, event_description: str) -> bool:
        """
        Capture frames for a single described event
        
        Capture starts IMMEDIATELY without waiting for user confirmation
        
        Args:
            event_description: What the user is about to do
            
        Returns:
            True if successful
        """
        try:
            event = EventCapture(event_description)
            
            # Clear frame buffer
            self.captured_frames = []
            
            # Start monitoring immediately
            logger.info(f"\nCapturing: '{event_description}'")
            logger.info("Press Ctrl+C when done with action...")
            
            try:
                while True:
                    frame = self._read_can_frame()
                    if frame:
                        event.add_frame(frame)
                        logger.debug(f"  Frame: {frame}")
            except KeyboardInterrupt:
                logger.info("\nCapture stopped")
            
            event.finish()
            
            # Store event
            self.captured_events.append(event)
            
            logger.info(f"✓ Captured {len(event.frames)} frames in {event.get_duration():.1f} seconds")
            
            # Show summary
            if event.frames:
                unique_ids = set(f.frame_id for f in event.frames)
                logger.info(f"  Modules involved: {len(unique_ids)}")
                logger.info(f"  Module IDs: {', '.join(sorted(unique_ids))}")
            else:
                logger.warning("  ⚠ No frames captured - check CAN bus connection")
            
            return True
            
        except Exception as e:
            logger.error(f"Error capturing event: {e}")
            return False
    
    def _display_captured_events(self):
        """Display summary of all captured events"""
        if not self.captured_events:
            logger.info("No events captured yet")
            return
        
        logger.info("\n" + "=" * 60)
        logger.info("CAPTURED EVENTS SUMMARY")
        logger.info("=" * 60)
        
        for i, event in enumerate(self.captured_events, 1):
            logger.info(f"\nEvent {i}: {event.description}")
            logger.info(f"  Duration: {event.get_duration():.1f} seconds")
            logger.info(f"  Frames captured: {len(event.frames)}")
            
            if event.frames:
                unique_ids = set(f.frame_id for f in event.frames)
                logger.info(f"  Unique module IDs: {len(unique_ids)}")
                
                # Show frame distribution
                frame_counts = {}
                for frame in event.frames:
                    frame_counts[frame.frame_id] = frame_counts.get(frame.frame_id, 0) + 1
                
                for frame_id in sorted(frame_counts.keys()):
                    module_name = self.MODULE_IDS.get(frame_id, "Unknown")
                    logger.info(f"    {frame_id} ({module_name}): {frame_counts[frame_id]} frames")
        
        logger.info("\n" + "=" * 60)
    
    def _export_events_to_file(self) -> bool:
        """
        Export captured events to detailed file for analysis
        
        Returns:
            True if successful
        """
        try:
            filename = "can_events_capture.txt"
            
            logger.info(f"Exporting events to {filename}...")
            
            with open(filename, 'w') as f:
                f.write("CAN BUS EVENT CAPTURE ANALYSIS\n")
                f.write("=" * 80 + "\n\n")
                
                f.write(f"Total Events Captured: {len(self.captured_events)}\n")
                f.write(f"Total Frames: {sum(len(e.frames) for e in self.captured_events)}\n\n")
                
                for i, event in enumerate(self.captured_events, 1):
                    f.write("=" * 80 + "\n")
                    f.write(f"EVENT {i}: {event.description}\n")
                    f.write("=" * 80 + "\n")
                    f.write(f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(event.start_time))}\n")
                    f.write(f"End Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(event.end_time))}\n")
                    f.write(f"Duration: {event.get_duration():.1f} seconds\n")
                    f.write(f"Frames Captured: {len(event.frames)}\n\n")
                    
                    if event.frames:
                        # Show unique modules touched
                        unique_ids = set(f.frame_id for f in event.frames)
                        f.write(f"Modules Communicating: {len(unique_ids)}\n")
                        for mid in sorted(unique_ids):
                            f.write(f"  - {mid}: {self.MODULE_IDS.get(mid, 'Unknown')}\n")
                        
                        f.write("\nDETAILED FRAME DATA:\n")
                        f.write("-" * 80 + "\n")
                        
                        for j, frame in enumerate(event.frames, 1):
                            elapsed = frame.timestamp - event.start_time
                            f.write(f"{j:4d}. [{elapsed:7.3f}s] ID: {frame.frame_id:6s} | Data: {frame.data}\n")
                    
                    f.write("\n")
            
            logger.info(f"✓ Events exported to: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting events: {e}")
            return False
