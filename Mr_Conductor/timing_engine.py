#!/usr/bin/env python3
"""
Mr. Conductor - Core Timing Engine
Handles Ableton Link synchronization and master timing reference
"""

import time
import threading
import logging
import json
from dataclasses import dataclass, asdict
from typing import Optional, Callable, Dict, Any
import socket
import struct

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TimingState:
    """Current timing state of the system"""
    bpm: float = 120.0
    is_playing: bool = False
    beat_position: float = 0.0
    quantum: int = 4  # beats per bar
    start_time: float = 0.0
    last_beat_time: float = 0.0
    connected_peers: int = 0
    timing_accuracy: float = 0.0  # milliseconds

class LinkProtocol:
    """Simplified Ableton Link protocol implementation"""
    
    MULTICAST_GROUP = '224.76.78.75'
    PORT = 20808
    MAGIC_BYTES = b'_abl'
    
    def __init__(self):
        self.socket = None
        self.running = False
        
    def start(self):
        """Start Link protocol broadcasting"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            
            # Join multicast group
            mreq = struct.pack("4sl", socket.inet_aton(self.MULTICAST_GROUP), socket.INADDR_ANY)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            
            self.socket.bind(('', self.PORT))
            self.running = True
            logger.info("Link protocol started on %s:%d", self.MULTICAST_GROUP, self.PORT)
            
        except Exception as e:
            logger.error("Failed to start Link protocol: %s", e)
            
    def stop(self):
        """Stop Link protocol"""
        self.running = False
        if self.socket:
            self.socket.close()
            
    def broadcast_timing(self, timing_state: TimingState):
        """Broadcast timing information to Link peers"""
        if not self.running or not self.socket:
            return
            
        try:
            # Create simplified Link packet
            packet_data = {
                'magic': self.MAGIC_BYTES.decode('latin-1'),
                'bpm': timing_state.bpm,
                'beat': timing_state.beat_position,
                'playing': timing_state.is_playing,
                'quantum': timing_state.quantum,
                'timestamp': time.time()
            }
            
            packet = json.dumps(packet_data).encode('utf-8')
            self.socket.sendto(packet, (self.MULTICAST_GROUP, self.PORT))
            
        except Exception as e:
            logger.error("Failed to broadcast timing: %s", e)

class TimingEngine:
    """Core timing engine for Mr. Conductor"""
    
    def __init__(self):
        self.state = TimingState()
        self.link = LinkProtocol()
        self.running = False
        self.thread = None
        self.callbacks: Dict[str, Callable] = {}
        self.last_broadcast_time = 0.0
        self.broadcast_interval = 0.02  # 50Hz broadcast rate
        
    def add_callback(self, name: str, callback: Callable[[TimingState], None]):
        """Add callback for timing updates"""
        self.callbacks[name] = callback
        
    def remove_callback(self, name: str):
        """Remove timing callback"""
        if name in self.callbacks:
            del self.callbacks[name]
            
    def set_bpm(self, bpm: float):
        """Set the master BPM"""
        if 60.0 <= bpm <= 200.0:
            self.state.bpm = bpm
            logger.info("BPM set to %.1f", bpm)
        else:
            logger.warning("BPM %.1f out of range (60-200)", bpm)
            
    def start_playback(self):
        """Start playback and timing"""
        self.state.is_playing = True
        self.state.start_time = time.time()
        self.state.last_beat_time = self.state.start_time
        logger.info("Playback started at BPM %.1f", self.state.bpm)
        
    def stop_playback(self):
        """Stop playback"""
        self.state.is_playing = False
        logger.info("Playback stopped")
        
    def get_state(self) -> TimingState:
        """Get current timing state"""
        return self.state
        
    def get_state_dict(self) -> Dict[str, Any]:
        """Get timing state as dictionary"""
        return asdict(self.state)
        
    def _update_timing(self):
        """Update timing calculations"""
        current_time = time.time()
        
        if self.state.is_playing:
            # Calculate beat position
            elapsed_time = current_time - self.state.start_time
            beats_per_second = self.state.bpm / 60.0
            self.state.beat_position = elapsed_time * beats_per_second
            
            # Update last beat time for accuracy measurement
            beat_interval = 60.0 / self.state.bpm
            expected_beat_time = self.state.start_time + (int(self.state.beat_position) * beat_interval)
            self.state.timing_accuracy = abs(current_time - expected_beat_time) * 1000  # ms
            
        # Broadcast Link data at specified interval
        if current_time - self.last_broadcast_time >= self.broadcast_interval:
            self.link.broadcast_timing(self.state)
            self.last_broadcast_time = current_time
            
        # Call registered callbacks
        for callback in self.callbacks.values():
            try:
                callback(self.state)
            except Exception as e:
                logger.error("Callback error: %s", e)
                
    def _timing_loop(self):
        """Main timing loop"""
        logger.info("Timing engine started")
        
        while self.running:
            try:
                self._update_timing()
                time.sleep(0.001)  # 1ms resolution
                
            except Exception as e:
                logger.error("Timing loop error: %s", e)
                
        logger.info("Timing engine stopped")
        
    def start(self):
        """Start the timing engine"""
        if self.running:
            logger.warning("Timing engine already running")
            return
            
        self.running = True
        self.link.start()
        
        # Start timing thread with high priority
        self.thread = threading.Thread(target=self._timing_loop, daemon=True)
        self.thread.start()
        
        logger.info("Mr. Conductor timing engine started")
        
    def stop(self):
        """Stop the timing engine"""
        if not self.running:
            return
            
        self.running = False
        self.link.stop()
        
        if self.thread:
            self.thread.join(timeout=1.0)
            
        logger.info("Mr. Conductor timing engine stopped")

# Global timing engine instance
timing_engine = TimingEngine()

def get_timing_engine() -> TimingEngine:
    """Get the global timing engine instance"""
    return timing_engine

if __name__ == "__main__":
    # Test the timing engine
    engine = get_timing_engine()
    
    def print_timing(state: TimingState):
        if state.is_playing:
            print(f"Beat: {state.beat_position:.2f}, BPM: {state.bpm}, Accuracy: {state.timing_accuracy:.2f}ms")
    
    engine.add_callback("test", print_timing)
    engine.start()
    
    try:
        print("Starting Mr. Conductor timing engine test...")
        print("Commands: s=start, t=stop, q=quit, b<number>=set BPM")
        
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 's':
                engine.start_playback()
            elif cmd == 't':
                engine.stop_playback()
            elif cmd.startswith('b'):
                try:
                    bpm = float(cmd[1:])
                    engine.set_bpm(bpm)
                except ValueError:
                    print("Invalid BPM format")
                    
    except KeyboardInterrupt:
        pass
    finally:
        engine.stop()
        print("Mr. Conductor timing engine test completed")

