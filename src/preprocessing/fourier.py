import numpy as np
import scipy.io.wavfile as wav
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from typing import Tuple, List
import scipy.signal as signal
import librosa


def load_audio(file_path: str) -> Tuple[int, np.ndarray]:
    """
    Carrega um arquivo de áudio .wav

    Returns:
        fs: taxa de amostragem (Hz) - sampling rate, qtd de amostras por segundo
            Pelo teorema de Nyquist, a maior frequencia que conseguimos detectar é fs/2
        signal: vetor de amostras do sinal sonoro
            é o sinal digital, ou seja, a representação numérica do som no domínio do tempo
            
            Se o áudio tiver N amostras, então a duraçao do audio é N/fs, 
            ou seja, duracao = len(signal)/fs
    """
    fs, signal = wav.read(file_path)
    # Se o áudio for estéreo, converte para mono
    if len(signal.shape) == 2:
        signal = signal.mean(axis=1)
    return fs, signal


def apply_fft(signal: np.ndarray, fs: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Aplica a FFT (transformada rápida) no sinal e retorna as frequências e amplitudes.

    Returns:
        freqs: vetor de frequências reais (Hz)
        magnitudes: vetor de magnitudes normalizadas
    """
    N = len(signal)
    fft_result = np.fft.fft(signal)
    
    # normalização e corte da simetria: 
    # pega o módulo de cada número complexo → isso nos dá quão intensa é cada frequência.
    # Porque o resultado da FFT de um sinal real é simétrico e só usamos a metade positiva (frequencias positivas)
    magnitudes = np.abs(fft_result[:N//2]) * 2 / N # * 2/ N é a normalização
    freqs = np.fft.fftfreq(N, d=1/fs)[:N//2] # Gera vetor de frequências correspondentes
    return freqs, magnitudes, fft_result


def apply_stft_with_hamming(signal: np.ndarray, fs: int, window_size: int = 2048, hop_size: int = 512):
    """
    Aplica STFT com janela de Hamming e retorna espectrograma.
    """
    window = np.hamming(window_size)
    stft_result = librosa.stft(signal, n_fft=window_size, hop_length=hop_size, window=window)
    magnitude = np.abs(stft_result)
    freqs = librosa.fft_frequencies(sr=fs, n_fft=window_size)
    return freqs, magnitude


def generate_winding(signal: np.ndarray, fs: int, freq: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Gera a curva winding para uma dada frequência.
    Na essência, é uma visualização em coordenadas complexas da integral da 
    transformada de Fourier: cada frequência “roda” o sinal como se ele 
    orbitasse no plano complexo. A massa do centro nos mostra o quanto essa 
    frequência contribui.

    Args:
        signal: sinal no domínio do tempo.
        fs: taxa de amostragem.
        freq: frequência a ser analisada.

    Returns:
        Tuple (x, y): coordenadas da curva winding no plano complexo.
    """
    t = np.arange(len(signal)) / fs
    complex_exponential = np.exp(-2j * np.pi * freq * t)
    winding = signal * complex_exponential
    x = winding.real
    y = winding.imag
    return x, y


def get_dominant_frequencies(freqs: np.ndarray, magnitudes: np.ndarray, threshold: float = 0.01) -> List[float]:
    """
    Seleciona as frequências dominantes com base em um limiar de magnitude relativa.

    Returns:
        Lista de frequências dominantes
    """
    max_magnitude = np.max(magnitudes)
    indices = np.where(magnitudes > threshold * max_magnitude)[0]
    return freqs[indices].tolist()


def plot_time_domain(signal: np.ndarray, fs: int, title: str = "Sinal no Domínio do Tempo") -> None:
    duration = len(signal) / fs
    time = np.linspace(0, duration, len(signal))
    plt.figure(figsize=(12, 4))
    plt.plot(time, signal, color='blue')
    plt.title(title)
    plt.xlabel("Tempo (s)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


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


def plot_time_components(signal: np.ndarray, fs: int, freqs: List[float], duration: float = 1.0) -> None:
    """
    Plota as componentes senoidais correspondentes a frequências fornecidas,
    reconstruídas a partir da FFT do sinal original.

    Args:
        signal: vetor com o sinal no tempo (mono)
        fs: taxa de amostragem do sinal
        freqs: lista de frequências a extrair (em Hz)
        duration: tempo (em segundos) a ser exibido nos gráficos
    """
    from scipy.fft import fft, ifft, fftfreq

    N = len(signal)
    t = np.arange(N) / fs
    spectrum = fft(signal)
    fft_freqs = fftfreq(N, 1/fs)

    # Constrói os sinais por faixa de frequência
    components = []

    for f in freqs:
        band = (f - 5, f + 5)  # faixa de ±5Hz ao redor da frequência alvo
        filtered = np.zeros_like(spectrum, dtype=complex)
        mask = (np.abs(fft_freqs) >= band[0]) & (np.abs(fft_freqs) <= band[1])
        filtered[mask] = spectrum[mask]
        reconstructed = np.real(ifft(filtered))
        components.append(reconstructed)

    # Plotar
    num_plots = len(freqs)
    max_samples = int(fs * duration)
    time_axis = t[:max_samples]

    plt.figure(figsize=(12, 2.5 * num_plots))
    for i, comp in enumerate(components):
        plt.subplot(num_plots, 1, i + 1)
        plt.plot(time_axis, comp[:max_samples])
        plt.title(f"Componente: ~{freqs[i]} Hz")
        plt.xlabel("Tempo (s)")
        plt.ylabel("Amplitude")
        plt.grid(True)

    plt.tight_layout()
    plt.show()


def plot_frequency_components(signal: np.ndarray, fs: int, freqs: List[float], bandwidth: float = 10.0) -> None:
    """
    Plota os espectros (no domínio da frequência) das componentes senoidais
    centradas nas frequências fornecidas, reconstruídas a partir da FFT do sinal.

    Args:
        signal: vetor com o sinal no tempo (mono)
        fs: taxa de amostragem do sinal
        freqs: lista de frequências centrais (em Hz) a analisar
        bandwidth: largura da faixa (em Hz) em torno da frequência central
    """
    from scipy.fft import fft, ifft, fftfreq

    N = len(signal)
    spectrum = fft(signal)
    fft_freqs = fftfreq(N, 1/fs)

    plt.figure(figsize=(12, 2.5 * len(freqs)))

    for i, f in enumerate(freqs):
        band = (f - bandwidth / 2, f + bandwidth / 2)
        filtered = np.zeros_like(spectrum, dtype=complex)
        mask = (np.abs(fft_freqs) >= band[0]) & (np.abs(fft_freqs) <= band[1])
        filtered[mask] = spectrum[mask]
        reconstructed = np.real(ifft(filtered))

        # FFT da componente reconstruída
        component_spectrum = np.abs(fft(reconstructed))[:N // 2] * 2 / N
        component_freqs = fft_freqs[:N // 2]

        plt.subplot(len(freqs), 1, i + 1)
        plt.plot(component_freqs, component_spectrum)
        plt.title(f"Espectro da Componente ~{f:.2f} Hz")
        plt.xlabel("Frequência (Hz)")
        plt.ylabel("Magnitude")
        plt.grid(True)

    plt.tight_layout()
    plt.show()
    
def plot_winding(signal: np.ndarray, fs: int, freq: float, duration: float = 1.0) -> None:
    """
    Plota a curva winding para uma frequência específica.

    Args:
        signal: vetor com o sinal de entrada.
        fs: taxa de amostragem.
        freq: frequência para a curva winding.
        duration: duração do sinal em segundos a ser usada para plot.
    """
    n_samples = int(fs * duration)
    x, y = generate_winding(signal[:n_samples], fs, freq)

    plt.figure(figsize=(6, 6))
    plt.plot(x, y, color='cyan')
    plt.scatter(np.mean(x), np.mean(y), color='red', label='Centro de Massa')
    plt.title(f"Winding - {freq:.2f} Hz")
    plt.xlabel("Re")
    plt.ylabel("Im")
    plt.grid(True)
    plt.axis("equal")
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_signal_in_time(filepath: str, duration: float = 5.0):
    """
    Plota o gráfico no tempo da senoide da música original.
    
    Parameters:
        filepath (str): caminho do arquivo .wav
        duration (float): duração (em segundos) a ser exibida no gráfico
    """
    fs, signal = load_audio(filepath)

    # Garante mono
    if signal.ndim > 1:
        signal = signal[:, 0]

    # Recorta os primeiros segundos
    max_samples = int(fs * duration)
    time = np.linspace(0, duration, max_samples)
    signal = signal[:max_samples]

    plt.figure(figsize=(12, 4))
    plt.plot(time, signal, color='deepskyblue')
    plt.title(f"Sinal no tempo (primeiros {duration} segundos)")
    plt.xlabel("Tempo (s)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# # Exemplo de uso
# PATH = '../../data/raw/Ludovico Einaudi - Experience.wav'
# fs, signal = load_audio(PATH)
# freqs, magnitudes, _ = apply_fft(signal, fs)
# dominantes = get_dominant_frequencies(freqs, magnitudes, threshold=0.05)


# plot_signal_in_time(PATH)

# plot_time_components(signal, fs, dominantes[:2])
# plot_frequency_components(signal, fs, dominantes[:7])

# for freq in dominantes[:7]:
#     plot_winding(signal, fs, freq, duration=0.25)
