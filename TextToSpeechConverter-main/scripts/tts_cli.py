import os
import sys
import argparse
import pyttsx3
from gtts import gTTS
import time
import json
from datetime import datetime

# Define paths relative to the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
SAMPLES_DIR = os.path.join(PROJECT_DIR, 'samples')
LOGS_DIR = os.path.join(PROJECT_DIR, 'logs')

# Ensure directories exist
os.makedirs(SAMPLES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

class TTSEngine:
    """Text-to-Speech engine with multiple backend options"""
    
    def __init__(self, backend='pyttsx3', language='en'):
        self.backend = backend
        self.language = language
        
        # Initialize pyttsx3 if needed
        if backend == 'pyttsx3':
            self.engine = pyttsx3.init()
            self.voices = self.engine.getProperty('voices')
            self.default_rate = self.engine.getProperty('rate')
            self.default_volume = self.engine.getProperty('volume')
        
        # Log initialization
        self._log_event('init', {'backend': backend, 'language': language})
    
    def set_voice(self, voice_index=None):
        """Set voice by index"""
        if self.backend != 'pyttsx3':
            print("Voice selection only available with pyttsx3 backend")
            return False
        
        if voice_index is not None and 0 <= voice_index < len(self.voices):
            self.engine.setProperty('voice', self.voices[voice_index].id)
            return True
        return False
    
    def set_rate(self, rate=None):
        """Set speech rate (words per minute)"""
        if self.backend != 'pyttsx3':
            print("Rate adjustment only available with pyttsx3 backend")
            return
        
        if rate is not None:
            self.engine.setProperty('rate', rate)
    
    def set_volume(self, volume=None):
        """Set volume (0.0 to 1.0)"""
        if self.backend != 'pyttsx3':
            print("Volume adjustment only available with pyttsx3 backend")
            return
            
        if volume is not None and 0.0 <= volume <= 1.0:
            self.engine.setProperty('volume', volume)
    
    def list_voices(self):
        """List available voices"""
        if self.backend != 'pyttsx3':
            print("Voice listing only available with pyttsx3 backend")
            return []
            
        return [{'index': i, 'name': voice.name, 'id': voice.id} 
                for i, voice in enumerate(self.voices)]
    
    def speak(self, text, output_file=None):
        """Convert text to speech using selected backend"""
        if not text:
            return {'success': False, 'error': 'No text provided'}
        
        # Preprocess text to handle special characters and improve speech quality
        text = self._preprocess_text(text)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Use appropriate backend
            if self.backend == 'pyttsx3':
                result = self._speak_pyttsx3(text, output_file)
            elif self.backend == 'gtts':
                result = self._speak_gtts(text, output_file)
            else:
                return {'success': False, 'error': f'Unknown backend: {self.backend}'}
            
            # Calculate time taken
            elapsed_time = time.time() - start_time
            
            # Add timing to result
            result['elapsed_time'] = elapsed_time
            
            # Log successful conversion
            self._log_event('speak', {
                'text_length': len(text),
                'output_file': output_file,
                'elapsed_time': elapsed_time,
                'backend': self.backend
            })
            
            return result
            
        except Exception as e:
            # Log errors
            self._log_event('error', {
                'text_length': len(text),
                'error': str(e),
                'backend': self.backend
            })
            
            return {'success': False, 'error': str(e)}
    
    def _speak_pyttsx3(self, text, output_file):
        """Use pyttsx3 engine for TTS"""
        if output_file:
            self.engine.save_to_file(text, output_file)
            self.engine.runAndWait()
            return {'success': True, 'output_file': output_file}
        else:
            self.engine.say(text)
            self.engine.runAndWait()
            return {'success': True}
    
    def _speak_gtts(self, text, output_file):
        """Use Google Text-to-Speech for TTS"""
        # If no output file specified, create a temporary one
        temp_file = False
        if not output_file:
            output_file = os.path.join(SAMPLES_DIR, f"gtts_temp_{int(time.time())}.mp3")
            temp_file = True
        
        # Generate speech
        tts = gTTS(text=text, lang=self.language, slow=False)
        tts.save(output_file)
        
        # Play if no permanent output file was requested
        if temp_file:
            os.system(f'start "" "{output_file}"')
            # Wait for playback to start
            time.sleep(1)
        
        return {'success': True, 'output_file': output_file, 'temp_file': temp_file}
    
    def _preprocess_text(self, text):
        """Preprocess text to improve speech quality"""
        # Replace special characters with their spoken form
        replacements = {
            '&': ' and ',
            '+': ' plus ',
            '@': ' at ',
            '%': ' percent ',
            '=': ' equals ',
            '#': ' number ',
            '...': ', dot dot dot',
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Handle common abbreviations
        abbreviations = {
            'Dr.': 'Doctor',
            'Mr.': 'Mister',
            'Mrs.': 'Misses',
            'Ms.': 'Miss',
            'Prof.': 'Professor',
            'e.g.': 'for example',
            'i.e.': 'that is',
            'etc.': 'etcetera',
            'vs.': 'versus',
            'approx.': 'approximately'
        }
        
        for abbr, expansion in abbreviations.items():
            # Replace only if it's a standalone word (with spaces or punctuation around it)
            text = text.replace(f' {abbr} ', f' {expansion} ')
            
            # Also check at the beginning and end of the text
            if text.startswith(f'{abbr} '):
                text = f'{expansion} {text[len(abbr)+1:]}'
            if text.endswith(f' {abbr}'):
                text = f'{text[:-len(abbr)-1]} {expansion}'
        
        return text
    
    def _log_event(self, event_type, details):
        """Log events to file for analytics"""
        log_file = os.path.join(LOGS_DIR, 'tts_events.jsonl')
        
        # Create log entry
        entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'event': event_type,
            'details': details
        }
        
        # Append to log file
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

def main():
    """Main function for command-line interface"""
    parser = argparse.ArgumentParser(description='Text-to-Speech Conversion Tool')
    
    # Input options
    input_group = parser.add_argument_group('Input Options')
    input_group.add_argument('--text', type=str, help='Text to convert to speech')
    input_group.add_argument('--file', type=str, help='Text file to convert to speech')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output', type=str, help='Output MP3 file path')
    
    # TTS Engine options
    engine_group = parser.add_argument_group('TTS Engine Options')
    engine_group.add_argument('--backend', type=str, choices=['pyttsx3', 'gtts'], 
                             default='pyttsx3', help='TTS backend to use')
    engine_group.add_argument('--language', type=str, default='en', 
                             help='Language code (for gtts)')
    
    # Voice options (pyttsx3 only)
    voice_group = parser.add_argument_group('Voice Options (pyttsx3 only)')
    voice_group.add_argument('--list-voices', action='store_true', 
                            help='List available voices')
    voice_group.add_argument('--voice', type=int, 
                            help='Voice index to use')
    voice_group.add_argument('--rate', type=int, 
                            help='Speech rate (words per minute)')
    voice_group.add_argument('--volume', type=float, 
                            help='Volume (0.0 to 1.0)')
    
    # Interactive mode
    parser.add_argument('--interactive', action='store_true', 
                       help='Run in interactive mode')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Initialize TTS engine
    tts = TTSEngine(backend=args.backend, language=args.language)
    
    # List voices if requested
    if args.list_voices:
        voices = tts.list_voices()
        print(f"Available voices ({len(voices)}):")
        for voice in voices:
            print(f"{voice['index']}. {voice['name']} (ID: {voice['id']})")
        return
    
    # Set voice properties if specified
    if args.backend == 'pyttsx3':
        if args.voice is not None:
            if not tts.set_voice(args.voice):
                print(f"Warning: Voice index {args.voice} not found. Using default voice.")
        
        if args.rate is not None:
            tts.set_rate(args.rate)
        
        if args.volume is not None:
            tts.set_volume(args.volume)
    
    # Run in interactive mode if requested
    if args.interactive:
        run_interactive_mode(tts)
        return
    
    # Get input text
    text = None
    
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
            print(f"Loaded text from: {args.file}")
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    elif args.text:
        text = args.text
    else:
        parser.print_help()
        return
    
    # Convert text to speech
    print(f"Converting text to speech using {args.backend}...")
    result = tts.speak(text, args.output)
    
    # Show results
    if result['success']:
        print(f"Conversion completed in {result['elapsed_time']:.2f} seconds")
        if args.output:
            print(f"Audio saved to: {args.output}")
    else:
        print(f"Error: {result['error']}")

def run_interactive_mode(tts):
    """Run the TTS application in interactive mode"""
    print("\nText-to-Speech Interactive Mode")
    print("===============================")
    print("Type your text and press Enter to hear it spoken.")
    print("Commands:")
    print("  /backend <name>   - Switch TTS backend (pyttsx3 or gtts)")
    print("  /voice <index>    - Change voice (pyttsx3 only)")
    print("  /rate <rate>      - Change speech rate (pyttsx3 only)")
    print("  /volume <vol>     - Change volume (0.0-1.0) (pyttsx3 only)")
    print("  /language <code>  - Change language (gtts only)")
    print("  /save <file>      - Save next speech to file")
    print("  /voices           - List available voices (pyttsx3 only)")
    print("  /help             - Show this help")
    print("  /exit             - Exit interactive mode")
    print("===============================")
    
    output_file = None
    
    while True:
        # Get user input
        user_input = input("\n> ")
        
        # Check for commands
        if user_input.startswith('/'):
            cmd_parts = user_input.split(maxsplit=1)
            command = cmd_parts[0].lower()
            
            if command == '/exit':
                print("Exiting interactive mode.")
                break
                
            elif command == '/help':
                print("Commands:")
                print("  /backend <name>   - Switch TTS backend (pyttsx3 or gtts)")
                print("  /voice <index>    - Change voice (pyttsx3 only)")
                print("  /rate <rate>      - Change speech rate (pyttsx3 only)")
                print("  /volume <vol>     - Change volume (0.0-1.0) (pyttsx3 only)")
                print("  /language <code>  - Change language (gtts only)")
                print("  /save <file>      - Save next speech to file")
                print("  /voices           - List available voices (pyttsx3 only)")
                print("  /help             - Show this help")
                print("  /exit             - Exit interactive mode")
                
            elif command == '/voices':
                voices = tts.list_voices()
                print(f"Available voices ({len(voices)}):")
                for voice in voices:
                    print(f"{voice['index']}. {voice['name']}")
            
            elif command == '/voice':
                if tts.backend != 'pyttsx3':
                    print("Voice selection is only available with pyttsx3 backend.")
                    continue
                    
                if len(cmd_parts) > 1:
                    try:
                        voice_index = int(cmd_parts[1].strip())
                        if tts.set_voice(voice_index):
                            print(f"Voice changed to index: {voice_index}")
                        else:
                            print(f"Voice index {voice_index} not found. Using default voice.")
                    except ValueError:
                        print("Voice index must be a number.")
                else:
                    print("Usage: /voice <index>")
            
            elif command == '/rate':
                if tts.backend != 'pyttsx3':
                    print("Rate adjustment is only available with pyttsx3 backend.")
                    continue
                    
                if len(cmd_parts) > 1:
                    try:
                        rate = int(cmd_parts[1].strip())
                        tts.set_rate(rate)
                        print(f"Speech rate changed to: {rate}")
                    except ValueError:
                        print("Rate must be an integer.")
                else:
                    print("Usage: /rate <rate>")
            
            elif command == '/volume':
                if tts.backend != 'pyttsx3':
                    print("Volume adjustment is only available with pyttsx3 backend.")
                    continue
                    
                if len(cmd_parts) > 1:
                    try:
                        volume = float(cmd_parts[1].strip())
                        if 0.0 <= volume <= 1.0:
                            tts.set_volume(volume)
                            print(f"Volume changed to: {volume}")
                        else:
                            print("Volume must be between 0.0 and 1.0.")
                    except ValueError:
                        print("Volume must be a number between 0.0 and 1.0.")
                else:
                    print("Usage: /volume <vol>")
            
            elif command == '/backend':
                if len(cmd_parts) > 1:
                    backend = cmd_parts[1].strip().lower()
                    if backend in ['pyttsx3', 'gtts']:
                        tts = TTSEngine(backend=backend)
                        print(f"TTS backend changed to: {backend}")
                    else:
                        print(f"Unknown backend: {backend}. Available: pyttsx3, gtts")
                else:
                    print("Usage: /backend <name>")
            
            elif command == '/language':
                if tts.backend != 'gtts':
                    print("Language selection is only available with gtts backend.")
                    continue
                    
                if len(cmd_parts) > 1:
                    language = cmd_parts[1].strip().lower()
                    tts.language = language
                    print(f"Language changed to: {language}")
                else:
                    print("Usage: /language <code>")
            
            elif command == '/save':
                if len(cmd_parts) > 1:
                    output_file = cmd_parts[1].strip()
                    print(f"Next speech will be saved to: {output_file}")
                else:
                    print("Usage: /save <file>")
            
            else:
                print(f"Unknown command: {command}")
        
        # Process text input
        else:
            if user_input.strip():
                print("Converting text to speech...")
                result = tts.speak(user_input, output_file)
                
                if result['success']:
                    print(f"Processed in {result['elapsed_time']:.2f} seconds")
                    if output_file:
                        print(f"Audio saved to: {output_file}")
                        output_file = None  # Reset output file after use
                else:
                    print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()