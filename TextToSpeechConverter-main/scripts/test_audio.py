# test_audio.py

# Basic audio test script
import pyttsx3
import platform
import os
import datetime

def system_info():
    """Returns basic system information"""
    info = {
        "OS": platform.system() + " " + platform.version(),
        "Architecture": platform.architecture(),
        "Python Version": platform.python_version(),
        "Testing Date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return info

def test_audio():
    """Tests the audio output using pyttsx3"""
    engine = pyttsx3.init()
    engine.say("Audio test successful. The TTS system is working correctly.")
    engine.runAndWait()
    print("Audio test completed successfully!")

if __name__ == "__main__":
    # Print system info
    info = system_info()
    print("System Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Test audio
    print("\nTesting audio output...")
    test_audio()
    
    # Save system info to documentation
    os.makedirs('../docs', exist_ok=True)
    with open('../docs/system_info.txt', 'w') as f:
        f.write("SYSTEM INFORMATION\n")
        f.write("=================\n\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")