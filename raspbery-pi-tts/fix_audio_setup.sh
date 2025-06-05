#!/bin/bash
echo "🔧 Fixing Raspberry Pi Audio Setup..."

# 1. Fix audio output to 3.5mm
echo "Setting audio output to 3.5mm jack..."
amixer cset numid=3 1

# 2. Configure PulseAudio
echo "Configuring PulseAudio..."
pulseaudio --kill 2>/dev/null
pulseaudio --start
pactl set-default-sink 0
pactl set-default-source 3

# 3. Create ALSA config
echo "Creating ALSA configuration..."
cat > ~/.asoundrc << EOF
pcm.!default {
    type hw
    card 0
    device 0
}
ctl.!default {
    type hw
    card 0
}
EOF

# 4. Test audio
echo "Testing audio output..."
speaker-test -t wav -c 2 -D plughw:0,0 &
SPEAKER_PID=$!
sleep 3
kill $SPEAKER_PID 2>/dev/null

echo "✓ Audio setup complete!"
echo "Test with: aplay test_mic.wav"




chmod +x fix_audio_setup.sh
./fix_audio_setup.sh