"""
Communication Manager - Gerenciador de comunicação serial com Arduino
Responsável por estabelecer e manter comunicação com o Arduino Mega
"""

import serial
import threading
import time
import queue
from typing import Callable, Optional
from dataclasses import dataclass
import logging


@dataclass
class RawAudioData:
    """Dados brutos recebidos do Arduino"""
    amplitude: float
    frequency_dominant: float
    bass_level: float
    mid_level: float
    treble_level: float
    beat_detected: bool
    timestamp: float

    @classmethod
    def from_string(cls, data_string: str) -> Optional['RawAudioData']:
        """Cria objeto a partir de string do Arduino"""
        try:
            # Formato: "AMP:123,FREQ:440,BASS:89,MID:76,TREBLE:45,BEAT:1"
            parts = data_string.strip().split(',')
            data_dict = {}

            for part in parts:
                if ':' in part:
                    key, value = part.split(':', 1)
                    data_dict[key] = value

            return cls(
                amplitude=float(data_dict.get('AMP', 0)) /
                1024.0,  # Normalizar ADC
                frequency_dominant=float(data_dict.get('FREQ', 440)),
                bass_level=float(data_dict.get('BASS', 0)) / 1024.0,
                mid_level=float(data_dict.get('MID', 0)) / 1024.0,
                treble_level=float(data_dict.get('TREBLE', 0)) / 1024.0,
                beat_detected=bool(int(data_dict.get('BEAT', 0))),
                timestamp=time.time()
            )

        except (ValueError, KeyError) as e:
            logging.warning(
                f"Erro ao parsear dados do Arduino: {e} - Data: {data_string}")
            return None


class CommunicationManager:
    """Gerenciador de comunicação serial com Arduino"""

    def __init__(self, port: str = 'COM3', baudrate: int = 115200, timeout: float = 0.1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout

        # Estado da conexão
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.is_reading = False

        # Threading
        self.read_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # Callback para processar dados
        self.data_callback: Optional[Callable[[RawAudioData], None]] = None

        # Estatísticas
        self.bytes_received = 0
        self.packets_received = 0
        self.packets_lost = 0
        self.last_packet_time = 0

        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def detect_arduino_ports(self) -> list:
        """Detecta portas COM onde pode haver um Arduino"""
        import serial.tools.list_ports

        arduino_ports = []
        ports = serial.tools.list_ports.comports()

        for port in ports:
            # Procurar por identificadores típicos do Arduino
            if any(keyword in port.description.lower() for keyword in
                   ['arduino', 'ch340', 'cp210', 'ftdi', 'mega']):
                arduino_ports.append(port.device)

        return arduino_ports

    def connect(self) -> bool:
        """Estabelece conexão com Arduino"""
        try:
            # Tentar detectar automaticamente se porta não especificada
            if self.port == 'auto':
                ports = self.detect_arduino_ports()
                if not ports:
                    self.logger.error(
                        "Nenhum Arduino detectado automaticamente")
                    return False
                self.port = ports[0]
                self.logger.info(
                    f"Arduino detectado automaticamente em: {self.port}")

            # Estabelecer conexão
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                write_timeout=1.0
            )

            # Aguardar inicialização do Arduino
            time.sleep(2.5)

            # Limpar buffer inicial
            self.serial_connection.flush()
            self.serial_connection.reset_input_buffer()

            self.is_connected = True
            self.logger.info(
                f"✅ Conectado ao Arduino em {self.port} @ {self.baudrate} baud")

            # Testar comunicação
            return self._test_communication()

        except serial.SerialException as e:
            self.logger.error(f"❌ Erro de conexão serial: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Erro inesperado na conexão: {e}")
            return False

    def _test_communication(self) -> bool:
        """Testa a comunicação com Arduino"""
        self.logger.info("🔍 Testando comunicação...")

        start_time = time.time()
        test_packets = 0

        while time.time() - start_time < 3.0:  # Testar por 3 segundos
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore')
                    if line.strip():
                        data = RawAudioData.from_string(line)
                        if data:
                            test_packets += 1
                            if test_packets >= 5:  # Pelo menos 5 pacotes válidos
                                self.logger.info(
                                    f"✅ Comunicação OK - {test_packets} pacotes recebidos")
                                return True

            except Exception as e:
                self.logger.warning(f"Erro no teste de comunicação: {e}")
                continue

            time.sleep(0.1)

        if test_packets > 0:
            self.logger.warning(
                f"⚠️ Comunicação parcial - apenas {test_packets} pacotes recebidos")
            return True
        else:
            self.logger.error("❌ Nenhum dado válido recebido do Arduino")
            return False

    def start_reading(self, callback: Callable[[RawAudioData], None]):
        """Inicia leitura contínua em thread separada"""
        if not self.is_connected:
            self.logger.error(
                "Não é possível iniciar leitura - Arduino não conectado")
            return False

        self.data_callback = callback
        self.is_reading = True
        self.stop_event.clear()

        # Iniciar thread de leitura
        self.read_thread = threading.Thread(
            target=self._read_loop, daemon=True)
        self.read_thread.start()

        self.logger.info("📡 Leitura de dados iniciada")
        return True

    def _read_loop(self):
        """Loop principal de leitura de dados"""
        consecutive_errors = 0
        max_consecutive_errors = 10

        while not self.stop_event.is_set() and self.is_reading:
            try:
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    # Ler linha do Arduino
                    line = self.serial_connection.readline().decode('utf-8', errors='ignore')

                    if line.strip():
                        # Atualizar estatísticas
                        self.bytes_received += len(line)
                        current_time = time.time()

                        # Parsear dados
                        audio_data = RawAudioData.from_string(line)

                        if audio_data:
                            # Verificar perda de pacotes (simples)
                            if self.last_packet_time > 0:
                                time_diff = current_time - self.last_packet_time
                                if time_diff > 0.1:  # Mais de 100ms sem dados
                                    expected_packets = int(
                                        time_diff / 0.02)  # ~50Hz esperado
                                    if expected_packets > 2:
                                        self.packets_lost += expected_packets - 1

                            self.last_packet_time = current_time
                            self.packets_received += 1
                            consecutive_errors = 0

                            # Enviar dados para callback
                            if self.data_callback:
                                self.data_callback(audio_data)
                        else:
                            self.packets_lost += 1

                else:
                    # Sem dados disponíveis, aguardar um pouco
                    time.sleep(0.001)

            except serial.SerialException as e:
                consecutive_errors += 1
                self.logger.warning(f"Erro de comunicação serial: {e}")

                if consecutive_errors >= max_consecutive_errors:
                    self.logger.error(
                        "Muitos erros consecutivos - encerrando leitura")
                    break

                time.sleep(0.1)

            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Erro inesperado na leitura: {e}")

                if consecutive_errors >= max_consecutive_errors:
                    break

                time.sleep(0.1)

        self.logger.info("📡 Loop de leitura finalizado")

    def send_command(self, command: str) -> bool:
        """Envia comando para o Arduino"""
        if not self.is_connected or not self.serial_connection:
            return False

        try:
            self.serial_connection.write(f"{command}\n".encode())
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar comando: {e}")
            return False

    def get_statistics(self) -> dict:
        """Retorna estatísticas de comunicação"""
        uptime = time.time() - (self.last_packet_time -
                                3600) if self.last_packet_time > 0 else 0

        return {
            'connected': self.is_connected,
            'bytes_received': self.bytes_received,
            'packets_received': self.packets_received,
            'packets_lost': self.packets_lost,
            'packet_loss_rate': self.packets_lost / max(self.packets_received + self.packets_lost, 1),
            'uptime_seconds': uptime,
            'data_rate_bps': self.bytes_received / max(uptime, 1) if uptime > 0 else 0
        }

    def disconnect(self):
        """Desconecta do Arduino"""
        self.logger.info("🔌 Desconectando do Arduino...")

        # Parar leitura
        if self.is_reading:
            self.is_reading = False
            self.stop_event.set()

            # Aguardar thread finalizar
            if self.read_thread and self.read_thread.is_alive():
                self.read_thread.join(timeout=2.0)

        # Fechar conexão serial
        if self.serial_connection:
            try:
                self.serial_connection.close()
            except Exception as e:
                self.logger.warning(f"Erro ao fechar conexão serial: {e}")

        self.is_connected = False
        self.serial_connection = None

        # Log de estatísticas finais
        stats = self.get_statistics()
        self.logger.info(f"📊 Estatísticas finais:")
        self.logger.info(f"   Pacotes recebidos: {stats['packets_received']}")
        self.logger.info(f"   Pacotes perdidos: {stats['packets_lost']}")
        self.logger.info(f"   Taxa de perda: {stats['packet_loss_rate']:.2%}")
        self.logger.info(f"   Bytes recebidos: {stats['bytes_received']}")

        self.logger.info("✅ Desconexão concluída")

    def __del__(self):
        """Destrutor - garantir desconexão"""
        if self.is_connected:
            self.disconnect()
