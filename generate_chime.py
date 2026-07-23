import wave
import struct
import math
import os

filepath = os.path.join('static', 'audio', 'chime.wav')

# Generate a pleasant chime (two notes: e.g., C5 and E5)
sample_rate = 44100
duration = 0.5  # seconds

# C5 = 523.25 Hz, E5 = 659.25 Hz
freq1 = 523.25
freq2 = 659.25

with wave.open(filepath, 'w') as obj:
    obj.setnchannels(1) # mono
    obj.setsampwidth(2)
    obj.setframerate(sample_rate)
    
    for i in range(int(sample_rate * duration)):
        # Generate two tones simultaneously
        t = float(i) / sample_rate
        # Envelope to make it sound like a chime (decay)
        envelope = math.exp(-3 * t)
        
        val1 = math.sin(2.0 * math.pi * freq1 * t)
        val2 = math.sin(2.0 * math.pi * freq2 * t)
        
        # Combine and apply envelope
        value = (val1 + val2) / 2.0 * envelope
        
        # Convert to 16-bit integer
        data = int(value * 32767.0)
        obj.writeframesraw(struct.pack('<h', data))
        
print(f"Generated {filepath}")
