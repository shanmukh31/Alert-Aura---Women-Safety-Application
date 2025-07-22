import sounddevice as sd
import threading
import time
import numpy as np
from emotion_detection import predict_emotion
from dbmeter import calculate_decibel # Import the decibel meter function

class EmotionMonitor:
    def __init__(self, callback):
        self.monitoring = False
        self.callback = callback
    
    def start(self):
        """Start emotion monitoring in a separate thread"""
        self.monitoring = True
        threading.Thread(target=self._monitor_loop, daemon=True).start()
    
    def stop(self):
        """Stop emotion monitoring"""
        self.monitoring = False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Record audio
                audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
                sd.wait()
                
                # Process audio
                audio_array = audio.flatten()
                
                # Get emotion and decibel level
                emotion, confidence = predict_emotion(audio_array)
                decibels = calculate_decibel(audio_array)  # Calculate decibel level
                confidence_percent = f"{confidence * 100:.2f}%"
                decibel_str = f"{decibels:.1f} dB"
                
                # Call callback with results
                self.callback(emotion, confidence_percent, decibel_str)
                
                # Wait before next detection
                for _ in range(10):
                    if not self.monitoring:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                self.callback(None, None, None, str(e)) 