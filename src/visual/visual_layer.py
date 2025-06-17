import time
import numpy as np
from scipy.fft import rfft, rfftfreq
from utils.serial_utils import send_serial_message
from audio.rhythm import RhythmDetector


class VisualLayerManager:
    def __init__(self, ser):
        self.silence_mode = False
        self.ser = ser
        self.last_winding_clear = 0
        self.last_wave_update = 0
        self.last_spectrum_update = 0
        self.last_rhythm_analysis = 0
        self.winding_count = 0
        self.rhythm_detector = RhythmDetector()
        self.spectrum_bands = 10
        self.spectrum_sensitivity = 5000.0

    def should_clear_windings(self, now, interval):
        return (now - self.last_winding_clear) >= interval

    def should_update(self, now, last, interval):
        return (now - last) >= interval

    def clear_windings(self, now):
        send_serial_message(self.ser, "CLEAR_WINDINGS")
        self.last_winding_clear = now
        self.winding_count = 0

    def update_rhythm(self, now, audio_data, sr):
        bpm, strength = self.rhythm_detector.detect_bpm_and_rhythm(audio_data)
        multiplier = self.rhythm_detector.get_tempo_multiplier()
        rhythm_data = f"{bpm:.1f},{strength:.3f},{multiplier:.3f}"
        send_serial_message(self.ser, f"RHYTHM:{rhythm_data}")
        self.last_rhythm_analysis = now
        print(
            f"BPM: {bpm:.1f} | Beat: {strength:.2f} | Tempo: {multiplier:.2f}x")

    def generate_rhythm_sync_spectrum(self, audio_data, sr):
        fft = np.abs(rfft(audio_data))
        freqs = rfftfreq(len(audio_data), 1 / sr)
        bands = np.logspace(np.log10(20), np.log10(
            sr / 2), self.spectrum_bands + 1)

        values = []
        multiplier = self.rhythm_detector.get_tempo_multiplier()
        strength = self.rhythm_detector.beat_strength
        boost = 1.0 + (strength * self.spectrum_sensitivity * multiplier)

        for i in range(self.spectrum_bands):
            mask = (freqs >= bands[i]) & (freqs < bands[i + 1])
            energy = np.mean(fft[mask]) if np.any(mask) else 0
            final = energy * boost
            values.append(min(255, int(final * 100)))

        return ",".join(map(str, values))

    def update_waves(self, now, audio_data, sr):
        # Simulação de atualização de onda
        amplitude = np.mean(np.abs(audio_data))
        dominant_freq = self.get_dominant_frequency(audio_data, sr)
        tempo_multiplier = self.rhythm_detector.get_tempo_multiplier()
        beat_strength = self.rhythm_detector.beat_strength
        wave_data = f"{amplitude:.3f},{dominant_freq:.1f},{tempo_multiplier:.3f},{beat_strength:.3f}"
        send_serial_message(self.ser, f"WAVE:{wave_data}")
        self.last_wave_update = now

    def update_spectrum(self, now, audio_data, sr):
        spectrum_data = self.generate_rhythm_sync_spectrum(audio_data, sr)
        send_serial_message(self.ser, f"SPECTRUM:{spectrum_data}")
        self.last_spectrum_update = now

    def get_dominant_frequency(self, samples, sr):
        if len(samples) == 0:
            return 440.0
        yf = np.abs(rfft(samples))
        xf = rfftfreq(len(samples), 1 / sr)
        idx = np.argmax(yf)
        return xf[idx]
