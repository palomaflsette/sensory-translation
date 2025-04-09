import numpy as np
import os
from vispy import app, scene
from vispy.scene import Line, Markers
from src.preprocessing.fourier import load_audio
from timeit import default_timer as timer


class Wave3DViewer:

     def __init__(self, filepath):
        # Carrega o áudio
        self.fs, self.signal = load_audio(filepath)
        if self.signal.ndim > 1:
            self.signal = self.signal[:, 0]

        # Normaliza
        self.signal = self.signal / np.max(np.abs(self.signal))
        self.time = np.linspace(0, len(self.signal) /
                                self.fs, len(self.signal))

        # Parâmetros de perspectiva (Z = profundidade crescente)
        self.z = np.linspace(-0.1, 10, len(self.signal))  # profundidade
        self.x = self.signal * 1.0                     # amplitude no eixo X
        # pode dar leve curvatura se quiser
        self.y = np.zeros_like(self.signal)

        # Posição inicial: vazio
        self.current_index = 0
        self.max_index = len(self.signal)
        self.step = int(self.fs * 0.005)  # atualiza a cada ~1ms de áudio

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

        # Linha inicial
        self.line = Line(pos=np.zeros((2, 3)), color='cyan',
                         parent=self.view.scene)

        # Bolinha (futura navezinha 🎯)
     #    self.marker = Markers(parent=self.view.scene)
     #    self.marker.set_data(pos=np.array(
     #        [[0, 0, 0]]), face_color='red', size=8)

        # Timer
        self.timer = app.Timer(interval=0.01, connect=self.update, start=True)

        # Conecta evento de interação do mouse com a função que imprime a posição da câmera
        self.canvas.events.mouse_move.connect(self.print_camera_position)
        self.canvas.events.mouse_wheel.connect(self.print_camera_position)
        self.canvas.events.key_press.connect(self.print_camera_position)

        # Marcação de tempo para controlar animação da câmera
        self.start_time = timer()  # tempo de início

     def print_camera_position(self, event=None):
        cam = self.view.camera
        print(f"[CÂMERA] center={np.round(cam.center, 2)} | distance={np.round(cam.distance, 2)} | azimuth={np.round(cam.azimuth, 2)} | elevation={np.round(cam.elevation, 2)}")

        # Posição da curva (primeiro e último ponto)
        pos = self.line.pos
        if pos is not None and len(pos) > 0:
            first = np.round(pos[0], 2)
            last = np.round(pos[-1], 2)
            print(f"[SENOIDE] início={first} | fim={last}")

     def update(self, event):
          # Crescimento da curva
          end = min(self.current_index + self.step, self.max_index)
          x = self.x[:end]
          y = self.y[:end]
          z = self.z[:end]
          pos = np.c_[x, y, z]
          self.line.set_data(pos=pos)

          # if len(pos) > 0:
          #      self.marker.set_data(pos=np.array(
          #           [pos[-1]]), face_color='red', size=8)

          self.current_index = end
          if self.current_index >= self.max_index:
               self.timer.stop()

          # Animação da câmera após 20 segundos
          elapsed = timer() - self.start_time

          if elapsed > 20.0:
               cam = self.view.camera
               cam.distance -= 0.0002  # aumenta suavemente


if __name__ == '__main__':
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    AUDIO_PATH = os.path.join(
        BASE_DIR, "..", "..", "data", "raw", "Ludovico Einaudi - Experience.wav")

    viewer = Wave3DViewer(AUDIO_PATH)
    app.run()
