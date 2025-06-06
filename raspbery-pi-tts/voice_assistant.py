#!/usr/bin/env python3
"""
Complete Raspberry Pi Voice Assistant
Voice Input → Whisper STT → Ollama LLM → TTS Output
Optimized for maximum speed!
"""

import sounddevice as sd
import soundfile as sf
import whisper
import requests
import subprocess
import numpy as np
import time
import threading
from pathlib import Path
import sys
import termios
import tty
import json
import pyttsx3

class RaspberryPiVoiceAssistant:
    def __init__(self):
        print("🤖 Initializing Raspberry Pi Voice Assistant...")
        
        # Audio settings (optimized from your working setup)
        self.sample_rate = 44100  # Your working sample rate
        self.channels = 1
        self.mic_device_sd = 2    # Your working mic device
        self.speaker_device_alsa = 'plughw:0,0'  # Your working speaker
        
        # Recording state
        self.is_recording = False
        self.recording_data = []
        
        # Conversation memory
        self.conversation_history = []
        self.max_history = 10
        
        # Setup components
        self.setup_directories()
        self.load_whisper()
        self.setup_tts()
        self.test_ollama()
        
        print("✅ Voice Assistant ready!")
    
    def setup_directories(self):
        """Create directory structure"""
        Path("voice_assistant").mkdir(exist_ok=True)
        Path("voice_assistant/recordings").mkdir(exist_ok=True)
        Path("voice_assistant/conversations").mkdir(exist_ok=True)
    
    def load_whisper(self):
        """Load Whisper model for speech recognition"""
        print("🧠 Loading Whisper model...")
        start_time = time.time()
        self.whisper_model = whisper.load_model('tiny')
        load_time = time.time() - start_time
        print(f"✅ Whisper loaded in {load_time:.1f}s")
    
    def setup_tts(self):
        """Setup text-to-speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 180)  # Faster speech
            self.tts_engine.setProperty('volume', 0.9)
            print("✅ TTS engine ready")
        except Exception as e:
            print(f"⚠️  TTS engine failed: {e}")
            self.tts_engine = None
    
    def test_ollama(self):
        """Test Ollama connection"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    self.llm_model = models[0]['name']  # Use first available model
                    print(f"✅ Ollama ready with model: {self.llm_model}")
                else:
                    print("❌ No models found in Ollama!")
                    self.llm_model = None
            else:
                print("❌ Ollama not responding!")
                self.llm_model = None
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            self.llm_model = None
    
    def get_char(self):
        """Get single character input"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch
    
    def audio_callback(self, indata, frames, time, status):
        """Audio recording callback"""
        if self.is_recording:
            self.recording_data.append(indata.copy())
    
    def start_recording(self):
        """Start voice recording"""
        if self.is_recording:
            return
        
        print("🔴 LISTENING... (Press 'S' to stop)")
        self.is_recording = True
        self.recording_data = []
        
        try:
            self.stream = sd.InputStream(
                device=self.mic_device_sd,
                channels=self.channels,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                dtype=np.float32
            )
            self.stream.start()
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            self.is_recording = False
    
    def stop_recording_and_process(self):
        """Stop recording and process the speech"""
        if not self.is_recording:
            return
        
        print("⏹️  Processing your speech...")
        self.is_recording = False
        
        try:
            self.stream.stop()
            self.stream.close()
        except:
            pass
        
        if not self.recording_data:
            print("❌ No audio recorded!")
            return
        
        # Save audio
        recording = np.concatenate(self.recording_data, axis=0)
        timestamp = int(time.time())
        audio_file = f"voice_assistant/recordings/voice_{timestamp}.wav"
        sf.write(audio_file, recording, self.sample_rate)
        
        # Process the speech
        self.process_voice_input(audio_file)
    
    def process_voice_input(self, audio_file):
        """Complete pipeline: Audio → Text → LLM → Speech"""
        try:
            # 1. Speech to Text
            print("🎯 Converting speech to text...")
            start_time = time.time()
            result = self.whisper_model.transcribe(audio_file)
            user_text = result['text'].strip()
            stt_time = time.time() - start_time
            
            print(f"💬 You said: \"{user_text}\" ({stt_time:.1f}s)")
            
            if not user_text:
                print("❌ No speech detected!")
                return
            
            # 2. Send to LLM
            print("🤖 Thinking...")
            start_time = time.time()
            response_text = self.ask_llm(user_text)
            llm_time = time.time() - start_time
            
            print(f"🧠 Assistant: \"{response_text}\" ({llm_time:.1f}s)")
            
            # 3. Convert response to speech
            print("🔊 Speaking response...")
            start_time = time.time()
            self.speak_response(response_text)
            tts_time = time.time() - start_time
            
            # 4. Save conversation
            self.save_conversation(user_text, response_text)
            
            total_time = stt_time + llm_time + tts_time
            print(f"⚡ Total processing time: {total_time:.1f}s")
            print("🎉 Ready for next question!")
            
        except Exception as e:
            print(f"❌ Processing failed: {e}")
    
    def ask_llm(self, user_text):
        """Send question to LLM with conversation memory"""
        if not self.llm_model:
            return "Sorry, the AI model is not available."
        
        try:
            # Build context with recent conversation
            context = self.build_conversation_context()
            full_prompt = f"{context}\nUser: {user_text}\nAssistant:"
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_ctx": 2048  # Limit context for speed
                    }
                },
                timeout=45  # Shorter timeout for speed
            )
            
            if response.status_code == 200:
                return response.json()['response'].strip()
            else:
                return "Sorry, I couldn't process that request."
                
        except requests.exceptions.Timeout:
            return "Sorry, I'm thinking too slowly. Please try again."
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)[:50]}..."
    
    def build_conversation_context(self):
        """Build conversation context from recent history"""
        if not self.conversation_history:
            return "You are a helpful AI assistant running on a Raspberry Pi. Keep responses concise and friendly."
        
        context = "Recent conversation:\n"
        for entry in self.conversation_history[-3:]:  # Last 3 exchanges
            context += f"User: {entry['user']}\nAssistant: {entry['assistant']}\n"
        
        return context
    
    def speak_response(self, text):
        """Convert text to speech and play through earphones"""
        try:
            if self.tts_engine:
                # Method 1: Use pyttsx3 with file output
                timestamp = int(time.time())
                audio_file = f"voice_assistant/response_{timestamp}.wav"
                
                self.tts_engine.save_to_file(text, audio_file)
                self.tts_engine.runAndWait()
                
                # Play through correct device
                subprocess.run([
                    'aplay', '-D', self.speaker_device_alsa, audio_file
                ], capture_output=True)
            else:
                # Method 2: Fallback to espeak
                subprocess.run([
                    'espeak', text, '-s', '180', '-a', '90'
                ])
                
        except Exception as e:
            print(f"⚠️  Speech output failed: {e}")
    
    def save_conversation(self, user_text, assistant_text):
        """Save conversation to memory and file"""
        conversation_entry = {
            'timestamp': time.time(),
            'user': user_text,
            'assistant': assistant_text
        }
        
        # Add to memory
        self.conversation_history.append(conversation_entry)
        
        # Keep only recent conversations
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
        
        # Save to file
        try:
            log_file = f"voice_assistant/conversations/conversation_{int(time.time())}.json"
            with open(log_file, 'w') as f:
                json.dump(conversation_entry, f, indent=2)
        except:
            pass
    
    def show_conversation_history(self):
        """Display recent conversation history"""
        if not self.conversation_history:
            print("📭 No conversation history")
            return
        
        print("\n💭 RECENT CONVERSATION:")
        print("=" * 40)
        for i, entry in enumerate(self.conversation_history[-5:], 1):
            print(f"{i}. You: {entry['user'][:50]}...")
            print(f"   AI: {entry['assistant'][:50]}...")
            print()
        print("=" * 40)
    
    def run(self):
        """Main voice assistant loop"""
        print("\n🎤 RASPBERRY PI VOICE ASSISTANT")
        print("=" * 50)
        print("Commands:")
        print("  L - Start listening")
        print("  S - Stop and process speech")
        print("  H - Show conversation history")
        print("  Q - Quit")
        print("=" * 50)
        
        if not self.llm_model:
            print("⚠️  LLM not available - check Ollama setup!")
        
        try:
            while True:
                print(f"\nReady for command... (L/S/H/Q)")
                key = self.get_char().lower()
                
                if key == 'l':
                    self.start_recording()
                    
                elif key == 's':
                    self.stop_recording_and_process()
                    
                elif key == 'h':
                    self.show_conversation_history()
                    
                elif key == 'q':
                    print("\n👋 Goodbye!")
                    break
                    
                else:
                    print(f"Unknown command: {key}")
                    
        except KeyboardInterrupt:
            print("\n👋 Interrupted! Goodbye!")
        finally:
            try:
                if hasattr(self, 'stream') and self.stream.active:
                    self.stream.stop()
                    self.stream.close()
            except:
                pass

if __name__ == "__main__":
    assistant = RaspberryPiVoiceAssistant()
    assistant.run()