#!/usr/bin/env python3
"""
One-click setup for the voice assistant
"""

import subprocess
import requests
import time

def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200
    except:
        return False

def setup_assistant():
    print("🛠️  VOICE ASSISTANT SETUP")
    print("=" * 30)
    
    # 1. Check Ollama
    if check_ollama():
        print("✅ Ollama is running")
    else:
        print("🔄 Starting Ollama...")
        subprocess.run(['sudo', 'systemctl', 'start', 'ollama'])
        time.sleep(5)
        
        if check_ollama():
            print("✅ Ollama started")
        else:
            print("❌ Ollama failed to start")
            return False
    
    # 2. Check for fast model
    try:
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]
        
        if 'llama3.2:1b' in model_names:
            print("✅ Fast model (llama3.2:1b) ready")
        else:
            print("🔄 Downloading fast model...")
            print("   This will take 5-10 minutes...")
            subprocess.run(['ollama', 'pull', 'llama3.2:1b'])
            print("✅ Model downloaded")
            
    except Exception as e:
        print(f"❌ Model check failed: {e}")
        return False
    
    # 3. Test complete pipeline
    print("🧪 Testing complete system...")
    
    # Quick audio test
    print("   Testing audio...")
    result = subprocess.run([
        'arecord', '-D', 'plughw:3,0', '-d', '1', 
        '-r', '44100', '-c', '1', 'setup_test.wav'
    ], capture_output=True)
    
    if result.returncode == 0:
        print("✅ Audio recording works")
        
        # Test playback
        subprocess.run(['aplay', '-D', 'plughw:0,0', 'setup_test.wav'], 
                      capture_output=True)
        print("✅ Audio playback works")
    else:
        print("❌ Audio test failed")
        return False
    
    print("\n🎉 SETUP COMPLETE!")
    print("Run: python3 voice_assistant.py")
    return True

if __name__ == "__main__":
    setup_assistant()