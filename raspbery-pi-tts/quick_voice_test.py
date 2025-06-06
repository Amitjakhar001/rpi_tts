#!/usr/bin/env python3
"""
Quick voice assistant test - single interaction
"""

import subprocess
import whisper
import requests
import time

def quick_test():
    print("🚀 QUICK VOICE TEST")
    
    # Record
    print("🎤 Recording 5 seconds... SPEAK NOW!")
    subprocess.run([
        'arecord', '-D', 'plughw:3,0',
        '-d', '5', '-r', '44100', '-c', '1',
        'quick_test.wav'
    ])
    
    # Transcribe
    print("🧠 Transcribing...")
    model = whisper.load_model('tiny')
    result = model.transcribe('quick_test.wav')
    user_text = result['text'].strip()
    print(f"💬 You said: \"{user_text}\"")
    
    # LLM
    print("🤖 Getting AI response...")
    start_time = time.time()
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",  # Fastest model
                "prompt": f"Respond briefly to: {user_text}",
                "stream": False
            },
            timeout=30
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            ai_response = response.json()['response']
            print(f"🤖 AI says: \"{ai_response}\"")
            print(f"⚡ Response time: {response_time:.1f} seconds")
            
            # Speak response
            subprocess.run(['espeak', ai_response, '-s', '180'])
            
        else:
            print("❌ AI request failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()