# Mr. Conductor - Project Structure

This document describes the complete project structure and organization of the Mr. Conductor system.

## 📁 Directory Structure

```
mr-conductor/
├── README.md                    # Main project documentation
├── LICENSE                      # MIT License
├── install.sh                   # Main installation script
├── requirements.txt             # Python dependencies
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
│
├── src/                        # Core Python modules
│   ├── __init__.py            # Package initialization
│   ├── timing_engine.py       # Ableton Link timing engine
│   ├── midi_clock.py          # MIDI clock generation
│   ├── midi_router.py         # Advanced MIDI routing
│   ├── gpio_controller.py     # GPIO/hardware control
│   └── mr_conductor.py        # Main system controller
│
├── web/                        # Web application
│   ├── app.py                 # Flask application
│   ├── templates/             # HTML templates
│   │   └── index.html         # Main web interface
│   └── static/                # Static assets
│       ├── css/
│       │   └── style.css      # Main stylesheet
│       ├── js/
│       │   └── app.js         # JavaScript application
│       └── images/            # Mr. Conductor artwork
│           ├── 0ffd40a4-ca26-4b0e-a439-a0612479d51e.png  # Main logo
│           ├── 7575a6bc-ee72-45cd-a52b-baa69a214819.png  # Pattern 1
│           ├── d42ed271-4975-4d35-8dab-8a9ff3374006.png  # Mascot
│           └── 9fc76670-614b-450b-a256-543be874f5c4.png  # Pattern 2
│
├── scripts/                    # Installation and setup scripts
│   ├── setup-wifi-hotspot.sh  # WiFi hotspot configuration
│   └── configure-system.sh    # System optimization
│
├── config/                     # Configuration files
│   └── mr-conductor.conf      # Main configuration
│
├── docs/                       # Documentation
│   ├── API.md                 # API documentation
│   ├── HARDWARE.md            # Hardware setup guide
│   ├── TROUBLESHOOTING.md     # Common issues and solutions
│   └── CONTRIBUTING.md        # Contribution guidelines
│
├── tests/                      # Test suite
│   ├── test_timing_engine.py  # Timing engine tests
│   ├── test_midi_router.py    # MIDI routing tests
│   └── test_web_interface.py  # Web interface tests
│
├── data/                       # Runtime data
│   ├── scenes/                # Saved scenes
│   └── backups/               # Configuration backups
│
└── logs/                       # Log files
    ├── mr-conductor.log       # Application logs
    ├── health.log             # Health monitoring
    └── network.log            # Network activity
```

## 🔧 Core Components

### Timing Engine (`src/timing_engine.py`)
- **Purpose**: Ableton Link synchronization and timing
- **Features**: 
  - Link session management
  - BPM control and synchronization
  - Beat position tracking
  - Peer discovery and connection
- **Dependencies**: Custom Link implementation
- **Key Classes**: `TimingEngine`, `TimingState`

### MIDI Clock Generator (`src/midi_clock.py`)
- **Purpose**: Convert timing to MIDI clock signals
- **Features**:
  - 24 PPQN MIDI clock generation
  - Start/stop/continue messages
  - Multiple device support
  - Active sensing
- **Dependencies**: python-rtmidi
- **Key Classes**: `MIDIClockGenerator`, `MIDIDevice`

### MIDI Router (`src/midi_router.py`)
- **Purpose**: Advanced MIDI message routing and processing
- **Features**:
  - Message filtering by type, channel, velocity
  - Note transposition and velocity curves
  - Channel mapping
  - Real-time processing
- **Dependencies**: python-rtmidi
- **Key Classes**: `MIDIRouter`, `MIDIFilter`, `MIDITransform`

### GPIO Controller (`src/gpio_controller.py`)
- **Purpose**: Physical hardware interface
- **Features**:
  - Button input handling with debouncing
  - LED output control and patterns
  - Interrupt-driven GPIO
  - Hardware abstraction
- **Dependencies**: RPi.GPIO
- **Key Classes**: `GPIOController`, `GPIOPin`

### System Controller (`src/mr_conductor.py`)
- **Purpose**: Main system orchestration
- **Features**:
  - Component integration
  - Scene management
  - Event handling
  - Status monitoring
- **Dependencies**: All core modules
- **Key Classes**: `MrConductor`, `SceneManager`

## 🌐 Web Application

### Flask App (`web/app.py`)
- **Framework**: Flask with SocketIO
- **Features**:
  - RESTful API endpoints
  - Real-time WebSocket communication
  - Static file serving
  - CORS support
- **Routes**:
  - `/` - Main interface
  - `/api/status` - System status
  - `/api/transport/*` - Playback control
  - `/api/bpm` - BPM control
  - `/api/scenes/*` - Scene management

### Frontend (`web/static/`)
- **Technologies**: HTML5, CSS3, JavaScript ES6
- **Features**:
  - Responsive design
  - Real-time updates via WebSocket
  - Touch-friendly controls
  - Mr. Conductor theme
- **Components**:
  - Transport controls
  - BPM slider
  - Scene management
  - Device monitoring
  - System status

## 🔧 Configuration System

### Main Config (`config/mr-conductor.conf`)
```ini
[system]
version = 1.0.0
install_dir = /home/pi/mr-conductor

[network]
ssid = JAM-PI
password = MrConductor2025
ip_address = 192.168.4.1

[audio]
sample_rate = 48000
buffer_size = 256
default_bpm = 120

[midi]
enable_routing = true
auto_connect = true
```

### Environment Variables (`.env`)
- `MR_CONDUCTOR_HOME` - Installation directory
- `MR_CONDUCTOR_CONFIG` - Configuration file path
- `FLASK_ENV` - Flask environment
- `FLASK_DEBUG` - Debug mode

## 📦 Installation System

### Main Installer (`install.sh`)
- **Purpose**: Complete system installation
- **Features**:
  - Dependency installation
  - Python environment setup
  - Service configuration
  - System optimization
- **Steps**:
  1. System requirements check
  2. Package installation
  3. Python virtual environment
  4. Configuration files
  5. Systemd services
  6. Network setup

### WiFi Hotspot Setup (`scripts/setup-wifi-hotspot.sh`)
- **Purpose**: Configure Raspberry Pi as access point
- **Components**:
  - hostapd configuration
  - dnsmasq DHCP server
  - iptables NAT rules
  - Network interface setup

### System Configuration (`scripts/configure-system.sh`)
- **Purpose**: Optimize Pi for audio performance
- **Optimizations**:
  - Audio latency settings
  - GPIO permissions
  - CPU governor
  - Network stack tuning

## 🧪 Testing Framework

### Test Structure
```
tests/
├── test_timing_engine.py      # Timing system tests
├── test_midi_router.py        # MIDI routing tests
├── test_web_interface.py      # Web API tests
├── test_gpio_controller.py    # Hardware tests
└── conftest.py               # Test configuration
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **System Tests**: End-to-end functionality
- **Performance Tests**: Timing accuracy and throughput

## 📊 Monitoring and Logging

### Log Files
- **Application**: `/var/log/mr-conductor/mr-conductor.log`
- **Health**: `/var/log/mr-conductor/health.log`
- **Network**: `/var/log/mr-conductor/network.log`
- **System**: `journalctl -u mr-conductor`

### Health Monitoring
- **CPU Usage**: Threshold alerts at 80%
- **Memory Usage**: Threshold alerts at 80%
- **Temperature**: Threshold alerts at 70°C
- **Service Status**: Automatic restart on failure
- **Disk Space**: Threshold alerts at 90%

## 🔄 Data Flow

### Timing Flow
```
Ableton Link ← → Timing Engine → MIDI Clock → Hardware Devices
                      ↓
                 Web Interface ← → Users
```

### MIDI Flow
```
USB MIDI Input → MIDI Router → Filters/Transforms → MIDI Output
                      ↓
                 Web Interface (Monitoring)
```

### Control Flow
```
Web Interface → Flask API → System Controller → Components
GPIO Buttons → GPIO Controller → System Controller → Components
```

## 🚀 Deployment

### Systemd Service
```ini
[Unit]
Description=Mr. Conductor Offline Band Nervous System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/mr-conductor
ExecStart=/home/pi/mr-conductor/venv/bin/python web/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Network Configuration
- **Access Point**: wlan0 as hotspot
- **IP Range**: 192.168.4.1/24
- **DHCP**: 192.168.4.2 - 192.168.4.20
- **DNS**: Local resolution for .local domains

### Security
- **Firewall**: UFW with minimal open ports
- **Services**: Only essential services enabled
- **Permissions**: Least privilege principle
- **Updates**: Automated security updates

This structure provides a complete, maintainable, and scalable foundation for the Mr. Conductor system.

