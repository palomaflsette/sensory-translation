from scipy.fft import rfft, rfftfreq
import numpy as np


def get_dominant_frequency(samples, sr):
    """
    Retorna a frequência dominante em um trecho de áudio.

    Parameters:
    - samples (np.ndarray): Sinal de áudio (mono).
    - sr (int): Taxa de amostragem.

    Returns:
    - float: Frequência dominante em Hz.
    """
    if len(samples) == 0:
        return 440.0  # valor padrão caso não haja dados

    yf = np.abs(rfft(samples))
    xf = rfftfreq(len(samples), 1 / sr)
    idx = np.argmax(yf)
    return xf[idx]
