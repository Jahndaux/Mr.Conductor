#!/usr/bin/env python3
"""
Mr. Conductor - Flask Web Application
Provides web interface for the offline band nervous system
"""

import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, disconnect
import threading
import time

# Import Mr. Conductor components
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mr_conductor import get_mr_conductor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mr-conductor-secret-key-2025'

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Get Mr. Conductor instance
conductor = get_mr_conductor()

# Track connected clients
connected_clients = set()

@app.route('/')
def index():
    """Main control panel page"""
    return render_template('index.html')

@app.route('/api/status')
def api_status():
    """Get system status"""
    try:
        status = conductor.get_detailed_status()
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"Status API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transport/<action>', methods=['POST'])
def api_transport(action):
    """Transport control (start/stop)"""
    try:
        if action == 'start':
            conductor.start_playback()
            message = "Playback started"
        elif action == 'stop':
            conductor.stop_playback()
            message = "Playback stopped"
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid transport action'
            }), 400
            
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Transport API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/bpm', methods=['POST'])
def api_set_bpm():
    """Set BPM"""
    try:
        data = request.get_json()
        bpm = float(data.get('bpm', 120))
        
        if not 60 <= bpm <= 200:
            return jsonify({
                'success': False,
                'error': 'BPM must be between 60 and 200'
            }), 400
            
        conductor.set_bpm(bpm)
        
        return jsonify({
            'success': True,
            'message': f'BPM set to {bpm}'
        })
        
    except Exception as e:
        logger.error(f"BPM API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scenes', methods=['GET'])
def api_get_scenes():
    """Get all scenes"""
    try:
        scenes = conductor.scene_manager.get_scenes()
        current_scene = conductor.scene_manager.get_current_scene()
        
        return jsonify({
            'success': True,
            'data': {
                'scenes': scenes,
                'current_scene': current_scene
            }
        })
        
    except Exception as e:
        logger.error(f"Scenes API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scenes', methods=['POST'])
def api_create_scene():
    """Create new scene"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        bpm = float(data.get('bpm', conductor.status.bpm))
        notes = data.get('notes', '').strip()
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Scene name is required'
            }), 400
            
        if conductor.create_scene(name, bpm, notes):
            return jsonify({
                'success': True,
                'message': f'Scene "{name}" created'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create scene'
            }), 500
            
    except Exception as e:
        logger.error(f"Create scene API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scenes/<scene_name>/load', methods=['POST'])
def api_load_scene(scene_name):
    """Load a scene"""
    try:
        if conductor.load_scene(scene_name):
            return jsonify({
                'success': True,
                'message': f'Scene "{scene_name}" loaded'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Scene "{scene_name}" not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Load scene API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/midi/devices')
def api_midi_devices():
    """Get MIDI devices"""
    try:
        devices = conductor.midi_clock.get_devices()
        return jsonify({
            'success': True,
            'data': devices
        })
        
    except Exception as e:
        logger.error(f"MIDI devices API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# WebSocket events for real-time updates
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    connected_clients.add(request.sid)
    logger.info(f"Client connected: {request.sid} (Total: {len(connected_clients)})")
    
    # Send initial status
    status = conductor.get_detailed_status()
    emit('status_update', status)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    connected_clients.discard(request.sid)
    logger.info(f"Client disconnected: {request.sid} (Total: {len(connected_clients)})")

@socketio.on('request_status')
def handle_status_request():
    """Handle status request from client"""
    try:
        status = conductor.get_detailed_status()
        emit('status_update', status)
    except Exception as e:
        logger.error(f"Status request error: {e}")
        emit('error', {'message': str(e)})

def broadcast_status_updates():
    """Background thread to broadcast status updates"""
    while True:
        try:
            if connected_clients:
                status = conductor.get_detailed_status()
                socketio.emit('status_update', status)
            time.sleep(0.5)  # Update every 500ms
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            time.sleep(1.0)

# Event handlers for Mr. Conductor events
def on_play_start():
    """Handle play start event"""
    socketio.emit('transport_change', {'action': 'start'})

def on_play_stop():
    """Handle play stop event"""
    socketio.emit('transport_change', {'action': 'stop'})

def on_bpm_change(old_bpm, new_bpm):
    """Handle BPM change event"""
    socketio.emit('bpm_change', {'old_bpm': old_bpm, 'new_bpm': new_bpm})

def on_scene_change(scene_name):
    """Handle scene change event"""
    socketio.emit('scene_change', {'scene_name': scene_name})

# Register event callbacks
conductor.add_event_callback('play_start', on_play_start)
conductor.add_event_callback('play_stop', on_play_stop)
conductor.add_event_callback('bpm_change', on_bpm_change)
conductor.add_event_callback('scene_change', on_scene_change)

def create_app():
    """Application factory"""
    # Start Mr. Conductor system
    conductor.start()
    
    # Add some default scenes
    conductor.create_scene("Song 1", 120.0, "Default song 1")
    conductor.create_scene("Song 2", 140.0, "Upbeat song")
    conductor.create_scene("Song 3", 90.0, "Slow ballad")
    conductor.create_scene("Song 4", 160.0, "Fast rock song")
    
    # Add some test MIDI devices
    conductor.midi_clock.add_device("USB Roland", "usb_roland_1")
    conductor.midi_clock.add_device("USB Korg", "usb_korg_1")
    
    # Start background status broadcasting
    status_thread = threading.Thread(target=broadcast_status_updates, daemon=True)
    status_thread.start()
    
    logger.info("Mr. Conductor web application initialized")
    return app

if __name__ == '__main__':
    # Create and run the application
    app = create_app()
    
    # Run with SocketIO
    socketio.run(app, 
                host='0.0.0.0',  # Listen on all interfaces
                port=5000,
                debug=False,
                allow_unsafe_werkzeug=True)

