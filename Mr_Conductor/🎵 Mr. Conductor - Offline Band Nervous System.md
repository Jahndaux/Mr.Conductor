# 🎵 Mr. Conductor - Offline Band Nervous System

<div align="center">
  <img src="web/static/images/0ffd40a4-ca26-4b0e-a439-a0612479d51e.png" alt="Mr. Conductor" width="200"/>
  
  **Making bands sync in perfect harmony**
  
  [![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/user/mr-conductor)
  [![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-red.svg)](https://www.raspberrypi.org/)
  [![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
</div>

## 🎯 What is Mr. Conductor?

Mr. Conductor is a **complete offline band synchronization system** that transforms a Raspberry Pi into the central nervous system for your band. It creates its own WiFi network, broadcasts Ableton Link timing, outputs MIDI clock, and provides a beautiful web interface for control - all without needing internet connectivity.

Perfect for:
- **Live performances** where internet is unreliable
- **Rehearsal spaces** without WiFi
- **Outdoor gigs** and festivals
- **Home studios** wanting centralized sync
- **Collaborative jamming** with multiple devices

## ✨ Key Features

### 🌐 **Offline WiFi Hotspot**
- Creates "JAM-PI" network automatically
- Supports 20+ concurrent connections
- No internet required - completely self-contained
- Built-in DHCP and DNS services

### ⏱️ **Precision Timing**
- Ableton Link broadcast for DAW synchronization
- MIDI clock output to hardware synthesizers
- Sub-millisecond timing accuracy
- Supports BPM range 60-200 with smooth transitions

### 🎛️ **Beautiful Web Interface**
- Responsive design works on phones, tablets, laptops
- Real-time status updates via WebSocket
- Mr. Conductor character theme with animations
- Touch-friendly controls for mobile devices

### 🎹 **Advanced MIDI Routing**
- Intelligent MIDI device detection
- Flexible routing with filters and transforms
- Channel mapping and note transposition
- Program change management

### 🎬 **Scene Management**
- Save and recall complete band setups
- Store BPM, MIDI settings, and notes
- Quick scene switching during performance
- Backup and restore scene libraries

### 🔧 **Hardware Integration**
- Physical GPIO buttons for transport control
- Status LEDs for visual feedback
- USB MIDI device support
- Audio interface compatibility

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 4 (recommended) or Pi 3B+
- MicroSD card (16GB minimum, 32GB recommended)
- USB MIDI devices (optional)
- WiFi-capable devices for connection

### One-Line Installation

```bash
curl -sSL https://raw.githubusercontent.com/user/mr-conductor/main/install.sh | bash
```

### Manual Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/user/mr-conductor.git
   cd mr-conductor
   ```

2. **Run the installer:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. **Reboot your Pi:**
   ```bash
   sudo reboot
   ```

4. **Connect and enjoy:**
   - Connect to WiFi network "JAM-PI" (password: MrConductor2025)
   - Open browser to http://192.168.4.1:5000
   - Start making music!

## 📱 Using Mr. Conductor

### Web Interface

The main control interface is accessible at `http://192.168.4.1:5000` and includes:

- **Transport Controls**: Start/stop playback with large, touch-friendly buttons
- **BPM Control**: Smooth slider with real-time updates (60-200 BPM)
- **Scene Management**: Save and load complete band configurations
- **Device Status**: Real-time monitoring of connected MIDI devices
- **System Health**: CPU, memory, temperature, and timing accuracy
- **Network Info**: Connected devices and system statistics

### Physical Controls (GPIO)

- **Pin 18**: Start/Stop button
- **Pin 19-21**: Scene selection buttons (1-3)
- **Pin 22-23**: BPM up/down buttons
- **Pin 16**: Status LED (system running)
- **Pin 17**: Sync LED (timing active)
- **Pin 24**: Error LED (system issues)
- **Pin 25**: Activity LED (MIDI activity)

### MIDI Integration

Mr. Conductor automatically detects and routes MIDI devices:

1. **USB MIDI Devices**: Plug and play detection
2. **Ableton Link**: Broadcasts to network for DAW sync
3. **MIDI Clock**: Outputs to all connected hardware
4. **Program Changes**: Scene-based instrument switching

## 🔧 Configuration

### Network Settings

Edit `/home/pi/mr-conductor/config/mr-conductor.conf`:

```ini
[network]
ssid = JAM-PI
password = MrConductor2025
ip_address = 192.168.4.1
web_port = 5000
```

### Audio Settings

```ini
[audio]
sample_rate = 48000
buffer_size = 256
default_bpm = 120
```

### MIDI Settings

```ini
[midi]
enable_routing = true
auto_connect = true
```

## 🛠️ Advanced Usage

### Command Line Tools

```bash
# Check system status
sudo mr-conductor-status

# Monitor health
sudo mr-conductor-health

# View logs
journalctl -u mr-conductor -f

# Restart service
sudo systemctl restart mr-conductor
```

### Scene Management

Scenes store complete band configurations:

```python
# Create scene via web interface or API
POST /api/scenes
{
  "name": "Song 1 - Intro",
  "bpm": 120,
  "notes": "Start with piano, add drums at bar 8"
}

# Load scene
POST /api/scenes/Song%201%20-%20Intro/load
```

### MIDI Routing

Advanced MIDI routing with filters and transforms:

```python
# Add channel filter (only channel 1)
filter = MIDIFilter("Channel 1 Only")
filter.channel_filter = [1]

# Add transpose transform (+12 semitones)
transform = MIDITransform("Octave Up")
transform.transpose = 12
```

## 📊 System Monitoring

### Web Dashboard

Real-time monitoring includes:
- CPU usage and temperature
- Memory consumption
- Network activity
- MIDI message throughput
- Timing accuracy (±ms)
- Connected device count

### Health Checks

Automated health monitoring every 5 minutes:
- Service status verification
- Resource usage alerts
- Temperature monitoring
- Disk space checks

### Logging

Comprehensive logging system:
- Application logs: `/var/log/mr-conductor/`
- System logs: `journalctl -u mr-conductor`
- Health logs: `/var/log/mr-conductor/health.log`
- Network logs: `/var/log/mr-conductor-network.log`

## 🔌 Hardware Compatibility

### Tested MIDI Devices

- **Keyboards**: Roland, Yamaha, Korg USB models
- **Controllers**: Akai MPK, Novation Launchpad
- **Interfaces**: M-Audio, Focusrite, PreSonus
- **Synthesizers**: Most USB-MIDI compatible devices

### Audio Interfaces

- USB Audio Class compliant devices
- Built-in Raspberry Pi audio (basic)
- Professional interfaces via USB

### Network Devices

- **Computers**: Windows, macOS, Linux with Ableton Link
- **Mobile**: iOS/Android apps with Link support
- **DAWs**: Logic Pro X, Ableton Live, Reaper, etc.

## 🚨 Troubleshooting

### Common Issues

**WiFi hotspot not appearing:**
```bash
sudo systemctl status hostapd
sudo systemctl restart hostapd
```

**Web interface not accessible:**
```bash
sudo systemctl status mr-conductor
sudo systemctl restart mr-conductor
```

**MIDI devices not detected:**
```bash
lsusb  # Check USB devices
aconnect -l  # Check ALSA MIDI ports
```

**High CPU usage:**
```bash
sudo mr-conductor-health
htop  # Monitor processes
```

### Log Analysis

```bash
# Application errors
journalctl -u mr-conductor --since "1 hour ago"

# Network issues
tail -f /var/log/mr-conductor-network.log

# System health
tail -f /var/log/mr-conductor/health.log
```

### Performance Tuning

For optimal performance:
1. Use Class 10 SD card or better
2. Ensure adequate power supply (3A+ recommended)
3. Keep system temperature below 70°C
4. Limit concurrent MIDI connections to <10

## 🔄 Updates and Maintenance

### Updating Mr. Conductor

```bash
cd /home/pi/mr-conductor
git pull origin main
sudo systemctl restart mr-conductor
```

### Backup Configuration

```bash
# Backup scenes and settings
tar -czf mr-conductor-backup.tar.gz \
    /home/pi/mr-conductor/config/ \
    /home/pi/mr-conductor/data/
```

### System Maintenance

```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Clean logs
sudo journalctl --vacuum-time=7d

# Check disk space
df -h
```

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
git clone https://github.com/user/mr-conductor.git
cd mr-conductor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running Tests

```bash
python -m pytest tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ableton Link** for the synchronization protocol
- **Flask** and **Socket.IO** for the web framework
- **python-rtmidi** for MIDI support
- **Raspberry Pi Foundation** for the amazing hardware
- The **open source music community** for inspiration

## 📞 Support

- **Documentation**: [Wiki](https://github.com/user/mr-conductor/wiki)
- **Issues**: [GitHub Issues](https://github.com/user/mr-conductor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/user/mr-conductor/discussions)
- **Email**: support@mr-conductor.com

---

<div align="center">
  <img src="web/static/images/d42ed271-4975-4d35-8dab-8a9ff3374006.png" alt="Mr. Conductor Mascot" width="100"/>
  
  **Mr. Conductor - Making bands sync in perfect harmony**
  
  *Built with ❤️ for musicians, by musicians*
</div>

