from flask import Flask, render_template, request, jsonify, send_file
import os
import sys
import time
import json
import pyttsx3
from gtts import gTTS
from datetime import datetime
import uuid

# Define paths relative to the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
STATIC_DIR = os.path.join(PROJECT_DIR, 'static')
TEMPLATES_DIR = os.path.join(PROJECT_DIR, 'templates')
SAMPLES_DIR = os.path.join(PROJECT_DIR, 'samples')
LOGS_DIR = os.path.join(PROJECT_DIR, 'logs')

# Ensure directories exist
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Create the Flask application
app = Flask(__name__, 
            static_folder=STATIC_DIR,
            template_folder=TEMPLATES_DIR)

# TTS Engine class
class TTSEngine:
    """Text-to-Speech engine with multiple backend options"""
    
    def __init__(self, backend='pyttsx3', language='en'):
        self.backend = backend
        self.language = language
        
        # Initialize pyttsx3 if needed
        if backend == 'pyttsx3':
            self.engine = pyttsx3.init()
            self.voices = self.engine.getProperty('voices')
            self.default_rate = self.engine.getProperty('rate')
            self.default_volume = self.engine.getProperty('volume')
        
        # Log initialization
        self._log_event('init', {'backend': backend, 'language': language})
    
    def get_voices(self):
        """Get list of available voices"""
        if self.backend != 'pyttsx3':
            return []
            
        return [{'id': i, 'name': voice.name} 
                for i, voice in enumerate(self.voices)]
    
    def speak(self, text, voice_id=None, rate=None, volume=None):
        """Convert text to speech and return path to audio file"""
        if not text:
            return {'success': False, 'error': 'No text provided'}
        
        # Create unique filename for this conversion
        audio_id = str(uuid.uuid4())
        output_file = os.path.join(SAMPLES_DIR, f"{audio_id}.mp3")
        
        # Apply voice settings for pyttsx3
        if self.backend == 'pyttsx3':
            # Set voice if specified
            if voice_id is not None and 0 <= int(voice_id) < len(self.voices):
                self.engine.setProperty('voice', self.voices[int(voice_id)].id)
            
            # Set rate if specified
            if rate is not None:
                self.engine.setProperty('rate', int(rate))
            
            # Set volume if specified
            if volume is not None:
                self.engine.setProperty('volume', float(volume))
        
        # Preprocess text
        text = self._preprocess_text(text)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Use appropriate backend
            if self.backend == 'pyttsx3':
                self._speak_pyttsx3(text, output_file)
            elif self.backend == 'gtts':
                self._speak_gtts(text, output_file)
            else:
                return {'success': False, 'error': f'Unknown backend: {self.backend}'}
            
            # Calculate time taken
            elapsed_time = time.time() - start_time
            
            # Log successful conversion
            self._log_event('speak', {
                'text_length': len(text),
                'output_file': output_file,
                'elapsed_time': elapsed_time,
                'backend': self.backend
            })
            
            return {
                'success': True, 
                'audio_id': audio_id,
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            # Log errors
            self._log_event('error', {
                'text_length': len(text),
                'error': str(e),
                'backend': self.backend
            })
            
            return {'success': False, 'error': str(e)}
    
    def _speak_pyttsx3(self, text, output_file):
        """Use pyttsx3 engine for TTS"""
        self.engine.save_to_file(text, output_file)
        self.engine.runAndWait()
    
    def _speak_gtts(self, text, output_file):
        """Use Google Text-to-Speech for TTS"""
        tts = gTTS(text=text, lang=self.language, slow=False)
        tts.save(output_file)
    
    def _preprocess_text(self, text):
        """Preprocess text to improve speech quality"""
        # Replace special characters with their spoken form
        replacements = {
            '&': ' and ',
            '+': ' plus ',
            '@': ' at ',
            '%': ' percent ',
            '=': ' equals ',
            '#': ' number ',
            '...': ', dot dot dot',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Handle common abbreviations
        abbreviations = {
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Misses',
            'Ms.': 'Miss',
            'Prof.': 'Professor',
            'e.g.': 'for example',
            'i.e.': 'that is',
            'etc.': 'etcetera',
            'vs.': 'versus',
            'approx.': 'approximately'
        }
        
        for abbr, expansion in abbreviations.items():
            # Replace only if it's a standalone word (with spaces or punctuation around it)
            text = text.replace(f' {abbr} ', f' {expansion} ')
            
            # Also check at the beginning and end of the text
            if text.startswith(f'{abbr} '):
                text = f'{expansion} {text[len(abbr)+1:]}'
            if text.endswith(f' {abbr}'):
                text = f'{text[:-len(abbr)-1]} {expansion}'
        
        return text
    
    def _log_event(self, event_type, details):
        """Log events to file for analytics"""
        log_file = os.path.join(LOGS_DIR, 'tts_web_events.jsonl')
        
        # Create log entry
        entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'event': event_type,
            'details': details
        }
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

# Create TTS engine
tts_engine = TTSEngine(backend='pyttsx3')

# Create HTML template file
with open(os.path.join(TEMPLATES_DIR, 'index.html'), 'w') as f:
    f.write("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Text-to-Speech Converter</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .container {
            background-color: #f9f9f9;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        textarea {
            width: 100%;
            height: 150px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            resize: vertical;
        }
        select, input[type="range"] {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
        }
        .control-group {
            flex: 1;
            min-width: 200px;
        }
        .range-value {
            text-align: center;
            font-weight: bold;
            margin-top: 5px;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover {
            background-color: #2980b9;
        }
        #status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 4px;
            text-align: center;
        }
        .success {
            background-color: #d4edda;
            color: #155724;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .hidden {
            display: none;
        }
        .tab-container {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            background-color: #f1f1f1;
            border: 1px solid #ddd;
            border-bottom: none;
            border-radius: 5px 5px 0 0;
            margin-right: 5px;
        }
        .tab.active {
            background-color: #3498db;
            color: white;
            border-color: #3498db;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .history-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        footer {
            text-align: center;
            margin-top: 30px;
            color: #7f8c8d;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>Text-to-Speech Converter</h1>
    
    <div class="tab-container">
        <div class="tab active" data-tab="convert">Convert Text</div>
        <div class="tab" data-tab="settings">Settings</div>
        <div class="tab" data-tab="about">About</div>
    </div>
    
    <div id="convert" class="tab-content active">
        <div class="container">
            <div class="form-group">
                <label for="textInput">Enter text to convert to speech:</label>
                <textarea id="textInput" placeholder="Type or paste your text here..."></textarea>
            </div>
            
            <div class="controls">
                <div class="control-group">
                    <label for="backendSelect">TTS Engine:</label>
                    <select id="backendSelect">
                        <option value="pyttsx3">Offline TTS (pyttsx3)</option>
                        <option value="gtts">Google TTS (online)</option>
                    </select>
                </div>
                
                <div class="control-group" id="voiceControl">
                    <label for="voiceSelect">Voice:</label>
                    <select id="voiceSelect">
                        <!-- Voices will be populated by JavaScript -->
                    </select>
                </div>
            </div>
            
            <div class="form-group" id="rateControl">
                <label for="rateRange">Speech Rate: <span id="rateValue">150</span></label>
                <input type="range" id="rateRange" min="50" max="300" value="150">
            </div>
            
            <div class="form-group" id="volumeControl">
                <label for="volumeRange">Volume: <span id="volumeValue">1.0</span></label>
                <input type="range" id="volumeRange" min="0" max="10" value="10" step="1">
            </div>
            
            <button id="speakButton">Convert to Speech</button>
            <button id="downloadButton" class="hidden">Download MP3</button>
            
            <div id="status" class="hidden"></div>
            
            <audio id="audioPlayer" controls class="hidden" style="width: 100%; margin-top: 20px;"></audio>
        </div>
    </div>
    
    <div id="settings" class="tab-content">
        <div class="container">
            <h2>Settings</h2>
            
            <div class="form-group">
                <label for="languageSelect">Language (Google TTS only):</label>
                <select id="languageSelect">
                    <option value="en">English</option>
                    <option value="fr">French</option>
                    <option value="es">Spanish</option>
                    <option value="de">German</option>
                    <option value="it">Italian</option>
                    <option value="ja">Japanese</option>
                    <option value="ko">Korean</option>
                    <option value="zh-CN">Chinese (Simplified)</option>
                    <option value="ru">Russian</option>
                    <option value="pt">Portuguese</option>
                    <option value="hi">Hindi</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>
                    <input type="checkbox" id="autoPlayCheck" checked>
                    Auto-play audio after conversion
                </label>
            </div>
        </div>
    </div>
    
    <div id="about" class="tab-content">
        <div class="container">
            <h2>About this TTS System</h2>
            
            <p>This Text-to-Speech (TTS) system was designed for deployment on lightweight devices like Raspberry Pi. It features:</p>
            
            <ul>
                <li><strong>Offline TTS Engine</strong> - Works without internet using your computer's built-in voices</li>
                <li><strong>Google TTS</strong> - Higher quality voices when internet is available</li>
                <li><strong>Multiple Voices</strong> - Choose from various voices on your system</li>
                <li><strong>Adjustable Parameters</strong> - Control speech rate and volume</li>
                <li><strong>Simple Interface</strong> - Easy to use web interface</li>
            </ul>
            
            <p>This project was created as part of a demonstration of deploying TTS capabilities on resource-constrained devices.</p>
        </div>
    </div>
    
    <footer>
        Text-to-Speech Converter | Raspberry Pi TTS Project
    </footer>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Tab navigation
            const tabs = document.querySelectorAll('.tab');
            const tabContents = document.querySelectorAll('.tab-content');
            
            tabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    const tabId = this.getAttribute('data-tab');
                    
                    // Update active tab
                    tabs.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Update active content
                    tabContents.forEach(content => {
                        content.classList.remove('active');
                    });
                    document.getElementById(tabId).classList.add('active');
                });
            });
            
            // Elements
            const textInput = document.getElementById('textInput');
            const backendSelect = document.getElementById('backendSelect');
            const voiceSelect = document.getElementById('voiceSelect');
            const rateRange = document.getElementById('rateRange');
            const rateValue = document.getElementById('rateValue');
            const volumeRange = document.getElementById('volumeRange');
            const volumeValue = document.getElementById('volumeValue');
            const languageSelect = document.getElementById('languageSelect');
            const autoPlayCheck = document.getElementById('autoPlayCheck');
            const speakButton = document.getElementById('speakButton');
            const downloadButton = document.getElementById('downloadButton');
            const status = document.getElementById('status');
            const audioPlayer = document.getElementById('audioPlayer');
            
            // Voice controls
            const voiceControl = document.getElementById('voiceControl');
            const rateControl = document.getElementById('rateControl');
            const volumeControl = document.getElementById('volumeControl');
            
            // Update displayed values when sliders change
            rateRange.addEventListener('input', function() {
                rateValue.textContent = this.value;
            });
            
            volumeRange.addEventListener('input', function() {
                volumeValue.textContent = (this.value / 10).toFixed(1);
            });
            
            // Load available voices
            function loadVoices() {
                fetch('/voices')
                    .then(response => response.json())
                    .then(data => {
                        voiceSelect.innerHTML = '';
                        data.voices.forEach(voice => {
                            const option = document.createElement('option');
                            option.value = voice.id;
                            option.textContent = voice.name;
                            voiceSelect.appendChild(option);
                        });
                    })
                    .catch(error => {
                        console.error('Error loading voices:', error);
                    });
            }
            
            // Show/hide controls based on selected backend
            backendSelect.addEventListener('change', function() {
                const backend = this.value;
                
                if (backend === 'pyttsx3') {
                    voiceControl.style.display = 'block';
                    rateControl.style.display = 'block';
                    volumeControl.style.display = 'block';
                    loadVoices();
                } else {
                    voiceControl.style.display = 'none';
                    rateControl.style.display = 'none';
                    volumeControl.style.display = 'none';
                }
            });
            
            // Initial load of voices
            loadVoices();
            
            // Convert text to speech
            speakButton.addEventListener('click', function() {
                const text = textInput.value.trim();
                
                if (!text) {
                    showStatus('Please enter some text to convert', 'error');
                    return;
                }
                
                // Show loading status
                showStatus('Converting text to speech...', 'normal');
                audioPlayer.classList.add('hidden');
                downloadButton.classList.add('hidden');
                
                // Prepare request data
                const data = {
                    text: text,
                    backend: backendSelect.value,
                    language: languageSelect.value
                };
                
                // Add pyttsx3-specific parameters
                if (backendSelect.value === 'pyttsx3') {
                    data.voice_id = voiceSelect.value;
                    data.rate = rateRange.value;
                    data.volume = volumeRange.value / 10;
                }
                
                // Send request to server
                fetch('/speak', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show success message
                        showStatus(`Conversion completed in ${data.elapsed_time.toFixed(2)} seconds`, 'success');
                        
                        // Update audio player
                        audioPlayer.src = `/audio/${data.audio_id}`;
                        audioPlayer.classList.remove('hidden');
                        
                        // Set up download button
                        downloadButton.onclick = function() {
                            window.location.href = `/download/${data.audio_id}`;
                        };
                        downloadButton.classList.remove('hidden');
                        
                        // Auto-play if enabled
                        if (autoPlayCheck.checked) {
                            audioPlayer.play();
                        }
                    } else {
                        showStatus(`Error: ${data.error}`, 'error');
                    }
                })
                .catch(error => {
                    showStatus(`Error: ${error.message}`, 'error');
                });
            });
            
            // Helper function to show status messages
            function showStatus(message, type) {
                status.textContent = message;
                status.className = type === 'error' ? 'error' : (type === 'success' ? 'success' : '');
                status.classList.remove('hidden');
            }
        });
    </script>
</body>
</html>
    """)

# Create static folder and files if needed

# Routes
@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/voices')
def voices():
    """Return available voices"""
    voices = tts_engine.get_voices()
    return jsonify({'voices': voices})

@app.route('/speak', methods=['POST'])
def speak():
    """Convert text to speech"""
    data = request.json
    
    if not data or 'text' not in data:
        return jsonify({'success': False, 'error': 'No text provided'})
    
    # Get parameters
    text = data['text']
    backend = data.get('backend', 'pyttsx3')
    language = data.get('language', 'en')
    
    # Create TTS engine with selected backend if needed
    global tts_engine
    if tts_engine.backend != backend or tts_engine.language != language:
        tts_engine = TTSEngine(backend=backend, language=language)
    
    # Get additional parameters for pyttsx3
    voice_id = data.get('voice_id')
    rate = data.get('rate')
    volume = data.get('volume')
    
    # Convert text to speech
    result = tts_engine.speak(text, voice_id, rate, volume)
    
    return jsonify(result)

@app.route('/audio/<audio_id>')
def get_audio(audio_id):
    """Return audio file"""
    # Validate audio_id to prevent directory traversal
    if not audio_id or '..' in audio_id or '/' in audio_id:
        return "Invalid audio ID", 400
    
    audio_path = os.path.join(SAMPLES_DIR, f"{audio_id}.mp3")
    
    if not os.path.exists(audio_path):
        return "Audio file not found", 404
    
    return send_file(audio_path, mimetype='audio/mpeg')

@app.route('/download/<audio_id>')
def download_audio(audio_id):
    """Download audio file"""
    # Validate audio_id to prevent directory traversal
    if not audio_id or '..' in audio_id or '/' in audio_id:
        return "Invalid audio ID", 400
    
    audio_path = os.path.join(SAMPLES_DIR, f"{audio_id}.mp3")
    
    if not os.path.exists(audio_path):
        return "Audio file not found", 404
    
    return send_file(audio_path, 
                    mimetype='audio/mpeg',
                    as_attachment=True,
                    download_name='tts_output.mp3')

if __name__ == '__main__':
    # Run the Flask app
    print("Starting TTS Web Server...")
    print(f"Open http://localhost:5000 in your web browser")
    app.run(host='0.0.0.0', port=5000, debug=True)