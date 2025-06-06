#!/usr/bin/env python3
"""
Complete setup and troubleshooting script
"""

import subprocess
import requests
import time
import os

def run_command(cmd, description):
    """Run command with description"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
            return True, result.stdout
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False, "Timeout"
    except Exception as e:
        print(f"💥 {description} - ERROR: {e}")
        return False, str(e)

def fix_and_setup():
    print("🛠️  COMPLETE VOICE ASSISTANT SETUP & FIX")
    print("=" * 50)
    
    # 1. Check and start Ollama
    print("\n📋 Step 1: Ollama Setup")
    
    # Check if Ollama is installed
    success, output = run_command("which ollama", "Checking Ollama installation")
    if not success:
        print("❌ Ollama not found! Please install it first:")
        print("curl -fsSL https://ollama.com/install.sh | sh")
        return False
    
    # Start Ollama service
    success, output = run_command("sudo systemctl start ollama", "Starting Ollama service")
    time.sleep(5)  # Give it time to start
    
    # Enable auto-start
    run_command("sudo systemctl enable ollama", "Enabling Ollama auto-start")
    
    # Check if Ollama is responding
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            print("✅ Ollama is responding")
            models = response.json().get('models', [])
            print(f"📦 Found {len(models)} models: {[m['name'] for m in models]}")
        else:
            print("❌ Ollama not responding properly")
            return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False
    
    # 2. Download fast model if needed
    print("\n📋 Step 2: Model Setup")
    
    fast_models = ['llama3.2:1b', 'phi3:mini', 'gemma:2b']
    has_fast_model = any(m['name'] in fast_models for m in models)
    
    if not has_fast_model:
        print("🔄 Downloading fast model (llama3.2:1b)...")
        print("   This will take 5-15 minutes depending on internet speed...")
        
        success, output = run_command("ollama pull llama3.2:1b", "Downloading llama3.2:1b")
        if not success:
            print("❌ Model download failed!")
            return False
    else:
        print("✅ Fast model already available")
    
    # 3. Test audio system
    print("\n📋 Step 3: Audio System Test")
    
    # Test recording
    success, output = run_command(
        "arecord -D plughw:3,0 -d 1 -f S16_LE -r 44100 -c 1 test_audio.wav",
        "Testing audio recording"
    )
    if not success:
        print("❌ Audio recording failed! Check your USB microphone.")
        return False
    
    # Test playback
    success, output = run_command(
        "aplay -D plughw:0,0 test_audio.wav",
        "Testing audio playback"
    )
    if not success:
        print("⚠️  Audio playback failed, but continuing...")
    
    # 4. Test Whisper
    print("\n📋 Step 4: Whisper Test")
    
    try:
        import whisper
        model = whisper.load_model('tiny')
        print("✅ Whisper model loaded successfully")
    except Exception as e:
        print(f"❌ Whisper test failed: {e}")
        return False
    
    # 5. End-to-end test
    print("\n📋 Step 5: Complete System Test")
    
    try:
        # Quick LLM test
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": "Say hello in exactly 5 words",
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            ai_response = response.json()['response']
            print(f"✅ LLM test successful: '{ai_response[:50]}...'")
        else:
            print("❌ LLM test failed")
            return False
            
    except Exception as e:
        print(f"❌ LLM test error: {e}")
        return False
    
    # 6. Performance check
    print("\n📋 Step 6: Performance Check")
    
    import psutil
    
    # Check system resources
    memory = psutil.virtual_memory()
    print(f"💾 Memory: {memory.percent:.1f}% used ({memory.available // 1024 // 1024} MB available)")
    
    if memory.percent > 80:
        print("⚠️  High memory usage! Consider closing other applications.")
    
    try:
        with open('/sys/class/thermal/thermal_zone0/temp') as f:
            temp = float(f.read()) / 1000
            print(f"🌡️  CPU Temperature: {temp:.1f}°C")
            
            if temp > 70:
                print("⚠️  High CPU temperature! Ensure good cooling.")
    except:
        pass
    
    print("\n🎉 SETUP COMPLETE!")
    print("✅ All systems are ready!")
    print("\nNext steps:")
    print("1. Run: python3 quick_voice_test.py")
    print("2. Then: python3 voice_assistant.py")
    
    return True

if __name__ == "__main__":
    success = fix_and_setup()
    if not success:
        print("\n❌ Setup failed! Check the errors above.")
    else:
        print("\n🚀 Ready to go!")