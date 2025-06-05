#!/usr/bin/env python3
"""
Audio Hardware Test for Raspberry Pi
Tests USB mic input + 3.5mm output setup
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import os
from pathlib import Path

class AudioTester:
    def __init__(self):
        self.sample_rate = 16000  # Good for speech recognition
        self.channels = 1         # Mono for speech
        self.setup_directories()
        
    def setup_directories(self):
        """Create directories for audio files"""
        Path("audio_tests").mkdir(exist_ok=True)
        Path("audio_tests/recordings").mkdir(exist_ok=True)
        
    def list_audio_devices(self):
        """Show all available audio devices"""
        print("\n🎤 AUDIO DEVICES DETECTED:")
        print("=" * 50)
        devices = sd.query_devices()
        
        print("INPUT DEVICES:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"  {i}: {device['name']} (Channels: {device['max_input_channels']})")
                
        print("\nOUTPUT DEVICES:")
        for i, device in enumerate(devices):
            if device['max_output_channels'] > 0:
                print(f"  {i}: {device['name']} (Channels: {device['max_output_channels']})")
        print("=" * 50)
        
        return devices
    
    def test_microphone(self, device_id=None, duration=5):
        """Test microphone recording"""
        print(f"\n🎙️  Testing microphone recording ({duration} seconds)...")
        print("Speak into your microphone now!")
        
        try:
            # Record audio
            recording = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                device=device_id,
                dtype=np.float32
            )
            sd.wait()  # Wait until recording is finished
            
            # Save recording
            filename = f"audio_tests/recordings/mic_test_{int(time.time())}.wav"
            sf.write(filename, recording, self.sample_rate)
            
            # Analyze recording
            volume = np.sqrt(np.mean(recording**2))
            max_volume = np.max(np.abs(recording))
            
            print(f"✓ Recording saved: {filename}")
            print(f"✓ Average volume: {volume:.4f}")
            print(f"✓ Peak volume: {max_volume:.4f}")
            
            if max_volume < 0.01:
                print("⚠️  Very quiet recording - check mic levels!")
            elif max_volume > 0.95:
                print("⚠️  Recording might be clipped - reduce mic gain!")
            else:
                print("✓ Recording levels look good!")
                
            return filename, True
            
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return None, False
    
    def test_playback(self, filename):
        """Test audio playback through 3.5mm"""
        print(f"\n🔊 Testing playback through 3.5mm jack...")
        print("You should hear the recording in your earphones!")
        
        try:
            # Load and play audio
            data, sample_rate = sf.read(filename)
            sd.play(data, sample_rate)
            sd.wait()  # Wait until playback is finished
            
            print("✓ Playback completed!")
            return True
            
        except Exception as e:
            print(f"❌ Playback failed: {e}")
            return False
    
    def find_best_input_device(self):
        """Find the best input device (likely your USB mic)"""
        devices = sd.query_devices()
        
        # Look for USB devices first
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                name = device['name'].lower()
                if 'usb' in name or 'microphone' in name or 'mic' in name:
                    print(f"🎯 Found likely microphone: {device['name']} (Device {i})")
                    return i
        
        # Fallback to default input
        try:
            default_input = sd.default.device[0]
            print(f"📍 Using default input device: {devices[default_input]['name']}")
            return default_input
        except:
            return None
    
    def run_complete_test(self):
        """Run complete audio system test"""
        print("🧪 RASPBERRY PI AUDIO SYSTEM TEST")
        print("=" * 50)
        
        # List devices
        devices = self.list_audio_devices()
        
        # Find best microphone
        mic_device = self.find_best_input_device()
        if mic_device is None:
            print("❌ No suitable microphone found!")
            return False
        
        # Test recording
        filename, record_success = self.test_microphone(mic_device, duration=3)
        if not record_success:
            return False
        
        # Test playback
        playback_success = self.test_playback(filename)
        
        # Final result
        if record_success and playback_success:
            print("\n🎉 AUDIO SYSTEM TEST PASSED!")
            print("✓ USB microphone working")
            print("✓ 3.5mm output working") 
            print("✓ Ready for speech recognition!")
            return True
        else:
            print("\n❌ AUDIO SYSTEM TEST FAILED!")
            return False

if __name__ == "__main__":
    tester = AudioTester()
    tester.run_complete_test()