from gtts import gTTS
import os
import time

# Test simple text
test_text = "This is a test of the Google Text to Speech system."

print("Testing Google TTS (gTTS)...")
print(f"Converting text: '{test_text}'")

# Create output file path
output_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                          "samples", "gtts_test.mp3")

# Convert text to speech
tts = gTTS(text=test_text, lang='en', slow=False)
tts.save(output_file)

print(f"File saved to: {output_file}")

# Try to play the file using different methods based on platform
if os.name == 'nt':  # Windows
    try:
        print("Attempting to play using Windows default player...")
        os.system(f'start {output_file}')
    except Exception as e:
        print(f"Error playing file: {e}")
else:  # macOS or Linux
    try:
        if os.path.exists('/usr/bin/xdg-open'):  # Linux
            os.system(f'xdg-open {output_file}')
        else:  # macOS
            os.system(f'open {output_file}')
    except Exception as e:
        print(f"Error playing file: {e}")

print("Wait for 5 seconds to allow playback to start...")
time.sleep(5)
print("Test complete!")