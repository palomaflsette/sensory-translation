import time
from serial import Serial

def init_serial_connection(port='COM4', baud_rate=115200, delay=1.0):
    """
    Inicializa a conexão serial com o Arduino.

    Parâmetros:
    - port: Porta serial (ex: 'COM4')
    - baud_rate: Taxa de transmissão
    - delay: Tempo de espera após iniciar (em segundos)

    Retorna:
    - Objeto serial pronto para uso
    """
    ser = Serial(port, baud_rate)
    time.sleep(delay)
    return ser


def send_serial_message(ser, message):
    """
    Envia uma mensagem genérica pela porta serial.

    Parâmetros:
    - ser: objeto serial
    - message: string a ser enviada
    """
    ser.write(f"{message}\n".encode())
    ser.flush()


def send_winding(ser, x, y, color, fade_factor=1.0, delay=0.0001):
    """
    Envia uma curva winding ao Arduino ponto a ponto.

    Parâmetros:
    - ser: objeto serial
    - x, y: coordenadas da curva
    - color: tupla (r, g, b)
    - fade_factor: fator de opacidade da cor
    - delay: atraso entre pontos (em segundos)
    """
    r, g, b = [int(c * fade_factor) for c in color]
    for xi, yi in zip(x, y):
        ser.write(f"WINDING:{int(xi)},{int(yi)},{r},{g},{b}\n".encode())
        ser.flush()
        time.sleep(delay)
