"""
Visual Configuration - Configurações para o sistema de visualização
Centraliza todas as configurações visuais e parâmetros do sistema
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import numpy as np


class VisualConfig:
    """Classe de configuração para o sistema visual"""

    def __init__(self, config_path: Optional[str] = None):
        # Configurações padrão
        self._load_defaults()

        # Carregar configurações de arquivo se fornecido
        if config_path and os.path.exists(config_path):
            self._load_from_file(config_path)
        else:
            # Tentar carregar do diretório padrão
            default_config = Path(__file__).parent.parent / \
                "data" / "presets" / "default_config.json"
            if default_config.exists():
                self._load_from_file(str(default_config))

    def _load_defaults(self):
        """Carrega configurações padrão"""

        # === CONFIGURAÇÕES DE DISPLAY ===
        self.window_width = 1600
        self.window_height = 900
        self.target_fps = 60
        self.vsync = True
        self.fullscreen = False

        # === CONFIGURAÇÕES DE COMUNICAÇÃO ===
        self.arduino_port = 'COM3'  # ou 'auto' para detecção automática
        self.arduino_baudrate = 115200
        self.connection_timeout = 5.0

        # === CONFIGURAÇÕES DE PROCESSAMENTO ===
        self.audio_buffer_size = 1000
        self.analysis_window = 50
        self.smoothing_factor = 0.1
        self.beat_detection_sensitivity = 1.2

        # === MODOS DE VISUALIZAÇÃO ===
        self.visual_modes = [
            {
                'name': 'full_spectrum',
                'display_name': '🌈 Espectro Completo',
                'effects': ['frequency_bars', 'polar_flower', 'particles'],
                'primary_color_scheme': 'rainbow'
            },
            {
                'name': 'lorenz_focus',
                'display_name': '🌀 Atrator de Lorenz',
                'effects': ['lorenz_attractor', 'trail_effect'],
                'primary_color_scheme': 'dynamic'
            },
            {
                'name': 'particle_storm',
                'display_name': '✨ Tempestade de Partículas',
                'effects': ['particle_explosion', 'waveform_3d', 'energy_field'],
                'primary_color_scheme': 'fire'
            },
            {
                'name': 'frequency_analyzer',
                'display_name': '📊 Analisador de Frequência',
                'effects': ['frequency_bars', 'waveform_3d', 'spectral_waterfall'],
                'primary_color_scheme': 'matrix'
            },
            {
                'name': 'fractal_garden',
                'display_name': '🎭 Jardim Fractal',
                'effects': ['julia_fractal', 'mandelbrot_zoom', 'polar_flower'],
                'primary_color_scheme': 'pastel'
            },
            {
                'name': 'harmonic_space',
                'display_name': '🎼 Espaço Harmônico',
                'effects': ['circle_of_fifths', 'chord_visualization', 'harmonic_rings'],
                'primary_color_scheme': 'gold'
            },
            {
                'name': 'neural_network',
                'display_name': '🧠 Rede Neural',
                'effects': ['neural_visualization', 'connection_web', 'data_flow'],
                'primary_color_scheme': 'cyber'
            },
            {
                'name': 'cosmic_dance',
                'display_name': '🌌 Dança Cósmica',
                'effects': ['galaxy_simulation', 'gravitational_waves', 'star_birth'],
                'primary_color_scheme': 'cosmic'
            }
        ]

        # === ESQUEMAS DE CORES ===
        self.color_schemes = {
            'rainbow': {
                'primary': [255, 0, 0],
                'secondary': [0, 255, 0],
                'tertiary': [0, 0, 255],
                'background': [0, 0, 0],
                'accent': [255, 255, 255],
                'hue_range': (0.0, 1.0),
                'saturation': 0.9,
                'brightness': 0.9
            },
            'dynamic': {
                'primary': [255, 100, 0],
                'secondary': [100, 255, 100],
                'tertiary': [100, 100, 255],
                'background': [5, 5, 15],
                'accent': [255, 255, 200],
                'hue_range': (0.0, 0.8),
                'saturation': 0.8,
                'brightness': 0.95
            },
            'fire': {
                'primary': [255, 50, 0],
                'secondary': [255, 150, 0],
                'tertiary': [255, 255, 0],
                'background': [20, 0, 0],
                'accent': [255, 200, 100],
                'hue_range': (0.0, 0.15),
                'saturation': 1.0,
                'brightness': 1.0
            },
            'matrix': {
                'primary': [0, 255, 0],
                'secondary': [0, 200, 0],
                'tertiary': [0, 150, 0],
                'background': [0, 10, 0],
                'accent': [100, 255, 100],
                'hue_range': (0.25, 0.4),
                'saturation': 0.9,
                'brightness': 0.8
            },
            'pastel': {
                'primary': [255, 182, 193],
                'secondary': [173, 216, 230],
                'tertiary': [221, 160, 221],
                'background': [248, 248, 255],
                'accent': [255, 255, 255],
                'hue_range': (0.8, 1.0),
                'saturation': 0.4,
                'brightness': 0.9
            },
            'gold': {
                'primary': [255, 215, 0],
                'secondary': [255, 165, 0],
                'tertiary': [255, 140, 0],
                'background': [25, 25, 0],
                'accent': [255, 255, 200],
                'hue_range': (0.12, 0.18),
                'saturation': 1.0,
                'brightness': 0.9
            },
            'cyber': {
                'primary': [0, 255, 255],
                'secondary': [255, 0, 255],
                'tertiary': [255, 255, 0],
                'background': [0, 0, 20],
                'accent': [255, 255, 255],
                'hue_range': (0.5, 0.8),
                'saturation': 1.0,
                'brightness': 1.0
            },
            'cosmic': {
                'primary': [75, 0, 130],
                'secondary': [138, 43, 226],
                'tertiary': [72, 61, 139],
                'background': [0, 0, 0],
                'accent': [255, 255, 255],
                'hue_range': (0.7, 0.9),
                'saturation': 0.8,
                'brightness': 0.7
            }
        }

        # === CONFIGURAÇÕES DE EFEITOS ===
        self.effect_parameters = {
            'lorenz_attractor': {
                'sigma_base': 10.0,
                'rho_base': 28.0,
                'beta_base': 8.0/3.0,
                'audio_modulation_strength': 0.5,
                'trail_length': 200,
                'point_size': 3
            },
            'frequency_bars': {
                'num_bars': 64,
                'bar_width_ratio': 0.8,
                'smoothing': 0.7,
                'peak_hold_time': 0.5,
                'reflection_alpha': 0.3
            },
            'particle_explosion': {
                'max_particles': 5000,
                'particle_life': 2.0,
                'explosion_force': 300.0,
                'gravity': 50.0,
                'air_resistance': 0.98
            },
            'polar_flower': {
                'base_petals': 5,
                'petal_variation': 8,
                'rotation_speed': 0.02,
                'size_modulation': 1.5,
                'resolution': 200
            },
            'julia_fractal': {
                'max_iterations': 100,
                'escape_radius': 2.0,
                'zoom_speed': 0.01,
                'c_real_range': (-0.8, -0.6),
                'c_imag_range': (0.2, 0.3)
            },
            'waveform_3d': {
                'wave_length': 400,
                'amplitude_scale': 100,
                'z_perspective': 0.3,
                'line_thickness': 3
            }
        }

        # === CONFIGURAÇÕES DE PERFORMANCE ===
        self.performance = {
            'enable_vsync': True,
            'enable_antialiasing': True,
            'particle_limit': 10000,
            'effect_quality': 'high',  # 'low', 'medium', 'high', 'ultra'
            'background_alpha': 10,    # Trail effect intensity
            'update_frequency': 60     # Hz
        }

        # === CONFIGURAÇÕES DE DEBUG ===
        self.debug = {
            'show_fps': True,
            'show_audio_data': True,
            'show_processing_stats': True,
            'show_effect_info': False,
            'log_level': 'INFO'
        }

        # === CONFIGURAÇÕES EXPERIMENTAIS ===
        self.experimental = {
            'enable_ai_features': False,
            'enable_beat_prediction': True,
            'enable_harmonic_analysis': True,
            'enable_style_transfer': False,
            'neural_enhancement': False
        }

    def _load_from_file(self, config_path: str):
        """Carrega configurações de arquivo JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Atualizar configurações com dados do arquivo
            for section, settings in config_data.items():
                if hasattr(self, section):
                    if isinstance(getattr(self, section), dict):
                        getattr(self, section).update(settings)
                    else:
                        setattr(self, section, settings)
                else:
                    setattr(self, section, settings)

            print(f"✅ Configurações carregadas de: {config_path}")

        except Exception as e:
            print(f"⚠️ Erro ao carregar configurações: {e}")

    def save_to_file(self, config_path: str):
        """Salva configurações em arquivo JSON"""
        try:
            # Criar diretório se não existir
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            # Preparar dados para serialização
            config_data = {}
            for attr_name in dir(self):
                if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                    attr_value = getattr(self, attr_name)

                    # Serializar apenas tipos JSON-compatíveis
                    if isinstance(attr_value, (dict, list, str, int, float, bool)):
                        config_data[attr_name] = attr_value

            # Salvar arquivo
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)

            print(f"✅ Configurações salvas em: {config_path}")

        except Exception as e:
            print(f"❌ Erro ao salvar configurações: {e}")

    def get_current_mode_config(self, mode_index: int) -> Dict:
        """Retorna configuração do modo visual atual"""
        if 0 <= mode_index < len(self.visual_modes):
            return self.visual_modes[mode_index]
        return self.visual_modes[0]  # Fallback para primeiro modo

    def get_color_scheme(self, scheme_name: str) -> Dict:
        """Retorna esquema de cores"""
        return self.color_schemes.get(scheme_name, self.color_schemes['rainbow'])

    def get_effect_parameters(self, effect_name: str) -> Dict:
        """Retorna parâmetros de um efeito específico"""
        return self.effect_parameters.get(effect_name, {})

    def update_audio_sensitivity(self, bass_gain: float = 1.0, mid_gain: float = 1.0,
                                 treble_gain: float = 1.0, beat_sensitivity: float = 1.0):
        """Atualiza sensibilidade de áudio em tempo real"""
        if not hasattr(self, 'audio_gains'):
            self.audio_gains = {}

        self.audio_gains.update({
            'bass_gain': bass_gain,
            'mid_gain': mid_gain,
            'treble_gain': treble_gain,
            'beat_sensitivity': beat_sensitivity
        })

    def get_arduino_ports(self) -> List[str]:
        """Retorna lista de portas possíveis para Arduino"""
        import serial.tools.list_ports

        ports = []
        for port in serial.tools.list_ports.comports():
            if any(keyword in port.description.lower() for keyword in
                   ['arduino', 'ch340', 'cp210', 'ftdi', 'mega', 'usb']):
                ports.append(port.device)

        return ports

    def validate_config(self) -> List[str]:
        """Valida configurações e retorna lista de erros/avisos"""
        issues = []

        # Validar resolução
        if self.window_width < 800 or self.window_height < 600:
            issues.append(
                "⚠️ Resolução muito baixa pode afetar a experiência visual")

        # Validar FPS
        if self.target_fps > 120:
            issues.append("⚠️ FPS muito alto pode causar uso excessivo de CPU")
        elif self.target_fps < 30:
            issues.append(
                "⚠️ FPS muito baixo pode resultar em animações travadas")

        # Validar porta Arduino
        if self.arduino_port != 'auto':
            available_ports = self.get_arduino_ports()
            if self.arduino_port not in available_ports and available_ports:
                issues.append(
                    f"⚠️ Porta {self.arduino_port} não encontrada. Disponíveis: {available_ports}")

        # Validar limites de partículas
        if hasattr(self, 'performance') and self.performance.get('particle_limit', 0) > 50000:
            issues.append("⚠️ Limite de partículas muito alto pode causar lag")

        # Validar esquemas de cores
        for mode in self.visual_modes:
            scheme_name = mode.get('primary_color_scheme')
            if scheme_name not in self.color_schemes:
                issues.append(
                    f"❌ Esquema de cores '{scheme_name}' não encontrado para modo '{mode['name']}'")

        # Validar efeitos
        for mode in self.visual_modes:
            for effect in mode.get('effects', []):
                if effect not in self.effect_parameters:
                    issues.append(
                        f"⚠️ Parâmetros não definidos para efeito '{effect}' no modo '{mode['name']}'")

        # Validar configurações de áudio
        if self.audio_buffer_size < 100 or self.audio_buffer_size > 8192:
            issues.append(
                "⚠️ Tamanho do buffer de áudio fora do range recomendado (100-8192)")

        if self.analysis_window < 10 or self.analysis_window > 500:
            issues.append(
                "⚠️ Janela de análise fora do range recomendado (10-500)")

        return issues

    def get_optimized_settings(self) -> Dict:
        """Retorna configurações otimizadas baseadas no sistema"""
        import psutil

        # Detectar specs do sistema
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)

        optimized = {}

        # Configurações baseadas na CPU
        if cpu_count >= 8:
            optimized['target_fps'] = 60
            optimized['particle_limit'] = 10000
            optimized['effect_quality'] = 'ultra'
        elif cpu_count >= 4:
            optimized['target_fps'] = 45
            optimized['particle_limit'] = 5000
            optimized['effect_quality'] = 'high'
        else:
            optimized['target_fps'] = 30
            optimized['particle_limit'] = 2000
            optimized['effect_quality'] = 'medium'

        # Configurações baseadas na RAM
        if memory_gb < 4:
            optimized['audio_buffer_size'] = 512
            optimized['analysis_window'] = 30
        elif memory_gb < 8:
            optimized['audio_buffer_size'] = 1024
            optimized['analysis_window'] = 50
        else:
            optimized['audio_buffer_size'] = 2048
            optimized['analysis_window'] = 100

        return optimized

    def apply_preset(self, preset_name: str):
        """Aplica um preset de configurações predefinido"""
        presets = {
            'performance': {
                'target_fps': 30,
                'particle_limit': 1000,
                'effect_quality': 'low',
                'enable_antialiasing': False,
                'background_alpha': 20,
                'audio_buffer_size': 512
            },
            'quality': {
                'target_fps': 60,
                'particle_limit': 15000,
                'effect_quality': 'ultra',
                'enable_antialiasing': True,
                'background_alpha': 5,
                'audio_buffer_size': 2048
            },
            'balanced': {
                'target_fps': 45,
                'particle_limit': 5000,
                'effect_quality': 'high',
                'enable_antialiasing': True,
                'background_alpha': 10,
                'audio_buffer_size': 1024
            },
            'debug': {
                'show_fps': True,
                'show_audio_data': True,
                'show_processing_stats': True,
                'show_effect_info': True,
                'log_level': 'DEBUG'
            }
        }

        if preset_name in presets:
            preset_config = presets[preset_name]

            # Aplicar configurações do preset
            for key, value in preset_config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                elif hasattr(self, 'performance') and key in ['particle_limit', 'effect_quality', 'enable_antialiasing', 'background_alpha']:
                    self.performance[key] = value
                elif hasattr(self, 'debug') and key in ['show_fps', 'show_audio_data', 'show_processing_stats', 'show_effect_info', 'log_level']:
                    self.debug[key] = value

            print(f"✅ Preset '{preset_name}' aplicado com sucesso!")
        else:
            print(
                f"❌ Preset '{preset_name}' não encontrado. Disponíveis: {list(presets.keys())}")

    def create_custom_color_scheme(self, name: str, primary: List[int], secondary: List[int],
                                   tertiary: List[int], background: List[int], accent: List[int],
                                   hue_range: Tuple[float, float] = (0.0, 1.0),
                                   saturation: float = 0.8, brightness: float = 0.9):
        """Cria um novo esquema de cores personalizado"""
        self.color_schemes[name] = {
            'primary': primary,
            'secondary': secondary,
            'tertiary': tertiary,
            'background': background,
            'accent': accent,
            'hue_range': hue_range,
            'saturation': saturation,
            'brightness': brightness
        }
        print(f"✅ Esquema de cores '{name}' criado com sucesso!")

    def create_custom_visual_mode(self, name: str, display_name: str, effects: List[str],
                                  color_scheme: str = 'rainbow'):
        """Cria um novo modo visual personalizado"""
        custom_mode = {
            'name': name,
            'display_name': display_name,
            'effects': effects,
            'primary_color_scheme': color_scheme
        }

        # Verificar se o esquema de cores existe
        if color_scheme not in self.color_schemes:
            print(
                f"⚠️ Esquema de cores '{color_scheme}' não encontrado. Usando 'rainbow'.")
            custom_mode['primary_color_scheme'] = 'rainbow'

        self.visual_modes.append(custom_mode)
        print(f"✅ Modo visual '{name}' criado com sucesso!")

    def get_system_info(self) -> Dict:
        """Retorna informações do sistema para otimização"""
        try:
            import psutil
            import platform

            return {
                'platform': platform.system(),
                'cpu_count': psutil.cpu_count(),
                'memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'python_version': platform.python_version()
            }
        except ImportError:
            return {'error': 'psutil não instalado - instale com: pip install psutil'}

    def export_settings_summary(self) -> str:
        """Exporta um resumo das configurações atuais"""
        summary = []
        summary.append("=== RESUMO DAS CONFIGURAÇÕES ===")
        summary.append(f"Resolução: {self.window_width}x{self.window_height}")
        summary.append(f"FPS Alvo: {self.target_fps}")
        summary.append(f"Porta Arduino: {self.arduino_port}")
        summary.append(f"Modos Visuais: {len(self.visual_modes)} disponíveis")
        summary.append(
            f"Esquemas de Cores: {len(self.color_schemes)} disponíveis")

        if hasattr(self, 'performance'):
            summary.append(
                f"Qualidade de Efeitos: {self.performance.get('effect_quality', 'N/A')}")
            summary.append(
                f"Limite de Partículas: {self.performance.get('particle_limit', 'N/A')}")

        # Validar configurações
        issues = self.validate_config()
        if issues:
            summary.append("\n=== AVISOS/PROBLEMAS ===")
            summary.extend(issues)
        else:
            summary.append("\n✅ Todas as configurações estão válidas!")

        return '\n'.join(summary)

    def reset_to_defaults(self):
        """Reseta todas as configurações para os valores padrão"""
        self._load_defaults()
        print("✅ Configurações resetadas para os valores padrão!")

    def auto_detect_arduino(self) -> Optional[str]:
        """Detecta automaticamente a porta do Arduino"""
        try:
            import serial.tools.list_ports

            for port in serial.tools.list_ports.comports():
                # Verificar se é um Arduino baseado no VID/PID ou descrição
                if (hasattr(port, 'vid') and port.vid in [0x2341, 0x1A86, 0x10C4]) or \
                   any(keyword in port.description.lower() for keyword in
                       ['arduino', 'ch340', 'cp210', 'ftdi']):
                    return port.device

            return None
        except ImportError:
            print("⚠️ pyserial não instalado - instale com: pip install pyserial")
            return None

    def interpolate_color(self, color1: List[int], color2: List[int], factor: float) -> List[int]:
        """Interpola entre duas cores"""
        factor = max(0.0, min(1.0, factor))  # Clamp entre 0 e 1

        return [
            int(color1[i] + (color2[i] - color1[i]) * factor)
            for i in range(3)
        ]

    def hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Converte HSV para RGB"""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(r * 255), int(g * 255), int(b * 255)

    def generate_gradient_colors(self, scheme_name: str, steps: int = 64) -> List[Tuple[int, int, int]]:
        """Gera um gradiente de cores baseado em um esquema"""
        scheme = self.get_color_scheme(scheme_name)
        colors = []

        hue_min, hue_max = scheme['hue_range']
        saturation = scheme['saturation']
        brightness = scheme['brightness']

        for i in range(steps):
            hue = hue_min + (hue_max - hue_min) * (i / (steps - 1))
            colors.append(self.hsv_to_rgb(hue, saturation, brightness))

        return colors

    def __str__(self) -> str:
        """Representação string da configuração"""
        return f"VisualConfig(modes={len(self.visual_modes)}, schemes={len(self.color_schemes)}, resolution={self.window_width}x{self.window_height})"

    def __repr__(self) -> str:
        return self.__str__()
