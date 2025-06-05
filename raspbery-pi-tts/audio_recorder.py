#!/usr/bin/env python3
"""
Keyboard-Controlled Audio Recorder
Press 'L' to start recording, 'S' to stop
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import threading
from pathlib import Path
import sys
import termios
import tty
import select

class KeyboardRecorder:
    def __init__(self):
        self.sample_rate = 16000
        self.channels = 1
        self.is_recording = False
        self.recording_data = []
        self.setup_directories()
        self.find_microphone()
        
    def setup_directories(self):
        """Create directory structure"""
        Path("audio_tests/recordings").mkdir(parents=True, exist_ok=True)
        
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
            
        print("🔴 RECORDING... (Press 'S' to stop)")
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
    
    def stop_recording(self):
        """Stop recording and save file"""
        if not self.is_recording:
            print("⚠️  Not currently recording!")
            return None
            
        print("⏹️  Stopping recording...")
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
        
        return filename
    
    def run(self):
        """Main recording loop"""
        print("🎤 KEYBOARD-CONTROLLED AUDIO RECORDER")
        print("=" * 40)
        print("Commands:")
        print("  L - Start recording")
        print("  S - Stop recording")
        print("  Q - Quit")
        print("=" * 40)
        
        try:
            while True:
                print("\nWaiting for command... (L/S/Q)")
                key = self.get_char().lower()
                
                if key == 'l':
                    self.start_recording()
                elif key == 's':
                    filename = self.stop_recording()
                    if filename:
                        # Play back the recording
                        print("🔊 Playing back recording...")
                        data, sr = sf.read(filename)
                        sd.play(data, sr)
                        sd.wait()
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
    recorder = KeyboardRecorder()
    recorder.run()