#!/usr/bin/env python3
"""
Speech-to-Text using OpenAI Whisper
Optimized for Raspberry Pi
"""

import whisper
import time
import os
from pathlib import Path

class WhisperSTT:
    def __init__(self, model_size='tiny'):
        """
        Initialize Whisper STT
        model_size: 'tiny', 'base', 'small' (tiny is fastest for Pi)
        """
        print(f"🧠 Loading Whisper model '{model_size}'...")
        start_time = time.time()
        
        self.model = whisper.load_model(model_size)
        
        load_time = time.time() - start_time
        print(f"✓ Model loaded in {load_time:.1f} seconds")
        
        self.model_size = model_size
        self.setup_directories()
    
    def setup_directories(self):
        """Create directories for transcriptions"""
        Path("audio_tests/transcriptions").mkdir(parents=True, exist_ok=True)
    
    def transcribe_file(self, audio_file, language=None):
        """
        Transcribe audio file to text
        audio_file: path to audio file
        language: optional language hint ('en', 'es', etc.)
        """
        if not os.path.exists(audio_file):
            print(f"❌ Audio file not found: {audio_file}")
            return None
        
        print(f"🎯 Transcribing: {audio_file}")
        start_time = time.time()
        
        try:
            # Transcribe with Whisper
            if language:
                result = self.model.transcribe(audio_file, language=language)
            else:
                result = self.model.transcribe(audio_file)
            
            transcription_time = time.time() - start_time
            
            # Extract results
            text = result['text'].strip()
            language_detected = result['language']
            
            print(f"✓ Transcription completed in {transcription_time:.1f} seconds")
            print(f"📝 Language detected: {language_detected}")
            print(f"💬 Text: \"{text}\"")
            
            # Save transcription
            self.save_transcription(audio_file, text, language_detected, transcription_time)
            
            return {
                'text': text,
                'language': language_detected,
                'processing_time': transcription_time,
                'audio_file': audio_file
            }
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None
    
    def save_transcription(self, audio_file, text, language, processing_time):
        """Save transcription to file"""
        timestamp = int(time.time())
        filename = f"audio_tests/transcriptions/transcription_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Audio File: {audio_file}\n")
            f.write(f"Language: {language}\n")
            f.write(f"Processing Time: {processing_time:.1f}s\n")
            f.write(f"Model: {self.model_size}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write("-" * 50 + "\n")
            f.write(f"Transcription:\n{text}\n")
        
        print(f"💾 Transcription saved: {filename}")
    
    def transcribe_latest_recording(self):
        """Find and transcribe the most recent recording"""
        recordings_dir = Path("audio_tests/recordings")
        
        if not recordings_dir.exists():
            print("❌ No recordings directory found!")
            return None
        
        # Find the most recent recording
        recordings = list(recordings_dir.glob("*.wav"))
        if not recordings:
            print("❌ No recordings found!")
            return None
        
        latest_recording = max(recordings, key=os.path.getctime)
        print(f"🎯 Found latest recording: {latest_recording}")
        
        return self.transcribe_file(str(latest_recording))
    
    def benchmark_model(self, test_file=None):
        """Benchmark the model performance"""
        if test_file is None:
            # Use latest recording
            result = self.transcribe_latest_recording()
        else:
            result = self.transcribe_file(test_file)
        
        if result:
            print(f"\n📊 PERFORMANCE BENCHMARK:")
            print(f"Model: {self.model_size}")
            print(f"Processing Time: {result['processing_time']:.1f}s")
            print(f"Text Length: {len(result['text'])} characters")
            print(f"Language: {result['language']}")

if __name__ == "__main__":
    # Test the STT system
    stt = WhisperSTT('tiny')  # Start with tiny model
    
    print("\n🧪 Testing Speech-to-Text System")
    print("Make sure you have some recordings in audio_tests/recordings/")
    
    # Transcribe latest recording
    result = stt.transcribe_latest_recording()
    
    if result:
        stt.benchmark_model()