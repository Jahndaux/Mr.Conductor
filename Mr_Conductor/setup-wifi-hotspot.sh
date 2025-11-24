#!/bin/bash
# Mr. Conductor - WiFi Hotspot Setup Script
# Sets up Raspberry Pi as WiFi access point for offline band networking

set -e

# Configuration
SSID="JAM-PI"
PASSWORD="MrConductor2025"
INTERFACE="wlan0"
IP_ADDRESS="192.168.4.1"
NETMASK="255.255.255.0"
DHCP_RANGE_START="192.168.4.2"
DHCP_RANGE_END="192.168.4.20"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check if running on Raspberry Pi
check_platform() {
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        warning "This doesn't appear to be a Raspberry Pi"
        warning "Some features may not work correctly"
    fi
}

# Update system packages
update_system() {
    log "Updating system packages..."
    apt update
    apt upgrade -y
}

# Install required packages
install_packages() {
    log "Installing required packages..."
    apt install -y \
        hostapd \
        dnsmasq \
        iptables-persistent \
        bridge-utils \
        python3-pip \
        python3-venv \
        git \
        vim \
        htop \
        screen
}

# Configure hostapd (WiFi access point)
configure_hostapd() {
    log "Configuring hostapd..."
    
    # Create hostapd configuration
    cat > /etc/hostapd/hostapd.conf << EOF
# Mr. Conductor WiFi Hotspot Configuration
interface=${INTERFACE}
driver=nl80211
ssid=${SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=${PASSWORD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# Additional settings for better performance
country_code=US
ieee80211n=1
ieee80211d=1
ht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]
EOF

    # Set hostapd daemon configuration
    echo 'DAEMON_CONF="/etc/hostapd/hostapd.conf"' > /etc/default/hostapd
    
    # Enable and start hostapd
    systemctl unmask hostapd
    systemctl enable hostapd
}

# Configure dnsmasq (DHCP server)
configure_dnsmasq() {
    log "Configuring dnsmasq..."
    
    # Backup original configuration
    if [[ -f /etc/dnsmasq.conf ]]; then
        cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
    fi
    
    # Create new dnsmasq configuration
    cat > /etc/dnsmasq.conf << EOF
# Mr. Conductor DHCP Configuration
interface=${INTERFACE}
dhcp-range=${DHCP_RANGE_START},${DHCP_RANGE_END},${NETMASK},24h

# DNS settings
server=8.8.8.8
server=8.8.4.4

# Local domain
domain=jam-pi.local
local=/jam-pi.local/

# DHCP options
dhcp-option=option:router,${IP_ADDRESS}
dhcp-option=option:dns-server,${IP_ADDRESS}

# Logging
log-queries
log-dhcp

# Cache settings
cache-size=1000
EOF

    # Enable dnsmasq
    systemctl enable dnsmasq
}

# Configure network interfaces
configure_network() {
    log "Configuring network interfaces..."
    
    # Configure static IP for WiFi interface
    cat > /etc/dhcpcd.conf << EOF
# Mr. Conductor Network Configuration
# Static IP configuration for WiFi hotspot
interface ${INTERFACE}
static ip_address=${IP_ADDRESS}/24
nohook wpa_supplicant

# Allow other interfaces to use DHCP
interface eth0
# DHCP configuration for ethernet (if available)
EOF

    # Disable wpa_supplicant on WiFi interface
    systemctl disable wpa_supplicant
}

# Configure IP forwarding and NAT
configure_routing() {
    log "Configuring IP forwarding and NAT..."
    
    # Enable IP forwarding
    echo 'net.ipv4.ip_forward=1' >> /etc/sysctl.conf
    
    # Configure iptables for NAT (if ethernet available)
    iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
    iptables -A FORWARD -i eth0 -o ${INTERFACE} -m state --state RELATED,ESTABLISHED -j ACCEPT
    iptables -A FORWARD -i ${INTERFACE} -o eth0 -j ACCEPT
    
    # Save iptables rules
    iptables-save > /etc/iptables/rules.v4
}

# Create Mr. Conductor service
create_service() {
    log "Creating Mr. Conductor systemd service..."
    
    cat > /etc/systemd/system/mr-conductor.service << EOF
[Unit]
Description=Mr. Conductor Offline Band Nervous System
After=network.target hostapd.service dnsmasq.service
Wants=hostapd.service dnsmasq.service

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/mr-conductor
Environment=PATH=/home/pi/mr-conductor/venv/bin
ExecStart=/home/pi/mr-conductor/venv/bin/python /home/pi/mr-conductor/web/app.py
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mr-conductor

[Install]
WantedBy=multi-user.target
EOF

    # Enable the service
    systemctl daemon-reload
    systemctl enable mr-conductor
}

# Create network monitoring script
create_monitoring() {
    log "Creating network monitoring script..."
    
    cat > /usr/local/bin/mr-conductor-monitor << 'EOF'
#!/bin/bash
# Mr. Conductor Network Monitor

LOG_FILE="/var/log/mr-conductor-network.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

check_services() {
    # Check hostapd
    if ! systemctl is-active --quiet hostapd; then
        log_message "WARNING: hostapd is not running, attempting restart"
        systemctl restart hostapd
    fi
    
    # Check dnsmasq
    if ! systemctl is-active --quiet dnsmasq; then
        log_message "WARNING: dnsmasq is not running, attempting restart"
        systemctl restart dnsmasq
    fi
    
    # Check Mr. Conductor service
    if ! systemctl is-active --quiet mr-conductor; then
        log_message "WARNING: mr-conductor service is not running, attempting restart"
        systemctl restart mr-conductor
    fi
}

check_connectivity() {
    # Check if WiFi interface is up
    if ! ip link show wlan0 | grep -q "state UP"; then
        log_message "WARNING: WiFi interface is down"
        ip link set wlan0 up
    fi
    
    # Check DHCP leases
    LEASE_COUNT=$(wc -l < /var/lib/dhcp/dhcpcd.leases 2>/dev/null || echo "0")
    log_message "INFO: Active DHCP leases: $LEASE_COUNT"
}

# Main monitoring loop
while true; do
    check_services
    check_connectivity
    sleep 60
done
EOF

    chmod +x /usr/local/bin/mr-conductor-monitor
    
    # Create monitoring service
    cat > /etc/systemd/system/mr-conductor-monitor.service << EOF
[Unit]
Description=Mr. Conductor Network Monitor
After=mr-conductor.service

[Service]
Type=simple
ExecStart=/usr/local/bin/mr-conductor-monitor
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable mr-conductor-monitor
}

# Create status check script
create_status_script() {
    log "Creating status check script..."
    
    cat > /usr/local/bin/mr-conductor-status << 'EOF'
#!/bin/bash
# Mr. Conductor Status Check

echo "=== Mr. Conductor System Status ==="
echo

# System info
echo "System Information:"
echo "  Hostname: $(hostname)"
echo "  Uptime: $(uptime -p)"
echo "  Load: $(uptime | awk -F'load average:' '{print $2}')"
echo "  Memory: $(free -h | awk 'NR==2{printf "%.1f/%.1fGB (%.2f%%)", $3/1024/1024, $2/1024/1024, $3*100/$2}')"
echo "  Temperature: $(vcgencmd measure_temp 2>/dev/null | cut -d= -f2 || echo "N/A")"
echo

# Network status
echo "Network Status:"
echo "  WiFi Interface: $(ip addr show wlan0 | grep 'inet ' | awk '{print $2}' || echo "Not configured")"
echo "  WiFi Status: $(systemctl is-active hostapd)"
echo "  DHCP Status: $(systemctl is-active dnsmasq)"
echo

# Connected devices
echo "Connected Devices:"
if [[ -f /var/lib/dhcp/dhcpcd.leases ]]; then
    awk '{print "  " $4 " (" $2 ")"}' /var/lib/dhcp/dhcpcd.leases | sort -u
else
    echo "  No DHCP leases found"
fi
echo

# Service status
echo "Service Status:"
echo "  Mr. Conductor: $(systemctl is-active mr-conductor)"
echo "  Monitor: $(systemctl is-active mr-conductor-monitor)"
echo "  SSH: $(systemctl is-active ssh)"
echo

# Port status
echo "Port Status:"
echo "  Web Interface: $(netstat -ln | grep ':5000' >/dev/null && echo "Listening" || echo "Not listening")"
echo "  SSH: $(netstat -ln | grep ':22' >/dev/null && echo "Listening" || echo "Not listening")"
echo

# Recent logs
echo "Recent Log Entries:"
journalctl -u mr-conductor --no-pager -n 5 --since "5 minutes ago" | tail -n +2 || echo "  No recent logs"
EOF

    chmod +x /usr/local/bin/mr-conductor-status
}

# Create uninstall script
create_uninstall() {
    log "Creating uninstall script..."
    
    cat > /usr/local/bin/mr-conductor-uninstall << 'EOF'
#!/bin/bash
# Mr. Conductor Uninstall Script

echo "WARNING: This will remove Mr. Conductor and restore original network settings"
read -p "Are you sure? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

echo "Stopping services..."
systemctl stop mr-conductor mr-conductor-monitor hostapd dnsmasq
systemctl disable mr-conductor mr-conductor-monitor hostapd dnsmasq

echo "Removing service files..."
rm -f /etc/systemd/system/mr-conductor.service
rm -f /etc/systemd/system/mr-conductor-monitor.service
systemctl daemon-reload

echo "Restoring network configuration..."
if [[ -f /etc/dnsmasq.conf.backup ]]; then
    mv /etc/dnsmasq.conf.backup /etc/dnsmasq.conf
fi

# Restore original dhcpcd.conf (basic version)
cat > /etc/dhcpcd.conf << 'EOL'
# A sample configuration for dhcpcd.
option rapid_commit
option domain_name_servers, domain_name, domain_search, host_name
option classless_static_routes
option interface_mtu
require dhcp_server_identifier
slaac private
EOL

echo "Removing configuration files..."
rm -f /etc/hostapd/hostapd.conf
rm -f /usr/local/bin/mr-conductor-*

echo "Cleaning up iptables..."
iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE 2>/dev/null || true
iptables -D FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -i wlan0 -o eth0 -j ACCEPT 2>/dev/null || true

echo "Re-enabling wpa_supplicant..."
systemctl enable wpa_supplicant

echo "Mr. Conductor has been uninstalled. Please reboot to complete the process."
EOF

    chmod +x /usr/local/bin/mr-conductor-uninstall
}

# Main installation function
main() {
    log "Starting Mr. Conductor WiFi Hotspot Setup"
    
    check_root
    check_platform
    
    info "This will configure your Raspberry Pi as a WiFi hotspot"
    info "SSID: $SSID"
    info "Password: $PASSWORD"
    info "IP Address: $IP_ADDRESS"
    
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Installation cancelled"
        exit 0
    fi
    
    update_system
    install_packages
    configure_hostapd
    configure_dnsmasq
    configure_network
    configure_routing
    create_service
    create_monitoring
    create_status_script
    create_uninstall
    
    log "WiFi hotspot setup completed successfully!"
    echo
    info "Network Configuration:"
    info "  SSID: $SSID"
    info "  Password: $PASSWORD"
    info "  IP Address: $IP_ADDRESS"
    info "  Web Interface: http://$IP_ADDRESS:5000"
    echo
    info "Useful commands:"
    info "  Check status: sudo mr-conductor-status"
    info "  View logs: journalctl -u mr-conductor -f"
    info "  Restart service: sudo systemctl restart mr-conductor"
    info "  Uninstall: sudo mr-conductor-uninstall"
    echo
    warning "Please reboot your Raspberry Pi to complete the setup:"
    warning "  sudo reboot"
}

# Run main function
main "$@"

