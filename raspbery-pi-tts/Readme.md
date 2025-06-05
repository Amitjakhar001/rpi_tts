

# Run the comprehensive hardware test
python3 hardware_test.py

# This will test:
# - Python environment
# - Audio system
# - espeak installation
# - Required Python packages
# - TTS engines
# - GPIO (if available)
# - System resources
# - Network connectivity

After creating both files if we want these scripts to be executable
# Make scripts executable
chmod +x raspberry_pi_tts.py
chmod +x hardware_test.py

# Create project directory
mkdir ~/raspberry-pi-tts
cd ~/raspberry-pi-tts

# Create Python virtual environment
python3 -m venv tts-env
# Activate virtual environment
source tts-env/bin/activate
# You should see (tts-env) in your prompt now
python3 hardware_test.py   # check hardware run test 
python3 raspberry_pi_tts.py # now application will start in cli 


# Install Python 3 and pip (usually pre-installed, but let's ensure)
sudo apt install python3 python3-pip python3-venv python3-dev -y
# Install audio system dependencies
sudo apt install alsa-utils pulseaudio pulseaudio-utils -y
# Install espeak for text-to-speech
sudo apt install espeak espeak-data libespeak-dev -y
# Install additional audio libraries
sudo apt install portaudio19-dev python3-pyaudio -y
# Install git for project management
sudo apt install git -y
# Install build tools
sudo apt install build-essential -y


Further if we want audio quality improvemtns

# Install better audio codecs
sudo apt install ffmpeg

# Adjust audio buffer size (add to /boot/config.txt)
echo "audio_pwm_mode=2" | sudo tee -a /boot/config.txt



###################    About all packages we installed

python3	            Installs the latest version of Python 3 (required for all Python scripts).
python3-pip	        Python package installer; allows you to install Python packages like 
                    pyttsx3, flask, etc.
python3-venv	    Enables you to create virtual environments (more below).
python3-dev	        Provides header files to compile Python extensions. Required for packages like pyaudio.

alsa-utils	        Tools for ALSA (Advanced Linux Sound Architecture) — helps control audio on Linux.
pulseaudio	        A sound server that manages audio input/output — more flexible than ALSA alone.
pulseaudio-utils	Extra tools for managing pulseaudio (e.g., pacmd, pactl) useful for audio debugging.

espeak	            Lightweight open-source Text-to-Speech engine; converts text to voice.
espeak-data	        Provides voice data files needed by espeak.
libespeak-dev	    Development headers for integrating eSpeak with other applications (e.g., Python libs).

portaudio19-dev	    Audio I/O library required for real-time audio input/output (used by pyaudio).
python3-pyaudio	    Python bindings for PortAudio; lets you record/play audio with Python.

git	                Version control; useful for downloading and managing code from GitHub or GitLab.
build-essential 	Meta-package that includes GCC, make, and other build tools — required to compile some Python packages or 
                    audio libraries.
            

psutil (process and system utilities) is a cross-platform library for retrieving information on running processes and system utilization (CPU, memory, disks, network, sensors) in Python.

pyttsx3	            Python API to access TTS in a cross-platform way
espeak	            Backend engine (on Linux) that generates audio
libespeak-dev	    Shared library that allows Python (via pyttsx3) to access espeak
ALSA/PulseAudio	    Sends the audio to the speaker


pyttsx3 talks to → libespeak → audio system → you hear the voice



# how our model works
So we installed pyttsx3 which detect native tts engine like espeak for linux,sapi5 for windows,

Now pyttsx3 work like a wrapper around espeak 
espeak -> espeak shared library (libespeak.so) -> audio device

libespeak.so is a shared library in Linux that provides the text-to-speech functionality of the eSpeak software. It is a dynamically linked library, meaning that it is loaded into memory at runtime when a program needs to use its functions.
Here's a breakdown:
Shared library:
Files ending in .so are shared object libraries. These libraries contain code and data that can be used by multiple programs simultaneously, saving disk space and memory.
eSpeak:
eSpeak is a compact, open-source software speech synthesizer that supports many languages. It uses a "formant synthesis" method to generate speech, which makes it fast and efficient.
Text-to-speech:
libespeak.so provides the core functionality for converting written text into spoken words. This is useful for applications like screen readers, accessibility tools, and other programs that require voice output.
How it works:
When a program needs to use eSpeak's text-to-speech capabilities, it calls functions from libespeak.so.
The library's code is loaded into the program's memory space.
The program can then pass text to the library, which processes it and generates speech output.


import pyttsx3
engine = pyttsx3.init()
engine.say("Hello, Raspberry Pi")
engine.runAndWait()

pyttsx3 initializes and detects the platform (Linux).
It selects espeak as the TTS engine.
The text is passed to espeak, which generates phonemes (sound units).
espeak uses libespeak.so to synthesize the audio.
The audio is then sent to your speaker via ALSA/PulseAudio.



What is espeak?

espeak is a compact open-source Text-to-Speech engine for Linux (also available on Windows/macOS).
It supports many languages and is extremely lightweight.
On Raspberry Pi, it’s the default engine used by pyttsx3.

Works in command-line or through APIs (libespeak).
Can read from a string, text file, etc.
Provides control over:

Voice Pitch Speed Volume

 How does espeak actually generate audio?
Under the hood:

Text is tokenized into phonemes (speech sounds).
Prosody is added (intonation, rhythm).
Waveforms are generated using:
A formant synthesizer (models human vocal tract).
Pre-recorded phoneme samples.
These waveforms are converted into audio and played.
It doesn’t use AI/deep learning — it’s based on rule-based synthesis. That’s why it sounds robotic but is fast and low on resource usage (ideal for Raspberry Pi).


1. pyttsx3==2.90
What it does: A Python library that converts text to speech offline.

Key Features:
Works without internet (uses espeak, sapi5, or nsss depending on OS).
Can change voice, rate, and volume.
Why used: You want to speak text offline — pyttsx3 is ideal for that on Raspberry Pi using espeak.
Used for offline TTS using system voices (like espeak).

2. gTTS==2.3.2
What it does: Google Text-to-Speech – generates speech using Google's TTS API (requires internet).

Key Features:
More natural-sounding than pyttsx3.
Saves TTS output as MP3 files.
Why used: For high-quality voice output, when internet access is available.
Used for online TTS with more realistic voice output.


3. Flask==2.3.3
What it does: A lightweight web framework in Python.

Key Features:
Can create REST APIs or a web dashboard.
Useful for accepting text input from browser and playing it via TTS.
Why used: You may be building a web UI or REST API to accept text input, send it to TTS engine, and return/output the audio.
Used to create a simple web interface for user input/output.

4. pygame==2.5.2

What it does: A game development library — also supports audio playback.
Why used: You can use pygame.mixer or pygame.mixer.music to play .mp3 or .wav files generated by gTTS or pyttsx3.
Used for playing generated speech audio files.

5. sounddevice==0.4.6
What it does: Lets you record and play audio via NumPy arrays using PortAudio.
Why used: Allows real-time audio output or microphone input, more flexible than pygame.
Used for real-time TTS output (advanced use cases).

6. soundfile==0.12.1
What it does: Reads and writes sound files (like WAV, FLAC).
Why used: For saving or reading audio files, especially if you're processing or converting formats.
Used to save/load audio in WAV format efficiently.


7. numpy==1.24.3
What it does: Provides array and matrix operations, often used in audio and signal processing.
Why used: Required by sounddevice or matplotlib, and useful if you're analyzing or modifying audio data.
Backend support for audio buffers and data manipulation.

8. matplotlib==3.7.2
What it does: A plotting library for visualizing data.
Why used: Can visualize waveforms or audio signal plots, maybe to show volume changes or frequency curves.
Useful for visualizing audio signals or debugging.

9. psutil==5.9.5
What it does: Gives information about system usage (CPU, RAM, etc.).
Why used: You might want to monitor system performance (e.g., during TTS or playback to check for overloads).
Useful for resource management and debugging on Raspberry Pi.


10. requests==2.31.0
What it does: Makes HTTP requests.

Why used: May be used to:
Fetch text or voice data from an API.
Send audio to another server.
Use a RESTful backend for interaction.
Used to send/receive data from external APIs or web services.