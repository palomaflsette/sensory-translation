"""
Audio Processor - Processamento e análise de dados de áudio
Processa dados brutos do Arduino e extrai features musicais avançadas
"""

import numpy as np
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from scipy import signal
from scipy.stats import zscore
import logging

from core.communication_manager import RawAudioData


@dataclass
class ProcessedAudioData:
    """Dados de áudio processados e analisados"""
    # Dados básicos
    amplitude: float
    frequency_dominant: float
    bass_level: float
    mid_level: float
    treble_level: float
    beat_detected: bool
    timestamp: float

    # Features avançadas calculadas
    spectral_centroid: float = 0.0
    spectral_rolloff: float = 0.0
    spectral_flux: float = 0.0

    # Análise rítmica
    tempo_bpm: float = 0.0
    beat_confidence: float = 0.0
    rhythm_regularity: float = 0.0

    # Análise harmônica
    harmony_complexity: float = 0.0
    tonal_stability: float = 0.0
    chord_progression_tension: float = 0.0

    # Análise temporal
    attack_time: float = 0.0
    decay_time: float = 0.0
    sustain_level: float = 0.0
    release_time: float = 0.0  # Envelope ADSR

    # Análise de textura
    roughness: float = 0.0
    brightness: float = 0.0
    warmth: float = 0.0

    # Detecção de eventos
    onset_detected: bool = False
    silence_detected: bool = False
    dynamic_change: float = 0.0

    # Features para visualização
    energy_vector: np.ndarray = field(default_factory=lambda: np.zeros(4))
    frequency_bands: Dict[str, float] = field(default_factory=dict)


class AudioProcessor:
    """Processador de áudio em tempo real"""

    def __init__(self, buffer_size: int = 1000, analysis_window: int = 50):
        self.buffer_size = buffer_size
        self.analysis_window = analysis_window

        # Buffers para dados
        self.raw_buffer = deque(maxlen=buffer_size)
        self.processed_buffer = deque(maxlen=buffer_size)

        # Estado do processador
        self.is_running = False
        self.process_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Análise temporal
        self.beat_history = deque(maxlen=100)
        self.tempo_tracker = TempoTracker()
        self.envelope_analyzer = EnvelopeAnalyzer()
        self.harmonic_analyzer = HarmonicAnalyzer()

        # Configurar logging
        self.logger = logging.getLogger(__name__)

        # Estatísticas
        self.samples_processed = 0
        self.processing_time_avg = 0.0

    def add_data(self, raw_data: RawAudioData):
        """Adiciona dados brutos ao buffer de processamento"""
        with self.lock:
            self.raw_buffer.append(raw_data)

    def start(self):
        """Inicia processamento em thread separada"""
        if self.is_running:
            return

        self.is_running = True
        self.process_thread = threading.Thread(
            target=self._processing_loop, daemon=True)
        self.process_thread.start()
        self.logger.info("🔄 Processamento de áudio iniciado")

    def stop(self):
        """Para o processamento"""
        self.is_running = False
        if self.process_thread:
            self.process_thread.join(timeout=2.0)
        self.logger.info("⏹️ Processamento de áudio parado")

    def _processing_loop(self):
        """Loop principal de processamento"""
        while self.is_running:
            try:
                # Verificar se há dados para processar
                if len(self.raw_buffer) < 2:
                    time.sleep(0.001)
                    continue

                start_time = time.time()

                # Processar próximo sample
                with self.lock:
                    raw_data = self.raw_buffer[-1]  # Mais recente
                    recent_data = list(
                        self.raw_buffer)[-min(len(self.raw_buffer), self.analysis_window):]

                # Processar dados
                processed_data = self._process_audio_data(
                    raw_data, recent_data)

                # Adicionar ao buffer processado
                with self.lock:
                    self.processed_buffer.append(processed_data)

                # Atualizar estatísticas
                processing_time = time.time() - start_time
                self.samples_processed += 1
                self.processing_time_avg = (
                    (self.processing_time_avg *
                     (self.samples_processed - 1) + processing_time)
                    / self.samples_processed
                )

                # Controlar taxa de processamento
                time.sleep(max(0, 0.01 - processing_time))  # Máximo ~100Hz

            except Exception as e:
                self.logger.error(f"Erro no processamento: {e}")
                time.sleep(0.1)

    def _process_audio_data(self, current: RawAudioData, history: List[RawAudioData]) -> ProcessedAudioData:
        """Processa dados de áudio e extrai features avançadas"""

        # Análise básica de frequência
        spectral_features = self._analyze_spectral_features(current, history)

        # Análise rítmica
        rhythm_features = self._analyze_rhythm(current, history)

        # Análise harmônica
        harmonic_features = self._analyze_harmony(current, history)

        # Análise de envelope
        envelope_features = self._analyze_envelope(current, history)

        # Análise de textura
        texture_features = self._analyze_texture(current, history)

        # Detecção de eventos
        event_features = self._detect_events(current, history)

        # Features para visualização
        visual_features = self._extract_visual_features(current, history)

        # Construir objeto processado
        processed = ProcessedAudioData(
            # Dados básicos
            amplitude=current.amplitude,
            frequency_dominant=current.frequency_dominant,
            bass_level=current.bass_level,
            mid_level=current.mid_level,
            treble_level=current.treble_level,
            beat_detected=current.beat_detected,
            timestamp=current.timestamp,

            # Features calculadas
            **spectral_features,
            **rhythm_features,
            **harmonic_features,
            **envelope_features,
            **texture_features,
            **event_features,
            **visual_features
        )

        return processed

    def _analyze_spectral_features(self, current: RawAudioData, history: List[RawAudioData]) -> Dict:
        """Análise espectral avançada"""
        if len(history) < 3:
            return {'spectral_centroid': 0.0, 'spectral_rolloff': 0.0, 'spectral_flux': 0.0}

        # Simular centroide espectral baseado nas bandas de frequência
        total_energy = current.bass_level + \
            current.mid_level + current.treble_level + 1e-8

        # Frequências médias das bandas
        bass_freq = 125    # Centro da banda grave
        mid_freq = 2000    # Centro da banda média
        treble_freq = 8000  # Centro da banda aguda

        # Calcular centroide espectral ponderado
        spectral_centroid = (
            (current.bass_level * bass_freq +
             current.mid_level * mid_freq +
             current.treble_level * treble_freq) / total_energy
        )

        # Rolloff espectral (90% da energia)
        cumulative_energy = 0
        rolloff_threshold = total_energy * 0.9

        if current.bass_level >= rolloff_threshold:
            spectral_rolloff = bass_freq
        elif current.bass_level + current.mid_level >= rolloff_threshold:
            spectral_rolloff = mid_freq
        else:
            spectral_rolloff = treble_freq

        # Flux espectral (mudança espectral)
        if len(history) >= 2:
            prev = history[-2]
            flux = abs(current.bass_level - prev.bass_level) + \
                abs(current.mid_level - prev.mid_level) + \
                abs(current.treble_level - prev.treble_level)
        else:
            flux = 0.0

        return {
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'spectral_flux': flux
        }

    def _analyze_rhythm(self, current: RawAudioData, history: List[RawAudioData]) -> Dict:
        """Análise rítmica e detecção de tempo"""

        # Adicionar beat à história
        if current.beat_detected:
            self.beat_history.append(current.timestamp)

        # Calcular BPM baseado nos últimos beats
        tempo_bpm = self.tempo_tracker.calculate_tempo(list(self.beat_history))

        # Confiança do beat (baseada na regularidade)
        beat_confidence = 0.0
        rhythm_regularity = 0.0

        if len(self.beat_history) >= 4:
            # Calcular intervalos entre beats
            intervals = np.diff(list(self.beat_history))
            if len(intervals) > 0:
                mean_interval = np.mean(intervals)
                std_interval = np.std(intervals)

                # Regularidade baseada na variância dos intervalos
                rhythm_regularity = max(
                    0, 1.0 - (std_interval / max(mean_interval, 0.1)))

                # Confiança baseada na consistência
                beat_confidence = min(
                    1.0, rhythm_regularity * min(len(intervals) / 8, 1.0))

        return {
            'tempo_bpm': tempo_bpm,
            'beat_confidence': beat_confidence,
            'rhythm_regularity': rhythm_regularity
        }

    def _analyze_harmony(self, current: RawAudioData, history: List[RawAudioData]) -> Dict:
        """Análise harmônica avançada"""

        # Complexidade harmônica baseada na distribuição espectral
        total_energy = current.bass_level + \
            current.mid_level + current.treble_level + 1e-8

        # Shannon entropy como medida de complexidade
        probs = np.array([current.bass_level, current.mid_level,
                         current.treble_level]) / total_energy
        probs = probs[probs > 1e-8]  # Evitar log(0)

        harmony_complexity = - \
            np.sum(probs * np.log2(probs)) / np.log2(3)  # Normalizado

        # Estabilidade tonal (mudança na freq dominante)
        tonal_stability = 1.0
        if len(history) >= 5:
            recent_freqs = [d.frequency_dominant for d in history[-5:]]
            freq_std = np.std(recent_freqs)
            # Normalizar por 1kHz
            tonal_stability = max(0, 1.0 - (freq_std / 1000.0))

        # Tensão harmônica (baseada em mudanças espectrais)
        chord_progression_tension = 0.0
        if len(history) >= 3:
            # Medir mudanças nas proporções espectrais
            prev = history[-2]
            prev_total = prev.bass_level + prev.mid_level + prev.treble_level + 1e-8

            prev_ratios = np.array(
                [prev.bass_level, prev.mid_level, prev.treble_level]) / prev_total
            curr_ratios = np.array(
                [current.bass_level, current.mid_level, current.treble_level]) / total_energy

            chord_progression_tension = np.linalg.norm(
                curr_ratios - prev_ratios)

        return {
            'harmony_complexity': harmony_complexity,
            'tonal_stability': tonal_stability,
            'chord_progression_tension': chord_progression_tension
        }

    def _analyze_envelope(self, current: RawAudioData, history: List[RawAudioData]) -> Dict:
        """Análise do envelope ADSR"""
        return self.envelope_analyzer.analyze(current, history)

    def _analyze_texture(self, current: RawAudioData, history: List[RawAudioData]) -> Dict:
        """Análise de textura sonora"""

        # Rugosidade (irregularidade do sinal)
        roughness = 0.0
        if len(history) >= 10:
            amplitudes = [d.amplitude for d in history[-10:]]
            roughness = np.std(amplitudes) / (np.mean(amplitudes) + 1e-8)

        # Brilho (energia nas altas frequências)
        total_energy = current.bass_level + \
            current.mid_level + current.treble_level + 1e-8
        brightness = current.treble_level / total_energy

        # Aquecimento (energia nas baixas frequências)
        warmth = current.bass_level / total_energy

        return {
            'roughness': min(roughness, 2.0),  # Limitar valores extremos
            'brightness': brightness,
            'warmth': warmth
        }

    def _detect_events(self, current: RawAudioData, history: List[RawAudioData]) -> Dict:
        """Detecção de eventos musicais"""

        # Detecção de onset (início de nota)
        onset_detected = False
        if len(history) >= 3:
            # Onset baseado em aumento súbito da amplitude
            prev_amp = np.mean([d.amplitude for d in history[-3:-1]])
            if current.amplitude > prev_amp * 1.5 and current.amplitude > 0.1:
                onset_detected = True

        # Detecção de silêncio
        silence_threshold = 0.01
        silence_detected = current.amplitude < silence_threshold

        # Mudança dinâmica
        dynamic_change = 0.0
        if len(history) >= 5:
            recent_amps = [d.amplitude for d in history[-5:]]
            if len(recent_amps) > 0:
                amp_trend = np.polyfit(
                    range(len(recent_amps)), recent_amps, 1)[0]
                dynamic_change = amp_trend  # Positivo = crescendo, negativo = diminuendo

        return {
            'onset_detected': onset_detected,
            'silence_detected': silence_detected,
            'dynamic_change': dynamic_change
        }

    def _extract_visual_features(self, current: RawAudioData, history: List[RawAudioData]) -> Dict:
        """Extrai features específicas para visualização"""

        # Vetor de energia para os 4 motores virtuais
        energy_vector = np.array([
            current.bass_level,
            current.mid_level,
            current.treble_level,
            current.amplitude  # Energia total
        ])

        # Bandas de frequência detalhadas
        frequency_bands = {
            'sub_bass': current.bass_level * 0.7,      # Sub-graves
            'bass': current.bass_level,                 # Graves
            'low_mid': current.mid_level * 0.6,        # Médios baixos
            'mid': current.mid_level,                   # Médios
            'high_mid': current.mid_level * 0.4 + current.treble_level * 0.6,  # Médios altos
            'treble': current.treble_level,            # Agudos
            'brilliance': current.treble_level * 1.2   # Brilho
        }

        return {
            'energy_vector': energy_vector,
            'frequency_bands': frequency_bands
        }

    def get_current_analysis(self) -> Optional[ProcessedAudioData]:
        """Retorna a análise mais recente"""
        with self.lock:
            if self.processed_buffer:
                return self.processed_buffer[-1]
        return None

    def get_recent_analysis(self, samples: int = 50) -> List[ProcessedAudioData]:
        """Retorna análises recentes"""
        with self.lock:
            return list(self.processed_buffer)[-samples:]

    def get_statistics(self) -> Dict:
        """Retorna estatísticas do processador"""
        return {
            'samples_processed': self.samples_processed,
            'buffer_usage': len(self.processed_buffer) / self.buffer_size,
            'processing_time_avg': self.processing_time_avg,
            'is_running': self.is_running,
            'buffer_size': len(self.processed_buffer)
        }

    @property
    def buffer_usage(self) -> float:
        """Retorna uso do buffer como fração"""
        with self.lock:
            return len(self.processed_buffer) / self.buffer_size


class TempoTracker:
    """Rastreador de tempo musical"""

    def __init__(self):
        self.tempo_history = deque(maxlen=20)

    def calculate_tempo(self, beat_times: List[float]) -> float:
        """Calcula BPM baseado nos tempos dos beats"""
        if len(beat_times) < 2:
            return 0.0

        # Calcular intervalos entre beats
        intervals = np.diff(beat_times)

        if len(intervals) == 0:
            return 0.0

        # Filtrar intervalos muito pequenos ou grandes
        valid_intervals = intervals[(intervals > 0.3) & (intervals < 3.0)]

        if len(valid_intervals) == 0:
            return 0.0

        # Calcular BPM médio
        avg_interval = np.mean(valid_intervals)
        bpm = 60.0 / avg_interval

        # Suavizar com histórico
        self.tempo_history.append(bpm)
        smoothed_bpm = np.median(list(self.tempo_history))

        return smoothed_bpm


class EnvelopeAnalyzer:
    """Analisador de envelope ADSR"""

    def __init__(self):
        self.envelope_state = 'release'
        self.peak_amplitude = 0.0
        self.attack_start = 0.0
        self.release_start = 0.0

    def analyze(self, current: RawAudioData, history: List[RawAudioData]) -> Dict:
        """Analisa envelope ADSR"""

        # Valores padrão
        attack_time = 0.0
        decay_time = 0.0
        sustain_level = current.amplitude
        release_time = 0.0

        if len(history) >= 10:
            amplitudes = [d.amplitude for d in history[-10:]]
            times = [d.timestamp for d in history[-10:]]

            # Detectar fases do envelope
            # Possível ataque
            if current.amplitude > max(amplitudes[:-1]) * 1.2:
                self.envelope_state = 'attack'
                self.attack_start = current.timestamp
                self.peak_amplitude = current.amplitude

                # Estimar tempo de ataque
                attack_samples = len(
                    [a for a in amplitudes if a < current.amplitude * 0.9])
                if len(times) > attack_samples:
                    attack_time = times[-1] - times[-(attack_samples + 1)]

            elif self.envelope_state == 'attack' and current.amplitude < self.peak_amplitude * 0.9:
                self.envelope_state = 'decay'
                # Estimar decay time seria mais complexo...

            elif current.amplitude < 0.1:  # Possível release
                if self.envelope_state != 'release':
                    self.release_start = current.timestamp
                    self.envelope_state = 'release'

        return {
            'attack_time': attack_time,
            'decay_time': decay_time,
            'sustain_level': sustain_level,
            'release_time': release_time
        }


class HarmonicAnalyzer:
    """Analisador harmônico avançado"""

    def __init__(self):
        self.key_history = deque(maxlen=50)
        self.chord_history = deque(maxlen=20)

    def analyze_key(self, frequency: float) -> str:
        """Estima a tonalidade baseada na frequência dominante"""
        # Mapeamento simplificado de frequência para nota
        # (Implementação completa requereria análise mais sofisticada)

        if frequency < 100:
            return "C"
        elif frequency < 150:
            return "D"
        elif frequency < 200:
            return "E"
        elif frequency < 300:
            return "F"
        elif frequency < 400:
            return "G"
        elif frequency < 500:
            return "A"
        else:
            return "B"

    def detect_chord_progression(self, recent_keys: List[str]) -> float:
        """Detecta tensão na progressão harmônica"""
        # Implementação simplificada
        # Tensão baseada na frequência de mudanças de tonalidade

        if len(recent_keys) < 3:
            return 0.0

        changes = sum(1 for i in range(1, len(recent_keys))
                      if recent_keys[i] != recent_keys[i-1])

        return min(changes / len(recent_keys), 1.0)
