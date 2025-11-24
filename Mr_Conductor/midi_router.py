#!/usr/bin/env python3
"""
Mr. Conductor - Advanced MIDI Routing System
Handles complex MIDI routing, filtering, and transformation
"""

import time
import threading
import logging
import json
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import queue
import struct

logger = logging.getLogger(__name__)

class MIDIMessageType(Enum):
    """MIDI message types"""
    NOTE_OFF = 0x80
    NOTE_ON = 0x90
    POLY_AFTERTOUCH = 0xA0
    CONTROL_CHANGE = 0xB0
    PROGRAM_CHANGE = 0xC0
    CHANNEL_AFTERTOUCH = 0xD0
    PITCH_BEND = 0xE0
    SYSTEM_EXCLUSIVE = 0xF0
    TIMING_CLOCK = 0xF8
    START = 0xFA
    CONTINUE = 0xFB
    STOP = 0xFC
    ACTIVE_SENSING = 0xFE
    SYSTEM_RESET = 0xFF

@dataclass
class MIDIMessage:
    """MIDI message structure"""
    timestamp: float
    message_type: MIDIMessageType
    channel: int
    data1: int = 0
    data2: int = 0
    raw_data: bytes = b''
    
    def to_bytes(self) -> bytes:
        """Convert to raw MIDI bytes"""
        if self.raw_data:
            return self.raw_data
            
        if self.message_type.value >= 0xF0:
            # System message (no channel)
            return bytes([self.message_type.value])
        else:
            # Channel message
            status = self.message_type.value | (self.channel & 0x0F)
            if self.message_type in [MIDIMessageType.PROGRAM_CHANGE, MIDIMessageType.CHANNEL_AFTERTOUCH]:
                return bytes([status, self.data1])
            else:
                return bytes([status, self.data1, self.data2])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'type': self.message_type.name,
            'channel': self.channel,
            'data1': self.data1,
            'data2': self.data2
        }

class MIDIFilter:
    """MIDI message filter"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.channel_filter: Optional[List[int]] = None  # None = all channels
        self.message_type_filter: Optional[List[MIDIMessageType]] = None  # None = all types
        self.velocity_range: Optional[Tuple[int, int]] = None  # (min, max) for note velocity
        self.note_range: Optional[Tuple[int, int]] = None  # (min, max) for note numbers
        
    def should_pass(self, message: MIDIMessage) -> bool:
        """Check if message should pass through filter"""
        if not self.enabled:
            return True
            
        # Channel filter
        if self.channel_filter is not None and message.channel not in self.channel_filter:
            return False
            
        # Message type filter
        if self.message_type_filter is not None and message.message_type not in self.message_type_filter:
            return False
            
        # Velocity filter (for note messages)
        if (self.velocity_range is not None and 
            message.message_type in [MIDIMessageType.NOTE_ON, MIDIMessageType.NOTE_OFF]):
            velocity = message.data2
            if not (self.velocity_range[0] <= velocity <= self.velocity_range[1]):
                return False
                
        # Note range filter
        if (self.note_range is not None and 
            message.message_type in [MIDIMessageType.NOTE_ON, MIDIMessageType.NOTE_OFF]):
            note = message.data1
            if not (self.note_range[0] <= note <= self.note_range[1]):
                return False
                
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'channel_filter': self.channel_filter,
            'message_type_filter': [t.name for t in self.message_type_filter] if self.message_type_filter else None,
            'velocity_range': self.velocity_range,
            'note_range': self.note_range
        }

class MIDITransform:
    """MIDI message transformer"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
        self.channel_map: Optional[Dict[int, int]] = None  # Map input channels to output channels
        self.transpose: int = 0  # Semitones to transpose notes
        self.velocity_curve: Optional[List[int]] = None  # 128 velocity values for curve
        
    def transform(self, message: MIDIMessage) -> MIDIMessage:
        """Transform MIDI message"""
        if not self.enabled:
            return message
            
        # Create copy of message
        transformed = MIDIMessage(
            timestamp=message.timestamp,
            message_type=message.message_type,
            channel=message.channel,
            data1=message.data1,
            data2=message.data2
        )
        
        # Channel mapping
        if self.channel_map and message.channel in self.channel_map:
            transformed.channel = self.channel_map[message.channel]
            
        # Transpose notes
        if (self.transpose != 0 and 
            message.message_type in [MIDIMessageType.NOTE_ON, MIDIMessageType.NOTE_OFF]):
            new_note = max(0, min(127, message.data1 + self.transpose))
            transformed.data1 = new_note
            
        # Velocity curve
        if (self.velocity_curve and 
            message.message_type in [MIDIMessageType.NOTE_ON, MIDIMessageType.NOTE_OFF]):
            velocity = message.data2
            if 0 <= velocity < len(self.velocity_curve):
                transformed.data2 = self.velocity_curve[velocity]
                
        return transformed
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'channel_map': self.channel_map,
            'transpose': self.transpose,
            'velocity_curve': self.velocity_curve
        }

@dataclass
class MIDIConnection:
    """MIDI routing connection"""
    input_port: str
    output_port: str
    enabled: bool = True
    filters: List[MIDIFilter] = None
    transforms: List[MIDITransform] = None
    
    def __post_init__(self):
        if self.filters is None:
            self.filters = []
        if self.transforms is None:
            self.transforms = []
            
    def process_message(self, message: MIDIMessage) -> Optional[MIDIMessage]:
        """Process message through filters and transforms"""
        if not self.enabled:
            return None
            
        # Apply filters
        for filter_obj in self.filters:
            if not filter_obj.should_pass(message):
                return None
                
        # Apply transforms
        processed_message = message
        for transform in self.transforms:
            processed_message = transform.transform(processed_message)
            
        return processed_message
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'input_port': self.input_port,
            'output_port': self.output_port,
            'enabled': self.enabled,
            'filters': [f.to_dict() for f in self.filters],
            'transforms': [t.to_dict() for t in self.transforms]
        }

class MIDIPort:
    """MIDI port abstraction"""
    
    def __init__(self, port_id: str, name: str, is_input: bool):
        self.port_id = port_id
        self.name = name
        self.is_input = is_input
        self.is_connected = False
        self.last_activity = 0.0
        self.message_count = 0
        self.error_count = 0
        
    def send_message(self, message: MIDIMessage) -> bool:
        """Send MIDI message"""
        if not self.is_connected or self.is_input:
            return False
            
        try:
            # In a real implementation, this would use python-rtmidi
            # For now, simulate sending
            self.last_activity = time.time()
            self.message_count += 1
            logger.debug(f"MIDI OUT [{self.name}]: {message.to_dict()}")
            return True
        except Exception as e:
            logger.error(f"Failed to send MIDI to {self.name}: {e}")
            self.error_count += 1
            return False
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'port_id': self.port_id,
            'name': self.name,
            'is_input': self.is_input,
            'is_connected': self.is_connected,
            'last_activity': self.last_activity,
            'message_count': self.message_count,
            'error_count': self.error_count
        }

class MIDIRouter:
    """Advanced MIDI routing system"""
    
    def __init__(self):
        self.ports: Dict[str, MIDIPort] = {}
        self.connections: List[MIDIConnection] = []
        self.running = False
        self.thread = None
        self.message_queue = queue.Queue()
        
        # Statistics
        self.total_messages_processed = 0
        self.messages_per_second = 0.0
        self.last_stats_update = time.time()
        
        # Callbacks
        self.message_callbacks: List[Callable[[MIDIMessage, str], None]] = []
        
    def add_port(self, port_id: str, name: str, is_input: bool) -> bool:
        """Add MIDI port"""
        try:
            port = MIDIPort(port_id, name, is_input)
            port.is_connected = True  # Simulate connection
            self.ports[port_id] = port
            logger.info(f"Added MIDI port: {name} ({'input' if is_input else 'output'})")
            return True
        except Exception as e:
            logger.error(f"Failed to add MIDI port {name}: {e}")
            return False
            
    def remove_port(self, port_id: str) -> bool:
        """Remove MIDI port"""
        if port_id in self.ports:
            port = self.ports[port_id]
            
            # Remove connections using this port
            self.connections = [conn for conn in self.connections 
                             if conn.input_port != port_id and conn.output_port != port_id]
            
            del self.ports[port_id]
            logger.info(f"Removed MIDI port: {port.name}")
            return True
        return False
        
    def add_connection(self, input_port: str, output_port: str) -> bool:
        """Add MIDI routing connection"""
        if input_port not in self.ports or output_port not in self.ports:
            logger.error(f"Invalid ports for connection: {input_port} -> {output_port}")
            return False
            
        if not self.ports[input_port].is_input or self.ports[output_port].is_input:
            logger.error(f"Invalid port types for connection: {input_port} -> {output_port}")
            return False
            
        connection = MIDIConnection(input_port, output_port)
        self.connections.append(connection)
        logger.info(f"Added MIDI connection: {input_port} -> {output_port}")
        return True
        
    def remove_connection(self, input_port: str, output_port: str) -> bool:
        """Remove MIDI routing connection"""
        for i, conn in enumerate(self.connections):
            if conn.input_port == input_port and conn.output_port == output_port:
                del self.connections[i]
                logger.info(f"Removed MIDI connection: {input_port} -> {output_port}")
                return True
        return False
        
    def add_filter_to_connection(self, input_port: str, output_port: str, filter_obj: MIDIFilter) -> bool:
        """Add filter to connection"""
        for conn in self.connections:
            if conn.input_port == input_port and conn.output_port == output_port:
                conn.filters.append(filter_obj)
                logger.info(f"Added filter '{filter_obj.name}' to connection {input_port} -> {output_port}")
                return True
        return False
        
    def add_transform_to_connection(self, input_port: str, output_port: str, transform: MIDITransform) -> bool:
        """Add transform to connection"""
        for conn in self.connections:
            if conn.input_port == input_port and conn.output_port == output_port:
                conn.transforms.append(transform)
                logger.info(f"Added transform '{transform.name}' to connection {input_port} -> {output_port}")
                return True
        return False
        
    def route_message(self, message: MIDIMessage, input_port: str):
        """Route MIDI message through connections"""
        self.total_messages_processed += 1
        
        # Find connections from this input port
        for connection in self.connections:
            if connection.input_port == input_port and connection.enabled:
                # Process message through connection
                processed_message = connection.process_message(message)
                
                if processed_message:
                    # Send to output port
                    output_port = self.ports.get(connection.output_port)
                    if output_port:
                        output_port.send_message(processed_message)
                        
                        # Notify callbacks
                        for callback in self.message_callbacks:
                            try:
                                callback(processed_message, connection.output_port)
                            except Exception as e:
                                logger.error(f"Message callback error: {e}")
                                
    def simulate_input_message(self, port_id: str, message: MIDIMessage):
        """Simulate receiving a MIDI message (for testing)"""
        if port_id in self.ports and self.ports[port_id].is_input:
            self.message_queue.put((message, port_id))
            
    def _update_statistics(self):
        """Update performance statistics"""
        current_time = time.time()
        time_diff = current_time - self.last_stats_update
        
        if time_diff >= 1.0:  # Update every second
            self.messages_per_second = self.total_messages_processed / time_diff
            self.total_messages_processed = 0
            self.last_stats_update = current_time
            
    def _routing_loop(self):
        """Main routing loop"""
        logger.info("MIDI router started")
        
        while self.running:
            try:
                # Process queued messages
                try:
                    message, input_port = self.message_queue.get(timeout=0.1)
                    self.route_message(message, input_port)
                except queue.Empty:
                    pass
                    
                # Update statistics
                self._update_statistics()
                
            except Exception as e:
                logger.error(f"MIDI routing error: {e}")
                
        logger.info("MIDI router stopped")
        
    def start(self):
        """Start MIDI router"""
        if self.running:
            logger.warning("MIDI router already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._routing_loop, daemon=True)
        self.thread.start()
        
        logger.info("MIDI router started")
        
    def stop(self):
        """Stop MIDI router"""
        if not self.running:
            return
            
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=1.0)
            
        logger.info("MIDI router stopped")
        
    def get_ports(self) -> List[Dict[str, Any]]:
        """Get all MIDI ports"""
        return [port.to_dict() for port in self.ports.values()]
        
    def get_connections(self) -> List[Dict[str, Any]]:
        """Get all MIDI connections"""
        return [conn.to_dict() for conn in self.connections]
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            'total_ports': len(self.ports),
            'input_ports': len([p for p in self.ports.values() if p.is_input]),
            'output_ports': len([p for p in self.ports.values() if not p.is_input]),
            'total_connections': len(self.connections),
            'active_connections': len([c for c in self.connections if c.enabled]),
            'messages_per_second': self.messages_per_second,
            'total_messages_processed': self.total_messages_processed
        }
        
    def add_message_callback(self, callback: Callable[[MIDIMessage, str], None]):
        """Add callback for processed messages"""
        self.message_callbacks.append(callback)
        
    def remove_message_callback(self, callback: Callable[[MIDIMessage, str], None]):
        """Remove message callback"""
        if callback in self.message_callbacks:
            self.message_callbacks.remove(callback)

# Global MIDI router instance
midi_router = MIDIRouter()

def get_midi_router() -> MIDIRouter:
    """Get the global MIDI router instance"""
    return midi_router

if __name__ == "__main__":
    # Test the MIDI router
    router = get_midi_router()
    
    # Add some test ports
    router.add_port("input_1", "USB Keyboard", True)
    router.add_port("input_2", "USB Controller", True)
    router.add_port("output_1", "USB Synth 1", False)
    router.add_port("output_2", "USB Synth 2", False)
    
    # Add connections
    router.add_connection("input_1", "output_1")
    router.add_connection("input_1", "output_2")
    router.add_connection("input_2", "output_1")
    
    # Add a filter (only pass notes C3-C5)
    note_filter = MIDIFilter("Note Range Filter")
    note_filter.note_range = (60, 84)  # C3 to C5
    router.add_filter_to_connection("input_1", "output_1", note_filter)
    
    # Add a transform (transpose up one octave)
    transpose_transform = MIDITransform("Octave Up")
    transpose_transform.transpose = 12
    router.add_transform_to_connection("input_2", "output_1", transpose_transform)
    
    # Add message callback
    def message_callback(message: MIDIMessage, output_port: str):
        print(f"Routed to {output_port}: {message.to_dict()}")
    
    router.add_message_callback(message_callback)
    
    router.start()
    
    try:
        print("MIDI Router Test")
        print("Commands: n=note on, f=note off, c=control change, s=stats, q=quit")
        
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'n':
                # Simulate note on
                message = MIDIMessage(
                    timestamp=time.time(),
                    message_type=MIDIMessageType.NOTE_ON,
                    channel=0,
                    data1=60,  # Middle C
                    data2=100  # Velocity
                )
                router.simulate_input_message("input_1", message)
            elif cmd == 'f':
                # Simulate note off
                message = MIDIMessage(
                    timestamp=time.time(),
                    message_type=MIDIMessageType.NOTE_OFF,
                    channel=0,
                    data1=60,  # Middle C
                    data2=0    # Velocity
                )
                router.simulate_input_message("input_1", message)
            elif cmd == 'c':
                # Simulate control change
                message = MIDIMessage(
                    timestamp=time.time(),
                    message_type=MIDIMessageType.CONTROL_CHANGE,
                    channel=0,
                    data1=7,   # Volume
                    data2=100  # Value
                )
                router.simulate_input_message("input_2", message)
            elif cmd == 's':
                stats = router.get_statistics()
                print("MIDI Router Statistics:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                    
    except KeyboardInterrupt:
        pass
    finally:
        router.stop()
        print("MIDI router test completed")

