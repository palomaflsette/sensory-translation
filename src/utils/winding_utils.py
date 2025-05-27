import numpy as np

# --- Parâmetros
POINTS_PER_WINDING = 100


def generate_winding(freq, duration=0.08, points=POINTS_PER_WINDING):
    """
    Gera uma curva winding baseada na frequência fornecida.

    Parâmetros:
    - freq: Frequência dominante (Hz)
    - duration: Duração da curva (segundos)
    - points: Número de pontos da curva

    Retorna:
    - x, y: coordenadas da curva winding
    """
    t = np.linspace(0, duration, points)
    x = 160 + 80 * np.cos(2 * np.pi * freq * t)
    y = 120 + 80 * np.sin(2 * np.pi * freq * t)
    return x, y
