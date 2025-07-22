import torch
import torch.nn as nn
import numpy as np

# --- Define Model Classes ---
class LiquidLayer(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(LiquidLayer, self).__init__()
        self.w = nn.Parameter(torch.randn(hidden_size, input_size))
        self.alpha = nn.Parameter(torch.rand(hidden_size))

    def forward(self, x):
        z = torch.tanh(self.w @ x.T).T
        return z * self.alpha

class LiquidNeuralNetwork(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(LiquidNeuralNetwork, self).__init__()
        self.liquid = LiquidLayer(input_size, hidden_size)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        x = self.liquid(x)
        x = self.fc(x)
        return x

# --- Load Your Trained Model ---
model = LiquidNeuralNetwork(input_size=50, hidden_size=64, num_classes=4)  # Adjust class count
model.load_state_dict(torch.load("E:\Hack prix\liquid_model.pth"))  # Replace with your model file path
model.eval()

# --- Label Map (adjust based on your training)
label_map = {0: "Walking", 1: "Running", 2: "Sitting", 3: "Standing"}

# --- Predict Function ---
def predict_activity(input_vector):
    assert len(input_vector) == 50, "Input must be 50-dimensional"
    x = torch.tensor([input_vector], dtype=torch.float32)
    with torch.no_grad():
        out = model(x)
        probs = torch.softmax(out, dim=1)
        conf, idx = torch.max(probs, dim=1)
        label = label_map[idx.item()]
        return label, conf.item()
custom_inputs = [
    # First input
    [0.77, -0.42, -0.04, -0.18, 0.04, 0.04, -0.04, -0.04, 0.04, -0.04,
     0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, 0.04, 0.04, 0.04,
     -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04,
     -0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, -0.04,
     0.04, 0.04, -0.04, 0.04, -0.04, 0.04, 0.04, -0.04, 0.04, 0.04],
    
    # Second input
    [-7.141712188720703, -1.3797489404678345, -1.4743244647979736, -2.4590296745300293,
     0.6457638740539551, -2.2333781719207764, -0.8223496675491333, 0.027370205104351997,
     1.4218617677688599, -2.357050895690918, 0.34614503383636475, -0.059048812836408615,
     0.058187127113342285, -0.18423157930374146, 0.28658172488212585, -0.5763775706291199,
     0.3599643409252167, 0.35233256220817566, 0.49848732352256775, 0.32524818181991577,
     -0.28437328338623047, -0.027916865468025208, -0.06733408570289612, -0.07769753038883209,
     -0.2712530791759491, 0.31514036655426025, -0.33227652311325073, 0.2101690024137497,
     -0.2584279775619507, -0.2905064821243286, 0.20229914784431458, -0.2541504204273224,
     0.1986326277256012, -0.14399750530719757, 0.18883685767650604, -0.16962310671806335,
     -0.14629390835762024, 0.19317646324634552, 0.14222189784049988, -0.19504916667938232,
     -0.12527918815612793, 0.20916108787059784, -0.18004125356674194, -0.1210797056555748,
     -0.120667964220047, -0.11558661609888077, 0.15446516871452332, 0.1659548282623291,
     0.11470023542642593, -0.14440909028053284],
    
    # Third input
    [-6.98, -1.41, -1.56, -2.33, 0.72, -2.14, -0.79, 0.03, 1.35, -2.44,
     0.31, -0.07, 0.06, -0.19, 0.28, -0.59, 0.37, 0.33, 0.47, 0.31,
     -0.29, -0.03, -0.06, -0.08, -0.26, 0.32, -0.34, 0.22, -0.27, -0.28,
     0.20, -0.25, 0.21, -0.15, 0.19, -0.16, -0.14, 0.20, 0.14, -0.21,
     -0.12, 0.22, -0.19, -0.13, -0.12, -0.11, 0.16, 0.17, 0.11, -0.15],
    
    # Fourth input (all zeros)
    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    
    # Fifth input (all ones)
    [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
     1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
]
for i, vector in enumerate(custom_inputs, 1):
    label, confidence = predict_activity(vector)
    print(f"Input {i}: {label} ({confidence * 100:.2f}%)")