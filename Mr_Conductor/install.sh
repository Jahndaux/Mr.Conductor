#!/bin/bash
# Mr. Conductor - Main Installation Script
# Complete installation and setup of the Mr. Conductor system

set -e

# Version information
VERSION="1.0.0"
INSTALL_DIR="/home/pi/mr-conductor"
REPO_URL="https://github.com/user/mr-conductor.git"  # Placeholder URL

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ASCII Art Banner
show_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
    __  __         ____                _            _             
   |  \/  |_ __   / ___|___  _ __   __| |_   _  ___| |_ ___  _ __ 
   | |\/| | '__| | |   / _ \| '_ \ / _` | | | |/ __| __/ _ \| '__|
   | |  | | |_   | |__| (_) | | | | (_| | |_| | (__| || (_) | |   
   |_|  |_|_(_)   \____\___/|_| |_|\__,_|\__,_|\___|\__\___/|_|   
                                                                  
              Offline Band Nervous System v1.0.0
                    Making bands sync in harmony
EOF
    echo -e "${NC}"
}

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

step() {
    echo -e "${PURPLE}[STEP] $1${NC}"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should NOT be run as root"
        error "Please run as the 'pi' user and it will use sudo when needed"
        exit 1
    fi
}

# Check if running on Raspberry Pi
check_platform() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        warning "This doesn't appear to be a Raspberry Pi"
        warning "Installation may not work correctly on other platforms"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
}

# Check system requirements
check_requirements() {
    step "Checking system requirements..."
    
    # Check OS version
    if ! grep -q "Raspberry Pi OS" /etc/os-release 2>/dev/null; then
        warning "This system doesn't appear to be running Raspberry Pi OS"
    fi
    
    # Check available space
    AVAILABLE_SPACE=$(df /home | tail -1 | awk '{print $4}')
    REQUIRED_SPACE=1048576  # 1GB in KB
    
    if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
        error "Insufficient disk space. Need at least 1GB free in /home"
        exit 1
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com >/dev/null 2>&1; then
        warning "No internet connectivity detected"
        warning "Some packages may not install correctly"
    fi
    
    info "System requirements check passed"
}

# Install system dependencies
install_dependencies() {
    step "Installing system dependencies..."
    
    sudo apt update
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        build-essential \
        libasound2-dev \
        libjack-dev \
        portaudio19-dev \
        libffi-dev \
        libssl-dev \
        hostapd \
        dnsmasq \
        iptables-persistent \
        bridge-utils \
        chrony \
        ufw \
        vim \
        htop \
        screen \
        curl \
        wget \
        unzip
        
    info "System dependencies installed"
}

# Create installation directory
create_directories() {
    step "Creating installation directories..."
    
    # Remove existing installation if present
    if [[ -d "$INSTALL_DIR" ]]; then
        warning "Existing Mr. Conductor installation found"
        read -p "Remove existing installation? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
        else
            error "Cannot proceed with existing installation"
            exit 1
        fi
    fi
    
    # Create directories
    mkdir -p "$INSTALL_DIR"/{src,web,config,scripts,logs,data}
    
    info "Installation directories created"
}

# Copy source files
install_source_files() {
    step "Installing Mr. Conductor source files..."
    
    # In a real deployment, this would clone from git or extract from package
    # For now, we'll copy from the current build directory
    
    if [[ -d "/home/ubuntu/mr-conductor" ]]; then
        # Copy from build directory (development scenario)
        cp -r /home/ubuntu/mr-conductor/* "$INSTALL_DIR/"
    else
        # Create basic structure with placeholder files
        info "Creating basic project structure..."
        
        # Create main application files
        cat > "$INSTALL_DIR/src/__init__.py" << 'EOF'
# Mr. Conductor Package
__version__ = "1.0.0"
EOF

        # Create basic web app
        mkdir -p "$INSTALL_DIR/web/templates" "$INSTALL_DIR/web/static"
        
        # Create requirements file
        cat > "$INSTALL_DIR/requirements.txt" << 'EOF'
flask==2.3.3
flask-socketio==5.3.6
python-socketio==5.9.0
python-engineio==4.7.1
eventlet==0.33.3
python-rtmidi==1.4.9
numpy==1.24.3
scipy==1.10.1
requests==2.31.0
psutil==5.9.5
RPi.GPIO==0.7.1
EOF
    fi
    
    # Set ownership
    sudo chown -R pi:pi "$INSTALL_DIR"
    
    info "Source files installed"
}

# Setup Python virtual environment
setup_python_environment() {
    step "Setting up Python virtual environment..."
    
    cd "$INSTALL_DIR"
    
    # Create virtual environment
    python3 -m venv venv
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install requirements
    if [[ -f requirements.txt ]]; then
        pip install -r requirements.txt
    else
        # Install basic requirements
        pip install flask flask-socketio python-rtmidi numpy scipy requests psutil
        
        # Try to install RPi.GPIO (may fail on non-Pi systems)
        pip install RPi.GPIO || warning "RPi.GPIO installation failed (normal on non-Pi systems)"
    fi
    
    deactivate
    
    info "Python environment setup complete"
}

# Configure system settings
configure_system() {
    step "Configuring system settings..."
    
    # Run system configuration script
    if [[ -f "$INSTALL_DIR/scripts/configure-system.sh" ]]; then
        sudo bash "$INSTALL_DIR/scripts/configure-system.sh"
    else
        warning "System configuration script not found, skipping system optimization"
    fi
    
    info "System configuration complete"
}

# Setup WiFi hotspot
setup_wifi_hotspot() {
    step "Setting up WiFi hotspot..."
    
    read -p "Setup WiFi hotspot? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        if [[ -f "$INSTALL_DIR/scripts/setup-wifi-hotspot.sh" ]]; then
            sudo bash "$INSTALL_DIR/scripts/setup-wifi-hotspot.sh"
        else
            warning "WiFi hotspot script not found, skipping hotspot setup"
        fi
    else
        info "WiFi hotspot setup skipped"
    fi
}

# Create configuration files
create_config_files() {
    step "Creating configuration files..."
    
    # Create main configuration file
    cat > "$INSTALL_DIR/config/mr-conductor.conf" << EOF
# Mr. Conductor Configuration File
[system]
version = $VERSION
install_date = $(date '+%Y-%m-%d %H:%M:%S')
install_dir = $INSTALL_DIR

[network]
ssid = JAM-PI
password = MrConductor2025
ip_address = 192.168.4.1
web_port = 5000

[audio]
sample_rate = 48000
buffer_size = 256
default_bpm = 120

[midi]
enable_routing = true
auto_connect = true

[logging]
log_level = INFO
log_dir = $INSTALL_DIR/logs
max_log_size = 10MB
backup_count = 5
EOF

    # Create environment file
    cat > "$INSTALL_DIR/.env" << EOF
# Mr. Conductor Environment Variables
MR_CONDUCTOR_HOME=$INSTALL_DIR
MR_CONDUCTOR_CONFIG=$INSTALL_DIR/config/mr-conductor.conf
MR_CONDUCTOR_LOGS=$INSTALL_DIR/logs
FLASK_ENV=production
FLASK_DEBUG=false
EOF

    info "Configuration files created"
}

# Install systemd services
install_services() {
    step "Installing systemd services..."
    
    # Create main service file
    sudo tee /etc/systemd/system/mr-conductor.service > /dev/null << EOF
[Unit]
Description=Mr. Conductor Offline Band Nervous System
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
EnvironmentFile=$INSTALL_DIR/.env
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/web/app.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$INSTALL_DIR

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mr-conductor

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable mr-conductor
    
    info "Systemd services installed"
}

# Create desktop shortcuts (if GUI available)
create_shortcuts() {
    if [[ -n "$DISPLAY" ]] || [[ -d "/home/pi/Desktop" ]]; then
        step "Creating desktop shortcuts..."
        
        # Create desktop shortcut
        cat > /home/pi/Desktop/mr-conductor.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Mr. Conductor
Comment=Offline Band Nervous System
Exec=chromium-browser --app=http://192.168.4.1:5000
Icon=$INSTALL_DIR/web/static/images/0ffd40a4-ca26-4b0e-a439-a0612479d51e.png
Terminal=false
Categories=AudioVideo;Audio;
EOF

        chmod +x /home/pi/Desktop/mr-conductor.desktop
        
        info "Desktop shortcuts created"
    fi
}

# Run post-installation tests
run_tests() {
    step "Running post-installation tests..."
    
    # Test Python imports
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    python3 -c "
import sys
import flask
import socketio
print('✓ Flask and SocketIO imported successfully')

try:
    import rtmidi
    print('✓ python-rtmidi imported successfully')
except ImportError:
    print('⚠ python-rtmidi not available (may need system packages)')

try:
    import RPi.GPIO
    print('✓ RPi.GPIO imported successfully')
except ImportError:
    print('⚠ RPi.GPIO not available (normal on non-Pi systems)')

print('✓ Python environment test passed')
"
    
    deactivate
    
    # Test configuration files
    if [[ -f "$INSTALL_DIR/config/mr-conductor.conf" ]]; then
        info "✓ Configuration files present"
    else
        warning "⚠ Configuration files missing"
    fi
    
    # Test service file
    if systemctl list-unit-files | grep -q mr-conductor.service; then
        info "✓ Systemd service installed"
    else
        warning "⚠ Systemd service not found"
    fi
    
    info "Post-installation tests completed"
}

# Show completion message
show_completion() {
    echo
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}║  🎵 Mr. Conductor Installation Complete! 🎵                  ║${NC}"
    echo -e "${GREEN}║                                                              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo
    
    info "Installation Summary:"
    info "  Version: $VERSION"
    info "  Install Directory: $INSTALL_DIR"
    info "  Web Interface: http://192.168.4.1:5000"
    info "  Configuration: $INSTALL_DIR/config/mr-conductor.conf"
    info "  Logs: $INSTALL_DIR/logs/"
    echo
    
    info "Useful Commands:"
    info "  Start service: sudo systemctl start mr-conductor"
    info "  Stop service: sudo systemctl stop mr-conductor"
    info "  Check status: sudo systemctl status mr-conductor"
    info "  View logs: journalctl -u mr-conductor -f"
    info "  System status: sudo mr-conductor-status"
    echo
    
    info "Next Steps:"
    info "  1. Reboot your Raspberry Pi: sudo reboot"
    info "  2. Connect to WiFi network 'JAM-PI' (password: MrConductor2025)"
    info "  3. Open web browser to http://192.168.4.1:5000"
    info "  4. Start jamming with your band!"
    echo
    
    warning "Important Notes:"
    warning "  - The system will start automatically after reboot"
    warning "  - WiFi hotspot may take 1-2 minutes to become available"
    warning "  - Connect MIDI devices before starting playback"
    echo
    
    read -p "Reboot now? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        info "Rebooting system..."
        sudo reboot
    else
        info "Please reboot manually when ready: sudo reboot"
    fi
}

# Main installation function
main() {
    show_banner
    
    log "Starting Mr. Conductor Installation v$VERSION"
    
    check_root
    check_platform
    check_requirements
    
    info "This will install Mr. Conductor on your Raspberry Pi"
    info "Installation directory: $INSTALL_DIR"
    read -p "Continue with installation? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        info "Installation cancelled"
        exit 0
    fi
    
    # Installation steps
    install_dependencies
    create_directories
    install_source_files
    setup_python_environment
    create_config_files
    install_services
    configure_system
    setup_wifi_hotspot
    create_shortcuts
    run_tests
    show_completion
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Mr. Conductor Installation Script v$VERSION"
        echo
        echo "Usage: $0 [options]"
        echo
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --version, -v  Show version information"
        echo "  --uninstall    Uninstall Mr. Conductor"
        echo
        exit 0
        ;;
    --version|-v)
        echo "Mr. Conductor Installation Script v$VERSION"
        exit 0
        ;;
    --uninstall)
        echo "Uninstalling Mr. Conductor..."
        sudo systemctl stop mr-conductor 2>/dev/null || true
        sudo systemctl disable mr-conductor 2>/dev/null || true
        sudo rm -f /etc/systemd/system/mr-conductor.service
        sudo systemctl daemon-reload
        rm -rf "$INSTALL_DIR"
        rm -f /home/pi/Desktop/mr-conductor.desktop
        echo "Mr. Conductor uninstalled successfully"
        exit 0
        ;;
    "")
        # No arguments, run main installation
        main
        ;;
    *)
        error "Unknown argument: $1"
        error "Use --help for usage information"
        exit 1
        ;;
esac

