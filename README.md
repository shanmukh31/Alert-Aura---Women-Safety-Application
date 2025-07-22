
# 🚨 Alert Aura – AI-Powered Women Safety Application

> An autonomous, real-time threat detection system integrating gesture recognition, speech emotion detection, crime zone awareness, and sensor-based anomaly detection.

---

## 📌 Overview

**Alert Aura** is an AI-driven multimodal safety system developed to **autonomously detect and respond to emergencies**, particularly focused on enhancing women's safety. Unlike traditional panic-button systems, it **requires no user intervention**, functioning in real-time through camera input, voice emotion, sensor motion, and geolocation-based crime risk.

Developed using **Python, OpenCV, MediaPipe, PyTorch, Librosa**, and other tools, it fuses models for:
- Hand gesture recognition (fist = SOS)
- Emotion detection from speech (e.g., fear, panic)
- Panic keyword detection via speech-to-text
- Decibel-based threat alerts
- Sensor-based motion analysis
- Crime data–based location risk prediction

---

## 🧠 Models & Modules

### 1. 🎤 Speech Emotion Recognition Model (LSTM)
- **Model**: LSTM-based deep learning classifier using the TESS dataset.
- **Input**: Real-time audio from the microphone.
- **Features**: MFCCs extracted using `librosa`.
- **Output**: One of 7 emotions (e.g., Fear, Sad, Happy) + confidence score.
- **Trigger**: Panic-related emotions initiate SOS alert.

> 🧪 Accuracy: **93.21%**

### 2. 🔊 Speech-to-Text & SOS Keyword Detection (Whisper)
- **Model**: OpenAI's `whisper` ASR model.
- **Input**: 5-second audio clips.
- **Detection**: Flags phrases like "help", "save me", or "danger".
- **Output**: If such keywords are found → trigger alert.

> ⚠️ Fast response to verbal cues even in background noise.

### 3. ✊ Gesture Recognition Model (MediaPipe)
- **Framework**: Google's MediaPipe (pretrained).
- **Logic**: Rule-based detection of **fist** gesture using landmark analysis.
- **Output**: Activates full SOS pipeline.
- **Customization**: User can specify missing fingers (e.g., thumb amputee).

> 👁‍🗨 Always-on video monitoring with minimal CPU usage.

### 4. 📍 Location Risk Predictor
- **Logic**: Matches user’s GPS coordinates to a dataset of **Telangana crime statistics (2022)**.
- **Zones**:
  - Red → High crime
  - Orange → Medium
  - Green → Low
- **Output**: Displays zone and influences threat level calculation.

> 🗺️ Offline matching for fast and private use.

### 5. 🌀 Sensor Activity Recognition (Liquid Neural Network)
- **Input**: Accelerometer & gyroscope data.
- **Model**: Liquid Neural Network-based classifier.
- **Classes**: Sitting, walking, running, sleeping, anomaly.
- **Output**: Detects sudden or erratic movement → triggers alert.

> 🔍 Accuracy: **78.05%**, supports on-device edge computation.

### 6. 📢 Decibel Level Meter
- **Function**: Detects unusually loud noise levels (e.g., screaming).
- **Threshold**: >60 dB triggers threat evaluation.
- **Output**: Visual + logical input to SOS handler.

### 7. 🔗 Integrated Decision Engine
- **Input Sources**: Audio emotion, keyword, gesture, motion, decibel, location zone.
- **Logic**: Rule-based system (if-else logic).
- **Triggers**:
  - Send Whatsapp Alerts to emergency contact.
  - Start **video + audio recording** for 5 seconds.
  - Flash SOS warning on-screen.

> 🔁 Modular design → Each model operates independently but reports to a central decision unit.

---

## 🛠️ Tech Stack

| Component         | Tool/Library                          |
|------------------|----------------------------------------|
| Language          | Python 3.10+                           |
| UI Framework      | Tkinter                                |
| ML Libraries      | PyTorch, TensorFlow, Keras, Scikit-learn |
| Audio Processing  | Librosa, SoundDevice                   |
| Video Processing  | OpenCV, MediaPipe, FFmpeg              |
| ASR               | Whisper (OpenAI)                       |
| Geolocation       | Geocoder, Google Maps API (optional)   |
| Dataset           | TESS (speech), Telangana Crime Stats   |

---

## 💻 Installation & Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/yourusername/alert-aura.git
   cd alert-aura
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv aura_env
   source aura_env/bin/activate  # On Windows: aura_env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Download and place the required models:
   - `lstm_model2.pth1` (emotion)
   - `liquid_model` (sensor)
   - Whisper base model will auto-download on first run.

5. Run the integrated application:
   ```bash
   python main_gui.py
   ```

---

## 🎯 Key Features

- Real-time, multi-modal threat detection
- No internet needed for core functions
- Location-based crime zone awareness
- Video/audio evidence auto-capture
- Customization for physical impairments (missing fingers)
- Edge-device optimized & battery-conscious

---

## 📈 Results Snapshot

- Emotion Detection Accuracy: **93.21%**
- Sensor Activity Classification: **78.05%**
- Gesture Detection (Fist): **>95% in bright lighting**
- Keyword Detection (Whisper): **~98% precision**

## 🧑‍💻 Authors

- **N. Sushanth** 
- **D. Shanmukhaditya**  
- **R. Venkata Anirudh** 

---

## 📚 References

- [TESS Dataset](https://tspace.library.utoronto.ca/handle/1807/24487)  
- [MediaPipe Hands](https://google.github.io/mediapipe/)  
- [Whisper ASR](https://github.com/openai/whisper)  
- [Crime Data Source – Govt of India Open Data Portal](https://data.gov.in)
