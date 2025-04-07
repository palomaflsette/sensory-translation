import numpy as np
import scipy.io.wavfile as wav
import matplotlib.pyplot as plt
from typing import Tuple, List


def load_audio(file_path: str) -> Tuple[int, np.ndarray]:
    """
    Carrega um arquivo de áudio .wav

    Returns:
        fs: taxa de amostragem (Hz)
        signal: vetor de amostras do sinal sonoro
    """
    fs, signal = wav.read(file_path)
    # Se o áudio for estéreo, converte para mono
    if len(signal.shape) == 2:
        signal = signal.mean(axis=1)
    return fs, signal


def apply_fft(signal: np.ndarray, fs: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Aplica a FFT no sinal e retorna as frequências e amplitudes.

    Returns:
        freqs: vetor de frequências reais (Hz)
        magnitudes: vetor de magnitudes normalizadas
    """
    N = len(signal)
    fft_result = np.fft.fft(signal)
    # normalização e corte da simetria
    magnitudes = np.abs(fft_result)[:N//2] * 2 / N
    freqs = np.fft.fftfreq(N, d=1/fs)[:N//2]
    return freqs, magnitudes


def get_dominant_frequencies(freqs: np.ndarray, magnitudes: np.ndarray, threshold: float = 0.1) -> List[float]:
    """
    Seleciona as frequências dominantes com base em um limiar de magnitude relativa.

    Returns:
        Lista de frequências dominantes
    """
    max_magnitude = np.max(magnitudes)
    indices = np.where(magnitudes > threshold * max_magnitude)[0]
    return freqs[indices].tolist()


def plot_spectrum(freqs: np.ndarray, magnitudes: np.ndarray, title: str = "Espectro de Frequências") -> None:
    """
    Plota o espectro de frequência.
    """
    plt.figure(figsize=(10, 4))
    plt.plot(freqs, magnitudes, color='orange')
    plt.title(title)
    plt.xlabel("Frequência (Hz)")
    plt.ylabel("Magnitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
