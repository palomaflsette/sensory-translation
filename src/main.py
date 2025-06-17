import time
import threading
import numpy as np
import sounddevice as sd
from collections import deque

from utils.fft_utils import get_dominant_frequency
from utils.winding_utils import generate_winding
from utils.serial_utils import init_serial_connection, send_winding
from mapping.color_mapping import frequency_to_rgb
from visual.visual_layer import VisualLayerManager

SERIAL_PORT = 'COM4'
BAUD_RATE = 115200
SR = 44100  # taxa de amostragem
CHUNK = 1024
ANALYSIS_INTERVAL = 0.1
WINDING_CLEAR_INTERVAL = 5.0
RHYTHM_ANALYSIS_INTERVAL = 2.0

# Configurações para detecção de silêncio
SILENCE_THRESHOLD = 0.05  # Limiar de energia para detectar silêncio
SILENCE_TIME_THRESHOLD = 1.5  # Tempo em segundos para considerar silêncio
consecutive_silence_blocks = 0
last_audio_energy = 0.0

# --- serial e buffer de áudio ---
ser = init_serial_connection(SERIAL_PORT, BAUD_RATE)
AUDIO_BUFFER = deque(maxlen=10 * SR)


def audio_callback(indata, frames, time_info, status):
    if status:
        print(status)
    AUDIO_BUFFER.extend(indata[:, 0])


def detect_silence(block):
    """Detecta se o bloco atual é silêncio"""
    global consecutive_silence_blocks, last_audio_energy

    energy = np.sqrt(np.mean(block**2))
    last_audio_energy = energy

    if energy < SILENCE_THRESHOLD:
        consecutive_silence_blocks += 1
    else:
        consecutive_silence_blocks = 0

    # Considera silêncio se tem muitos blocos consecutivos de baixa energia
    silence_blocks_needed = int(SILENCE_TIME_THRESHOLD / ANALYSIS_INTERVAL)
    is_silent = consecutive_silence_blocks >= silence_blocks_needed

    return is_silent, energy


def send_silence_notification(is_silent):
    """Envia notificação de silêncio para o Arduino"""
    if is_silent:
        ser.write(b'SILENCE:1\n')
    else:
        ser.write(b'SILENCE:0\n')


def real_time_visualization():
    layer_manager = VisualLayerManager(ser)
    print("Iniciando MUSTEM - Visualização com som do eletreto...")
    print("Aguardando áudio...")

    with sd.InputStream(callback=audio_callback, samplerate=SR, channels=1, blocksize=CHUNK):
        start_time = time.time()
        last_silence_state = False

        while True:
            time.sleep(ANALYSIS_INTERVAL * 0.8)
            if len(AUDIO_BUFFER) < CHUNK:
                continue

            current_time = time.time() - start_time
            block = np.array(list(AUDIO_BUFFER)[-CHUNK:])

            # Detectar silêncio
            is_silent, energy = detect_silence(block)

            # Enviar notificação de mudança de estado
            if is_silent != last_silence_state:
                send_silence_notification(is_silent)
                if is_silent:
                    print(f"Silêncio detectado (energia: {energy:.4f})")
                else:
                    print(f"Áudio detectado (energia: {energy:.4f})")
                last_silence_state = is_silent

            # Status detalhado a cada 2 segundos
            if int(current_time) % 2 == 0 and current_time - int(current_time) < ANALYSIS_INTERVAL:
                if is_silent:
                    print(
                        f"Silêncio há {consecutive_silence_blocks * ANALYSIS_INTERVAL:.1f}s (energia: {energy:.4f})")
                else:
                    print(f"🎶 Processando áudio (energia: {energy:.4f})")

            # Se está em silêncio, não processar visualizações
            if is_silent:
                continue

            #  visualizações normalmente quando há áudio
            print(f"🎵 Energia do bloco: {energy:.4f}")

            # atualiza ritmo
            if layer_manager.should_update(current_time, layer_manager.last_rhythm_analysis, RHYTHM_ANALYSIS_INTERVAL):
                rhythm_block = np.array(
                    list(AUDIO_BUFFER)[-int(RHYTHM_ANALYSIS_INTERVAL * SR):])
                layer_manager.update_rhythm(current_time, rhythm_block, SR)

            # Limpa windings se necessário
            if layer_manager.should_clear_windings(current_time, WINDING_CLEAR_INTERVAL):
                layer_manager.clear_windings(current_time)

            # Gera winding
            freq = get_dominant_frequency(block, SR)
            color = frequency_to_rgb(freq)
            fade_factor = max(0.3, min(
                1.0, (WINDING_CLEAR_INTERVAL - (current_time - layer_manager.last_winding_clear))))
            x, y = generate_winding(freq)
            send_winding(ser, x, y, color, fade_factor)
            layer_manager.winding_count += 1

            # Atualiza outras camadas
            if layer_manager.should_update(current_time, layer_manager.last_wave_update, 0.05):
                layer_manager.update_waves(current_time, block, SR)

            if layer_manager.should_update(current_time, layer_manager.last_spectrum_update, 0.15):
                layer_manager.update_spectrum(current_time, block, SR)


def test_silence_sensitivity():
    """Função de teste para ajustar sensibilidade de silêncio"""
    print("🧪 Teste de sensibilidade de silêncio")
    print("Fale próximo ao microfone e observe os valores...")

    with sd.InputStream(callback=audio_callback, samplerate=SR, channels=1, blocksize=CHUNK):
        while True:
            time.sleep(0.2)
            if len(AUDIO_BUFFER) < CHUNK:
                continue

            block = np.array(list(AUDIO_BUFFER)[-CHUNK:])
            energy = np.sqrt(np.mean(block**2))

            status = "SILÊNCIO" if energy < SILENCE_THRESHOLD else "SOM"
            print(f"{status} - Energia: {energy:.6f} (Limite: {SILENCE_THRESHOLD})")


if __name__ == '__main__':
    try:
        #test_silence_sensitivity()
        real_time_visualization()
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuário.")
    finally:
        ser.close()
        print("MUSTEM finalizado!")
