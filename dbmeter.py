import numpy as np

def calculate_decibel(audio_data: np.ndarray) -> int:
   
    if audio_data is None or len(audio_data) == 0:
        return 0

    # Root Mean Square (RMS) of the signal
    rms = np.sqrt(np.mean(audio_data**2))

    # Avoid log of zero
    if rms <= 1e-10:
        return 0

    # Convert to decibels
    db = 20 * np.log10(rms)

    # Normalize relative to full-scale (0 dBFS = 1.0 max in float32)
    dbfs = int(db)
    return dbfs
