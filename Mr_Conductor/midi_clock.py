#!/usr/bin/env python3
"""
Mr. Conductor - MIDI Clock Generator
Converts Ableton Link timing to MIDI clock signals
"""

import time
import threading
import logging
from typing import List, Optional, Dict, Any
import json

# MIDI constants
MIDI_CLOCK = 0xF8
MIDI_START = 0xFA
MIDI_CONTINUE = 0xFB
MIDI_STOP = 0xFC
MIDI_ACTIVE_SENSING = 0xFE

# MIDI clock timing: 24 pulses per quarter note
PULSES_PER_QUARTER_NOTE = 24

logger = logging.getLogger(__name__)

class MIDIDevice:
    """Represents a MIDI output device"""
    
    def __init__(self, name: str, port_id: str):
        self.name = name
        self.port_id = port_id
        self.is_connected = False
        self.last_message_time = 0.0
        
    def send_message(self, message: bytes) -> bool:
        """Send MIDI message to device"""
        try:
            # In a real implementation, this would use python-rtmidi or similar
            # For now, we'll simulate the MIDI output
            self.last_message_time = time.time()
            logger.debug(f"MIDI -> {self.name}: {message.hex()}")
            return True
        except Exception as e:
            logger.error(f"Failed to send MIDI to {self.name}: {e}")
            return False
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'port_id': self.port_id,
            'is_connected': self.is_connected,
            'last_message_time': self.last_message_time
        }

class MIDIClockGenerator:
    """Generates MIDI clock signals from timing engine"""
    
    def __init__(self):
        self.devices: List[MIDIDevice] = []
        self.running = False
        self.thread = None
        self.last_clock_time = 0.0
        self.clock_pulse_count = 0
        self.is_playing = False
        self.current_bpm = 120.0
        
        # Timing calculations
        self.clock_interval = 0.0  # Time between clock pulses
        self._update_clock_interval()
        
    def _update_clock_interval(self):
        """Update clock interval based on current BPM"""
        # 24 pulses per quarter note, 4 quarter notes per minute at given BPM
        pulses_per_minute = PULSES_PER_QUARTER_NOTE * self.current_bpm
        pulses_per_second = pulses_per_minute / 60.0
        self.clock_interval = 1.0 / pulses_per_second
        
    def add_device(self, name: str, port_id: str) -> bool:
        """Add MIDI output device"""
        try:
            device = MIDIDevice(name, port_id)
            device.is_connected = True  # Simulate connection
            self.devices.append(device)
            logger.info(f"Added MIDI device: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to add MIDI device {name}: {e}")
            return False
            
    def remove_device(self, port_id: str) -> bool:
        """Remove MIDI output device"""
        for i, device in enumerate(self.devices):
            if device.port_id == port_id:
                del self.devices[i]
                logger.info(f"Removed MIDI device: {device.name}")
                return True
        return False
        
    def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of MIDI devices"""
        return [device.to_dict() for device in self.devices]
        
    def send_to_all_devices(self, message: bytes):
        """Send MIDI message to all connected devices"""
        for device in self.devices:
            if device.is_connected:
                device.send_message(message)
                
    def start_playback(self):
        """Start MIDI playback"""
        if not self.is_playing:
            self.is_playing = True
            self.clock_pulse_count = 0
            self.last_clock_time = time.time()
            
            # Send MIDI START message
            self.send_to_all_devices(bytes([MIDI_START]))
            logger.info("MIDI playback started")
            
    def stop_playback(self):
        """Stop MIDI playback"""
        if self.is_playing:
            self.is_playing = False
            
            # Send MIDI STOP message
            self.send_to_all_devices(bytes([MIDI_STOP]))
            logger.info("MIDI playback stopped")
            
    def set_bpm(self, bpm: float):
        """Set BPM and update clock interval"""
        self.current_bpm = bpm
        self._update_clock_interval()
        logger.debug(f"MIDI clock BPM set to {bpm}, interval: {self.clock_interval:.4f}s")
        
    def _send_clock_pulse(self):
        """Send a single MIDI clock pulse"""
        if self.is_playing:
            self.send_to_all_devices(bytes([MIDI_CLOCK]))
            self.clock_pulse_count += 1
            
    def _clock_loop(self):
        """Main MIDI clock generation loop"""
        logger.info("MIDI clock generator started")
        
        while self.running:
            try:
                current_time = time.time()
                
                if self.is_playing:
                    # Check if it's time for next clock pulse
                    if current_time - self.last_clock_time >= self.clock_interval:
                        self._send_clock_pulse()
                        self.last_clock_time = current_time
                        
                # Send active sensing every 300ms when not playing
                elif current_time - self.last_clock_time >= 0.3:
                    self.send_to_all_devices(bytes([MIDI_ACTIVE_SENSING]))
                    self.last_clock_time = current_time
                    
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                logger.error(f"MIDI clock loop error: {e}")
                
        logger.info("MIDI clock generator stopped")
        
    def start(self):
        """Start the MIDI clock generator"""
        if self.running:
            logger.warning("MIDI clock generator already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._clock_loop, daemon=True)
        self.thread.start()
        
        logger.info("MIDI clock generator started")
        
    def stop(self):
        """Stop the MIDI clock generator"""
        if not self.running:
            return
            
        self.running = False
        self.stop_playback()  # Ensure playback is stopped
        
        if self.thread:
            self.thread.join(timeout=1.0)
            
        logger.info("MIDI clock generator stopped")
        
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'is_running': self.running,
            'is_playing': self.is_playing,
            'bpm': self.current_bpm,
            'clock_interval': self.clock_interval,
            'pulse_count': self.clock_pulse_count,
            'device_count': len(self.devices),
            'connected_devices': len([d for d in self.devices if d.is_connected])
        }

# Global MIDI clock generator instance
midi_clock = MIDIClockGenerator()

def get_midi_clock() -> MIDIClockGenerator:
    """Get the global MIDI clock generator instance"""
    return midi_clock

if __name__ == "__main__":
    # Test the MIDI clock generator
    clock = get_midi_clock()
    
    # Add some test devices
    clock.add_device("Test Synth 1", "test_port_1")
    clock.add_device("Test Synth 2", "test_port_2")
    
    clock.start()
    
    try:
        print("Starting Mr. Conductor MIDI clock test...")
        print("Commands: s=start, t=stop, q=quit, b<number>=set BPM, d=show devices")
        
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 's':
                clock.start_playback()
            elif cmd == 't':
                clock.stop_playback()
            elif cmd == 'd':
                devices = clock.get_devices()
                print(f"MIDI Devices ({len(devices)}):")
                for device in devices:
                    status = "Connected" if device['is_connected'] else "Disconnected"
                    print(f"  - {device['name']}: {status}")
            elif cmd.startswith('b'):
                try:
                    bpm = float(cmd[1:])
                    clock.set_bpm(bpm)
                    print(f"BPM set to {bpm}")
                except ValueError:
                    print("Invalid BPM format")
                    
    except KeyboardInterrupt:
        pass
    finally:
        clock.stop()
        print("Mr. Conductor MIDI clock test completed")

