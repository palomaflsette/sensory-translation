"""
Visual Effects Engine - Motor de efeitos visuais
Implementa todos os efeitos visuais do sistema
"""

import pygame
import numpy as np
import math
import colorsys
import time
from typing import List, Tuple, Dict, Optional
from collections import deque
from dataclasses import dataclass
from abc import ABC, abstractmethod

from core.audio_processor import ProcessedAudioData
from visualization.config_visual import VisualConfig


@dataclass
class Particle:
    """Partícula individual do sistema de partículas"""
    x: float
    y: float
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    life: float = 1.0
    max_life: float = 1.0
    size: float = 1.0
    color_hue: float = 0.0
    color_sat: float = 1.0
    color_val: float = 1.0
    gravity_affected: bool = True
    trail: List[Tuple[float, float]] = None

    def __post_init__(self):
        if self.trail is None:
            self.trail = []


class EffectBase(ABC):
    """Classe base para todos os efeitos visuais"""

    def __init__(self, config: VisualConfig):
        self.config = config
        self.enabled = True
        self.alpha = 1.0

    @abstractmethod
    def update(self, audio_data: ProcessedAudioData, dt: float):
        """Atualiza o estado do efeito"""
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Renderiza o efeito"""
        pass


class LorenzAttractor(EffectBase):
    """Atrator de Lorenz modulado por áudio"""

    def __init__(self, config: VisualConfig):
        super().__init__(config)

        # Parâmetros do sistema de Lorenz
        params = config.get_effect_parameters('lorenz_attractor')
        self.sigma_base = params.get('sigma_base', 10.0)
        self.rho_base = params.get('rho_base', 28.0)
        self.beta_base = params.get('beta_base', 8.0/3.0)
        self.modulation_strength = params.get('audio_modulation_strength', 0.5)

        # Estado atual
        self.state = np.array([1.0, 1.0, 1.0], dtype=np.float64)
        self.trail = deque(maxlen=params.get('trail_length', 200))
        self.point_size = params.get('point_size', 3)

        # Cache para otimização
        self.dt = 0.01
        self.scale = 15.0

    def update(self, audio_data: ProcessedAudioData, dt: float):
        """Atualiza o estado do atrator"""
        # Modular parâmetros com dados de áudio
        sigma = self.sigma_base + audio_data.treble_level * self.modulation_strength * 5.0
        rho = self.rho_base + audio_data.bass_level * self.modulation_strength * 10.0
        beta = self.beta_base + audio_data.mid_level * self.modulation_strength * 2.0

        # Modular velocidade de integração
        dt_mod = self.dt + audio_data.amplitude * 0.02

        # Equações de Lorenz
        x, y, z = self.state
        dx = sigma * (y - x)
        dy = x * (rho - z) - y
        dz = x * y - beta * z

        # Integração de Euler
        self.state += np.array([dx, dy, dz]) * dt_mod

        # Adicionar ao trail
        self.trail.append(self.state.copy())

    def render(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Renderiza o atrator com trail"""
        if len(self.trail) < 2:
            return

        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        # Modular escala com amplitude
        current_scale = self.scale * (1.0 + audio_data.amplitude * 0.5)

        # Converter pontos para coordenadas de tela
        screen_points = []
        for i, point in enumerate(self.trail):
            x = center_x + point[0] * current_scale
            y = center_y + point[1] * current_scale

            if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                screen_points.append((int(x), int(y)))

        if len(screen_points) < 2:
            return

        # Renderizar trail com fade
        for i in range(1, len(screen_points)):
            # Fade baseado na posição no trail
            fade = i / len(screen_points)

            # Cor baseada na amplitude e posição
            hue = (audio_data.amplitude + fade * 0.5) % 1.0
            color = self._hsv_to_rgb(
                hue, 0.9, fade * audio_data.amplitude + 0.3)

            # Grossura da linha varia
            thickness = max(1, int(fade * self.point_size *
                            (1 + audio_data.amplitude)))

            try:
                pygame.draw.line(
                    surface, color, screen_points[i-1], screen_points[i], thickness)
            except:
                continue

        # Ponto atual destacado
        if screen_points:
            current_color = self._hsv_to_rgb(audio_data.amplitude, 1.0, 1.0)
            size = self.point_size * (2 + audio_data.amplitude * 3)
            pygame.draw.circle(surface, current_color,
                               screen_points[-1], int(size))

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Converte HSV para RGB"""
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)


class FrequencyBars(EffectBase):
    """Barras de frequência estilo spectrum analyzer"""

    def __init__(self, config: VisualConfig):
        super().__init__(config)

        params = config.get_effect_parameters('frequency_bars')
        self.num_bars = params.get('num_bars', 64)
        self.bar_width_ratio = params.get('bar_width_ratio', 0.8)
        self.smoothing = params.get('smoothing', 0.7)
        self.peak_hold_time = params.get('peak_hold_time', 0.5)
        self.reflection_alpha = params.get('reflection_alpha', 0.3)

        # Estado das barras
        self.bar_heights = np.zeros(self.num_bars)
        self.peak_heights = np.zeros(self.num_bars)
        self.peak_times = np.zeros(self.num_bars)

    def update(self, audio_data: ProcessedAudioData, dt: float):
        """Atualiza alturas das barras"""
        # Simular espectro com base nos dados disponíveis
        freq_bands = audio_data.frequency_bands

        # Criar espectro artificial expandido
        base_spectrum = [
            freq_bands.get('sub_bass', 0) * (1 + np.random.random() * 0.3),
            freq_bands.get('bass', 0) * (1 + np.random.random() * 0.3),
            freq_bands.get('low_mid', 0) * (1 + np.random.random() * 0.2),
            freq_bands.get('mid', 0) * (1 + np.random.random() * 0.2),
            freq_bands.get('high_mid', 0) * (1 + np.random.random() * 0.3),
            freq_bands.get('treble', 0) * (1 + np.random.random() * 0.4),
            freq_bands.get('brilliance', 0) * (1 + np.random.random() * 0.5),
        ]

        # Expandir para número desejado de barras
        spectrum = np.interp(
            np.linspace(0, len(base_spectrum)-1, self.num_bars),
            np.arange(len(base_spectrum)),
            base_spectrum
        )

        # Suavização
        self.bar_heights = (self.bar_heights * self.smoothing +
                            spectrum * (1 - self.smoothing))

        # Atualizar picos
        current_time = time.time()
        for i in range(self.num_bars):
            if self.bar_heights[i] > self.peak_heights[i]:
                self.peak_heights[i] = self.bar_heights[i]
                self.peak_times[i] = current_time
            elif current_time - self.peak_times[i] > self.peak_hold_time:
                # Decay do pico
                self.peak_heights[i] *= 0.95

    def render(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Renderiza as barras de frequência"""
        width = surface.get_width()
        height = surface.get_height()

        bar_width = (width / self.num_bars) * self.bar_width_ratio
        gap_width = width / self.num_bars - bar_width

        for i, magnitude in enumerate(self.bar_heights):
            x = i * (bar_width + gap_width)
            bar_height = magnitude * height * 0.4

            # Cor baseada na frequência
            hue = (i / self.num_bars + audio_data.amplitude * 0.1) % 1.0
            saturation = 0.9 + magnitude * 0.1
            brightness = magnitude * 0.7 + 0.3

            color = self._hsv_to_rgb(hue, saturation, brightness)

            # Barra principal
            if bar_height > 1:
                rect = pygame.Rect(x, height - bar_height,
                                   bar_width, bar_height)
                pygame.draw.rect(surface, color, rect)

                # Gradiente interno (efeito 3D)
                for j in range(int(bar_width) // 2):
                    inner_color = tuple(
                        min(255, int(c * (1 + j * 0.1))) for c in color)
                    inner_rect = pygame.Rect(x + j, height - bar_height + j,
                                             bar_width - 2*j, bar_height - 2*j)
                    if inner_rect.width > 0 and inner_rect.height > 0:
                        pygame.draw.rect(surface, inner_color, inner_rect)

            # Pico
            peak_height = self.peak_heights[i] * height * 0.4
            if peak_height > bar_height + 5:
                peak_rect = pygame.Rect(
                    x, height - peak_height - 3, bar_width, 3)
                peak_color = self._brighten_color(color, 0.5)
                pygame.draw.rect(surface, peak_color, peak_rect)

            # Reflexo
            if bar_height > 10:
                reflection_height = min(
                    bar_height * 0.3, height - (height - bar_height))
                reflection_alpha = int(self.reflection_alpha * 255)

                reflection_color = (*color, reflection_alpha)
                reflection_surface = pygame.Surface(
                    (bar_width, reflection_height), pygame.SRCALPHA)
                reflection_surface.fill(reflection_color)

                surface.blit(reflection_surface, (x, height))

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)

    def _brighten_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        return tuple(min(255, int(c * (1 + factor))) for c in color)


class ParticleSystem(EffectBase):
    """Sistema de partículas reativo"""

    def __init__(self, config: VisualConfig):
        super().__init__(config)

        params = config.get_effect_parameters('particle_explosion')
        self.max_particles = params.get('max_particles', 5000)
        self.particle_life = params.get('particle_life', 2.0)
        self.explosion_force = params.get('explosion_force', 300.0)
        self.gravity = params.get('gravity', 50.0)
        self.air_resistance = params.get('air_resistance', 0.98)

        self.particles: List[Particle] = []
        self.last_beat_time = 0

    def update(self, audio_data: ProcessedAudioData, dt: float):
        """Atualiza sistema de partículas"""
        # Criar explosão no beat
        if audio_data.beat_detected and time.time() - self.last_beat_time > 0.1:
            self._create_explosion(audio_data)
            self.last_beat_time = time.time()

        # Atualizar partículas existentes
        particles_to_remove = []

        for particle in self.particles:
            # Física
            if particle.gravity_affected:
                particle.vy += self.gravity * dt

            particle.vx *= self.air_resistance
            particle.vy *= self.air_resistance
            particle.vz *= self.air_resistance

            particle.x += particle.vx * dt
            particle.y += particle.vy * dt
            particle.z += particle.vz * dt

            # Atualizar vida
            particle.life -= dt / particle.max_life

            # Trail
            if len(particle.trail) > 20:
                particle.trail.pop(0)
            particle.trail.append((particle.x, particle.y))

            # Remover partículas mortas
            if particle.life <= 0:
                particles_to_remove.append(particle)

        # Limpar partículas mortas
        for particle in particles_to_remove:
            self.particles.remove(particle)

        # Limitar número de partículas
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]

    def _create_explosion(self, audio_data: ProcessedAudioData):
        """Cria explosão de partículas"""
        num_particles = int(50 * audio_data.amplitude *
                            (1 + audio_data.bass_level))

        # Centro da explosão (pode ser modulado)
        center_x = pygame.display.get_surface().get_width() // 2
        center_y = pygame.display.get_surface().get_height() // 2

        # Adicionar variação baseada em frequência dominante
        offset_x = math.cos(audio_data.frequency_dominant * 0.01) * 100
        offset_y = math.sin(audio_data.frequency_dominant * 0.01) * 100

        for _ in range(num_particles):
            angle = np.random.random() * 2 * math.pi
            speed = np.random.random() * self.explosion_force * audio_data.amplitude

            # Velocidade inicial
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            vz = (np.random.random() - 0.5) * speed * 0.5

            # Criar partícula
            particle = Particle(
                x=center_x + offset_x + np.random.randint(-20, 20),
                y=center_y + offset_y + np.random.randint(-20, 20),
                z=0,
                vx=vx,
                vy=vy,
                vz=vz,
                life=1.0,
                max_life=self.particle_life * (0.5 + np.random.random()),
                size=2 + np.random.random() * 4,
                color_hue=np.random.random(),
                color_sat=0.8 + np.random.random() * 0.2,
                color_val=0.7 + np.random.random() * 0.3,
                trail=[]
            )

            self.particles.append(particle)

    def render(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Renderiza partículas"""
        for particle in self.particles:
            # Calcular cor com fade
            alpha = particle.life
            color = self._hsv_to_rgb(
                particle.color_hue,
                particle.color_sat,
                particle.color_val * alpha
            )

            # Tamanho baseado na vida
            size = max(1, int(particle.size * alpha))

            # Posição na tela (com perspectiva Z)
            z_factor = 1 + particle.z * 0.001
            screen_x = int(particle.x * z_factor)
            screen_y = int(particle.y * z_factor)

            # Verificar limites da tela
            if (0 <= screen_x < surface.get_width() and
                    0 <= screen_y < surface.get_height()):

                # Desenhar partícula
                pygame.draw.circle(surface, color, (screen_x, screen_y), size)

                # Trail (opcional)
                if len(particle.trail) > 1 and alpha > 0.5:
                    trail_color = (*color, int(alpha * 128))
                    try:
                        trail_points = [(int(x), int(y))
                                        for x, y in particle.trail[-5:]]
                        if len(trail_points) > 1:
                            pygame.draw.lines(
                                surface, color, False, trail_points, 1)
                    except:
                        pass

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)


class PolarFlower(EffectBase):
    """Flores geométricas em coordenadas polares"""

    def __init__(self, config: VisualConfig):
        super().__init__(config)

        params = config.get_effect_parameters('polar_flower')
        self.base_petals = params.get('base_petals', 5)
        self.petal_variation = params.get('petal_variation', 8)
        self.rotation_speed = params.get('rotation_speed', 0.02)
        self.size_modulation = params.get('size_modulation', 1.5)
        self.resolution = params.get('resolution', 200)

        self.rotation_angle = 0.0

    def update(self, audio_data: ProcessedAudioData, dt: float):
        """Atualiza rotação e parâmetros"""
        # Rotação modulada por áudio
        rotation_speed = self.rotation_speed + audio_data.amplitude * 0.1
        self.rotation_angle += rotation_speed

    def render(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Renderiza flores polares"""
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2

        # Parâmetros modulados por áudio
        petals = int(self.base_petals + audio_data.frequency_dominant /
                     200) % self.petal_variation + 3
        base_radius = 80 + audio_data.amplitude * 120

        # Múltiplas camadas de flores
        for layer in range(3):
            layer_factor = 1 - layer * 0.3
            layer_radius = base_radius * layer_factor
            layer_rotation = self.rotation_angle + layer * 0.5

            points = []
            colors = []

            for i in range(self.resolution):
                angle = (2 * math.pi * i / self.resolution) + layer_rotation

                # Equação da rosa polar: r = a * cos(k * θ)
                r = layer_radius * abs(math.cos(petals * angle))
                r *= (1 + audio_data.bass_level * 0.5)  # Modulação por bass

                # Modular raio com diferentes frequências
                if layer == 0:  # Layer principal
                    r *= (1 + audio_data.treble_level * 0.3)
                elif layer == 1:  # Layer média
                    r *= (1 + audio_data.mid_level * 0.4)
                else:  # Layer interna
                    r *= (1 + audio_data.bass_level * 0.2)

                x = center_x + r * math.cos(angle)
                y = center_y + r * math.sin(angle)

                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    points.append((int(x), int(y)))

                    # Cor baseada no ângulo e layer
                    hue = (angle / (2 * math.pi) + layer * 0.2 +
                           audio_data.amplitude * 0.1) % 1.0
                    saturation = 0.8 + audio_data.treble_level * 0.2
                    brightness = layer_factor * \
                        (0.7 + audio_data.amplitude * 0.3)

                    colors.append(self._hsv_to_rgb(
                        hue, saturation, brightness))

            # Desenhar flower
            if len(points) > 3:
                # Desenhar como polígono filled
                try:
                    avg_color = tuple(
                        int(np.mean([c[i] for c in colors])) for i in range(3))
                    pygame.draw.polygon(surface, avg_color,
                                        points[:len(points)//2])
                except:
                    pass

                # Desenhar contorno
                if len(points) > 1:
                    outline_color = self._brighten_color(
                        colors[0], 0.3) if colors else (255, 255, 255)
                    pygame.draw.lines(surface, outline_color, True, points, 2)

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)

    def _brighten_color(self, color: Tuple[int, int, int], factor: float) -> Tuple[int, int, int]:
        return tuple(min(255, int(c * (1 + factor))) for c in color)


class VisualEffectsEngine:
    """Motor principal de efeitos visuais"""

    def __init__(self, width: int, height: int, config: VisualConfig):
        self.width = width
        self.height = height
        self.config = config

        # Inicializar efeitos
        self.effects = {
            'lorenz_attractor': LorenzAttractor(config),
            'frequency_bars': FrequencyBars(config),
            'particle_explosion': ParticleSystem(config),
            'polar_flower': PolarFlower(config)
        }

        # Estado do motor
        self.current_mode_index = 0
        self.last_update_time = time.time()

        # Superfícies para compositing
        self.main_surface = pygame.Surface((width, height))
        self.overlay_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    def next_mode(self):
        """Muda para próximo modo visual"""
        self.current_mode_index = (
            self.current_mode_index + 1) % len(self.config.visual_modes)
        print(f"🎭 Modo: {self.current_mode_name}")

    def set_mode(self, mode_index: int):
        """Define modo específico"""
        if 0 <= mode_index < len(self.config.visual_modes):
            self.current_mode_index = mode_index
            print(f"🎭 Modo: {self.current_mode_name}")

    @property
    def current_mode_name(self) -> str:
        """Nome do modo atual"""
        return self.config.visual_modes[self.current_mode_index]['display_name']

    def update_screen_size(self, width: int, height: int):
        """Atualiza tamanho da tela"""
        self.width = width
        self.height = height
        self.main_surface = pygame.Surface((width, height))
        self.overlay_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    def render_frame(self, audio_data: ProcessedAudioData, target_surface: pygame.Surface):
        """Renderiza frame completo"""
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        # Atualizar efeitos
        current_mode = self.config.visual_modes[self.current_mode_index]
        active_effects = current_mode['effects']

        for effect_name in active_effects:
            if effect_name in self.effects:
                self.effects[effect_name].update(audio_data, dt)

        # Limpar superfícies
        self.main_surface.fill((0, 0, 0))
        self.overlay_surface.fill((0, 0, 0, 0))

        # Renderizar efeitos ativos
        for effect_name in active_effects:
            if effect_name in self.effects:
                if effect_name in ['particle_explosion', 'polar_flower']:
                    # Efeitos overlay
                    self.effects[effect_name].render(
                        self.overlay_surface, audio_data)
                else:
                    # Efeitos principais
                    self.effects[effect_name].render(
                        self.main_surface, audio_data)
                    
                    # Combinar superfícies
                    target_surface.blit(self.main_surface, (0, 0))

                    # Aplicar overlay com blend mode
                    if self.overlay_surface:
                         target_surface.blit(self.overlay_surface, (0, 0),
                                             special_flags=pygame.BLEND_ADD)

                    # Aplicar pós-processamento se necessário
                    self._apply_post_effects(target_surface, audio_data)
                    
    def _apply_post_effects(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Aplica efeitos de pós-processamento"""
        # Aplicar fade/trail effect baseado no background alpha
        bg_alpha = self.config.performance.get('background_alpha', 10)
        if bg_alpha > 0:
            fade_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            fade_surface.fill((0, 0, 0, bg_alpha))
            surface.blit(fade_surface, (0, 0))
        
        # Efeito de flash no beat
        if audio_data.beat_detected:
            flash_intensity = min(100, int(audio_data.amplitude * 150))
            flash_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, flash_intensity))
            surface.blit(flash_surface, (0, 0), special_flags=pygame.BLEND_ADD)
    
    def add_custom_effect(self, name: str, effect: EffectBase):
        """Adiciona efeito personalizado"""
        self.effects[name] = effect
        print(f"✅ Efeito '{name}' adicionado ao motor")
    
    def remove_effect(self, name: str):
        """Remove efeito"""
        if name in self.effects:
            del self.effects[name]
            print(f"🗑️ Efeito '{name}' removido")
    
    def get_performance_stats(self) -> Dict:
        """Retorna estatísticas de performance"""
        active_effects = len([e for e in self.effects.values() if e.enabled])
        total_particles = 0
        
        # Contar partículas
        if 'particle_explosion' in self.effects:
            total_particles = len(self.effects['particle_explosion'].particles)
        
        return {
            'active_effects': active_effects,
            'total_effects': len(self.effects),
            'particles_count': total_particles,
            'current_mode': self.current_mode_name,
            'mode_index': self.current_mode_index
        }


class Waveform3D(EffectBase):
    """Visualização de forma de onda em 3D"""
    
    def __init__(self, config: VisualConfig):
        super().__init__(config)
        
        params = config.get_effect_parameters('waveform_3d')
        self.wave_length = params.get('wave_length', 400)
        self.amplitude_scale = params.get('amplitude_scale', 100)
        self.z_perspective = params.get('z_perspective', 0.3)
        self.line_thickness = params.get('line_thickness', 3)
        
        self.waveform_history = deque(maxlen=self.wave_length)
        self.time_offset = 0
        
    def update(self, audio_data: ProcessedAudioData, dt: float):
        """Atualiza histórico da forma de onda"""
        # Adicionar ponto atual ao histórico
        current_amplitude = audio_data.amplitude
        self.waveform_history.append(current_amplitude)
        
        # Atualizar offset de tempo para animação
        self.time_offset += dt * 2.0
        
    def render(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Renderiza forma de onda 3D"""
        if len(self.waveform_history) < 2:
            return
        
        width = surface.get_width()
        height = surface.get_height()
        center_y = height // 2
        
        # Converter waveform para pontos 3D
        points_3d = []
        for i, amplitude in enumerate(self.waveform_history):
            # Posição X ao longo da tela
            x = (i / len(self.waveform_history)) * width
            
            # Posição Y baseada na amplitude
            y = center_y + amplitude * self.amplitude_scale * math.sin(self.time_offset + i * 0.1)
            
            # Posição Z para perspectiva
            z = math.cos(self.time_offset + i * 0.05) * 100
            
            points_3d.append((x, y, z))
        
        # Converter para pontos 2D com perspectiva
        screen_points = []
        colors = []
        
        for i, (x, y, z) in enumerate(points_3d):
            # Aplicar perspectiva
            perspective_factor = 1 + z * self.z_perspective / 1000
            screen_x = int(x * perspective_factor)
            screen_y = int(y * perspective_factor)
            
            if 0 <= screen_x < width and 0 <= screen_y < height:
                screen_points.append((screen_x, screen_y))
                
                # Cor baseada na profundidade e posição
                hue = (i / len(points_3d) + audio_data.amplitude * 0.2) % 1.0
                brightness = 0.5 + (z + 100) / 200 * 0.5
                color = self._hsv_to_rgb(hue, 0.8, brightness)
                colors.append(color)
        
        # Desenhar linha da forma de onda
        if len(screen_points) > 1:
            for i in range(1, len(screen_points)):
                color = colors[i] if i < len(colors) else (255, 255, 255)
                thickness = max(1, int(self.line_thickness * (colors[i][2] / 255 if i < len(colors) else 1)))
                
                try:
                    pygame.draw.line(surface, color, screen_points[i-1], screen_points[i], thickness)
                except:
                    continue
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)


class JuliaFractal(EffectBase):
    """Fractal de Julia animado"""
    
    def __init__(self, config: VisualConfig):
        super().__init__(config)
        
        params = config.get_effect_parameters('julia_fractal')
        self.max_iterations = params.get('max_iterations', 100)
        self.escape_radius = params.get('escape_radius', 2.0)
        self.zoom_speed = params.get('zoom_speed', 0.01)
        self.c_real_range = params.get('c_real_range', (-0.8, -0.6))
        self.c_imag_range = params.get('c_imag_range', (0.2, 0.3))
        
        self.zoom_level = 1.0
        self.time = 0.0
        
        # Cache para otimização
        self.resolution_scale = 0.5  # Reduzir resolução para performance
        self.cached_fractal = None
        self.cache_update_timer = 0.0
        
    def update(self, audio_data: ProcessedAudioData, dt: float):
        """Atualiza parâmetros do fractal"""
        self.time += dt
        
        # Zoom modulado por amplitude
        zoom_factor = 1.0 + audio_data.amplitude * 0.1
        self.zoom_level *= (1.0 + self.zoom_speed * zoom_factor)
        
        # Resetar zoom periodicamente
        if self.zoom_level > 100:
            self.zoom_level = 1.0
        
        # Atualizar cache periodicamente
        self.cache_update_timer += dt
        
    def render(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Renderiza fractal de Julia"""
        # Atualizar cache se necessário (para performance)
        if self.cache_update_timer > 0.1:  # Atualizar a cada 100ms
            self._update_fractal_cache(surface, audio_data)
            self.cache_update_timer = 0.0
        
        # Renderizar fractal cached
        if self.cached_fractal:
            # Redimensionar para tela cheia
            scaled_fractal = pygame.transform.scale(
                self.cached_fractal, surface.get_size()
            )
            surface.blit(scaled_fractal, (0, 0))
    
    def _update_fractal_cache(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Atualiza cache do fractal"""
        # Resolução reduzida para performance
        cache_width = int(surface.get_width() * self.resolution_scale)
        cache_height = int(surface.get_height() * self.resolution_scale)
        
        if not self.cached_fractal or self.cached_fractal.get_size() != (cache_width, cache_height):
            self.cached_fractal = pygame.Surface((cache_width, cache_height))
        
        # Parâmetros modulados por áudio
        c_real = np.interp(audio_data.bass_level, [0, 1], self.c_real_range)
        c_imag = np.interp(audio_data.treble_level, [0, 1], self.c_imag_range)
        c = complex(c_real, c_imag)
        
        # Gerar fractal
        pixels = pygame.PixelArray(self.cached_fractal)
        
        for x in range(cache_width):
            for y in range(cache_height):
                # Converter coordenadas da tela para plano complexo
                real = (x - cache_width/2) / (cache_width/4) / self.zoom_level
                imag = (y - cache_height/2) / (cache_height/4) / self.zoom_level
                z = complex(real, imag)
                
                # Iteração do fractal de Julia
                iterations = self._julia_iterations(z, c)
                
                # Converter iterações para cor
                if iterations == self.max_iterations:
                    color = (0, 0, 0)  # Interior do fractal
                else:
                    # Cor baseada no número de iterações
                    hue = (iterations / self.max_iterations + audio_data.amplitude) % 1.0
                    saturation = 0.8
                    brightness = min(1.0, iterations / self.max_iterations * 2)
                    color = self._hsv_to_rgb(hue, saturation, brightness)
                
                pixels[x, y] = color
        
        del pixels  # Liberar PixelArray
    
    def _julia_iterations(self, z: complex, c: complex) -> int:
        """Calcula número de iterações para convergência"""
        for i in range(self.max_iterations):
            if abs(z) > self.escape_radius:
                return i
            z = z*z + c
        return self.max_iterations
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)


class EnergyField(EffectBase):
    """Campo de energia baseado em áudio"""
    
    def __init__(self, config: VisualConfig):
        super().__init__(config)
        
        self.grid_size = 32
        self.energy_field = np.zeros((self.grid_size, self.grid_size))
        self.decay_rate = 0.95
        
    def update(self, audio_data: ProcessedAudioData, dt: float):
        """Atualiza campo de energia"""
        # Adicionar energia baseada em frequências
        center = self.grid_size // 2
        
        # Bass no centro
        if audio_data.bass_level > 0.3:
            self._add_energy(center, center, audio_data.bass_level * 2.0, 3)
        
        # Mids nas bordas
        if audio_data.mid_level > 0.2:
            angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
            radius = center * 0.7
            for angle in angles:
                x = int(center + radius * np.cos(angle))
                y = int(center + radius * np.sin(angle))
                self._add_energy(x, y, audio_data.mid_level * 1.5, 2)
        
        # Treble nos cantos
        if audio_data.treble_level > 0.1:
            corners = [(2, 2), (2, self.grid_size-3), (self.grid_size-3, 2), (self.grid_size-3, self.grid_size-3)]
            for x, y in corners:
                self._add_energy(x, y, audio_data.treble_level, 1)
        
        # Decay natural
        self.energy_field *= self.decay_rate
        
        # Difusão
        self.energy_field = self._diffuse_field(self.energy_field)
    
    def _add_energy(self, x: int, y: int, intensity: float, radius: int):
        """Adiciona energia em uma posição"""
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.grid_size and 0 <= ny < self.grid_size:
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance <= radius:
                        falloff = max(0, 1 - distance / radius)
                        self.energy_field[nx, ny] += intensity * falloff
    
    def _diffuse_field(self, field: np.ndarray) -> np.ndarray:
        """Aplica difusão ao campo"""
        # Convolução simples para suavização
        kernel = np.array([[0.05, 0.1, 0.05],
                          [0.1, 0.6, 0.1],
                          [0.05, 0.1, 0.05]])
        
        diffused = np.zeros_like(field)
        
        for i in range(1, field.shape[0] - 1):
            for j in range(1, field.shape[1] - 1):
                diffused[i, j] = np.sum(field[i-1:i+2, j-1:j+2] * kernel)
        
        return diffused
    
    def render(self, surface: pygame.Surface, audio_data: ProcessedAudioData):
        """Renderiza campo de energia"""
        width = surface.get_width()
        height = surface.get_height()
        
        cell_width = width / self.grid_size
        cell_height = height / self.grid_size
        
        # Renderizar campo como gradiente
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                energy = min(1.0, self.energy_field[i, j])
                
                if energy > 0.05:  # Threshold para evitar renderizar energia muito baixa
                    x = int(i * cell_width)
                    y = int(j * cell_height)
                    
                    # Cor baseada na energia
                    hue = (energy + audio_data.amplitude * 0.3) % 1.0
                    saturation = 0.8
                    brightness = energy
                    
                    color = self._hsv_to_rgb(hue, saturation, brightness)
                    
                    # Desenhar célula com transparência
                    alpha = int(energy * 255)
                    cell_surface = pygame.Surface((int(cell_width)+1, int(cell_height)+1), pygame.SRCALPHA)
                    cell_surface.fill((*color, alpha))
                    surface.blit(cell_surface, (x, y))
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        rgb = colorsys.hsv_to_rgb(h, s, v)
        return tuple(int(c * 255) for c in rgb)


# Adicionar novos efeitos ao engine
def register_additional_effects(engine: VisualEffectsEngine):
    """Registra efeitos adicionais no motor"""
    engine.effects['waveform_3d'] = Waveform3D(engine.config)
    engine.effects['julia_fractal'] = JuliaFractal(engine.config)
    engine.effects['energy_field'] = EnergyField(engine.config)
    
    print("✅ Efeitos adicionais registrados: waveform_3d, julia_fractal, energy_field")


# Função de conveniência para criar engine completo
def create_full_visual_engine(width: int, height: int, config: VisualConfig) -> VisualEffectsEngine:
    """Cria motor de efeitos visuais completo com todos os efeitos"""
    engine = VisualEffectsEngine(width, height, config)
    register_additional_effects(engine)
    return engine
