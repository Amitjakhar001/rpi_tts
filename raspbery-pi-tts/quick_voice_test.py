#!/usr/bin/env python3
"""
Quick voice assistant test - single interaction
FIXED VERSION with better audio quality and error handling
"""

import subprocess
import whisper
import requests
import time
import sys

def check_ollama():
    """Check if Ollama is accessible"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama is running with {len(models)} models")
            return True, models
        else:
            print("❌ Ollama not responding properly")
            return False, []
    except Exception as e:
        print(f"❌ Ollama not accessible: {e}")
        return False, []

def quick_test():
    print("🚀 QUICK VOICE TEST (IMPROVED)")
    
    # Check Ollama first
    ollama_ok, models = check_ollama()
    if not ollama_ok:
        print("Please start Ollama first:")
        print("  sudo systemctl start ollama")
        print("  ollama pull llama3.2:1b")
        return
    
    if not models:
        print("No models found! Please download a model:")
        print("  ollama pull llama3.2:1b")
        return
    
    model_name = models[0]['name']
    print(f"🤖 Using model: {model_name}")
    
    # Record with better quality
    print("🎤 Recording 5 seconds... SPEAK NOW!")
    record_cmd = [
        'arecord', '-D', 'plughw:3,0',
        '-d', '5', 
        '-f', 'S16_LE',  # 16-bit audio
        '-r', '44100', 
        '-c', '1',
        'quick_test.wav'
    ]
    
    result = subprocess.run(record_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Recording failed: {result.stderr}")
        return
    
    print("✅ Recording completed")
    
    # Transcribe
    print("🧠 Transcribing...")
    try:
        model = whisper.load_model('tiny')
        result = model.transcribe('quick_test.wav')
        user_text = result['text'].strip()
        print(f"💬 You said: \"{user_text}\"")
        
        if not user_text:
            print("❌ No speech detected! Try speaking louder.")
            return
            
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return
    
    # LLM with better error handling
    print("🤖 Getting AI response...")
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": f"Respond briefly in 1-2 sentences to: {user_text}",
                "stream": False,
                "options": {
                    "num_ctx": 1024,  # Smaller context for speed
                    "temperature": 0.7
                }
            },
            timeout=60  # Longer timeout
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            ai_response = response.json()['response'].strip()
            print(f"🤖 AI says: \"{ai_response}\"")
            print(f"⚡ Response time: {response_time:.1f} seconds")
            
            # Speak response using correct audio device
            print("🔊 Speaking response...")
            speak_cmd = ['espeak', ai_response, '-s', '180', '-a', '90']
            subprocess.run(speak_cmd)
            
            print("✅ Test completed successfully!")
            
        else:
            print(f"❌ AI request failed: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ AI response timed out (>60s). The model might be too slow.")
        print("Try a smaller/faster model: ollama pull llama3.2:1b")
    except Exception as e:
        print(f"❌ AI request error: {e}")

if __name__ == "__main__":
    quick_test()