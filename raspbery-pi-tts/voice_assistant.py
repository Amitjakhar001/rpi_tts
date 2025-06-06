#!/usr/bin/env python3
"""
Complete Raspberry Pi Voice Assistant - WORKING VERSION
Voice Input → Whisper STT → Ollama LLM → Espeak TTS
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

class RaspberryPiVoiceAssistant:
    def __init__(self):
        print("🤖 Initializing Raspberry Pi Voice Assistant...")
        
        # Audio settings (from your working setup)
        self.sample_rate = 44100
        self.channels = 1
        self.mic_device_sd = 2    # Your working mic device
        
        # Recording state
        self.is_recording = False
        self.recording_data = []
        
        # Conversation memory
        self.conversation_history = []
        self.max_history = 5  # Keep last 5 exchanges
        
        # Setup components
        self.setup_directories()
        self.load_whisper()
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
    
    def test_ollama(self):
        """Test Ollama connection"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    self.llm_model = models[0]['name']
                    print(f"✅ Ollama ready with model: {self.llm_model}")
                    return True
                else:
                    print("❌ No models found in Ollama!")
                    self.llm_model = None
                    return False
            else:
                print("❌ Ollama not responding!")
                self.llm_model = None
                return False
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            self.llm_model = None
            return False
    
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
            print("⚠️  Already recording!")
            return
        
        print("🔴 LISTENING... (Press 'S' to stop)")
        print("    Speak clearly into your microphone!")
        
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
            print("✅ Recording started")
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            self.is_recording = False
    
    def stop_recording_and_process(self):
        """Stop recording and process the speech"""
        if not self.is_recording:
            print("⚠️  Not currently recording!")
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
        
        # Analyze recording quality
        volume = np.sqrt(np.mean(recording**2))
        if volume < 0.01:
            print("⚠️  Very quiet recording - try speaking louder!")
        
        # Process the speech
        self.process_voice_input(audio_file)
    
    def process_voice_input(self, audio_file):
        """Complete pipeline: Audio → Text → LLM → Speech"""
        total_start = time.time()
        
        try:
            # 1. Speech to Text
            print("🎯 Converting speech to text...")
            stt_start = time.time()
            result = self.whisper_model.transcribe(audio_file)
            user_text = result['text'].strip()
            stt_time = time.time() - stt_start
            
            print(f"💬 You said: \"{user_text}\" ({stt_time:.1f}s)")
            
            if not user_text or len(user_text) < 2:
                print("❌ No clear speech detected! Try speaking louder or closer to the mic.")
                return
            
            # 2. Send to LLM
            print("🤖 AI is thinking...")
            llm_start = time.time()
            response_text = self.ask_llm(user_text)
            llm_time = time.time() - llm_start
            
            print(f"🧠 AI responds: \"{response_text[:80]}{'...' if len(response_text) > 80 else ''}\" ({llm_time:.1f}s)")
            
            # 3. Convert response to speech
            print("🔊 Speaking response...")
            tts_start = time.time()
            self.speak_response(response_text)
            tts_time = time.time() - tts_start
            
            # 4. Save conversation
            self.save_conversation(user_text, response_text)
            
            total_time = time.time() - total_start
            print(f"⚡ Total time: {total_time:.1f}s (STT: {stt_time:.1f}s, LLM: {llm_time:.1f}s, TTS: {tts_time:.1f}s)")
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
            
            # Create optimized prompt
            if context:
                full_prompt = f"{context}\nHuman: {user_text}\nAssistant: "
            else:
                full_prompt = f"You are a helpful AI assistant. Respond briefly and naturally.\nHuman: {user_text}\nAssistant: "
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.llm_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_ctx": 1024,  # Small context for speed
                        "num_predict": 100,  # Limit response length
                        "stop": ["\nHuman:", "\nUser:"]  # Stop at next turn
                    }
                },
                timeout=45
            )
            
            if response.status_code == 200:
                ai_response = response.json()['response'].strip()
                # Clean up the response
                ai_response = ai_response.replace("Assistant:", "").strip()
                return ai_response
            else:
                return "Sorry, I couldn't process that request."
                
        except requests.exceptions.Timeout:
            return "Sorry, I'm thinking too slowly. Please try again."
        except Exception as e:
            return f"Sorry, I encountered an error."
    
    def build_conversation_context(self):
        """Build conversation context from recent history"""
        if not self.conversation_history:
            return ""
        
        context = "Previous conversation:\n"
        for entry in self.conversation_history[-2:]:  # Last 2 exchanges for speed
            context += f"Human: {entry['user']}\nAssistant: {entry['assistant']}\n"
        
        return context
    
    def speak_response(self, text):
        """Convert text to speech using espeak (works reliably)"""
        try:
            # Use espeak for reliable TTS output
            # Optimize espeak parameters for natural speech
            espeak_cmd = [
                'espeak',
                text,
                '-s', '170',  # Speed (words per minute)
                '-a', '80',   # Amplitude (volume)
                '-p', '50',   # Pitch
                '-g', '10'    # Gap between words
            ]
            
            subprocess.run(espeak_cmd, timeout=30)
            
        except subprocess.TimeoutExpired:
            print("⚠️  Speech output timed out")
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
        
        # Keep only recent conversations for performance
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
        print("=" * 50)
        for i, entry in enumerate(self.conversation_history, 1):
            user_text = entry['user'][:60] + "..." if len(entry['user']) > 60 else entry['user']
            ai_text = entry['assistant'][:60] + "..." if len(entry['assistant']) > 60 else entry['assistant']
            
            print(f"{i}. You: {user_text}")
            print(f"   AI:  {ai_text}")
            print()
        print("=" * 50)
    
    def show_system_status(self):
        """Show system status"""
        print(f"\n📊 SYSTEM STATUS:")
        print(f"🎤 Microphone: Device {self.mic_device_sd}")
        print(f"🧠 LLM Model: {self.llm_model}")
        print(f"💭 Conversation History: {len(self.conversation_history)} exchanges")
        print(f"🔊 TTS: espeak")
        
        # Show memory usage
        try:
            import psutil
            memory = psutil.virtual_memory()
            print(f"💾 Memory: {memory.percent:.1f}% used")
            
            with open('/sys/class/thermal/thermal_zone0/temp') as f:
                temp = float(f.read()) / 1000
                print(f"🌡️  CPU: {temp:.1f}°C")
        except:
            pass
    
    def run(self):
        """Main voice assistant loop"""
        print("\n🎤 RASPBERRY PI VOICE ASSISTANT")
        print("=" * 50)
        print("Commands:")
        print("  L - Start listening")
        print("  S - Stop and process speech")
        print("  H - Show conversation history")
        print("  I - Show system status")
        print("  Q - Quit")
        print("=" * 50)
        
        if not self.llm_model:
            print("⚠️  LLM not available - check Ollama setup!")
            return
        
        try:
            while True:
                print(f"\n🎯 Ready for command... (L/S/H/I/Q)")
                key = self.get_char().lower()
                
                if key == 'l':
                    self.start_recording()
                    
                elif key == 's':
                    self.stop_recording_and_process()
                    
                elif key == 'h':
                    self.show_conversation_history()
                    
                elif key == 'i':
                    self.show_system_status()
                    
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