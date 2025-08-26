#!/usr/bin/env python3
"""
Sensory Music System - Main Visualizer Application
Aplicação principal do sistema de visualização musical para deficientes auditivos
"""

import pygame
import sys
import json
from pathlib import Path
from typing import Optional

# Imports locais
from core.communication_manager import CommunicationManager
from core.audio_processor import AudioProcessor
from visualization.visual_effects import VisualEffectsEngine
from visualization.config_visual import VisualConfig


class SensoryMusicVisualizer:
    """Classe principal do sistema de visualização musical"""

    def __init__(self, config_path: Optional[str] = None):
        """Inicializa o visualizador principal"""
        # Carregar configurações
        self.config = VisualConfig(config_path)

        # Inicializar pygame
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.config.window_width, self.config.window_height),
            pygame.DOUBLEBUF | pygame.HWSURFACE
        )
        pygame.display.set_caption("🎵 Sensory Music System - Visual Engine")
        self.clock = pygame.time.Clock()

        # Componentes principais
        self.communication = CommunicationManager(
            port=self.config.arduino_port,
            baudrate=self.config.arduino_baudrate
        )

        self.audio_processor = AudioProcessor(
            buffer_size=self.config.audio_buffer_size
        )

        self.visual_engine = VisualEffectsEngine(
            width=self.config.window_width,
            height=self.config.window_height,
            config=self.config
        )

        # Estado da aplicação
        self.running = True
        self.paused = False
        self.show_debug = True
        self.fullscreen = False

    def initialize_system(self) -> bool:
        """Inicializa todos os componentes do sistema"""
        print("🎵 Iniciando Sensory Music System...")

        # Conectar com Arduino
        if not self.communication.connect():
            print("❌ Falha ao conectar com Arduino")
            return False

        # Iniciar processamento de áudio
        self.audio_processor.start()
        self.communication.start_reading(self.audio_processor.add_data)

        print("✅ Sistema inicializado com sucesso!")
        print("🎮 Controles:")
        print("   SPACE - Trocar modo visual")
        print("   D - Toggle debug info")
        print("   F - Toggle fullscreen")
        print("   P - Pausar/Despausar")
        print("   ESC - Sair")

        return True

    def handle_events(self):
        """Processa eventos do pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_SPACE:
                    self.visual_engine.next_mode()

                elif event.key == pygame.K_d:
                    self.show_debug = not self.show_debug

                elif event.key == pygame.K_f:
                    self.toggle_fullscreen()

                elif event.key == pygame.K_p:
                    self.paused = not self.paused
                    print("⏯️ ", "Pausado" if self.paused else "Retomado")

                elif event.key >= pygame.K_1 and event.key <= pygame.K_9:
                    # Trocar para modo específico
                    mode_index = event.key - pygame.K_1
                    self.visual_engine.set_mode(mode_index)

    def toggle_fullscreen(self):
        """Alterna entre modo fullscreen e janela"""
        self.fullscreen = not self.fullscreen

        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode(
                (self.config.window_width, self.config.window_height)
            )

        # Atualizar engine visual com novo tamanho
        self.visual_engine.update_screen_size(
            self.screen.get_width(),
            self.screen.get_height()
        )

    def render_frame(self):
        """Renderiza um frame completo"""
        if self.paused:
            return

        # Obter dados de áudio processados
        audio_data = self.audio_processor.get_current_analysis()

        if audio_data is None:
            # Sem dados ainda, renderizar tela de espera
            self.render_waiting_screen()
            return

        # Renderizar efeitos visuais
        self.visual_engine.render_frame(audio_data, self.screen)

        # Renderizar debug info se habilitado
        if self.show_debug:
            self.render_debug_info(audio_data)

    def render_waiting_screen(self):
        """Renderiza tela de espera quando não há dados"""
        self.screen.fill((10, 10, 20))

        font = pygame.font.Font(None, 48)
        text = font.render("🎵 Aguardando dados do Arduino...",
                           True, (100, 150, 255))
        text_rect = text.get_rect(center=(self.screen.get_width()//2,
                                          self.screen.get_height()//2))
        self.screen.blit(text, text_rect)

        # Indicador de conexão
        status_font = pygame.font.Font(None, 24)
        status_text = f"📡 Status: {'Conectado' if self.communication.is_connected else 'Desconectado'}"
        status_surface = status_font.render(status_text, True, (150, 150, 150))
        self.screen.blit(status_surface, (20, self.screen.get_height() - 40))

    def render_debug_info(self, audio_data):
        """Renderiza informações de debug"""
        debug_font = pygame.font.Font(None, 24)
        y_offset = 20

        debug_info = [
            f"🎭 Modo: {self.visual_engine.current_mode_name}",
            f"🔊 Amplitude: {audio_data.amplitude:.3f}",
            f"🎼 Freq Dominante: {audio_data.frequency_dominant:.0f} Hz",
            f"🔈 Bass: {audio_data.bass_level:.2f}",
            f"🔉 Mid: {audio_data.mid_level:.2f}",
            f"🔊 Treble: {audio_data.treble_level:.2f}",
            f"💓 Beat: {'🟢' if audio_data.beat_detected else '⭕'}",
            f"⚡ FPS: {self.clock.get_fps():.0f}",
            f"📊 Buffer: {self.audio_processor.buffer_usage:.0%}",
        ]

        for info in debug_info:
            text_surface = debug_font.render(
                info, True, (255, 255, 255), (0, 0, 0, 128))
            self.screen.blit(text_surface, (20, y_offset))
            y_offset += 25

    def main_loop(self):
        """Loop principal da aplicação"""
        while self.running:
            # Processar eventos
            self.handle_events()

            # Renderizar frame
            self.render_frame()

            # Atualizar display
            pygame.display.flip()

            # Controlar FPS
            self.clock.tick(self.config.target_fps)

    def cleanup(self):
        """Limpeza e finalização do sistema"""
        print("🧹 Finalizando sistema...")

        # Parar componentes
        if hasattr(self, 'audio_processor'):
            self.audio_processor.stop()

        if hasattr(self, 'communication'):
            self.communication.disconnect()

        # Finalizar pygame
        pygame.quit()

        print("✅ Sistema finalizado com sucesso!")

    def run(self):
        """Executa o sistema completo"""
        try:
            if not self.initialize_system():
                return False

            self.main_loop()

        except KeyboardInterrupt:
            print("\n🛑 Interrompido pelo usuário")

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            import traceback
            traceback.print_exc()

        finally:
            self.cleanup()

        return True


def main():
    """Função principal"""
    # Verificar argumentos da linha de comando
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]

    # Criar e executar visualizador
    visualizer = SensoryMusicVisualizer(config_path)
    success = visualizer.run()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
