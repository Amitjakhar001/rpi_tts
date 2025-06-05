#!/usr/bin/env python3
"""
Simple audio test using correct devices
"""

import subprocess
import time

def record_and_play():
    """Record from USB mic and play through 3.5mm"""
    print("🎤 Recording 5 seconds from USB mic...")
    
    # Record using correct device
    record_cmd = [
        'arecord', '-D', 'plughw:3,0',
        '-d', '5', '-r', '16000', '-c', '1',
        'simple_test.wav'
    ]
    
    subprocess.run(record_cmd)
    print("✓ Recording complete!")
    
    print("🔊 Playing back through 3.5mm jack...")
    # Play using correct device
    play_cmd = ['aplay', '-D', 'plughw:0,0', 'simple_test.wav']
    subprocess.run(play_cmd)
    
    print("✓ Test complete!")

if __name__ == "__main__":
    record_and_play()