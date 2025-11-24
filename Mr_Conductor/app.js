// Mr. Conductor - JavaScript Application
// Handles real-time communication and UI interactions

class MrConductorApp {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.currentStatus = null;
        this.isPlaying = false;
        this.currentBPM = 120;
        this.currentScene = null;
        
        this.init();
    }
    
    init() {
        this.initializeSocket();
        this.bindEventListeners();
        this.initializeUI();
        
        console.log('Mr. Conductor App initialized');
    }
    
    initializeSocket() {
        // Initialize Socket.IO connection
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to Mr. Conductor');
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.requestStatus();
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from Mr. Conductor');
            this.isConnected = false;
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('status_update', (status) => {
            this.handleStatusUpdate(status);
        });
        
        this.socket.on('transport_change', (data) => {
            this.handleTransportChange(data);
        });
        
        this.socket.on('bpm_change', (data) => {
            this.handleBPMChange(data);
        });
        
        this.socket.on('scene_change', (data) => {
            this.handleSceneChange(data);
        });
        
        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            this.showNotification('Connection error: ' + error.message, 'error');
        });
    }
    
    bindEventListeners() {
        // Transport controls
        document.getElementById('startBtn').addEventListener('click', () => {
            this.startPlayback();
        });
        
        document.getElementById('stopBtn').addEventListener('click', () => {
            this.stopPlayback();
        });
        
        // BPM control
        const bpmSlider = document.getElementById('bpmSlider');
        bpmSlider.addEventListener('input', (e) => {
            this.updateBPMDisplay(e.target.value);
        });
        
        bpmSlider.addEventListener('change', (e) => {
            this.setBPM(parseFloat(e.target.value));
        });
        
        // Scene controls
        document.querySelectorAll('.scene-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sceneName = e.target.dataset.scene;
                this.loadScene(sceneName);
            });
        });
        
        document.getElementById('saveSceneBtn').addEventListener('click', () => {
            this.showCreateSceneModal();
        });
        
        // Settings tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Modal controls
        document.getElementById('modalClose').addEventListener('click', () => {
            this.hideModal();
        });
        
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.hideModal();
        });
        
        document.getElementById('createSceneBtn').addEventListener('click', () => {
            this.createScene();
        });
        
        document.getElementById('modalOverlay').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                this.hideModal();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboard(e);
        });
    }
    
    initializeUI() {
        this.updateConnectionStatus(false);
        this.updateBPMDisplay(120);
        this.updateTransportButtons(false);
    }
    
    requestStatus() {
        if (this.socket && this.isConnected) {
            this.socket.emit('request_status');
        }
    }
    
    updateConnectionStatus(connected) {
        const statusIndicator = document.getElementById('connectionStatus');
        const statusText = statusIndicator.querySelector('.status-text');
        
        if (connected) {
            statusIndicator.classList.add('online');
            statusText.textContent = 'ONLINE';
        } else {
            statusIndicator.classList.remove('online');
            statusText.textContent = 'OFFLINE';
        }
    }
    
    handleStatusUpdate(status) {
        this.currentStatus = status;
        
        // Update system status
        if (status.system) {
            this.updateSystemStatus(status.system);
        }
        
        // Update timing status
        if (status.timing) {
            this.updateTimingStatus(status.timing);
        }
        
        // Update MIDI status
        if (status.midi) {
            this.updateMIDIStatus(status.midi);
        }
        
        // Update scenes
        if (status.scenes) {
            this.updateScenes(status.scenes, status.current_scene);
        }
    }
    
    updateSystemStatus(system) {
        // Update uptime
        const uptimeHours = Math.floor(system.uptime / 3600);
        const uptimeMinutes = Math.floor((system.uptime % 3600) / 60);
        document.getElementById('uptime').textContent = `${uptimeHours}h ${uptimeMinutes}m`;
        
        // Update other system stats
        document.getElementById('cpuUsage').textContent = `${system.cpu_usage.toFixed(1)}%`;
        document.getElementById('memoryUsage').textContent = `${system.memory_usage.toFixed(0)} MB`;
        document.getElementById('timingAccuracy').textContent = `±${system.timing_accuracy.toFixed(1)}ms`;
        document.getElementById('beatPosition').textContent = system.beat_position.toFixed(2);
        document.getElementById('deviceCount').textContent = system.connected_devices;
        
        // Update transport state
        if (system.is_playing !== this.isPlaying) {
            this.isPlaying = system.is_playing;
            this.updateTransportButtons(this.isPlaying);
        }
        
        // Update BPM
        if (system.bpm !== this.currentBPM) {
            this.currentBPM = system.bpm;
            this.updateBPMDisplay(this.currentBPM);
            document.getElementById('bpmSlider').value = this.currentBPM;
        }
    }
    
    updateTimingStatus(timing) {
        // Additional timing-specific updates can go here
    }
    
    updateMIDIStatus(midi) {
        // Update MIDI device list
        this.updateDevicesList(midi);
    }
    
    updateDevicesList(midiStatus) {
        const devicesList = document.getElementById('devicesList');
        
        // Clear existing devices
        devicesList.innerHTML = '';
        
        // Add MIDI devices
        if (midiStatus.device_count > 0) {
            // In a real implementation, we'd get the actual device list
            // For now, show some example devices
            const devices = [
                { name: 'USB Roland Synth', connected: true },
                { name: 'USB Korg Controller', connected: true },
                { name: 'Logic Pro X', connected: true },
                { name: 'iPad Link App', connected: false }
            ];
            
            devices.forEach(device => {
                const deviceItem = document.createElement('div');
                deviceItem.className = 'device-item';
                
                const statusClass = device.connected ? 'online' : 'offline';
                deviceItem.innerHTML = `
                    <span class="device-status ${statusClass}"></span>
                    <span class="device-name">${device.name}</span>
                `;
                
                devicesList.appendChild(deviceItem);
            });
        } else {
            devicesList.innerHTML = '<div class="device-item"><span class="device-status connecting"></span><span class="device-name">No devices connected</span></div>';
        }
    }
    
    updateScenes(scenes, currentScene) {
        this.currentScene = currentScene;
        
        // Update scene buttons
        document.querySelectorAll('.scene-btn').forEach(btn => {
            const sceneName = btn.dataset.scene;
            if (sceneName === currentScene) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
    }
    
    updateBPMDisplay(bpm) {
        document.getElementById('bpmDisplay').textContent = Math.round(bpm);
    }
    
    updateTransportButtons(isPlaying) {
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        if (isPlaying) {
            startBtn.classList.add('active');
            stopBtn.classList.remove('active');
        } else {
            startBtn.classList.remove('active');
            stopBtn.classList.add('active');
        }
    }
    
    // API Methods
    async startPlayback() {
        try {
            const response = await fetch('/api/transport/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            if (result.success) {
                this.showNotification('Playback started', 'success');
            } else {
                this.showNotification('Failed to start playback: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Start playback error:', error);
            this.showNotification('Connection error', 'error');
        }
    }
    
    async stopPlayback() {
        try {
            const response = await fetch('/api/transport/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            if (result.success) {
                this.showNotification('Playback stopped', 'success');
            } else {
                this.showNotification('Failed to stop playback: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Stop playback error:', error);
            this.showNotification('Connection error', 'error');
        }
    }
    
    async setBPM(bpm) {
        try {
            const response = await fetch('/api/bpm', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ bpm: bpm })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showNotification(`BPM set to ${bpm}`, 'success');
            } else {
                this.showNotification('Failed to set BPM: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Set BPM error:', error);
            this.showNotification('Connection error', 'error');
        }
    }
    
    async loadScene(sceneName) {
        try {
            const response = await fetch(`/api/scenes/${encodeURIComponent(sceneName)}/load`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            if (result.success) {
                this.showNotification(`Scene "${sceneName}" loaded`, 'success');
            } else {
                this.showNotification('Failed to load scene: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Load scene error:', error);
            this.showNotification('Connection error', 'error');
        }
    }
    
    async createScene() {
        const name = document.getElementById('sceneName').value.trim();
        const bpm = parseFloat(document.getElementById('sceneBpm').value);
        const notes = document.getElementById('sceneNotes').value.trim();
        
        if (!name) {
            this.showNotification('Scene name is required', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/scenes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    bpm: bpm,
                    notes: notes
                })
            });
            
            const result = await response.json();
            if (result.success) {
                this.showNotification(`Scene "${name}" created`, 'success');
                this.hideModal();
                this.clearSceneForm();
            } else {
                this.showNotification('Failed to create scene: ' + result.error, 'error');
            }
        } catch (error) {
            console.error('Create scene error:', error);
            this.showNotification('Connection error', 'error');
        }
    }
    
    // UI Helper Methods
    showCreateSceneModal() {
        document.getElementById('sceneBpm').value = this.currentBPM;
        document.getElementById('modalOverlay').classList.add('active');
        document.getElementById('sceneName').focus();
    }
    
    hideModal() {
        document.getElementById('modalOverlay').classList.remove('active');
    }
    
    clearSceneForm() {
        document.getElementById('sceneName').value = '';
        document.getElementById('sceneBpm').value = 120;
        document.getElementById('sceneNotes').value = '';
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            if (btn.dataset.tab === tabName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        // Update tab panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            if (panel.id === tabName + 'Tab') {
                panel.classList.add('active');
            } else {
                panel.classList.remove('active');
            }
        });
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // Add styles
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 20px',
            borderRadius: '8px',
            color: 'white',
            fontWeight: '600',
            fontSize: '14px',
            zIndex: '9999',
            opacity: '0',
            transform: 'translateY(-20px)',
            transition: 'all 0.3s ease'
        });
        
        // Set background color based on type
        switch (type) {
            case 'success':
                notification.style.background = '#4CAF50';
                break;
            case 'error':
                notification.style.background = '#f44336';
                break;
            case 'warning':
                notification.style.background = '#ff9800';
                break;
            default:
                notification.style.background = '#2196F3';
        }
        
        // Add to DOM
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateY(0)';
        }, 10);
        
        // Remove after delay
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
    
    handleKeyboard(e) {
        // Keyboard shortcuts
        if (e.ctrlKey || e.metaKey) {
            switch (e.key) {
                case ' ':
                    e.preventDefault();
                    if (this.isPlaying) {
                        this.stopPlayback();
                    } else {
                        this.startPlayback();
                    }
                    break;
                case 's':
                    e.preventDefault();
                    this.showCreateSceneModal();
                    break;
            }
        }
        
        // Escape key
        if (e.key === 'Escape') {
            this.hideModal();
        }
    }
    
    handleTransportChange(data) {
        // Handle real-time transport changes from server
        if (data.action === 'start') {
            this.isPlaying = true;
        } else if (data.action === 'stop') {
            this.isPlaying = false;
        }
        this.updateTransportButtons(this.isPlaying);
    }
    
    handleBPMChange(data) {
        // Handle real-time BPM changes from server
        this.currentBPM = data.new_bpm;
        this.updateBPMDisplay(this.currentBPM);
        document.getElementById('bpmSlider').value = this.currentBPM;
    }
    
    handleSceneChange(data) {
        // Handle real-time scene changes from server
        this.currentScene = data.scene_name;
        this.updateScenes([], this.currentScene);
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.mrConductor = new MrConductorApp();
});

// Add some visual flair
document.addEventListener('DOMContentLoaded', () => {
    // Add sparkle effect to the conductor logo
    const logo = document.querySelector('.conductor-logo');
    if (logo) {
        logo.addEventListener('mouseenter', () => {
            logo.style.transform = 'scale(1.1) rotate(5deg)';
        });
        
        logo.addEventListener('mouseleave', () => {
            logo.style.transform = 'scale(1) rotate(0deg)';
        });
    }
    
    // Add ripple effect to buttons
    document.querySelectorAll('.transport-btn, .scene-btn, .control-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
    
    // Add CSS for ripple animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes ripple {
            to {
                transform: scale(4);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
});

