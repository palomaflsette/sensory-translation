import time
import threading
import numpy as np
import soundfile as sf
import sounddevice as sd
from utils.fft_utils import get_dominant_frequency
from utils.winding_utils import generate_winding
from utils.serial_utils import init_serial_connection, send_winding
from mapping.color_mapping import frequency_to_rgb
from visual.visual_layer import VisualLayerManager

SERIAL_PORT = 'COM4'
BAUD_RATE = 115200
ANALYSIS_INTERVAL = 0.1
WINDING_CLEAR_INTERVAL = 5.0
RHYTHM_ANALYSIS_INTERVAL = 2.0

ser = init_serial_connection(SERIAL_PORT, BAUD_RATE)


def analyze_and_send_visuals(data, sr, start_time):
    analysis_samples = int(ANALYSIS_INTERVAL * sr)
    current_pos = 0
    layer_manager = VisualLayerManager(ser)

    print("Iniciando visualização com camadas rítmicas...")

    while current_pos + analysis_samples < len(data):
        current_time = time.time() - start_time
        expected_pos = int(current_time * sr)
        if current_pos < expected_pos:
            current_pos = max(current_pos, expected_pos - analysis_samples)

        block = data[current_pos:current_pos + analysis_samples]

        # Atualiza ritmo
        if layer_manager.should_update(current_time, layer_manager.last_rhythm_analysis, RHYTHM_ANALYSIS_INTERVAL):
            rhythm_samples = int(RHYTHM_ANALYSIS_INTERVAL * sr)
            rhythm_start = max(0, current_pos - rhythm_samples // 2)
            rhythm_end = min(len(data), current_pos + rhythm_samples // 2)
            rhythm_block = data[rhythm_start:rhythm_end]
            layer_manager.update_rhythm(current_time, rhythm_block, sr)

        # Limpa windings se necessário
        if layer_manager.should_clear_windings(current_time, WINDING_CLEAR_INTERVAL):
            layer_manager.clear_windings(current_time)

        # Gera winding
        freq = get_dominant_frequency(block, sr)
        color = frequency_to_rgb(freq)
        fade_factor = max(0.3, min(
            1.0, (WINDING_CLEAR_INTERVAL - (current_time - layer_manager.last_winding_clear))))
        x, y = generate_winding(freq)
        send_winding(ser, x, y, color, fade_factor)
        layer_manager.winding_count += 1

        # Atualiza outras camadas (onda, espectro)
        if layer_manager.should_update(current_time, layer_manager.last_wave_update, 0.05):
            layer_manager.update_waves(current_time, block, sr)

        if layer_manager.should_update(current_time, layer_manager.last_spectrum_update, 0.15):
            layer_manager.update_spectrum(current_time, block, sr)

        current_pos += analysis_samples
        time.sleep(ANALYSIS_INTERVAL * 0.8)


def play_with_visualization(file_path):
    data, sr = sf.read(file_path)
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    print(f"Reproduzindo: {file_path}")
    sd.play(data, sr)
    start_time = time.time()

    thread = threading.Thread(
        target=analyze_and_send_visuals, args=(data, sr, start_time))
    thread.daemon = True
    thread.start()
    sd.wait()


try:
    play_with_visualization("../assets/samples/Rush - YYZ.wav")
except KeyboardInterrupt:
    print("Interrompido pelo usuário.")
    sd.stop()
finally:
    ser.close()
