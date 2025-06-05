#!/usr/bin/env python3
"""
Keyboard-Controlled Audio Recorder for Raspberry Pi
Press 'L' to start recording, 'S' to stop
Uses correct devices: USB mic (plughw:3,0) + 3.5mm output (plughw:0,0)
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
import subprocess
import os

class KeyboardRecorder:
    def __init__(self):
        self.sample_rate = 16000  # Good for speech recognition
        self.channels = 1         # Mono for speech
        self.is_recording = False
        self.recording_data = []
        self.setup_directories()
        self.configure_audio_devices()
        
    def setup_directories(self):
        """Create directory structure"""
        Path("audio_tests").mkdir(exist_ok=True)
        Path("audio_tests/recordings").mkdir(exist_ok=True)
        print("✓ Directories created")
        
    def configure_audio_devices(self):
        """Configure audio devices for Raspberry Pi"""
        print("🔧 Configuring audio devices...")
        
        # Your specific device configuration
        self.mic_device_alsa = 'plughw:3,0'      # USB mic for ALSA commands
        self.speaker_device_alsa = 'plughw:0,0'   # 3.5mm jack for ALSA commands
        
        # Find corresponding sounddevice IDs
        devices = sd.query_devices()
        self.mic_device_sd = None
        
        print("\n🎤 Available audio devices:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  Input {i}: {device['name']} (Channels: {device['max_input_channels']})")
                # Look for USB audio device
                if 'usb' in device['name'].lower() or 'audio device' in device['name'].lower():
                    self.mic_device_sd = i
                    
        if self.mic_device_sd is None:
            # Fallback to default or device 3
            try:
                if len([d for d in devices if d['max_input_channels'] > 0]) > 3:
                    self.mic_device_sd = 3
                else:
                    self.mic_device_sd = sd.default.device[0]
            except:
                self.mic_device_sd = None
        
        print(f"✓ Using microphone: Device {self.mic_device_sd}")
        print(f"✓ Using speaker: {self.speaker_device_alsa}")
    
    def get_char(self):
        """Get single character input without pressing Enter"""
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
        if status:
            print(f"Audio status: {status}")
        if self.is_recording:
            self.recording_data.append(indata.copy())
    
    def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            print("⚠️  Already recording!")
            return
        
        if self.mic_device_sd is None:
            print("❌ No microphone device found!")
            return
            
        print("🔴 RECORDING... (Press 'S' to stop)")
        print("    Speak into your USB microphone now!")
        
        self.is_recording = True
        self.recording_data = []
        
        try:
            # Start audio stream with your USB mic
            self.stream = sd.InputStream(
                device=self.mic_device_sd,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                dtype=np.float32,
                blocksize=1024
            )
            self.stream.start()
            print("✓ Recording stream started")
            
        except Exception as e:
            print(f"❌ Failed to start recording: {e}")
            self.is_recording = False
    
    def stop_recording(self):
        """Stop recording and save file"""
        if not self.is_recording:
            print("⚠️  Not currently recording!")
            return None
            
        print("⏹️  Stopping recording...")
        self.is_recording = False
        
        try:
            self.stream.stop()
            self.stream.close()
        except:
            pass
        
        if not self.recording_data:
            print("❌ No audio data recorded!")
            return None
        
        # Combine all recorded chunks
        recording = np.concatenate(self.recording_data, axis=0)
        
        # Save to file
        timestamp = int(time.time())
        filename = f"audio_tests/recordings/recording_{timestamp}.wav"
        
        try:
            sf.write(filename, recording, self.sample_rate)
        except Exception as e:
            print(f"❌ Failed to save recording: {e}")
            return None
        
        # Analysis
        duration = len(recording) / self.sample_rate
        volume = np.sqrt(np.mean(recording**2))
        max_volume = np.max(np.abs(recording))
        
        print(f"✓ Recording saved: {filename}")
        print(f"✓ Duration: {duration:.1f} seconds")
        print(f"✓ Average volume: {volume:.4f}")
        print(f"✓ Peak volume: {max_volume:.4f}")
        
        # Check recording quality
        if max_volume < 0.01:
            print("⚠️  Very quiet recording - speak louder or move closer to mic!")
        elif max_volume > 0.95:
            print("⚠️  Recording might be clipped - speak softer or move away from mic!")
        else:
            print("✓ Recording levels look good!")
        
        return filename
    
    def play_recording(self, filename):
        """Play recording through 3.5mm jack using aplay"""
        if not os.path.exists(filename):
            print(f"❌ File not found: {filename}")
            return False
        
        print("🔊 Playing back recording through earphones...")
        
        try:
            # Use aplay with correct device for 3.5mm output
            result = subprocess.run([
                'aplay', '-D', self.speaker_device_alsa, filename
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✓ Playback completed!")
                return True
            else:
                print(f"❌ Playback failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Playback timed out")
            return False
        except Exception as e:
            print(f"❌ Playback error: {e}")
            return False
    
    def test_audio_system(self):
        """Test the complete audio system"""
        print("\n🧪 Testing audio system...")
        
        # Test recording capability
        try:
            devices = sd.query_devices()
            if self.mic_device_sd is not None:
                device_info = devices[self.mic_device_sd]
                print(f"✓ Microphone device: {device_info['name']}")
            else:
                print("❌ No microphone device configured")
                return False
        except Exception as e:
            print(f"❌ Device test failed: {e}")
            return False
        
        # Test ALSA recording
        print("Testing ALSA recording...")
        try:
            result = subprocess.run([
                'arecord', '-D', self.mic_device_alsa,
                '-d', '1', '-r', str(self.sample_rate), '-c', str(self.channels),
                'audio_tests/test_alsa.wav'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                print("✓ ALSA recording works")
                
                # Test ALSA playback
                result = subprocess.run([
                    'aplay', '-D', self.speaker_device_alsa,
                    'audio_tests/test_alsa.wav'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    print("✓ ALSA playback works")
                    print("🎉 Audio system test passed!")
                    return True
                else:
                    print(f"❌ ALSA playback failed: {result.stderr}")
            else:
                print(f"❌ ALSA recording failed: {result.stderr}")
        except Exception as e:
            print(f"❌ ALSA test failed: {e}")
        
        return False
    
    def show_status(self):
        """Show current system status"""
        print(f"\n📊 SYSTEM STATUS:")
        print(f"Recording: {'🔴 YES' if self.is_recording else '⚪ NO'}")
        print(f"Sample Rate: {self.sample_rate} Hz")
        print(f"Channels: {self.channels}")
        print(f"Microphone: Device {self.mic_device_sd} ({self.mic_device_alsa})")
        print(f"Speaker: {self.speaker_device_alsa}")
        
        # Show recent recordings
        recordings_dir = Path("audio_tests/recordings")
        if recordings_dir.exists():
            recordings = list(recordings_dir.glob("*.wav"))
            if recordings:
                print(f"Recent recordings: {len(recordings)} files")
                latest = max(recordings, key=os.path.getctime)
                print(f"Latest: {latest.name}")
            else:
                print("No recordings found")
    
    def run(self):
        """Main recording loop"""
        print("🎤 KEYBOARD-CONTROLLED AUDIO RECORDER")
        print("=" * 50)
        print("Hardware Configuration:")
        print(f"  📍 Microphone: USB Audio Device (card 3)")
        print(f"  📍 Output: 3.5mm Jack (card 0)")
        print()
        print("Commands:")
        print("  L - Start recording")
        print("  S - Stop recording and playback")
        print("  T - Test audio system")
        print("  I - Show system info")
        print("  Q - Quit")
        print("=" * 50)
        
        # Initial audio test
        if not self.test_audio_system():
            print("⚠️  Audio system test failed, but you can still try recording...")
        
        try:
            while True:
                print(f"\nWaiting for command... (L/S/T/I/Q)")
                key = self.get_char().lower()
                
                if key == 'l':
                    self.start_recording()
                    
                elif key == 's':
                    filename = self.stop_recording()
                    if filename:
                        # Automatically play back the recording
                        self.play_recording(filename)
                        
                elif key == 't':
                    self.test_audio_system()
                    
                elif key == 'i':
                    self.show_status()
                    
                elif key == 'q':
                    print("\n👋 Goodbye!")
                    break
                    
                elif key == '\x03':  # Ctrl+C
                    print("\n👋 Interrupted! Goodbye!")
                    break
                    
                else:
                    print(f"Unknown command: '{key}' (Use L/S/T/I/Q)")
                    
        except KeyboardInterrupt:
            print("\n👋 Interrupted! Goodbye!")
        finally:
            # Cleanup
            if hasattr(self, 'stream') and hasattr(self.stream, 'active'):
                try:
                    if self.stream.active:
                        self.stream.stop()
                        self.stream.close()
                except:
                    pass
            print("✓ Cleanup complete")

if __name__ == "__main__":
    recorder = KeyboardRecorder()
    recorder.run()