#!/usr/bin/env python3
"""
Configure audio devices for Raspberry Pi TTS system
"""

import sounddevice as sd
import subprocess
import os

def configure_audio():
    """Set up audio devices correctly"""
    print("🔧 Configuring audio devices...")
    
    # List all devices
    devices = sd.query_devices()
    
    # Find USB microphone (input)
    usb_mic_id = None
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            name = device['name'].lower()
            if 'usb' in name or 'audio device' in name:
                usb_mic_id = i
                break
    
    # Set environment variables for our scripts
    config = {
        'MIC_DEVICE': f'plughw:{usb_mic_id if usb_mic_id else 3},0',
        'SPEAKER_DEVICE': 'plughw:0,0',
        'SAMPLE_RATE': '16000',
        'CHANNELS': '1'
    }
    
    print(f"✓ Microphone device: {config['MIC_DEVICE']}")
    print(f"✓ Speaker device: {config['SPEAKER_DEVICE']}")
    
    # Test both devices
    print("\n🧪 Testing audio configuration...")
    
    # Test recording
    print("Recording 3 seconds...")
    record_cmd = [
        'arecord', '-D', config['MIC_DEVICE'], 
        '-d', '3', '-r', config['SAMPLE_RATE'], 
        '-c', config['CHANNELS'], 'test_config.wav'
    ]
    
    result = subprocess.run(record_cmd, capture_output=True)
    if result.returncode == 0:
        print("✓ Recording successful")
    else:
        print("❌ Recording failed")
        return False
    
    # Test playback
    print("Playing back...")
    play_cmd = ['aplay', '-D', config['SPEAKER_DEVICE'], 'test_config.wav']
    result = subprocess.run(play_cmd)
    
    if result.returncode == 0:
        print("✓ Playback successful")
        print("🎉 Audio configuration complete!")
        
        # Save config for other scripts
        with open('audio_config.txt', 'w') as f:
            for key, value in config.items():
                f.write(f"{key}={value}\n")
        
        return True
    else:
        print("❌ Playback failed")
        return False

if __name__ == "__main__":
    configure_audio()