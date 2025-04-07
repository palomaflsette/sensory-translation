import sys
import os
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))
import numpy as np
from src.preprocessing.fourier import apply_fft, get_dominant_frequencies


def test_apply_fft_with_sine_wave():
    # Gera um sinal senoidal de 440 Hz (nota Lá)
    fs = 44100  # taxa de amostragem
    duration = 1.0  # em segundos
    t = np.linspace(0, duration, int(fs * duration), endpoint=False)
    freq = 440
    x = 0.5 * np.sin(2 * np.pi * freq * t)

    freqs, magnitudes = apply_fft(x, fs)

    # Verifica se há um pico por volta de 440 Hz
    peak_freq = freqs[np.argmax(magnitudes)]
    assert abs(
        peak_freq - freq) < 2, f"Pico esperado em ~{freq}Hz, mas obtido em {peak_freq}Hz"


def test_get_dominant_frequencies_with_threshold():
    # Cria vetor de frequências e magnitudes artificiais
    freqs = np.array([100, 200, 300, 400])
    mags = np.array([0.1, 0.6, 0.05, 0.7])  # threshold = 0.5
    dom_freqs = get_dominant_frequencies(freqs, mags, threshold=0.5)

    assert 200 in dom_freqs and 400 in dom_freqs, "Frequências dominantes não identificadas corretamente"
    assert 100 not in dom_freqs and 300 not in dom_freqs, "Frequências fracas foram incluídas erroneamente"
