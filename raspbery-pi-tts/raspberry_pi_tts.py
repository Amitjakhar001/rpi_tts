#!/usr/bin/env python3
"""
Raspberry Pi Text-to-Speech System
Optimized for physical hardware deployment (No GPIO)
"""

import pyttsx3
import time
import os
import sys
import threading
from pathlib import Path
import psutil
import json

class RaspberryPiTTS:
    def __init__(self):
        self.engine = None
        self.voices = []
        self.current_voice_id = 0
        self.rate = 150
        self.volume = 0.9
        self.history = []
        self.initialize_tts()
        
    def initialize_tts(self):
        """Initialize the TTS engine"""
        try:
            print("Initializing TTS engine...")
            self.engine = pyttsx3.init()
            
            # Get available voices
            voices = self.engine.getProperty('voices')
            self.voices = []
            
            for i, voice in enumerate(voices):
                self.voices.append({
                    'id': i,
                    'name': voice.name,
                    'lang': getattr(voice, 'languages', ['en'])[0] if hasattr(voice, 'languages') else 'en'
                })
            
            # Set initial properties
            self.engine.setProperty('rate', self.rate)
            self.engine.setProperty('volume', self.volume)
            
            if self.voices:
                self.engine.setProperty('voice', voices[0].id)
                
            print(f"✓ TTS engine initialized with {len(self.voices)} voices")
            return True
            
        except Exception as e:
            print(f"❌ TTS initialization failed: {e}")
            print("Trying fallback initialization...")
            return self.fallback_tts_init()
    
    def fallback_tts_init(self):
        """Fallback TTS initialization using espeak directly"""
        try:
            # Test if espeak is available
            os.system("espeak 'TTS engine ready' 2>/dev/null")
            
            # Create mock voices for espeak
            self.voices = [
                {'id': 0, 'name': 'espeak-default', 'lang': 'en'},
                {'id': 1, 'name': 'espeak-male', 'lang': 'en'},
                {'id': 2, 'name': 'espeak-female', 'lang': 'en'}
            ]
            
            self.use_espeak = True
            print("✓ Fallback to espeak successful")
            return True
            
        except Exception as e:
            print(f"❌ Fallback TTS failed: {e}")
            return False
    
    def speak(self, text):
        """Convert text to speech"""
        if not text or len(text.strip()) == 0:
            print("❌ Error: No text provided")
            return False
        
        try:
            text = self._preprocess_text(text)
            word_count = len(text.split())
            
            print(f"\n🔊 SPEAKING: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
            print(f"Words: {word_count} | Rate: {self.rate} WPM | Volume: {self.volume}")
            
            if hasattr(self, 'use_espeak') and self.use_espeak:
                # Use espeak directly
                voice_param = ""
                if self.current_voice_id == 1:
                    voice_param = "+m3"  # Male voice
                elif self.current_voice_id == 2:
                    voice_param = "+f3"  # Female voice
                
                speed_param = int(self.rate * 0.8)  # Convert to espeak speed
                cmd = f'espeak "{text}" -s {speed_param} -a {int(self.volume * 100)} {voice_param}'
                os.system(cmd)
            else:
                # Use pyttsx3
                self.engine.say(text)
                self.engine.runAndWait()
            
            # Add to history
            self.history.append({
                'text': text[:50] + ('...' if len(text) > 50 else ''),
                'voice': self.voices[self.current_voice_id]['name'],
                'timestamp': time.time()
            })
            
            if len(self.history) > 10:
                self.history = self.history[-10:]
            
            print("✓ Speech completed!")
            return True
            
        except Exception as e:
            print(f"❌ Speech failed: {e}")
            return False
    
    def set_voice(self, voice_id):
        """Change voice"""
        try:
            voice_id = int(voice_id)
            if 0 <= voice_id < len(self.voices):
                self.current_voice_id = voice_id
                
                if hasattr(self, 'engine') and self.engine:
                    voices = self.engine.getProperty('voices')
                    if voice_id < len(voices):
                        self.engine.setProperty('voice', voices[voice_id].id)
                
                print(f"✓ Voice changed to: {self.voices[voice_id]['name']}")
                return True
            else:
                print(f"❌ Voice {voice_id} not found (0-{len(self.voices)-1})")
                return False
        except Exception as e:
            print(f"❌ Voice change failed: {e}")
            return False
    
    def set_rate(self, rate):
        """Set speech rate"""
        try:
            rate = int(rate)
            if 50 <= rate <= 300:
                self.rate = rate
                if hasattr(self, 'engine') and self.engine:
                    self.engine.setProperty('rate', rate)
                print(f"✓ Speech rate set to: {rate} WPM")
                return True
            else:
                print("❌ Rate must be 50-300 WPM")
                return False
        except Exception as e:
            print(f"❌ Rate change failed: {e}")
            return False
    
    def set_volume(self, volume):
        """Set volume"""
        try:
            volume = float(volume)
            if 0.0 <= volume <= 1.0:
                self.volume = volume
                if hasattr(self, 'engine') and self.engine:
                    self.engine.setProperty('volume', volume)
                print(f"✓ Volume set to: {volume}")
                return True
            else:
                print("❌ Volume must be 0.0-1.0")
                return False
        except Exception as e:
            print(f"❌ Volume change failed: {e}")
            return False
    
    def list_voices(self):
        """List available voices"""
        print("\n🎤 AVAILABLE VOICES:")
        print("-" * 30)
        for voice in self.voices:
            current = " ◄ CURRENT" if voice['id'] == self.current_voice_id else ""
            print(f"{voice['id']}. {voice['name']}{current}")
        print("-" * 30)
    
    def show_system_info(self):
        """Show system information"""
        try:
            cpu_temp = self.get_cpu_temperature()
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            print("\n🖥️  SYSTEM STATUS:")
            print("=" * 30)
            print(f"CPU Usage: {cpu_percent}%")
            print(f"CPU Temperature: {cpu_temp}°C")
            print(f"Memory Used: {memory.percent}%")
            print(f"Memory Available: {memory.available // 1024 // 1024} MB")
            print(f"Current Voice: {self.voices[self.current_voice_id]['name']}")
            print(f"Speech Rate: {self.rate} WPM")
            print(f"Volume: {self.volume}")
            print("=" * 30)
            
        except Exception as e:
            print(f"❌ System info error: {e}")
    
    def get_cpu_temperature(self):
        """Get CPU temperature"""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read()) / 1000.0
                return round(temp, 1)
        except:
            return "N/A"
    
    def show_history(self):
        """Show conversion history"""
        if not self.history:
            print("📜 No history available")
            return
        
        print("\n📜 RECENT CONVERSIONS:")
        print("-" * 40)
        for i, entry in enumerate(self.history[-5:], 1):
            print(f"{i}. \"{entry['text']}\"")
            print(f"   Voice: {entry['voice']}")
        print("-" * 40)
    
    def _preprocess_text(self, text):
        """Preprocess text for better speech"""
        replacements = {
            '&': ' and ',
            '@': ' at ',
            '%': ' percent ',
            '#': ' number ',
            '+': ' plus ',
            '=': ' equals ',
            '$': ' dollar ',
            '€': ' euro ',
            '£': ' pound '
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text.strip()
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            print("✓ Resources cleaned up")
        except:
            pass

def show_help():
    """Display help information"""
    print("\n📖 RASPBERRY PI TTS COMMANDS:")
    print("=" * 35)
    print("Speech Commands:")
    print("  speak <text>  - Convert text to speech")
    print("  <text>        - Direct speech (no command needed)")
    print()
    print("Voice Commands:")
    print("  voices        - List available voices")
    print("  voice <id>    - Change voice")
    print("  rate <wpm>    - Set speech rate (50-300)")
    print("  volume <vol>  - Set volume (0.0-1.0)")
    print()
    print("System Commands:")
    print("  info          - Show system information")
    print("  history       - Show recent conversions")
    print("  test          - Run system test")
    print("  help          - Show this help")
    print("  exit          - Exit program")
    print("=" * 35)

def run_system_test(tts):
    """Run comprehensive system test"""
    print("\n🧪 RUNNING SYSTEM TEST")
    print("=" * 30)
    
    tests = [
        "System test initiated",
        "Testing voice synthesis",
        "Checking audio output",
        "All systems operational"
    ]
    
    for i, test_text in enumerate(tests, 1):
        print(f"Test {i}/4: {test_text}")
        tts.speak(test_text)
        time.sleep(0.5)
    
    tts.show_system_info()
    print("\n✓ System test completed!")

def main():
    """Main program loop"""
    print("\n" + "=" * 50)
    print("🎤 RASPBERRY PI TTS SYSTEM v2.0")
    print("=" * 50)
    print("Hardware-Optimized Text-to-Speech System")
    print("Type 'help' for commands or 'exit' to quit")
    print("=" * 50)
    
    # Initialize TTS system
    tts = RaspberryPiTTS()
    
    if not tts.voices:
        print("❌ TTS system initialization failed!")
        return
    
    try:
        while True:
            try:
                # Get user input
                user_input = input("\nTTS> ").strip()
                
                if not user_input:
                    continue
                
                # Parse command
                parts = user_input.split(' ', 1)
                command = parts[0].lower()
                
                # Handle commands
                if command == 'exit' or command == 'quit':
                    print("👋 Shutting down TTS system...")
                    break
                
                elif command == 'help':
                    show_help()
                
                elif command == 'speak':
                    if len(parts) > 1:
                        tts.speak(parts[1])
                    else:
                        print("Usage: speak <text>")
                
                elif command == 'voices':
                    tts.list_voices()
                
                elif command == 'voice':
                    if len(parts) > 1:
                        tts.set_voice(parts[1])
                    else:
                        print("Usage: voice <0-N>")
                
                elif command == 'rate':
                    if len(parts) > 1:
                        tts.set_rate(parts[1])
                    else:
                        print("Usage: rate <50-300>")
                
                elif command == 'volume':
                    if len(parts) > 1:
                        tts.set_volume(parts[1])
                    else:
                        print("Usage: volume <0.0-1.0>")
                
                elif command == 'info':
                    tts.show_system_info()
                
                elif command == 'history':
                    tts.show_history()
                
                elif command == 'test':
                    run_system_test(tts)
                
                else:
                    # Treat as direct speech input
                    tts.speak(user_input)
            
            except KeyboardInterrupt:
                print("\n👋 Program interrupted. Shutting down...")
                break
                
            except Exception as e:
                print(f"❌ Error: {e}")
    
    finally:
        tts.cleanup()
        print("Goodbye!")

if __name__ == "__main__":
    main()