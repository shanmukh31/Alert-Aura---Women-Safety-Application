
import torch
import torch.nn as nn
import librosa
import numpy as np

SAMPLE_RATE = 16000
NUM_MFCC = 40

label_map = {
    0: "Disgust",
    1: "Happy",
    2: "Ps",
    3: "Fear",
    4: "Angry",
    5: "Sad",
    6: "Neutral"
}

class LSTMModel(nn.Module):
    def __init__(self):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size=1, hidden_size=256, batch_first=True)
        self.dropout1 = nn.Dropout(0.2)
        self.fc1 = nn.Linear(256, 128)
        self.dropout2 = nn.Dropout(0.2)
        self.fc2 = nn.Linear(128, 64)
        self.dropout3 = nn.Dropout(0.2)
        self.fc3 = nn.Linear(64, 7)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.dropout1(out[:, -1, :])
        out = torch.relu(self.fc1(out))
        out = self.dropout2(out)
        out = torch.relu(self.fc2(out))
        out = self.dropout3(out)
        out = self.fc3(out)
        return torch.softmax(out, dim=1)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = LSTMModel().to(device)
model.load_state_dict(torch.load('lstm_model2.pth', map_location=device,weights_only=True))
model.eval()

def predict_emotion(audio_array, sample_rate=SAMPLE_RATE):
    mfcc = librosa.feature.mfcc(y=audio_array, sr=sample_rate, n_mfcc=NUM_MFCC)
    mfcc = np.mean(mfcc.T, axis=0).reshape(NUM_MFCC, 1)
    input_tensor = torch.tensor(mfcc, dtype=torch.float32).unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = model(input_tensor)
        pred_class = torch.argmax(output, dim=1).item()
        confidence = output[0][pred_class].item()
    
    return label_map[pred_class], confidence
