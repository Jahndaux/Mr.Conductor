#!/usr/bin/env python3
"""
Mr. Conductor - GPIO Controller
Handles physical buttons, LEDs, and other GPIO-based controls
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import RPi.GPIO, fall back to simulation if not available
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
    logger.info("RPi.GPIO available - using real GPIO")
except ImportError:
    GPIO_AVAILABLE = False
    logger.warning("RPi.GPIO not available - using GPIO simulation")
    
    # Create mock GPIO module for development/testing
    class MockGPIO:
        BCM = "BCM"
        BOARD = "BOARD"
        IN = "IN"
        OUT = "OUT"
        PUD_UP = "PUD_UP"
        PUD_DOWN = "PUD_DOWN"
        RISING = "RISING"
        FALLING = "FALLING"
        BOTH = "BOTH"
        HIGH = 1
        LOW = 0
        
        @staticmethod
        def setmode(mode): pass
        
        @staticmethod
        def setup(pin, mode, pull_up_down=None): pass
        
        @staticmethod
        def input(pin): return 0
        
        @staticmethod
        def output(pin, state): pass
        
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None): pass
        
        @staticmethod
        def remove_event_detect(pin): pass
        
        @staticmethod
        def cleanup(): pass
    
    GPIO = MockGPIO()

class PinMode(Enum):
    """GPIO pin modes"""
    INPUT = "input"
    OUTPUT = "output"
    INPUT_PULLUP = "input_pullup"
    INPUT_PULLDOWN = "input_pulldown"

class EdgeType(Enum):
    """GPIO edge detection types"""
    RISING = "rising"
    FALLING = "falling"
    BOTH = "both"

@dataclass
class GPIOPin:
    """GPIO pin configuration"""
    pin_number: int
    name: str
    mode: PinMode
    initial_state: bool = False
    debounce_time: float = 0.05  # 50ms default debounce
    last_change_time: float = 0.0
    current_state: bool = False
    callback: Optional[Callable[[int, bool], None]] = None

class GPIOController:
    """GPIO controller for Mr. Conductor"""
    
    def __init__(self):
        self.pins: Dict[int, GPIOPin] = {}
        self.running = False
        self.monitor_thread = None
        
        # Default pin assignments (can be customized)
        self.default_pins = {
            'start_stop_button': 18,
            'scene_1_button': 19,
            'scene_2_button': 20,
            'scene_3_button': 21,
            'bpm_up_button': 22,
            'bpm_down_button': 23,
            'status_led': 16,
            'sync_led': 17,
            'error_led': 24,
            'activity_led': 25
        }
        
        # LED patterns
        self.led_patterns: Dict[str, Dict[str, Any]] = {}
        self.pattern_threads: Dict[str, threading.Thread] = {}
        
        # Button callbacks
        self.button_callbacks: Dict[str, List[Callable[[str], None]]] = {}
        
        if GPIO_AVAILABLE:
            GPIO.setmode(GPIO.BCM)
            
    def setup_default_pins(self):
        """Setup default pin configuration"""
        # Setup buttons (inputs with pull-up resistors)
        button_pins = ['start_stop_button', 'scene_1_button', 'scene_2_button', 
                      'scene_3_button', 'bpm_up_button', 'bpm_down_button']
        
        for button_name in button_pins:
            pin_num = self.default_pins[button_name]
            self.setup_pin(pin_num, button_name, PinMode.INPUT_PULLUP)
            self.add_button_callback(button_name, self._default_button_handler)
            
        # Setup LEDs (outputs)
        led_pins = ['status_led', 'sync_led', 'error_led', 'activity_led']
        
        for led_name in led_pins:
            pin_num = self.default_pins[led_name]
            self.setup_pin(pin_num, led_name, PinMode.OUTPUT)
            
        logger.info("Default GPIO pins configured")
        
    def setup_pin(self, pin_number: int, name: str, mode: PinMode, 
                  initial_state: bool = False, debounce_time: float = 0.05) -> bool:
        """Setup GPIO pin"""
        try:
            pin = GPIOPin(
                pin_number=pin_number,
                name=name,
                mode=mode,
                initial_state=initial_state,
                debounce_time=debounce_time,
                current_state=initial_state
            )
            
            if GPIO_AVAILABLE:
                if mode == PinMode.INPUT:
                    GPIO.setup(pin_number, GPIO.IN)
                elif mode == PinMode.INPUT_PULLUP:
                    GPIO.setup(pin_number, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                elif mode == PinMode.INPUT_PULLDOWN:
                    GPIO.setup(pin_number, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
                elif mode == PinMode.OUTPUT:
                    GPIO.setup(pin_number, GPIO.OUT)
                    GPIO.output(pin_number, GPIO.HIGH if initial_state else GPIO.LOW)
                    
                # Setup interrupt for input pins
                if mode in [PinMode.INPUT, PinMode.INPUT_PULLUP, PinMode.INPUT_PULLDOWN]:
                    GPIO.add_event_detect(pin_number, GPIO.BOTH, 
                                        callback=lambda pin: self._pin_interrupt(pin),
                                        bouncetime=int(debounce_time * 1000))
            
            self.pins[pin_number] = pin
            logger.info(f"Setup GPIO pin {pin_number} ({name}) as {mode.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup GPIO pin {pin_number}: {e}")
            return False
            
    def _pin_interrupt(self, pin_number: int):
        """Handle GPIO pin interrupt"""
        if pin_number not in self.pins:
            return
            
        pin = self.pins[pin_number]
        current_time = time.time()
        
        # Debounce check
        if current_time - pin.last_change_time < pin.debounce_time:
            return
            
        # Read current state
        if GPIO_AVAILABLE:
            new_state = GPIO.input(pin_number) == GPIO.HIGH
        else:
            new_state = not pin.current_state  # Simulate toggle for testing
            
        # Check if state actually changed
        if new_state != pin.current_state:
            pin.current_state = new_state
            pin.last_change_time = current_time
            
            # Call pin callback
            if pin.callback:
                try:
                    pin.callback(pin_number, new_state)
                except Exception as e:
                    logger.error(f"Pin callback error for pin {pin_number}: {e}")
                    
            # Handle button press (falling edge for pull-up buttons)
            if pin.mode == PinMode.INPUT_PULLUP and not new_state:
                self._handle_button_press(pin.name)
                
            logger.debug(f"GPIO pin {pin_number} ({pin.name}) changed to {new_state}")
            
    def _handle_button_press(self, button_name: str):
        """Handle button press event"""
        logger.info(f"Button pressed: {button_name}")
        
        # Call registered callbacks
        if button_name in self.button_callbacks:
            for callback in self.button_callbacks[button_name]:
                try:
                    callback(button_name)
                except Exception as e:
                    logger.error(f"Button callback error for {button_name}: {e}")
                    
    def _default_button_handler(self, button_name: str):
        """Default button handler"""
        logger.info(f"Default handler for button: {button_name}")
        
        # Flash activity LED
        self.flash_led('activity_led', 0.1)
        
    def set_pin_state(self, pin_number: int, state: bool) -> bool:
        """Set output pin state"""
        if pin_number not in self.pins:
            logger.error(f"Pin {pin_number} not configured")
            return False
            
        pin = self.pins[pin_number]
        if pin.mode != PinMode.OUTPUT:
            logger.error(f"Pin {pin_number} is not configured as output")
            return False
            
        try:
            if GPIO_AVAILABLE:
                GPIO.output(pin_number, GPIO.HIGH if state else GPIO.LOW)
            pin.current_state = state
            logger.debug(f"Set GPIO pin {pin_number} ({pin.name}) to {state}")
            return True
        except Exception as e:
            logger.error(f"Failed to set pin {pin_number} state: {e}")
            return False
            
    def get_pin_state(self, pin_number: int) -> Optional[bool]:
        """Get pin state"""
        if pin_number not in self.pins:
            return None
            
        pin = self.pins[pin_number]
        
        if pin.mode == PinMode.OUTPUT:
            return pin.current_state
        else:
            try:
                if GPIO_AVAILABLE:
                    return GPIO.input(pin_number) == GPIO.HIGH
                else:
                    return pin.current_state
            except Exception as e:
                logger.error(f"Failed to read pin {pin_number} state: {e}")
                return None
                
    def set_led(self, led_name: str, state: bool) -> bool:
        """Set LED state by name"""
        if led_name in self.default_pins:
            pin_number = self.default_pins[led_name]
            return self.set_pin_state(pin_number, state)
        return False
        
    def flash_led(self, led_name: str, duration: float = 0.5, count: int = 1):
        """Flash LED"""
        def flash_thread():
            for _ in range(count):
                self.set_led(led_name, True)
                time.sleep(duration / 2)
                self.set_led(led_name, False)
                time.sleep(duration / 2)
                
        thread = threading.Thread(target=flash_thread, daemon=True)
        thread.start()
        
    def start_led_pattern(self, led_name: str, pattern_name: str, 
                         on_time: float = 0.5, off_time: float = 0.5, repeat: bool = True):
        """Start LED pattern"""
        # Stop existing pattern
        self.stop_led_pattern(led_name)
        
        def pattern_thread():
            while pattern_name in self.led_patterns and self.led_patterns[pattern_name].get('running', False):
                self.set_led(led_name, True)
                time.sleep(on_time)
                self.set_led(led_name, False)
                time.sleep(off_time)
                
                if not repeat:
                    break
                    
        self.led_patterns[pattern_name] = {'running': True}
        thread = threading.Thread(target=pattern_thread, daemon=True)
        thread.start()
        self.pattern_threads[pattern_name] = thread
        
    def stop_led_pattern(self, pattern_name: str):
        """Stop LED pattern"""
        if pattern_name in self.led_patterns:
            self.led_patterns[pattern_name]['running'] = False
            del self.led_patterns[pattern_name]
            
        if pattern_name in self.pattern_threads:
            del self.pattern_threads[pattern_name]
            
    def add_button_callback(self, button_name: str, callback: Callable[[str], None]):
        """Add button callback"""
        if button_name not in self.button_callbacks:
            self.button_callbacks[button_name] = []
        self.button_callbacks[button_name].append(callback)
        
    def remove_button_callback(self, button_name: str, callback: Callable[[str], None]):
        """Remove button callback"""
        if button_name in self.button_callbacks and callback in self.button_callbacks[button_name]:
            self.button_callbacks[button_name].remove(callback)
            
    def simulate_button_press(self, button_name: str):
        """Simulate button press (for testing)"""
        if not GPIO_AVAILABLE:
            self._handle_button_press(button_name)
            
    def get_pin_status(self) -> Dict[str, Any]:
        """Get status of all pins"""
        status = {}
        for pin_number, pin in self.pins.items():
            status[pin.name] = {
                'pin_number': pin_number,
                'mode': pin.mode.value,
                'current_state': pin.current_state,
                'last_change_time': pin.last_change_time
            }
        return status
        
    def start(self):
        """Start GPIO controller"""
        if self.running:
            logger.warning("GPIO controller already running")
            return
            
        self.running = True
        self.setup_default_pins()
        
        # Set initial LED states
        self.set_led('status_led', True)  # System running
        self.set_led('sync_led', False)   # Not syncing yet
        self.set_led('error_led', False)  # No errors
        self.set_led('activity_led', False)
        
        logger.info("GPIO controller started")
        
    def stop(self):
        """Stop GPIO controller"""
        if not self.running:
            return
            
        self.running = False
        
        # Stop all LED patterns
        for pattern_name in list(self.led_patterns.keys()):
            self.stop_led_pattern(pattern_name)
            
        # Turn off all LEDs
        for led_name in ['status_led', 'sync_led', 'error_led', 'activity_led']:
            self.set_led(led_name, False)
            
        # Cleanup GPIO
        if GPIO_AVAILABLE:
            try:
                GPIO.cleanup()
            except Exception as e:
                logger.error(f"GPIO cleanup error: {e}")
                
        logger.info("GPIO controller stopped")

# Global GPIO controller instance
gpio_controller = GPIOController()

def get_gpio_controller() -> GPIOController:
    """Get the global GPIO controller instance"""
    return gpio_controller

if __name__ == "__main__":
    # Test the GPIO controller
    controller = get_gpio_controller()
    
    # Add custom button handlers
    def start_stop_handler(button_name: str):
        print(f"Start/Stop button pressed!")
        controller.flash_led('sync_led', 0.2, 3)
        
    def scene_handler(button_name: str):
        print(f"Scene button pressed: {button_name}")
        controller.flash_led('activity_led', 0.1, 2)
        
    controller.add_button_callback('start_stop_button', start_stop_handler)
    controller.add_button_callback('scene_1_button', scene_handler)
    controller.add_button_callback('scene_2_button', scene_handler)
    controller.add_button_callback('scene_3_button', scene_handler)
    
    controller.start()
    
    try:
        print("GPIO Controller Test")
        print("Commands: s=start/stop, 1/2/3=scene buttons, l=LED test, p=pattern test, q=quit")
        
        while True:
            cmd = input("> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 's':
                controller.simulate_button_press('start_stop_button')
            elif cmd in ['1', '2', '3']:
                controller.simulate_button_press(f'scene_{cmd}_button')
            elif cmd == 'l':
                print("Testing LEDs...")
                for led in ['status_led', 'sync_led', 'error_led', 'activity_led']:
                    controller.flash_led(led, 0.3)
                    time.sleep(0.5)
            elif cmd == 'p':
                print("Starting LED patterns...")
                controller.start_led_pattern('sync_led', 'sync_pattern', 0.2, 0.2)
                controller.start_led_pattern('activity_led', 'activity_pattern', 0.1, 0.9)
                time.sleep(5)
                controller.stop_led_pattern('sync_pattern')
                controller.stop_led_pattern('activity_pattern')
                print("Patterns stopped")
                
    except KeyboardInterrupt:
        pass
    finally:
        controller.stop()
        print("GPIO controller test completed")

