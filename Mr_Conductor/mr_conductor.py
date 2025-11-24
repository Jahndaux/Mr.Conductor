#!/usr/bin/env python3
"""
Mr. Conductor - System Controller
Integrates timing engine, MIDI clock, and provides unified control interface
"""

import time
import logging
import json
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime

from timing_engine import get_timing_engine, TimingState
from midi_clock import get_midi_clock

logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """Overall system status"""
    uptime: float = 0.0
    is_playing: bool = False
    bpm: float = 120.0
    beat_position: float = 0.0
    timing_accuracy: float = 0.0
    connected_devices: int = 0
    midi_devices: int = 0
    network_clients: int = 0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    temperature: float = 0.0

@dataclass
class Scene:
    """Musical scene/preset configuration"""
    name: str
    bpm: float
    midi_program_changes: Dict[str, int]  # device_id -> program number
    notes: str = ""
    created_at: float = 0.0

class SceneManager:
    """Manages musical scenes and presets"""
    
    def __init__(self):
        self.scenes: Dict[str, Scene] = {}
        self.current_scene: Optional[str] = None
        
    def create_scene(self, name: str, bpm: float, midi_programs: Dict[str, int] = None, notes: str = "") -> bool:
        """Create a new scene"""
        try:
            scene = Scene(
                name=name,
                bpm=bpm,
                midi_program_changes=midi_programs or {},
                notes=notes,
                created_at=time.time()
            )
            self.scenes[name] = scene
            logger.info(f"Created scene: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create scene {name}: {e}")
            return False
            
    def load_scene(self, name: str) -> bool:
        """Load and activate a scene"""
        if name not in self.scenes:
            logger.warning(f"Scene not found: {name}")
            return False
            
        try:
            scene = self.scenes[name]
            self.current_scene = name
            
            # Apply scene settings
            timing_engine = get_timing_engine()
            timing_engine.set_bpm(scene.bpm)
            
            midi_clock = get_midi_clock()
            midi_clock.set_bpm(scene.bpm)
            
            # TODO: Send MIDI program changes
            
            logger.info(f"Loaded scene: {name} (BPM: {scene.bpm})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load scene {name}: {e}")
            return False
            
    def delete_scene(self, name: str) -> bool:
        """Delete a scene"""
        if name in self.scenes:
            del self.scenes[name]
            if self.current_scene == name:
                self.current_scene = None
            logger.info(f"Deleted scene: {name}")
            return True
        return False
        
    def get_scenes(self) -> List[Dict[str, Any]]:
        """Get list of all scenes"""
        return [asdict(scene) for scene in self.scenes.values()]
        
    def get_current_scene(self) -> Optional[str]:
        """Get current active scene name"""
        return self.current_scene

class MrConductor:
    """Main Mr. Conductor system controller"""
    
    def __init__(self):
        self.timing_engine = get_timing_engine()
        self.midi_clock = get_midi_clock()
        self.scene_manager = SceneManager()
        
        self.start_time = time.time()
        self.status = SystemStatus()
        self.running = False
        self.status_thread = None
        
        # Event callbacks
        self.event_callbacks: Dict[str, List[Callable]] = {
            'play_start': [],
            'play_stop': [],
            'bpm_change': [],
            'scene_change': []
        }
        
        # Setup timing engine callback
        self.timing_engine.add_callback("system", self._on_timing_update)
        
    def add_event_callback(self, event: str, callback: Callable):
        """Add callback for system events"""
        if event in self.event_callbacks:
            self.event_callbacks[event].append(callback)
            
    def remove_event_callback(self, event: str, callback: Callable):
        """Remove event callback"""
        if event in self.event_callbacks and callback in self.event_callbacks[event]:
            self.event_callbacks[event].remove(callback)
            
    def _fire_event(self, event: str, *args, **kwargs):
        """Fire event to all registered callbacks"""
        for callback in self.event_callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Event callback error ({event}): {e}")
                
    def _on_timing_update(self, timing_state: TimingState):
        """Handle timing engine updates"""
        # Update system status
        self.status.is_playing = timing_state.is_playing
        self.status.bpm = timing_state.bpm
        self.status.beat_position = timing_state.beat_position
        self.status.timing_accuracy = timing_state.timing_accuracy
        self.status.connected_devices = timing_state.connected_peers
        
    def _update_system_status(self):
        """Update system status information"""
        try:
            # Update uptime
            self.status.uptime = time.time() - self.start_time
            
            # Update MIDI device count
            midi_status = self.midi_clock.get_status()
            self.status.midi_devices = midi_status['connected_devices']
            
            # TODO: Update CPU, memory, temperature from system
            # For now, simulate some values
            self.status.cpu_usage = 25.0  # Placeholder
            self.status.memory_usage = 512.0  # MB, placeholder
            self.status.temperature = 45.0  # Celsius, placeholder
            
        except Exception as e:
            logger.error(f"Status update error: {e}")
            
    def _status_loop(self):
        """Background thread for status updates"""
        while self.running:
            try:
                self._update_system_status()
                time.sleep(1.0)  # Update every second
            except Exception as e:
                logger.error(f"Status loop error: {e}")
                
    def start(self):
        """Start Mr. Conductor system"""
        if self.running:
            logger.warning("Mr. Conductor already running")
            return
            
        logger.info("Starting Mr. Conductor system...")
        
        # Start components
        self.timing_engine.start()
        self.midi_clock.start()
        
        # Start status monitoring
        self.running = True
        self.status_thread = threading.Thread(target=self._status_loop, daemon=True)
        self.status_thread.start()
        
        logger.info("Mr. Conductor system started successfully")
        
    def stop(self):
        """Stop Mr. Conductor system"""
        if not self.running:
            return
            
        logger.info("Stopping Mr. Conductor system...")
        
        # Stop playback first
        self.stop_playback()
        
        # Stop components
        self.running = False
        self.midi_clock.stop()
        self.timing_engine.stop()
        
        if self.status_thread:
            self.status_thread.join(timeout=1.0)
            
        logger.info("Mr. Conductor system stopped")
        
    def start_playback(self):
        """Start playback"""
        if not self.status.is_playing:
            self.timing_engine.start_playback()
            self.midi_clock.start_playback()
            self._fire_event('play_start')
            logger.info("Playback started")
            
    def stop_playback(self):
        """Stop playback"""
        if self.status.is_playing:
            self.timing_engine.stop_playback()
            self.midi_clock.stop_playback()
            self._fire_event('play_stop')
            logger.info("Playback stopped")
            
    def set_bpm(self, bpm: float):
        """Set system BPM"""
        old_bpm = self.status.bpm
        self.timing_engine.set_bpm(bpm)
        self.midi_clock.set_bpm(bpm)
        self._fire_event('bpm_change', old_bpm, bpm)
        logger.info(f"BPM changed from {old_bpm} to {bpm}")
        
    def load_scene(self, scene_name: str) -> bool:
        """Load a musical scene"""
        if self.scene_manager.load_scene(scene_name):
            self._fire_event('scene_change', scene_name)
            return True
        return False
        
    def create_scene(self, name: str, bpm: float, notes: str = "") -> bool:
        """Create a new scene with current settings"""
        return self.scene_manager.create_scene(name, bpm, {}, notes)
        
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return asdict(self.status)
        
    def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed system status"""
        return {
            'system': asdict(self.status),
            'timing': self.timing_engine.get_state_dict(),
            'midi': self.midi_clock.get_status(),
            'scenes': self.scene_manager.get_scenes(),
            'current_scene': self.scene_manager.get_current_scene(),
            'timestamp': time.time()
        }

# Global Mr. Conductor instance
mr_conductor = MrConductor()

def get_mr_conductor() -> MrConductor:
    """Get the global Mr. Conductor instance"""
    return mr_conductor

if __name__ == "__main__":
    # Test Mr. Conductor system
    conductor = get_mr_conductor()
    
    # Add some test scenes
    conductor.create_scene("Song 1", 120.0, "Intro and verse")
    conductor.create_scene("Song 2", 140.0, "Fast chorus")
    conductor.create_scene("Song 3", 90.0, "Slow ballad")
    
    conductor.start()
    
    try:
        print("Mr. Conductor System Test")
        print("Commands: s=start, t=stop, q=quit, b<number>=set BPM")
        print("          l<name>=load scene, c<name>=create scene, status=show status")
        
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 's':
                conductor.start_playback()
            elif cmd == 't':
                conductor.stop_playback()
            elif cmd == 'status':
                status = conductor.get_detailed_status()
                print(json.dumps(status, indent=2))
            elif cmd.startswith('b'):
                try:
                    bpm = float(cmd[1:])
                    conductor.set_bpm(bpm)
                except ValueError:
                    print("Invalid BPM format")
            elif cmd.startswith('l'):
                scene_name = cmd[1:].strip()
                if conductor.load_scene(scene_name):
                    print(f"Loaded scene: {scene_name}")
                else:
                    print(f"Scene not found: {scene_name}")
            elif cmd.startswith('c'):
                scene_name = cmd[1:].strip()
                if conductor.create_scene(scene_name, conductor.status.bpm):
                    print(f"Created scene: {scene_name}")
                else:
                    print(f"Failed to create scene: {scene_name}")
                    
    except KeyboardInterrupt:
        pass
    finally:
        conductor.stop()
        print("Mr. Conductor system test completed")

