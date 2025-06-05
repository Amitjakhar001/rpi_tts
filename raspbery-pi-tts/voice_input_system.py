#!/usr/bin/env python3
"""
Complete Voice Input System
L = Start Recording, S = Stop & Transcribe
"""

import sounddevice as sd
import soundfile as sf
import whisper
import numpy as np
import time
import threading
from pathlib import Path
import sys
import termios
import tty

class VoiceInputSystem:
    def __init__(self, model_size='tiny'):
        print("🎤 Initializing Voice Input System...")
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.is_recording = False
        self.recording_data = []
        
        # Setup
        self.setup_directories()
        self.find_microphone()
        self.load_stt_model(model_size)
        
        print("✓ Voice Input System ready!")
    
    def setup_directories(self):
        """Create directory structure"""
        Path("audio_tests/recordings").mkdir(parents=True, exist_ok=True)
        Path("audio_tests/transcriptions").mkdir(parents=True, exist_ok=True)
    
    def find_microphone(self):
        """Find the best microphone device"""
        devices = sd.query_devices()
        self.mic_device = None
        
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                name = device['name'].lower()
                if 'usb' in name or 'microphone' in name or 'mic' in name:
                    self.mic_device = i
                    print(f"🎤 Using microphone: {device['name']}")
                    break
        
        if self.mic_device is None:
            self.mic_device = sd.default.device[0]
            print(f"📍 Using default input device")
    
    def load_stt_model(self, model_size):
        """Load Whisper model"""
        print(f"🧠 Loading Whisper model '{model_size}'...")
        start_time = time.time()
        self.stt_model = whisper.load_model(model_size)
        load_time = time.time() - start_time
        print(f"✓ Model loaded in {load_time:.1f} seconds")
    
    def get_char(self):
        """Get single character input without Enter"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    def audio_callback(self, indata, frames, time, status):
        """Callback function for audio recording"""
        if self.is_recording:
            self.recording_data.append(indata.copy())
    
    def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            print("⚠️  Already recording!")
            return
            
        print("🔴 RECORDING... (Press 'S' to stop and transcribe)")
        self.is_recording = True
        self.recording_data = []
        
        # Start audio stream
        self.stream = sd.InputStream(
            device=self.mic_device,
            channels=self.channels,
            samplerate=self.sample_rate,
            callback=self.audio_callback,
            dtype=np.float32
        )
        self.stream.start()
    
    def stop_and_transcribe(self):
        """Stop recording and transcribe immediately"""
        if not self.is_recording:
            print("⚠️  Not currently recording!")
            return None
            
        print("⏹️  Stopping recording and transcribing...")
        self.is_recording = False
        self.stream.stop()
        self.stream.close()
        
        if not self.recording_data:
            print("❌ No audio data recorded!")
            return None
        
        # Combine all recorded chunks
        recording = np.concatenate(self.recording_data, axis=0)
        
        # Save to file
        timestamp = int(time.time())
        filename = f"audio_tests/recordings/recording_{timestamp}.wav"
        sf.write(filename, recording, self.sample_rate)
        
        # Analysis
        duration = len(recording) / self.sample_rate
        volume = np.sqrt(np.mean(recording**2))
        
        print(f"✓ Recording saved: {filename}")
        print(f"✓ Duration: {duration:.1f} seconds")
        print(f"✓ Average volume: {volume:.4f}")
        
        # Transcribe immediately
        print("🧠 Transcribing...")
        transcribe_start = time.time()
        
        try:
            result = self.stt_model.transcribe(filename)
            transcribe_time = time.time() - transcribe_start
            
            text = result['text'].strip()
            language = result['language']
            
            print(f"✓ Transcription completed in {transcribe_time:.1f} seconds")
            print(f"📝 Language: {language}")
            print(f"💬 TRANSCRIPTION: \"{text}\"")
            
            # Save transcription
            self.save_transcription(filename, text, language, transcribe_time)
            
            return {
                'text': text,
                'language': language,
                'audio_file': filename,
                'duration': duration,
                'processing_time': transcribe_time
            }
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None
    
    def save_transcription(self, audio_file, text, language, processing_time):
        """Save transcription to file"""
        timestamp = int(time.time())
        filename = f"audio_tests/transcriptions/transcription_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Audio File: {audio_file}\n")
            f.write(f"Language: {language}\n")
            f.write(f"Processing Time: {processing_time:.1f}s\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write("-" * 50 + "\n")
            f.write(f"Transcription:\n{text}\n")
        
        print(f"💾 Transcription saved: {filename}")
    
    def run(self):
        """Main loop"""
        print("\n🎤 VOICE INPUT SYSTEM")
        print("=" * 50)
        print("Commands:")
        print("  L - Start recording")
        print("  S - Stop recording and transcribe")
        print("  Q - Quit")
        print("=" * 50)
        
        try:
            while True:
                print(f"\nWaiting for command... (L/S/Q)")
                key = self.get_char().lower()
                
                if key == 'l':
                    self.start_recording()
                elif key == 's':
                    result = self.stop_and_transcribe()
                    if result:
                        print(f"\n🎯 READY FOR NEXT RECORDING!")
                elif key == 'q':
                    print("👋 Goodbye!")
                    break
                else:
                    print(f"Unknown command: {key}")
                    
        except KeyboardInterrupt:
            print("\n👋 Interrupted! Goodbye!")
        finally:
            if hasattr(self, 'stream') and self.stream.active:
                self.stream.stop()
                self.stream.close()

if __name__ == "__main__":
    system = VoiceInputSystem('tiny')  # Use 'base' for better accuracy
    system.run()