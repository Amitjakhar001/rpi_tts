import os
import time
import glob

# Define paths relative to the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
SAMPLES_DIR = os.path.join(PROJECT_DIR, 'samples')

def play_audio_file(audio_file):
    """Play an audio file and wait for it to finish"""
    print(f"Playing: {os.path.basename(audio_file)}")
    
    # Start the audio file
    os.system(f'start "" "{audio_file}"')
    
    # Estimate wait time based on file size
    # MP3 files are roughly 1MB per minute, so we can estimate duration
    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    estimated_seconds = max(5, file_size_mb * 60)  # At least 5 seconds
    
    print(f"  Waiting {estimated_seconds:.1f} seconds for playback to complete...")
    time.sleep(min(estimated_seconds, 15))  # Cap at 15 seconds max
    print(f"  Completed playback of {os.path.basename(audio_file)}")
    print()

def main():
    """Test all audio files in the samples directory"""
    print("Testing all audio files in the samples directory")
    print("=" * 50)
    
    # Find all MP3 files in the samples directory
    audio_files = glob.glob(os.path.join(SAMPLES_DIR, "*.mp3"))
    
    if not audio_files:
        print("No audio files found in the samples directory!")
        return
    
    print(f"Found {len(audio_files)} audio files:")
    for i, file in enumerate(audio_files, 1):
        print(f"{i}. {os.path.basename(file)}")
    
    print("\nStarting playback test...")
    print("=" * 50)
    
    # Play each audio file
    for audio_file in audio_files:
        play_audio_file(audio_file)
    
    print("All audio files tested!")

if __name__ == "__main__":
    main()