import time
import numpy as np
from scipy.fft import rfft, rfftfreq


class RhythmDetector:
    def __init__(self, sr=44100):
        self.sr = sr
        self.bpm_history = []
        self.current_bpm = 120
        self.beat_strength = 0.0

    def detect_bpm_and_rhythm(self, audio_data):
        try:
            fft = np.abs(rfft(audio_data))
            freqs = rfftfreq(len(audio_data), 1 / self.sr)
            low_freq_energy = np.sum(fft[(freqs >= 20) & (freqs <= 200)])

            window_size = int(0.1 * self.sr)
            energy_windows = [
                np.sum(audio_data[i:i + window_size]**2)
                for i in range(0, len(audio_data) - window_size, window_size // 2)
            ]

            if len(energy_windows) < 4:
                return self.current_bpm, 0.0

            from scipy.signal import find_peaks
            peaks, _ = find_peaks(
                energy_windows, height=np.mean(energy_windows))

            if len(peaks) > 1:
                intervals = np.diff(peaks) * (window_size // 2) / self.sr
                if len(intervals) > 0:
                    avg_interval = np.median(intervals)
                    if avg_interval > 0:
                        detected_bpm = 60.0 / avg_interval
                        if 60 <= detected_bpm <= 200:
                            self.bpm_history.append(detected_bpm)
                            if len(self.bpm_history) > 5:
                                self.bpm_history.pop(0)
                            self.current_bpm = np.median(self.bpm_history)

            current_energy = np.sum(audio_data**2)
            avg_energy = np.mean(energy_windows)
            self.beat_strength = min(1.0, current_energy / (avg_energy + 1e-6))

            return self.current_bpm, self.beat_strength

        except Exception as e:
            print(f"Erro na detecção de ritmo: {e}")
            return self.current_bpm, 0.0

    def get_tempo_multiplier(self):
        return max(0.3, min(3.0, self.current_bpm / 120.0))
