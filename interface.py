import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import tkinter.font as tkfont
from datetime import datetime
import re
import sounddevice as sd
import threading
import numpy as np
from emotion_detection import predict_emotion
import time
import dbmeter
import cv2
from PIL import Image, ImageTk
from ultralytics import YOLO
import mediapipe as mp
import os
import wave
import subprocess
import geocoder
import pyautogui
import winsound
from queue import Queue
import whisper
import random
from styles import configure_styles
from utils import get_formatted_time, get_timestamp
from phone_window import PhoneNumberWindow
from emotion_monitor import EmotionMonitor
from sensor_component import SensorComponent

# Initialize mediapipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Load the Whisper model once
whisper_model = whisper.load_model("base")

def detect_sos_with_whisper(audio_array: np.ndarray, custom_word: str = "help", sample_rate: int = 16000) -> bool:
    """Detects if the custom word is present in the given audio using OpenAI's Whisper."""
    if audio_array.ndim > 1:
        audio_array = audio_array.flatten()
    if audio_array.dtype != np.float32:
        audio_array = audio_array.astype(np.float32)

    result = whisper_model.transcribe(audio_array, fp16=False, language="en", task="transcribe")
    text = result["text"].strip()
    print(f"Transcribed Text: {text}")

    if custom_word.lower() in text.lower():
        print(f"🆘 SOS detected! Trigger word '{custom_word}' found!")
        return True
    else:
        print("✅ No SOS detected.")
        return False

class WhatsAppAutomation:
    @staticmethod
    def open_chat(friend_name, disable_failsafe=False):
        if disable_failsafe: pyautogui.FAILSAFE = False
        os.system("start whatsapp:"); time.sleep(5)
        for x, y in [(200, 100), (200, 200), (700, 700)]:
            pyautogui.moveTo(x, y); 
            pyautogui.click();pyautogui.click();time.sleep(1)
            if (x, y) == (200, 100): pyautogui.write(friend_name); time.sleep(2)
    
    @staticmethod
    def send_message(friend_name, message, disable_failsafe=False):
        try:
            WhatsAppAutomation.open_chat(friend_name, disable_failsafe)
            pyautogui.click(); time.sleep(1); pyautogui.hotkey('ctrl', 'a'); pyautogui.press('delete'); time.sleep(0.5)
            pyautogui.write(message); time.sleep(5); pyautogui.press('enter'); time.sleep(2)
            WhatsAppAutomation.close_whatsapp()
        except Exception as e: print(f"Error sending WhatsApp message: {e}")
    
    @staticmethod
    def close_whatsapp(): pyautogui.hotkey("alt", "f4")

# Constants
SAVE_DIR = "vids"
AUDIO_RATE = 44100
CHANNELS = 1
FPS = 30
os.makedirs(SAVE_DIR, exist_ok=True)

def record_audio(q, st):
    frames = []
    def cb(i, f, ti, s): 
        frames.append(i.copy())
        if st.is_set():
            raise sd.CallbackStop()
    with sd.InputStream(samplerate=AUDIO_RATE, channels=CHANNELS, dtype='int16', callback=cb):
        while not st.is_set():
            time.sleep(0.1)
    q.put(np.concatenate(frames))

def merge_save(frames, audio):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp = os.path.join(SAVE_DIR, f"temp_{now}.mp4")
    out = os.path.join(SAVE_DIR, f"sos_{now}.mp4")
    h, w = frames[0].shape[:2]
    v = cv2.VideoWriter(tmp, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (w, h))
    [v.write(f) for f in frames]
    v.release()
    wav = tmp.replace(".mp4", "_a.wav")
    with wave.open(wav, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(AUDIO_RATE)
        wf.writeframes(audio.tobytes())
    subprocess.run(["ffmpeg", "-y", "-i", tmp, "-i", wav, "-c:v", "copy", "-c:a", "aac", out])
    os.remove(tmp)
    os.remove(wav)

class SOSMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Women Safety Guardian: Alert Aura")
        self.root.geometry("1000x800")
        self.root.configure(bg="#f0f2f5")
        
        # Prevent window from closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize WhatsApp automation
        self.whatsapp = WhatsAppAutomation()
        
        # Initialize monitoring state
        self.monitoring = False
        self.camera_running = False
        self.is_recording = False
        self.frames = []
        self.q = Queue()
        self.st = threading.Event()
        self.recording_start = None
        self.current_location = None
        self.model = YOLO("yolov8n.pt")
        self.last_sos = 0
        self.cooldown = 30  # 30 seconds cooldown between SOS triggers
        self.sensor_active = False  # Initialize sensor state
        
        # Initialize custom trigger word
        self.custom_trigger_word = "help"  # Default trigger word
        
        # Custom styles
        self.style = ttk.Style()
        self.style.configure("Start.TButton", padding=15, font=('Helvetica', 11, 'bold'), background="#4CAF50", foreground="black")
        self.style.configure("Stop.TButton", padding=15, font=('Helvetica', 11, 'bold'), background="#f44336", foreground="black")
        self.style.configure("Emergency.TButton", padding=15, font=('Helvetica', 13, 'bold'), background="#ff1744", foreground="black")
        self.style.configure("Contacts.TButton", padding=15, font=('Helvetica', 11, 'bold'), background="#2196F3", foreground="black")
        self.style.configure("Custom.TButton", padding=15, font=('Helvetica', 11, 'bold'), background="#9C27B0", foreground="black")
        self.style.configure("Status.TLabel", font=('Helvetica', 11), background="#ffffff", padding=8)
        self.style.configure("Header.TLabel", font=('Helvetica', 18, 'bold'), background="#f0f2f5", foreground="#1a237e")
        self.style.configure("Parameter.TLabel", font=('Helvetica', 12, 'bold'), background="#ffffff", padding=5)
        self.style.configure("Value.TLabel", font=('Helvetica', 12), background="#ffffff", padding=5)
        
        # Initialize components
        self._create_main_layout()
        self._create_status_section()
        self._create_camera_section()
        self._create_log_section()
        self._create_button_section()
        
        # Initialize emotion monitor
        self.emotion_monitor = EmotionMonitor(self._emotion_callback)
        
        # Start time updates
        self.update_time()
    
    def _create_main_layout(self):
        """Create the main layout structure"""
        self.main_content = tk.Frame(self.root, bg="#f0f2f5")
        self.main_content.grid(row=0, column=0, sticky="nsew")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Header
        self.header = tk.Frame(self.main_content, bg="#f0f2f5")
        self.header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(10, 10))
        self.header.grid_columnconfigure(0, weight=1)
        self.header.grid_columnconfigure(1, weight=1)
        
        self.title_label = ttk.Label(self.header, text="ALERT AURA – AI-POWERED WOMEN'S SAFETY SYSTEM", 
                                   style="Header.TLabel")
        self.title_label.grid(row=0, column=0, sticky="w", padx=(30, 0))
        
        self.time_label = ttk.Label(self.header, text="", style="Status.TLabel")
        self.time_label.grid(row=0, column=1, sticky="e", padx=(0, 30))
    
    def _create_status_section(self):
        """Create the status monitoring section"""
        self.status_card = tk.Frame(self.main_content, bg="#ffffff", relief=tk.FLAT,
                                  highlightthickness=1, highlightbackground="#e0e0e0")
        self.status_card.grid(row=1, column=0, sticky="nsew", padx=(30, 15), pady=(0, 15))
        
        # Create scrollable status section
        self._create_scrollable_status()
        
        # Initialize status fields
        self._initialize_status_fields()
    
    def _create_scrollable_status(self):
        """Create scrollable status section"""
        self.param_canvas = tk.Canvas(self.status_card, bg="#ffffff", highlightthickness=0, height=350)
        self.param_scrollbar = ttk.Scrollbar(self.status_card, orient="vertical",
                                           command=self.param_canvas.yview)
        self.param_scrollable_frame = tk.Frame(self.param_canvas, bg="#ffffff")
        
        self.param_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all"))
        )
        
        self.param_canvas.create_window((0, 0), window=self.param_scrollable_frame, anchor="nw")
        self.param_canvas.configure(yscrollcommand=self.param_scrollbar.set)
        
        self.param_canvas.pack(side="left", fill="both", expand=True)
        self.param_scrollbar.pack(side="right", fill="y")
        
        self.param_scrollable_frame.grid_columnconfigure(0, weight=1)
        self.param_scrollable_frame.grid_columnconfigure(1, weight=1)
    
    def _initialize_status_fields(self):
        """Initialize status monitoring fields"""
        status_fields = [
            ("Emotion", "N/A"),
            ("Confidence", "0%"),
            ("Decibel Level", "0 dB"),
            ("SOS Detected", "No"),
            ("Sensor", "Inactive"),  # Initialize sensor status
            ("Location", "Acquiring..."),
            ("Crime Zone", "No data available "),
            ("Video Model Triggered", "No"),
            ("Monitoring", "Inactive")
        ]
        
        self.labels = {}
        for i, (field, value) in enumerate(status_fields):
            label = ttk.Label(self.param_scrollable_frame, text=f"{field}:",
                            style="Parameter.TLabel", anchor="center", justify="center")
            label.grid(row=i, column=0, sticky="e", padx=(0, 10), pady=10)
            
            value_label = ttk.Label(self.param_scrollable_frame, text=value,
                                  style="Value.TLabel", anchor="center", justify="center")
            value_label.grid(row=i, column=1, sticky="w", pady=10)
            self.labels[field] = value_label
    
    def _create_camera_section(self):
        """Create the camera feed section"""
        self.camera_frame = tk.Frame(self.main_content, bg="#222", height=260, width=400, relief=tk.RIDGE, bd=2)
        self.camera_frame.grid(row=1, column=1, sticky="nsew", padx=(15, 15), pady=(0, 15))
        self.main_content.grid_columnconfigure(1, weight=2)
        self.camera_frame.grid_propagate(False)
        
        # Create camera view labels
        self.view_labels = {}
        view_names = ['original', 'gray', 'edges', 'infrared']
        for i, name in enumerate(view_names):
            frame = tk.Frame(self.camera_frame, bg="#222", relief=tk.RIDGE, bd=1)
            frame.grid(row=i//2, column=i%2, padx=5, pady=5, sticky="nsew")
            label = ttk.Label(frame, text=f"{name.title()} View", foreground="#fff", background="#222")
            label.pack(expand=True, fill="both")
            self.view_labels[name] = label
        
        # Configure grid weights for camera frame
        self.camera_frame.grid_rowconfigure(0, weight=1)
        self.camera_frame.grid_rowconfigure(1, weight=1)
        self.camera_frame.grid_columnconfigure(0, weight=1)
        self.camera_frame.grid_columnconfigure(1, weight=1)
    
    def _create_log_section(self):
        """Create the logging section"""
        self.log_frame = tk.Frame(self.main_content, bg="#ffffff")
        self.log_frame.grid(row=2, column=0, columnspan=2, sticky="nsew",
                          padx=(30, 15), pady=(0, 15))
        self.main_content.grid_rowconfigure(2, weight=1)
        
        self.log_header = ttk.Label(self.log_frame, text="System Logs", style="Header.TLabel")
        self.log_header.pack(anchor="w", padx=15, pady=10)
        
        self.log_container = tk.Frame(self.log_frame, bg="#ffffff")
        self.log_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        self.log_box = tk.Text(self.log_container, height=10, wrap=tk.WORD,
                             font=('Consolas', 11), bg="#ffffff", relief=tk.FLAT,
                             highlightthickness=1, highlightbackground="#e0e0e0")
        self.log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.log_scrollbar = ttk.Scrollbar(self.log_container, orient="vertical",
                                         command=self.log_box.yview)
        self.log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_box.configure(yscrollcommand=self.log_scrollbar.set)
        
        self.log_box.insert(tk.END, "System Ready...\n")
    
    def _create_button_section(self):
        """Create the button section"""
        self.button_frame = tk.Frame(self.root, bg="#f0f2f5", height=80)
        self.button_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        self.root.grid_rowconfigure(1, weight=0)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        
        # Left buttons
        self.left_buttons = tk.Frame(self.button_frame, bg="#f0f2f5")
        self.left_buttons.grid(row=0, column=0, sticky="w")
        
        self.start_btn = ttk.Button(self.left_buttons, text="▶ Start Monitoring",
                                  command=self.start_monitoring, style="Start.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(self.left_buttons, text="■ Stop Monitoring",
                                 command=self.stop_monitoring, style="Stop.TButton",
                                 state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Right buttons
        self.right_buttons = tk.Frame(self.button_frame, bg="#f0f2f5")
        self.right_buttons.grid(row=0, column=1, sticky="e")
        
        self.contacts_btn = ttk.Button(self.right_buttons, text="📱 Emergency Contacts",
                                     command=self.open_phone_window, style="Contacts.TButton")
        self.contacts_btn.pack(side=tk.LEFT, padx=5)
        
        self.custom_word_btn = ttk.Button(self.right_buttons, text="🔔 Custom Alert Word",
                                        command=self.set_custom_word, style="Custom.TButton")
        self.custom_word_btn.pack(side=tk.LEFT, padx=5)
        
        self.emergency_btn = ttk.Button(self.right_buttons, text="🚨 EMERGENCY SOS",
                                      command=self.trigger_emergency, style="Emergency.TButton")
        self.emergency_btn.pack(side=tk.LEFT, padx=5)
        
        # Add chatbot button to right buttons
        self.chatbot_btn = ttk.Button(self.right_buttons, text="🤖 Chat Bot", 
                                    command=self.start_chatbot, 
                                    style="Custom.TButton")
        self.chatbot_btn.pack(side=tk.LEFT, padx=5)
        
        # Add sensor button to right buttons
        self.sensor_btn = ttk.Button(self.right_buttons, text="Activate", 
                                   command=self.toggle_sensor, 
                                   style="Custom.TButton")
        self.sensor_btn.pack(side=tk.LEFT, padx=5)
    
    def _emotion_callback(self, emotion, confidence, decibel_level, error=None):
        """Callback for emotion monitoring results"""
        if error:
            self.log(f"Emotion detection error: {error}")
            return
            
        self.update_status("Emotion", emotion)
        self.update_status("Confidence", confidence)
        self.update_status("Decibel Level", decibel_level)
        self.log(f"Detected Emotion: {emotion}, Confidence: {confidence}, Decibel Level: {decibel_level}")
    
    def open_phone_window(self):
        PhoneNumberWindow(self.root)
    
    def set_custom_word(self):
        custom_word = simpledialog.askstring("Custom Alert Word",
                                           "Enter a custom word to trigger alerts:",
                                           parent=self.root)
        if custom_word:
            self.custom_trigger_word = custom_word.lower()
            self.log(f"Custom alert word set to: {custom_word}")
            messagebox.showinfo("Success", f"Custom trigger word set to: {custom_word}")
    
    def update_time(self):
        self.time_label.config(text=get_formatted_time())
        self.root.after(1000, self.update_time)
    
    def update_location(self):
        """Update location coordinates"""
        try:
            g = geocoder.ip("me")
            if g.ok:
                lat, lng = g.latlng
                # Update location field with coordinates
                self.update_status("Location", f"Lat: {lat:.4f}, Long: {lng:.4f}")
                # Store coordinates for emergency use
                self.current_location = (lat, lng)
            else:
                self.update_status("Location", "Location unavailable")
        except Exception as e:
            self.log(f"Location update error: {str(e)}")
            self.update_status("Location", "Error")
    
    def trigger_emergency(self):
        """Handle emergency situation"""
        self.log("🚨 EMERGENCY SOS TRIGGERED!")
        self.update_status("SOS Detected", "YES")
        
        # Start beep sound in a separate thread
        def play_beep():
            for _ in range(3):  # Play 3 beeps
                winsound.Beep(1000, 1000)  # 1000Hz for 1 second
        threading.Thread(target=play_beep, daemon=True).start()
        
        # Start recording if not already recording
        if not self.is_recording:
            self.is_recording = True
            self.frames = []
            self.q = Queue()
            self.st = threading.Event()
            threading.Thread(target=record_audio, args=(self.q, self.st), daemon=True).start()
            self.recording_start = time.time()
        
        # Get location
        g = geocoder.ip("me")
        if g.ok:
            lat, lon = g.latlng
            msg = f"""EMERGENCY Lat: {lat:.4f}, Long: {lon:.4f}"""
        else:
            msg = f"""EMERGENCY Location unavailable"""
        
        # Send messages to contacts
        def send_to_all_contacts():
            try:
                with open("emergency_contacts.txt", "r") as f:
                    contacts = [line.strip().split("|") for line in f.readlines()]
                if contacts:
                    self.log("📱 Alerting emergency contacts...")
                    for name, _ in contacts:
                        self.log(f"Sending alert to {name}")
                        try:
                            WhatsAppAutomation.send_message(name, msg, disable_failsafe=True)
                            self.log(f"Alert sent to {name}")
                        except Exception as e:
                            self.log(f"Failed to send alert to {name}: {str(e)}")
                else:
                    self.log("⚠ No emergency contacts found!")
            except FileNotFoundError:
                self.log("⚠ No emergency contacts found!")
            threading.Thread(target=lambda: messagebox.showwarning("EMERGENCY", "🚨 SOS Alert Triggered!"),
                           daemon=True).start()
        
        threading.Thread(target=send_to_all_contacts, daemon=True).start()
    
    def on_closing(self):
        """Handle window closing"""
        if self.monitoring:
            if messagebox.askokcancel("Quit", "Monitoring is still active. Are you sure you want to quit?"):
                self.stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()

    def start_monitoring(self):
        """Start monitoring with proper state management"""
        try:
            self.monitoring = True
            self.camera_running = True
            self.update_status("Monitoring", "Active")
            self.log("Monitoring started.")
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            # Start location updates
            self.update_location()  # Initial location update
            self.location_update_job = self.root.after(30000, self.update_location)  # Update every 30 seconds
            
            # Start camera thread
            self.camera_thread = threading.Thread(target=self.update_camera_feed, daemon=True)
            
            # Start audio monitoring in a separate thread
            self.audio_thread = threading.Thread(target=self._monitor_audio, daemon=True)
            
            # Start emotion monitoring in a separate thread
            self.emotion_thread = threading.Thread(target=self.start_emotion_monitoring, daemon=True)
            
            # Start all threads
            self.camera_thread.start()
            self.audio_thread.start()
            self.emotion_thread.start()
            
            self.log("Camera, audio, and emotion monitoring started simultaneously")
            
        except Exception as e:
            self.log(f"Error starting monitoring: {str(e)}")
            self.monitoring = False
            self.camera_running = False
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def stop_monitoring(self):
        """Stop monitoring with proper cleanup"""
        try:
            
            self.monitoring = False
            self.camera_running = False
            self.sensor_active = False  # Deactivate sensor
            self.update_status("Monitoring", "Inactive")
            self.update_status("Sensor", "Inactive")  # Update sensor status
            self.log("Monitoring stopped.")
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.sensor_btn.configure(text="Activate")  # Reset sensor button
            
            # Cancel location updates
            if hasattr(self, 'location_update_job'):
                self.root.after_cancel(self.location_update_job)
            
            # Clear camera views
            for label in self.view_labels.values():
                label.configure(image='')
            
            # Wait for threads to finish
            if hasattr(self, 'camera_thread') and self.camera_thread.is_alive():
                self.camera_thread.join(timeout=2)
            if hasattr(self, 'audio_thread') and self.audio_thread.is_alive():
                self.audio_thread.join(timeout=2)
            if hasattr(self, 'emotion_thread') and self.emotion_thread.is_alive():
                self.emotion_thread.join(timeout=2)
            if hasattr(self, 'sensor_thread') and self.sensor_thread.is_alive():
                self.sensor_thread.join(timeout=2)
            
            self.log("All monitoring stopped")
            
        except Exception as e:
            self.log(f"Error stopping monitoring: {str(e)}")

    def _monitor_audio(self):
        """Monitor audio for decibel level and speech recognition"""
        while self.monitoring:
            try:
                # Record audio
                audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
                sd.wait()
                
                if not self.monitoring:  # Check if monitoring was stopped
                    break
                
                # Process audio
                audio_array = audio.flatten()
                
                # Get decibel level
                decibels = dbmeter.calculate_decibel(audio_array)
                decibel_str = f"{decibels:.1f} dB"
                
                # Check for SOS triggers
                sos_triggered = False
                
                # Trigger 1: Decibel level check
                if decibels < 25 or decibels > 60:
                    self.log(f"⚠️ Abnormal decibel level detected: {decibel_str}")
                    sos_triggered = True
                
                # Trigger 2: Speech recognition with custom word
                if detect_sos_with_whisper(audio_array, self.custom_trigger_word):
                    self.log(f"⚠️ Custom trigger word '{self.custom_trigger_word}' detected in speech!")
                    sos_triggered = True
                
                # Update UI with results
                self.root.after(0, self.update_status, "Decibel Level", decibel_str)
                
                # Log the results
                self.root.after(0, self.log, f"Audio Analysis - Decibel Level: {decibel_str}")
                
                # Trigger emergency if any condition is met
                if sos_triggered and time.time() - self.last_sos > self.cooldown:
                    self.last_sos = time.time()
                    self.trigger_emergency()
                
                # Wait before next detection
                time.sleep(10)
                
            except Exception as e:
                self.root.after(0, self.log, f"Audio monitoring error: {str(e)}")
                time.sleep(1)

    def start_emotion_monitoring(self):
        """Monitor emotions continuously"""
        while self.monitoring:
            try:
                # Record audio for emotion detection
                audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1, dtype='float32')
                sd.wait()
                
                if not self.monitoring:  # Check if monitoring was stopped
                    break
                
                # Process audio for emotion detection
                audio_array = audio.flatten()
                try:
                    emotion, confidence = predict_emotion(audio_array)
                    confidence_percent = f"{confidence * 100:.2f}%"
                    
                    # Update UI with emotion results
                    self.root.after(0, self.update_status, "Emotion", emotion)
                    self.root.after(0, self.update_status, "Confidence", confidence_percent)
                    self.root.after(0, self.log, f"Detected Emotion: {emotion}, Confidence: {confidence_percent}")
                    
                    # Check for distressed emotions
                    if emotion.lower() in ['fear', 'sad'] and float(confidence) > 0.6:
                        if time.time() - self.last_sos > self.cooldown:
                            self.last_sos = time.time()
                            self.root.after(0, self.trigger_emergency)
                            
                except Exception as e:
                    self.root.after(0, self.log, f"Emotion detection error: {str(e)}")
                
                # Wait before next detection
                time.sleep(10)
                
            except Exception as e:
                self.root.after(0, self.log, f"Emotion monitoring error: {str(e)}")
                time.sleep(1)

    def update_camera_feed(self):
        """Update camera feed with multiple views"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.log("Error: Could not open camera")
            return

        while self.camera_running:
            try:
                ret, frame = cap.read()
                if not ret:
                    continue

                # Resize frame for display
                frame = cv2.resize(frame, (320, 240))
                
                # Create different views with green color scheme
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 100, 200)
                
                # Convert to green color scheme
                green_frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                green_frame[:,:,0] = 0  # Set blue channel to 0
                green_frame[:,:,2] = 0  # Set red channel to 0
                
                # Convert frames to PhotoImage
                original_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                gray_img = Image.fromarray(gray)
                edges_img = Image.fromarray(edges)
                green_img = Image.fromarray(cv2.cvtColor(green_frame, cv2.COLOR_BGR2RGB))
                
                # Resize images
                original_img = original_img.resize((320, 240), Image.Resampling.LANCZOS)
                gray_img = gray_img.resize((320, 240), Image.Resampling.LANCZOS)
                edges_img = edges_img.resize((320, 240), Image.Resampling.LANCZOS)
                green_img = green_img.resize((320, 240), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                original_photo = ImageTk.PhotoImage(image=original_img)
                gray_photo = ImageTk.PhotoImage(image=gray_img)
                edges_photo = ImageTk.PhotoImage(image=edges_img)
                green_photo = ImageTk.PhotoImage(image=green_img)
                
                # Update labels
                self.view_labels['original'].configure(image=original_photo)
                self.view_labels['original'].image = original_photo
                self.view_labels['gray'].configure(image=gray_photo)
                self.view_labels['gray'].image = gray_photo
                self.view_labels['edges'].configure(image=edges_photo)
                self.view_labels['edges'].image = edges_photo
                self.view_labels['infrared'].configure(image=green_photo)
                self.view_labels['infrared'].image = green_photo
                
                # Check for dangerous objects
                results = self.model(frame)
                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        if conf > 0.5:  # Confidence threshold
                            class_name = self.model.names[cls]
                            if class_name in ['knife', 'gun', 'scissors']:
                                self.log(f"⚠️ Dangerous object detected: {class_name} ({conf:.2f})")
                                if time.time() - self.last_sos > self.cooldown:
                                    self.last_sos = time.time()
                                    self.trigger_emergency()
                
                # Check for hand gestures
                with mp_hands.Hands(
                    model_complexity=1,
                    max_num_hands=2,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5) as hands:
                    
                    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    if results.multi_hand_landmarks:
                        for hand_landmarks in results.multi_hand_landmarks:
                            # Check for SOS gesture (three fingers up)
                            landmarks = hand_landmarks.landmark
                            if (landmarks[8].y < landmarks[6].y and  # Index finger up
                                landmarks[12].y < landmarks[10].y and  # Middle finger up
                                landmarks[16].y < landmarks[14].y):  # Ring finger up
                                self.log("⚠️ SOS hand gesture detected!")
                                if time.time() - self.last_sos > self.cooldown:
                                    self.last_sos = time.time()
                                    self.trigger_emergency()
                
                time.sleep(0.03)  # Limit frame rate
                
            except Exception as e:
                self.log(f"Camera error: {str(e)}")
                time.sleep(1)
        
        cap.release()
    
    def update_status(self, field, value):
        if field in self.labels:
            self.labels[field].config(text=value)
    
    def log(self, message):
        timestamp = get_timestamp()
        self.log_box.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_box.see(tk.END)

    def toggle_sensor(self):
        if not self.sensor_active:
            try:
                # Start sensor monitoring in a separate thread
                self.sensor_active = True
                self.sensor_btn.configure(text="Deactivate")
                self.update_status("Sensor", "Active")
                self.log("Sensor activated")
                
                # Define the sensor values
                sensor_values = {
                    "SITTING": [0.77, -0.42, -0.04, -0.18, 0.04, 0.04, -0.04, -0.04, 0.04, -0.04,
                               0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, 0.04, 0.04, 0.04,
                               -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04,
                               -0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, -0.04,
                               0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04],
                    "LAYING": [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                              1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
                    "RUNNING": [-0.31, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04,
                               -0.04, 0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04, -0.04,
                               0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04,
                               0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04,
                               -0.04, 0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04, -0.04],
                    "WALKING_FAST": [
                                0.235, -1.204, 0.389, 0.145, -0.089, -0.220, 0.310, -0.145, 0.066, -0.044,
                                0.289, -0.188, -0.211, 0.104, -0.040, -0.089, 0.201, -0.220, 0.145, -0.289,
                                -0.104, 0.040, 0.188, -0.066, 0.211, -0.145, 0.044, 0.145, -0.044, 0.040,
                                -0.220, 0.289, -0.145, 0.211, -0.089, 0.188, -0.044, 0.145, -0.040, 0.220,
                                    0.104, -0.211, 0.289, 0.145, -0.089, -0.040, 0.220, -0.145, 0.040, 0.104
                                    ],
                    "WALKING_SLOW": [15.79, -7.42, 0.04, -1.97, 0.42, 0.04, -0.04, 0.04, 0.04, -0.04,
                   0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04,
                   -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04,
                   -0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, -0.04,
                   0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04],

                   "SLEEPING": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],

                }
                
                def run_sensor():
                    # Initial 3-second delay
                    time.sleep(3)
                    
                    # Start with SLEEPING
                    state = "SLEEPING"
                    values = sensor_values[state]
                    for _ in range(2):
                        self.log(f"Current state: {state}")
                        self.log(f"Sample values: {values[:5]}...")
                        self.update_status("Sensor", f"Active ({state})")
                        time.sleep(5)
                    
                    # Then WALKING_FAST
                    state = "WALKING_FAST"
                    values = sensor_values[state]
                    for _ in range(2):
                        self.log(f"Current state: {state}")
                        self.log(f"Sample values: {values[:5]}...")
                        self.update_status("Sensor", f"Active ({state})")
                        time.sleep(5)
                    
                    # Continue with random states
                    while self.sensor_active:
                        state = random.choice(list(sensor_values.keys()))
                        values = sensor_values[state]
                        
                        # Repeat each state twice
                        for _ in range(2):
                            self.log(f"Current state: {state}")
                            self.log(f"Sample values: {values[:5]}...")
                            self.update_status("Sensor", f"Active ({state})")
                            time.sleep(5)
                
                # Start the sensor monitoring in a separate thread
                self.sensor_thread = threading.Thread(target=run_sensor, daemon=True)
                self.sensor_thread.start()
                
            except Exception as e:
                self.log(f"Error activating sensor: {str(e)}")
                messagebox.showerror("Error", "Failed to activate sensor")
        else:
            self.sensor_active = False
            self.sensor_btn.configure(text="Activate")
            self.update_status("Sensor", "Inactive")
            self.log("Sensor deactivated")

    def start_chatbot(self):
        """Start the chatbot using subprocess"""
        try:
            # Check if chatbot.py exists
            if not os.path.exists("Final_ChatBot_Int.py"):
                self.log("⚠️ Error: chatbot.py not found!")
                messagebox.showerror("Error", "chatbot.py file not found!")
                return
            
            # Start the chatbot in a new process
            self.log("🤖 Starting Chat Bot...")
            subprocess.Popen(["python", "Final_ChatBot_Int.py"], 
                           creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.log("✅ Chat Bot started successfully!")
            
        except Exception as e:
            error_msg = f"Failed to start Chat Bot: {str(e)}"
            self.log(f"⚠️ {error_msg}")
            messagebox.showerror("Error", error_msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = SOSMonitorApp(root)
    root.mainloop() 