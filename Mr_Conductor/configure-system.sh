#!/bin/bash
# Mr. Conductor - System Configuration Script
# Configures Raspberry Pi system settings for optimal performance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Configure system settings for audio performance
configure_audio() {
    log "Configuring audio settings..."
    
    # Add user to audio group
    usermod -a -G audio pi
    
    # Configure ALSA settings
    cat > /home/pi/.asoundrc << 'EOF'
# Mr. Conductor ALSA Configuration
pcm.!default {
    type hw
    card 0
    device 0
}

ctl.!default {
    type hw
    card 0
}
EOF

    chown pi:pi /home/pi/.asoundrc
    
    # Set audio buffer sizes for low latency
    echo "@audio - rtprio 95" >> /etc/security/limits.conf
    echo "@audio - memlock unlimited" >> /etc/security/limits.conf
    echo "pi - rtprio 95" >> /etc/security/limits.conf
    echo "pi - memlock unlimited" >> /etc/security/limits.conf
}

# Configure GPIO permissions
configure_gpio() {
    log "Configuring GPIO permissions..."
    
    # Add user to gpio group
    usermod -a -G gpio pi
    
    # Create udev rule for GPIO access
    cat > /etc/udev/rules.d/99-gpio.rules << 'EOF'
# Mr. Conductor GPIO Rules
SUBSYSTEM=="gpio", KERNEL=="gpiochip*", ACTION=="add", PROGRAM="/bin/sh -c 'chown root:gpio /sys/class/gpio/export /sys/class/gpio/unexport ; chmod 220 /sys/class/gpio/export /sys/class/gpio/unexport'"
SUBSYSTEM=="gpio", KERNEL=="gpio*", ACTION=="add", PROGRAM="/bin/sh -c 'chown root:gpio /sys%p/active_low /sys%p/direction /sys%p/edge /sys%p/value ; chmod 660 /sys%p/active_low /sys%p/direction /sys%p/edge /sys%p/value'"
EOF
}

# Configure system performance
configure_performance() {
    log "Configuring system performance..."
    
    # CPU governor for consistent performance
    echo 'GOVERNOR="performance"' > /etc/default/cpufrequtils
    
    # Disable unnecessary services
    systemctl disable bluetooth
    systemctl disable hciuart
    systemctl disable triggerhappy
    
    # Configure kernel parameters
    cat >> /boot/config.txt << 'EOF'

# Mr. Conductor Performance Settings
# GPU memory split (minimal for headless)
gpu_mem=16

# Disable audio (we'll use USB audio)
dtparam=audio=off

# Enable SPI and I2C for potential expansions
dtparam=spi=on
dtparam=i2c=on

# USB power settings
max_usb_current=1

# Overclock settings (conservative)
arm_freq=1000
core_freq=500
sdram_freq=500
over_voltage=2
EOF

    # Configure cmdline.txt for better performance
    sed -i 's/$/ isolcpus=3 rcu_nocbs=3 irqaffinity=0,1,2/' /boot/cmdline.txt
}

# Configure networking optimizations
configure_network_optimization() {
    log "Configuring network optimizations..."
    
    # TCP/IP optimizations
    cat >> /etc/sysctl.conf << 'EOF'

# Mr. Conductor Network Optimizations
# Increase network buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 65536 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Reduce network latency
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq

# WiFi power management off
net.ipv4.conf.wlan0.send_redirects = 0
EOF
}

# Configure logging
configure_logging() {
    log "Configuring logging..."
    
    # Create log directory
    mkdir -p /var/log/mr-conductor
    chown pi:pi /var/log/mr-conductor
    
    # Configure logrotate
    cat > /etc/logrotate.d/mr-conductor << 'EOF'
/var/log/mr-conductor/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
    postrotate
        systemctl reload mr-conductor 2>/dev/null || true
    endscript
}
EOF

    # Configure rsyslog for Mr. Conductor
    cat > /etc/rsyslog.d/30-mr-conductor.conf << 'EOF'
# Mr. Conductor logging
if $programname == 'mr-conductor' then /var/log/mr-conductor/mr-conductor.log
& stop
EOF

    systemctl restart rsyslog
}

# Configure firewall
configure_firewall() {
    log "Configuring firewall..."
    
    # Install and configure ufw
    apt install -y ufw
    
    # Default policies
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow Mr. Conductor web interface
    ufw allow 5000/tcp
    
    # Allow mDNS for service discovery
    ufw allow 5353/udp
    
    # Allow DHCP
    ufw allow 67/udp
    ufw allow 68/udp
    
    # Enable firewall
    ufw --force enable
}

# Configure time synchronization
configure_time() {
    log "Configuring time synchronization..."
    
    # Install chrony for better time sync
    apt install -y chrony
    
    # Configure chrony
    cat > /etc/chrony/chrony.conf << 'EOF'
# Mr. Conductor Time Configuration
# Use multiple NTP servers
pool 0.pool.ntp.org iburst
pool 1.pool.ntp.org iburst
pool 2.pool.ntp.org iburst

# Allow clients on local network to sync
allow 192.168.4.0/24

# Serve time even if not synchronized
local stratum 10

# Log settings
logdir /var/log/chrony
log measurements statistics tracking
EOF

    systemctl enable chrony
}

# Configure USB settings for MIDI
configure_usb_midi() {
    log "Configuring USB MIDI settings..."
    
    # Create udev rules for MIDI devices
    cat > /etc/udev/rules.d/99-midi.rules << 'EOF'
# Mr. Conductor MIDI Device Rules
# USB MIDI devices
SUBSYSTEM=="usb", ATTR{bInterfaceClass}=="01", ATTR{bInterfaceSubClass}=="03", GROUP="audio", MODE="0664"

# ALSA MIDI devices
KERNEL=="midiC[0-9]*D[0-9]*", GROUP="audio", MODE="0664"

# Set permissions for MIDI devices
ACTION=="add", SUBSYSTEM=="sound", KERNEL=="midiC*", GROUP="audio", MODE="0664"
EOF

    # Configure ALSA MIDI
    cat > /etc/modprobe.d/alsa-midi.conf << 'EOF'
# Mr. Conductor ALSA MIDI Configuration
# Load snd-seq module for MIDI sequencing
options snd-seq ports=4
EOF
}

# Create system health check script
create_health_check() {
    log "Creating system health check script..."
    
    cat > /usr/local/bin/mr-conductor-health << 'EOF'
#!/bin/bash
# Mr. Conductor System Health Check

HEALTH_LOG="/var/log/mr-conductor/health.log"
ALERT_THRESHOLD_CPU=80
ALERT_THRESHOLD_MEMORY=80
ALERT_THRESHOLD_TEMP=70

log_health() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$HEALTH_LOG"
}

check_cpu() {
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    CPU_USAGE=${CPU_USAGE%.*}  # Remove decimal
    
    if [[ $CPU_USAGE -gt $ALERT_THRESHOLD_CPU ]]; then
        log_health "ALERT: High CPU usage: ${CPU_USAGE}%"
        return 1
    fi
    
    log_health "INFO: CPU usage: ${CPU_USAGE}%"
    return 0
}

check_memory() {
    MEMORY_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    
    if [[ $MEMORY_USAGE -gt $ALERT_THRESHOLD_MEMORY ]]; then
        log_health "ALERT: High memory usage: ${MEMORY_USAGE}%"
        return 1
    fi
    
    log_health "INFO: Memory usage: ${MEMORY_USAGE}%"
    return 0
}

check_temperature() {
    TEMP=$(vcgencmd measure_temp 2>/dev/null | cut -d= -f2 | cut -d"'" -f1)
    TEMP=${TEMP%.*}  # Remove decimal
    
    if [[ $TEMP -gt $ALERT_THRESHOLD_TEMP ]]; then
        log_health "ALERT: High temperature: ${TEMP}°C"
        return 1
    fi
    
    log_health "INFO: Temperature: ${TEMP}°C"
    return 0
}

check_disk() {
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | cut -d'%' -f1)
    
    if [[ $DISK_USAGE -gt 90 ]]; then
        log_health "ALERT: High disk usage: ${DISK_USAGE}%"
        return 1
    fi
    
    log_health "INFO: Disk usage: ${DISK_USAGE}%"
    return 0
}

check_services() {
    SERVICES=("mr-conductor" "hostapd" "dnsmasq" "chrony")
    FAILED_SERVICES=()
    
    for service in "${SERVICES[@]}"; do
        if ! systemctl is-active --quiet "$service"; then
            FAILED_SERVICES+=("$service")
        fi
    done
    
    if [[ ${#FAILED_SERVICES[@]} -gt 0 ]]; then
        log_health "ALERT: Failed services: ${FAILED_SERVICES[*]}"
        return 1
    fi
    
    log_health "INFO: All services running"
    return 0
}

# Run all checks
ISSUES=0

check_cpu || ((ISSUES++))
check_memory || ((ISSUES++))
check_temperature || ((ISSUES++))
check_disk || ((ISSUES++))
check_services || ((ISSUES++))

if [[ $ISSUES -eq 0 ]]; then
    log_health "INFO: System health check passed"
    exit 0
else
    log_health "WARNING: System health check found $ISSUES issues"
    exit 1
fi
EOF

    chmod +x /usr/local/bin/mr-conductor-health
    
    # Create health check service
    cat > /etc/systemd/system/mr-conductor-health.service << 'EOF'
[Unit]
Description=Mr. Conductor Health Check
After=mr-conductor.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/mr-conductor-health
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOF

    # Create health check timer
    cat > /etc/systemd/system/mr-conductor-health.timer << 'EOF'
[Unit]
Description=Run Mr. Conductor Health Check every 5 minutes
Requires=mr-conductor-health.service

[Timer]
OnBootSec=5min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
EOF

    systemctl daemon-reload
    systemctl enable mr-conductor-health.timer
}

# Main configuration function
main() {
    log "Starting Mr. Conductor System Configuration"
    
    check_root
    
    info "This will optimize your Raspberry Pi for Mr. Conductor"
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Configuration cancelled"
        exit 0
    fi
    
    configure_audio
    configure_gpio
    configure_performance
    configure_network_optimization
    configure_logging
    configure_firewall
    configure_time
    configure_usb_midi
    create_health_check
    
    log "System configuration completed successfully!"
    echo
    info "System optimizations applied:"
    info "  - Audio configuration for low latency"
    info "  - GPIO permissions configured"
    info "  - Performance optimizations enabled"
    info "  - Network stack optimized"
    info "  - Logging configured"
    info "  - Firewall configured"
    info "  - Time synchronization enabled"
    info "  - USB MIDI support configured"
    info "  - Health monitoring enabled"
    echo
    warning "Please reboot to apply all changes:"
    warning "  sudo reboot"
}

# Run main function
main "$@"

