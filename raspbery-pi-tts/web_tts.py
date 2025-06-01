#!/usr/bin/env python3
"""
Web Interface for Raspberry Pi TTS System (No GPIO)
Flask-based web application for browser access
"""

from flask import Flask, render_template, request, jsonify, send_file
import pyttsx3
import os
import tempfile
import threading
import time
from pathlib import Path
import psutil

app = Flask(__name__)

class WebTTS:
    def __init__(self):
        self.engine = None
        self.voices = []
        self.current_voice_id = 0
        self.rate = 150
        self.volume = 0.9
        self.initialize_tts()
        
def initialize_tts(self):
    """Initialize the TTS engine"""
    try:
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        
        self.voices = []
        if voices:
            for i, voice in enumerate(voices):
                # Safely extract voice information
                voice_name = str(voice.name) if voice.name else f"Voice {i}"
                voice_lang = 'en'
                
                # Safely get language
                if hasattr(voice, 'languages') and voice.languages:
                    try:
                        if isinstance(voice.languages, (list, tuple)) and len(voice.languages) > 0:
                            voice_lang = str(voice.languages[0])
                        else:
                            voice_lang = str(voice.languages)
                    except:
                        voice_lang = 'en'
                
                self.voices.append({
                    'id': i,
                    'name': voice_name,
                    'lang': voice_lang
                })
            
            # Set default voice
            self.engine.setProperty('voice', voices[0].id)
        else:
            # Fallback voices if no system voices found
            self.voices = [
                {'id': 0, 'name': 'Default Voice', 'lang': 'en'},
                {'id': 1, 'name': 'Alternative Voice', 'lang': 'en'}
            ]
        
        self.engine.setProperty('rate', self.rate)
        self.engine.setProperty('volume', self.volume)
        
        print(f"✓ Web TTS initialized with {len(self.voices)} voices")
        return True
        
    except Exception as e:
        print(f"TTS initialization failed: {e}")
        # Create fallback voices
        self.voices = [
            {'id': 0, 'name': 'espeak-default', 'lang': 'en'},
            {'id': 1, 'name': 'espeak-male', 'lang': 'en'},
            {'id': 2, 'name': 'espeak-female', 'lang': 'en'}
        ]
        self.use_espeak = True
        print("✓ Fallback to espeak voices")
        return True
    def speak_to_file(self, text, filename):
        """Generate speech and save to file"""
        try:
            self.engine.save_to_file(text, filename)
            self.engine.runAndWait()
            return True
        except:
            # Fallback to espeak
            os.system(f'espeak "{text}" -w {filename}')
            return os.path.exists(filename)
    
    def get_system_info(self):
        """Get system information"""
        try:
            cpu_temp = self.get_cpu_temperature()
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'cpu_usage': cpu_percent,
                'cpu_temp': cpu_temp,
                'memory_percent': memory.percent,
                'memory_available': memory.available // 1024 // 1024,
                'voices_count': len(self.voices),
                'current_voice': self.voices[self.current_voice_id]['name'] if self.voices else 'None',
                'rate': self.rate,
                'volume': self.volume
            }
        except:
            return {'error': 'Unable to get system info'}
    
    def get_cpu_temperature(self):
        """Get CPU temperature"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read()) / 1000.0
                return round(temp, 1)
        except:
            return "N/A"

# Global TTS instance
tts = WebTTS()

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/voices')
def get_voices():
    """Get available voices"""
    return jsonify({
        'voices': tts.voices,
        'current': tts.current_voice_id
    })

@app.route('/api/speak', methods=['POST'])
def speak():
    """Convert text to speech"""
    data = request.get_json()
    text = data.get('text', '').strip()
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp_path = tmp.name
        
        # Generate speech
        if tts.speak_to_file(text, tmp_path):
            return jsonify({
                'success': True,
                'message': f'Speech generated for: {text[:50]}{"..." if len(text) > 50 else ""}'
            })
        else:
            return jsonify({'error': 'Speech generation failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice', methods=['POST'])
def set_voice():
    """Change voice"""
    data = request.get_json()
    voice_id = data.get('voice_id')
    
    try:
        voice_id = int(voice_id)
        if 0 <= voice_id < len(tts.voices):
            tts.current_voice_id = voice_id
            
            if tts.engine:
                voices = tts.engine.getProperty('voices')
                if voice_id < len(voices):
                    tts.engine.setProperty('voice', voices[voice_id].id)
            
            return jsonify({
                'success': True,
                'voice': tts.voices[voice_id]['name']
            })
        else:
            return jsonify({'error': 'Invalid voice ID'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rate', methods=['POST'])
def set_rate():
    """Set speech rate"""
    data = request.get_json()
    rate = data.get('rate')
    
    try:
        rate = int(rate)
        if 50 <= rate <= 300:
            tts.rate = rate
            if tts.engine:
                tts.engine.setProperty('rate', rate)
            
            return jsonify({
                'success': True,
                'rate': rate
            })
        else:
            return jsonify({'error': 'Rate must be 50-300 WPM'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/volume', methods=['POST'])
def set_volume():
    """Set volume"""
    data = request.get_json()
    volume = data.get('volume')
    
    try:
        volume = float(volume)
        if 0.0 <= volume <= 1.0:
            tts.volume = volume
            if tts.engine:
                tts.engine.setProperty('volume', volume)
            
            return jsonify({
                'success': True,
                'volume': volume
            })
        else:
            return jsonify({'error': 'Volume must be 0.0-1.0'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system')
def system_info():
    """Get system information"""
    return jsonify(tts.get_system_info())

# Create templates directory and HTML template
def create_template():
    """Create HTML template for web interface"""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Raspberry Pi TTS System</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        .control-group {
            margin-bottom: 25px;
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .control-group h3 {
            margin: 0 0 15px 0;
            color: #fff;
            font-size: 1.2em;
        }
        .text-input {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            margin-bottom: 15px;
            box-sizing: border-box;
        }
        .button {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s ease;
            margin: 5px;
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        .button:active {
            transform: translateY(0);
        }
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }
        .slider-container {
            margin: 10px 0;
        }
        .slider {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: rgba(255, 255, 255, 0.3);
            outline: none;
            -webkit-appearance: none;
        }
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #ff6b6b;
            cursor: pointer;
        }
        .status {
            background: rgba(0, 255, 0, 0.2);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #00ff00;
        }
        .error {
            background: rgba(255, 0, 0, 0.2);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border-left: 4px solid #ff0000;
        }
        .system-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .info-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .info-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #fff;
        }
        .info-label {
            font-size: 0.9em;
            color: rgba(255, 255, 255, 0.8);
        }
        select {
            width: 100%;
            padding: 10px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎤 Raspberry Pi TTS System</h1>
        
        <div class="control-group">
            <h3>💬 Text to Speech</h3>
            <textarea id="textInput" class="text-input" rows="4" placeholder="Enter text to convert to speech..."></textarea>
            <button class="button" onclick="speak()">🔊 Speak</button>
            <button class="button" onclick="clearText()">🗑️ Clear</button>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <h3>🎭 Voice Selection</h3>
                <select id="voiceSelect" onchange="changeVoice()">
                    <option value="">Loading voices...</option>
                </select>
            </div>
            
            <div class="control-group">
                <h3>⚡ Speech Rate</h3>
                <div class="slider-container">
                    <input type="range" min="50" max="300" value="150" class="slider" id="rateSlider" onchange="changeRate()">
                    <div>Rate: <span id="rateValue">150</span> WPM</div>
                </div>
            </div>
            
            <div class="control-group">
                <h3>🔊 Volume</h3>
                <div class="slider-container">
                    <input type="range" min="0" max="1" step="0.1" value="0.9" class="slider" id="volumeSlider" onchange="changeVolume()">
                    <div>Volume: <span id="volumeValue">0.9</span></div>
                </div>
            </div>
        </div>
        
        <div class="control-group">
            <h3>📊 System Information</h3>
            <button class="button" onclick="updateSystemInfo()">🔄 Refresh</button>
            <div id="systemInfo" class="system-info">
                <div class="info-card">
                    <div class="info-value" id="cpuUsage">--</div>
                    <div class="info-label">CPU Usage</div>
                </div>
                <div class="info-card">
                    <div class="info-value" id="cpuTemp">--</div>
                    <div class="info-label">CPU Temp</div>
                </div>
                <div class="info-card">
                    <div class="info-value" id="memoryUsage">--</div>
                    <div class="info-label">Memory</div>
                </div>
                <div class="info-card">
                    <div class="info-value" id="voiceCount">--</div>
                    <div class="info-label">Voices</div>
                </div>
            </div>
        </div>
        
        <div id="messages"></div>
    </div>

    <script>
        let voices = [];
        
        function showMessage(message, type = 'status') {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            messagesDiv.appendChild(messageDiv);
            
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
        
        function speak() {
            const text = document.getElementById('textInput').value.trim();
            if (!text) {
                showMessage('Please enter some text to speak', 'error');
                return;
            }
            
            fetch('/api/speak', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage(data.message);
                } else {
                    showMessage(data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('Error: ' + error, 'error');
            });
        }
        
        function clearText() {
            document.getElementById('textInput').value = '';
        }
        
        function loadVoices() {
            fetch('/api/voices')
            .then(response => response.json())
            .then(data => {
                voices = data.voices;
                const select = document.getElementById('voiceSelect');
                select.innerHTML = '';
                
                voices.forEach(voice => {
                    const option = document.createElement('option');
                    option.value = voice.id;
                    option.textContent = voice.name;
                    if (voice.id === data.current) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            })
            .catch(error => {
                showMessage('Error loading voices: ' + error, 'error');
            });
        }
        
        function changeVoice() {
            const voiceId = document.getElementById('voiceSelect').value;
            
            fetch('/api/voice', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ voice_id: voiceId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('Voice changed to: ' + data.voice);
                } else {
                    showMessage(data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('Error changing voice: ' + error, 'error');
            });
        }
        
        function changeRate() {
            const rate = document.getElementById('rateSlider').value;
            document.getElementById('rateValue').textContent = rate;
            
            fetch('/api/rate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ rate: rate })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('Speech rate set to: ' + data.rate + ' WPM');
                } else {
                    showMessage(data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('Error changing rate: ' + error, 'error');
            });
        }
        
        function changeVolume() {
            const volume = document.getElementById('volumeSlider').value;
            document.getElementById('volumeValue').textContent = volume;
            
            fetch('/api/volume', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ volume: volume })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showMessage('Volume set to: ' + data.volume);
                } else {
                    showMessage(data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('Error changing volume: ' + error, 'error');
            });
        }
        
        function updateSystemInfo() {
            fetch('/api/system')
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    document.getElementById('cpuUsage').textContent = data.cpu_usage.toFixed(1) + '%';
                    document.getElementById('cpuTemp').textContent = data.cpu_temp + '°C';
                    document.getElementById('memoryUsage').textContent = data.memory_percent.toFixed(1) + '%';
                    document.getElementById('voiceCount').textContent = data.voices_count;
                    showMessage('System information updated');
                } else {
                    showMessage('Error getting system info: ' + data.error, 'error');
                }
            })
            .catch(error => {
                showMessage('Error updating system info: ' + error, 'error');
            });
        }
        
        // Initialize on page load
        window.onload = function() {
            loadVoices();
            updateSystemInfo();
            showMessage('TTS Web Interface loaded successfully!');
        };
        
        // Allow Enter key to speak
        document.getElementById('textInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && e.ctrlKey) {
                speak();
            }
        });
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'index.html', 'w') as f:
        f.write(html_content)

if __name__ == '__main__':
    print("Creating web interface template...")
    create_template()
    
    print("Starting Raspberry Pi TTS Web Server...")
    print("Access the web interface at: http://localhost:5000")
    print("Or from other devices at: http://[your-pi-ip]:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)