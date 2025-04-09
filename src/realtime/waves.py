import numpy as np
import os
from vispy import app, scene
from vispy.scene import Line, Markers
from scipy.fft import fft, ifft, fftfreq
from vispy.visuals.transforms import STTransform
import math
from src.preprocessing.fourier import load_audio, apply_fft, get_dominant_frequencies
from timeit import default_timer as timer


class Wave3DViewer:

     def __init__(self, filepath):
          # Carrega o áudio
          self.fs, self.signal = load_audio(filepath)
          if self.signal.ndim > 1:
               self.signal = self.signal[:, 0]
               
          """Para o gráfico senoidal no domínio do tempo"""
          # Normaliza
          self.signal = self.signal / np.max(np.abs(self.signal))
          self.time = np.linspace(0, len(self.signal) /
          self.fs, len(self.signal))
          
          # Parâmetros de perspectiva (Z = profundidade crescente)
          self.z = np.linspace(-0.1, 10, len(self.signal))*10  # profundidade
          self.x = self.signal                     # amplitude no eixo X
          # pode dar leve curvatura se quiser
          self.y = np.zeros_like(self.signal)
          """"""""""""""""""""""""""""""

          """Componentes """
          freqs, magnitudes, spectrum = apply_fft(self.signal, self.fs)
          self.dom_freqs = get_dominant_frequencies(
          freqs, magnitudes, threshold=0.05)[:2]
          self.fft_freqs = fftfreq(len(self.signal), 1 / self.fs)
          self.spectrum = spectrum

          # Reconstrói componentes dominantes
          self.comp1 = self.reconstruct_component(self.dom_freqs[0])
          self.comp2 = self.reconstruct_component(self.dom_freqs[1])

          # Parâmetros de perspectiva (Z = profundidade crescente)
          self.z1 = np.linspace(0, 10, len(self.comp1))*30  # profundidade
          self.y1 = self.comp1 *50                    # amplitude no eixo X
          self.x1 = np.zeros_like(self.comp1)

          self.z2 = np.linspace(0, 10, len(self.comp2)) *30 # profundidade
          self.y2 = self.comp2      *50               # amplitude no eixo X
          self.x2 = np.zeros_like(self.comp2)
          """"""""""""""""""""""""""""""

          # Estado da animação
          self.current_index = 0
          self.max_index = len(self.signal)

          self.max_index_comp1 = len(self.comp1)
          self.max_index_comp2 = len(self.comp2)
          self.step = int(self.fs * 0.05)  # 5ms

          # Cria a cena
          self.canvas = scene.SceneCanvas(
          keys='interactive', bgcolor='black', size=(1200, 800), show=True)
          self.view = self.canvas.central_widget.add_view()

          # Câmera fixa, olhando para a profundidade
          self.view.camera = scene.cameras.TurntableCamera(
          elevation=1.0, azimuth=-90.0, distance=5.3, up='y'
          )
          self.view.camera.fov = 45
          self.view.camera.center = (0, 0, 5)  # Começa olhando "pra frente"

          # Curvas
          self.line = Line(pos=np.zeros((2, 3)), color='cyan',
          parent=self.view.scene)
          self.line1 = Line(pos=np.zeros((2, 3)),
          color='magenta', parent=self.view.scene)
          self.line2 = Line(pos=np.zeros((2, 3)),
          color='yellow', parent=self.view.scene)
          

          #self.line1.transform = STTransform(translate=(0, 0, 0))

          # Bolinha (futura navezinha 🎯)
          #    self.marker = Markers(parent=self.view.scene)
          #    self.marker.set_data(pos=np.array(
          #        [[0, 0, 0]]), face_color='red', size=8)

          self.timer = app.Timer(interval=0.01, connect=self.update, start=True)

          # Conecta evento de interação do mouse com a função que imprime a posição da câmera
          self.canvas.events.mouse_move.connect(self.print_camera_position)
          self.canvas.events.mouse_wheel.connect(self.print_camera_position)
          self.canvas.events.key_press.connect(self.print_camera_position)

          # x1 = self.x1[:]
          # y1 = self.y1[:]
          # z1 = self.z1[:]
          # pos1 = np.c_[x1, y1, z1]
          # self.line1.set_data(pos=pos1)

          # x2 = self.x2[:]
          # y2 = self.y2[:]
          # z2 = self.z2[:]
          # pos2 = np.c_[x2, y2, z2]
          # self.line2.set_data(pos=pos2)

          # # Curva principal
          # x = self.x[:]
          # y = self.y[:]
          # z = self.z[:]
          # pos = np.c_[x, y, z]
          # self.line.set_data(pos=pos)

          # Marcação de tempo para controlar animação da câmera
          self.start_time = timer()  # tempo de início
          

     def apply_proportional_zoom(self,line, x, y, z, scale_factor=2.0):
          """
          Aplica um zoom proporcional a um gráfico 3D no VisPy,
          mantendo o centro visual do gráfico constante.

          Args:
               line: objeto Line do VisPy.
               x, y, z: coordenadas do gráfico.
               scale_factor: fator de escala para o eixo Y.
          """
          x_center = np.mean(x)
          y_center = np.mean(y)
          z_center = np.mean(z)

          # Compensação para manter a posição visual do centro após escala
          translate_x = x_center * (1 - scale_factor if scale_factor != 0 else 0)
          translate_y = y_center * (1 - scale_factor if scale_factor != 0 else 0)
          translate_z = z_center * (1 - scale_factor if scale_factor != 0 else 0)

          line.transform = STTransform(
               translate=(translate_x, translate_y, translate_z),
               scale=(1, scale_factor, 1)
          )


     def reconstruct_component(self, target_freq):
          band = (target_freq - 5, target_freq + 5)
          mask = (np.abs(self.fft_freqs) >= band[0]) & (
          np.abs(self.fft_freqs) <= band[1])
          filtered = np.zeros_like(self.spectrum, dtype=complex)
          filtered[mask] = self.spectrum[mask]
          return np.real(ifft(filtered))
     
     def print_camera_position(self, event=None):
          cam = self.view.camera
          print(f"[CÂMERA] center={np.round(cam.center, 2)} | \
               distance={np.round(cam.distance, 2)} | \
                    azimuth={np.round(cam.azimuth, 2)} | \
                         elevation={np.round(cam.elevation, 2)}\n")
          
          # Posição da curva (primeiro e último ponto)
          sine_pos = self.line.pos
          if sine_pos is not None and len(sine_pos) > 0:
               first_s1 = np.round(sine_pos[0], 2)
               last_s1 = np.round(sine_pos[-1], 2)
               print(f"[SENOIDE] início={first_s1} | fim={last_s1}")
               transformed = self.view.scene.transform.map(last_s1)
               print(f"[SENOIDE - transformada] fim (scene coords): {np.round(transformed, 2)}\n")
          
          pos_comp1 = self.line1.pos
          if pos_comp1 is not None and len(pos_comp1) > 0:
               first_c1 = np.round(pos_comp1[0], 2)
               last_c1 = np.round(pos_comp1[-1], 2)
               print(f"[COMPONENTE 1] início={first_c1} | fim={last_c1}")
               transformed1 = self.view.scene.transform.map(last_s1)
               print(
                   f"[COMPONENTE 1 - transformada] fim (scene coords): {np.round(transformed1, 2)}\n")
          
          pos_comp2 = self.line2.pos
          if pos_comp2 is not None and len(pos_comp2) > 0:
               first_c2 = np.round(pos_comp2[0], 2)
               last_c2 = np.round(pos_comp2[-1], 2)
               print(f"[COMPONENTE 2] início={first_c2} | fim={last_c2}")
               transformed2 = self.view.scene.transform.map(last_s1)
               print(
                   f"[COMPONENTE 2 - transformada] fim (scene coords): {np.round(transformed2, 2)}\n")
          
     def update(self, event):
          # Crescimento da curva
          end = min(self.current_index + self.step, self.max_index)
     
          # Curva principal
          x = self.x[:end]
          y = self.y[:end]-0.05
          z = self.z[:end]
          pos = np.c_[x, y, z]
          self.line.set_data(pos=pos)

          # Componente 1
          x1 = self.x1[:end]+0.07
          y1 = self.y1[:end]
          z1 = self.z1[:end]-0.1
          pos1 = np.c_[x1, y1, z1]
          self.line1.set_data(pos=pos1)


          # Componente 2
          x2 = self.x2[:end]-0.07
          y2 = self.y2[:end]
          z2 = self.z2[:end]-0.1
          pos2 = np.c_[x2, y2, z2]
          self.line2.set_data(pos=pos2)
          

          self.current_index = end
          if self.current_index >= self.max_index:
               self.timer.stop()

          # Animação da câmera após 20 segundos
          elapsed = timer() - self.start_time

          if elapsed > 5.0:
               cam = self.view.camera
               cam.distance -= 0.008  # aumenta suavemente


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    AUDIO_PATH = os.path.join(
    BASE_DIR, "..", "..", "data", "raw", "Ludovico Einaudi - Experience.wav")
    
viewer = Wave3DViewer(AUDIO_PATH)
app.run()


