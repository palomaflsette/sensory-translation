#include <MCUFRIEND_kbv.h>
#include <Adafruit_GFX.h>

MCUFRIEND_kbv tft;

#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240
#define ELETRETO_PIN A8

// Configurações de análise de áudio simples
#define SAMPLES 32  // Amostras para análise
#define AMPLITUDE_THRESHOLD 30  // Limiar para detectar som
#define SILENCE_THRESHOLD_MS 2000  // 2 segundos para considerar silêncio

// Buffer para análise simples
int audioSamples[SAMPLES];
int sampleIndex = 0;

// Estados e buffers
struct AudioAnalysis {
  float dominantFreq;
  float amplitude;
  float energy;
  unsigned long lastUpdate;
  bool isActive;
};

struct BeatDetection {
  float bpm;
  float strength;
  float tempoMultiplier;
  unsigned long lastBeat;
  unsigned long lastAnalysis;
  float energyHistory[8];
  int historyIndex;
};

struct SpectrumData {
  float bands[6];  // Reduzido para 6 bandas simples
  unsigned long lastUpdate;
  float smoothedBands[6];
};

struct WindingData {
  float phase;
  int pointCount;
  unsigned long lastClear;
  unsigned long lastUpdate;
  float fadeAmount;
};

// Instâncias globais
AudioAnalysis audio;
BeatDetection beat;
SpectrumData spectrum;
WindingData winding;

// Estados de silêncio
bool isInSilence = false;
bool hasShownSilenceMessage = false;
unsigned long silenceStartTime = 0;
unsigned long lastAudioTime = 0;
int currentSilenceMessage = 0;
float textAnimPhase = 0.0;
unsigned long lastTextUpdate = 0;

// Configurações de timing
const unsigned long AUDIO_INTERVAL = 30;      // 33 Hz
const unsigned long WINDING_INTERVAL = 40;    // 25 Hz
const unsigned long WAVE_INTERVAL = 25;       // 40 Hz
const unsigned long SPECTRUM_INTERVAL = 100;  // 10 Hz
const unsigned long BEAT_INTERVAL = 400;      // 2.5 Hz
const unsigned long WINDING_CLEAR = 8000;     // 8 segundos

// Mensagens de silêncio
const char* silenceMessages[] = {
  "~ Listen ~", "Silence...", "Peaceful", "Waiting...", 
  "~ ~ ~", "Breathe...", "Zen Mode", "Stillness"
};
const int NUM_SILENCE_MESSAGES = 8;

void setup() {
  Serial.begin(115200);
  
  // Inicializar TFT
  uint16_t ID = tft.readID();
  if (ID == 0xD3D3) ID = 0x9481;
  tft.begin(ID);
  tft.setRotation(1);
  
  // Configurar ADC para maior velocidade
  analogReference(DEFAULT);
  
  // Inicializar estruturas
  initializeStructures();
  
  // Tela de boas-vindas
  showWelcomeScreen();
  
  Serial.println("MUSTEM AUTONOMOUS - READY (Simple Audio Mode)");
}

void loop() {
  unsigned long currentTime = millis();
  
  // Amostragem de áudio simples
  if (currentTime - audio.lastUpdate >= AUDIO_INTERVAL) {
    performSimpleAudioAnalysis(currentTime);
  }
  
  // Verificar estado de silêncio
  checkSilenceState(currentTime);
  
  // Se em silêncio, apenas animar mensagem
  if (isInSilence) {
    if (hasShownSilenceMessage) {
      updateSilenceAnimation(currentTime);
    }
    return;
  }
  
  // Processar visualizações quando há áudio
  if (audio.isActive) {
    // Detecção de batidas
    if (currentTime - beat.lastAnalysis >= BEAT_INTERVAL) {
      detectBeat(currentTime);
    }
    
    // Atualizar windings
    if (currentTime - winding.lastUpdate >= WINDING_INTERVAL) {
      updateWindings(currentTime);
    }
    
    // Atualizar ondas
    if (currentTime - audio.lastUpdate >= WAVE_INTERVAL) {
      updateWaveLayer(currentTime);
    }
    
    // Atualizar espectro
    if (currentTime - spectrum.lastUpdate >= SPECTRUM_INTERVAL) {
      updateSpectrumLayer(currentTime);
    }
    
    // Limpar windings periodicamente
    if (currentTime - winding.lastClear >= WINDING_CLEAR) {
      clearWindingsGradually();
      winding.lastClear = currentTime;
    }
  }
}

void initializeStructures() {
  // Audio
  audio.dominantFreq = 440.0;
  audio.amplitude = 0.0;
  audio.energy = 0.0;
  audio.lastUpdate = 0;
  audio.isActive = false;
  
  // Beat
  beat.bpm = 120.0;
  beat.strength = 0.0;
  beat.tempoMultiplier = 1.0;
  beat.lastBeat = 0;
  beat.lastAnalysis = 0;
  beat.historyIndex = 0;
  for (int i = 0; i < 8; i++) beat.energyHistory[i] = 0.0;
  
  // Spectrum
  for (int i = 0; i < 6; i++) {
    spectrum.bands[i] = 0.0;
    spectrum.smoothedBands[i] = 0.0;
  }
  spectrum.lastUpdate = 0;
  
  // Winding
  winding.phase = 0.0;
  winding.pointCount = 0;
  winding.lastClear = 0;
  winding.lastUpdate = 0;
  winding.fadeAmount = 1.0;
  
  // Audio samples
  for (int i = 0; i < SAMPLES; i++) {
    audioSamples[i] = 512; // Valor médio do ADC
  }
  sampleIndex = 0;
}

void performSimpleAudioAnalysis(unsigned long currentTime) {
  // Coletar nova amostra
  audioSamples[sampleIndex] = analogRead(ELETRETO_PIN);
  sampleIndex = (sampleIndex + 1) % SAMPLES;
  
  // Calcular energia e amplitude
  float energy = 0.0;
  float amplitude = 0.0;
  int dcOffset = 512; // Valor médio do ADC (10-bit)
  
  // Calcular DC offset dinâmico
  long dcSum = 0;
  for (int i = 0; i < SAMPLES; i++) {
    dcSum += audioSamples[i];
  }
  dcOffset = dcSum / SAMPLES;
  
  // Calcular energia e amplitude
  for (int i = 0; i < SAMPLES; i++) {
    float sample = audioSamples[i] - dcOffset;
    energy += sample * sample;
    amplitude += abs(sample);
  }
  energy = sqrt(energy / SAMPLES);
  amplitude = amplitude / SAMPLES;
  
  // Verificar se há áudio significativo
  bool hasAudio = energy > AMPLITUDE_THRESHOLD;
  
  if (hasAudio) {
    lastAudioTime = currentTime;
    audio.isActive = true;
    
    // Estimar frequência dominante usando análise de zero-crossing
    audio.dominantFreq = estimateFrequencyZeroCrossing();
    
    // Se frequência muito baixa, usar análise de picos
    if (audio.dominantFreq < 50) {
      audio.dominantFreq = estimateFrequencyPeaks();
    }
    
    audio.amplitude = amplitude / 50.0; // Normalizar
    audio.energy = energy;
    
    // Debug info
    if (currentTime % 1000 < 50) { // A cada segundo
      Serial.print("Freq: "); Serial.print(audio.dominantFreq);
      Serial.print(" Hz, Amp: "); Serial.print(audio.amplitude);
      Serial.print(", Energy: "); Serial.println(audio.energy);
    }
  } else {
    audio.isActive = false;
  }
  
  audio.lastUpdate = currentTime;
}

float estimateFrequencyZeroCrossing() {
  // Contar zero-crossings para estimar frequência
  int zeroCrossings = 0;
  int dcOffset = 512;
  
  // Calcular DC offset
  long dcSum = 0;
  for (int i = 0; i < SAMPLES; i++) {
    dcSum += audioSamples[i];
  }
  dcOffset = dcSum / SAMPLES;
  
  // Contar cruzamentos por zero
  bool lastPositive = (audioSamples[0] > dcOffset);
  for (int i = 1; i < SAMPLES; i++) {
    bool currentPositive = (audioSamples[i] > dcOffset);
    if (currentPositive != lastPositive) {
      zeroCrossings++;
    }
    lastPositive = currentPositive;
  }
  
  // Estimar frequência (cada ciclo = 2 zero crossings)
  float samplingRate = 1000.0 / AUDIO_INTERVAL; // Hz aproximado
  float frequency = (zeroCrossings * samplingRate) / (2.0 * SAMPLES);
  
  // Limitar a faixa razoável
  return constrain(frequency * 100, 80, 2000); // Multiplicar para ajustar escala
}

float estimateFrequencyPeaks() {
  // Encontrar picos no sinal para estimar frequência
  int peaks = 0;
  int dcOffset = 512;
  
  // Calcular DC offset
  long dcSum = 0;
  for (int i = 0; i < SAMPLES; i++) {
    dcSum += audioSamples[i];
  }
  dcOffset = dcSum / SAMPLES;
  
  // Encontrar picos locais
  for (int i = 1; i < SAMPLES - 1; i++) {
    if (audioSamples[i] > dcOffset + 10 && // Threshold para ruído
        audioSamples[i] > audioSamples[i-1] && 
        audioSamples[i] > audioSamples[i+1]) {
      peaks++;
    }
  }
  
  // Estimar frequência baseada nos picos
  float samplingRate = 1000.0 / AUDIO_INTERVAL;
  float frequency = (peaks * samplingRate) / SAMPLES;
  
  return constrain(frequency * 200, 100, 1500); // Ajustar escala
}

void detectBeat(unsigned long currentTime) {
  // Adicionar energia atual ao histórico
  beat.energyHistory[beat.historyIndex] = audio.energy;
  beat.historyIndex = (beat.historyIndex + 1) % 8;
  
  // Calcular média da energia
  float avgEnergy = 0.0;
  for (int i = 0; i < 8; i++) {
    avgEnergy += beat.energyHistory[i];
  }
  avgEnergy /= 8.0;
  
  // Detectar pico de energia (batida)
  float threshold = avgEnergy * 1.3; // Threshold mais baixo para análise simples
  if (audio.energy > threshold && (currentTime - beat.lastBeat) > 200) {
    beat.strength = min(1.0, (audio.energy - avgEnergy) / avgEnergy);
    beat.lastBeat = currentTime;
    
    // Estimar BPM baseado no intervalo entre batidas
    static unsigned long lastBeatTime = 0;
    if (lastBeatTime > 0) {
      unsigned long interval = currentTime - lastBeatTime;
      if (interval > 300 && interval < 2000) { // BPM entre 30-200
        float instantBPM = 60000.0 / interval;
        beat.bpm = beat.bpm * 0.8 + instantBPM * 0.2; // Suavização
      }
    }
    lastBeatTime = currentTime;
  } else {
    beat.strength *= 0.9; // Decay mais lento
  }
  
  // Calcular multiplicador de tempo baseado na energia
  beat.tempoMultiplier = 1.0 + (beat.strength * 1.5);
  
  beat.lastAnalysis = currentTime;
}

void updateWindings(unsigned long currentTime) {
  if (!audio.isActive) return;
  
  // Calcular fade baseado no tempo desde última limpeza
  unsigned long timeSinceClear = currentTime - winding.lastClear;
  winding.fadeAmount = max(0.3, 1.0 - (float)timeSinceClear / WINDING_CLEAR);
  
  // Gerar pontos da curva winding baseada na frequência
  const int WINDING_POINTS = 15; // Reduzido para melhor performance
  float centerX = SCREEN_WIDTH / 2;
  float centerY = SCREEN_HEIGHT / 2;
  float radius = 50 + audio.amplitude * 30;
  
  // Frequência determina velocidade de rotação
  float freqFactor = audio.dominantFreq / 440.0; // Normalizar por Lá 440Hz
  winding.phase += freqFactor * 0.2 * beat.tempoMultiplier;
  
  // Calcular cor baseada na frequência (mapeamento simples)
  uint16_t color = frequencyToColorSimple(audio.dominantFreq, winding.fadeAmount);
  
  // Desenhar winding
  for (int i = 0; i < WINDING_POINTS; i++) {
    float t = (float)i / WINDING_POINTS;
    float angle = winding.phase + t * 2 * PI * freqFactor;
    
    int x = centerX + radius * cos(angle);
    int y = centerY + radius * sin(angle);
    
    x = constrain(x, 0, SCREEN_WIDTH - 1);
    y = constrain(y, 0, SCREEN_HEIGHT - 1);
    
    // Adicionar efeito de batida
    if ((currentTime - beat.lastBeat) < 300) {
      float beatEffect = beat.strength * (1.0 - (currentTime - beat.lastBeat) / 300.0);
      x += random(-3, 4) * beatEffect;
      y += random(-3, 4) * beatEffect;
    }
    
    tft.drawPixel(x, y, color);
    
    // Conectar pontos com linhas ocasionalmente
    if (i > 0 && i % 3 == 0) {
      static int lastX = x, lastY = y;
      tft.drawLine(lastX, lastY, x, y, dimColor(color, 0.7));
      lastX = x;
      lastY = y;
    }
  }
  
  winding.pointCount += WINDING_POINTS;
  winding.lastUpdate = currentTime;
}

void updateWaveLayer(unsigned long currentTime) {
  if (!audio.isActive) return;
  
  // Limpar área da onda (parte inferior da tela)
  static float lastPhase = 0;
  int waveY = SCREEN_HEIGHT - 35;
  
  // Apagar onda anterior (apenas pontos-chave para performance)
  for (int x = 0; x < SCREEN_WIDTH; x += 4) {
    int oldY = waveY + 20 * sin(2 * PI * x / 30.0 + lastPhase);
    oldY = constrain(oldY, 0, SCREEN_HEIGHT - 1);
    tft.fillRect(x, oldY - 1, 4, 3, 0x0000); // Limpar área
  }
  
  // Calcular nova fase baseada na frequência
  float phaseSpeed = (audio.dominantFreq / 440.0) * 0.15 * beat.tempoMultiplier;
  lastPhase += phaseSpeed;
  
  // Desenhar nova onda
  float waveAmplitude = audio.amplitude * 20;
  float waveFreq = map(audio.dominantFreq, 80, 1500, 15, 60);
  uint16_t waveColor = frequencyToColorSimple(audio.dominantFreq, 1.0);
  
  // Efeito de batida na amplitude
  if ((currentTime - beat.lastBeat) < 200) {
    float beatBoost = 1.0 + beat.strength * 0.8;
    waveAmplitude *= beatBoost;
  }
  
  // Desenhar onda com menos pontos para melhor performance
  for (int x = 0; x < SCREEN_WIDTH; x += 2) {
    int y1 = waveY + waveAmplitude * sin(2 * PI * x / waveFreq + lastPhase);
    y1 = constrain(y1, 0, SCREEN_HEIGHT - 1);
    
    tft.drawPixel(x, y1, waveColor);
    tft.drawPixel(x + 1, y1, waveColor); // Espessar linha
  }
}

void updateSpectrumLayer(unsigned long currentTime) {
  if (!audio.isActive) return;
  
  // Análise simples de "espectro" baseada em características do sinal
  // Banda 0: Muito baixo (baseado em amplitude geral)
  spectrum.bands[0] = audio.amplitude * 0.8;
  
  // Banda 1-2: Baixo (baseado em variação lenta)
  float lowVariation = 0;
  for (int i = 0; i < SAMPLES - 4; i += 4) {
    lowVariation += abs(audioSamples[i] - audioSamples[i + 4]);
  }
  spectrum.bands[1] = (lowVariation / (SAMPLES / 4)) / 30.0;
  spectrum.bands[2] = spectrum.bands[1] * 0.8;
  
  // Banda 3-4: Médio (baseado em zero crossings)
  float midEnergy = audio.dominantFreq / 1000.0;
  spectrum.bands[3] = midEnergy * audio.amplitude;
  spectrum.bands[4] = spectrum.bands[3] * 0.7;
  
  // Banda 5: Alto (baseado em variação rápida)
  float highVariation = 0;
  for (int i = 0; i < SAMPLES - 1; i++) {
    highVariation += abs(audioSamples[i] - audioSamples[i + 1]);
  }
  spectrum.bands[5] = (highVariation / SAMPLES) / 40.0;
  
  // Suavizar todas as bandas
  for (int i = 0; i < 6; i++) {
    spectrum.smoothedBands[i] = spectrum.smoothedBands[i] * 0.6 + spectrum.bands[i] * 0.4;
    
    // Efeito de batida
    if ((currentTime - beat.lastBeat) < 300) {
      spectrum.smoothedBands[i] *= (1.0 + beat.strength * 0.5);
    }
    
    // Limitar valores
    spectrum.smoothedBands[i] = constrain(spectrum.smoothedBands[i], 0, 1.0);
  }
  
  // Desenhar espectro (lado direito da tela)
  drawSpectrumSimple(currentTime);
  
  spectrum.lastUpdate = currentTime;
}

void drawSpectrumSimple(unsigned long currentTime) {
  int spectrumX = SCREEN_WIDTH - 40;
  int spectrumWidth = 35;
  int barWidth = spectrumWidth / 6;
  
  for (int i = 0; i < 6; i++) {
    int x = spectrumX + i * barWidth;
    int maxHeight = SCREEN_HEIGHT - 50;
    int barHeight = spectrum.smoothedBands[i] * maxHeight;
    barHeight = constrain(barHeight, 0, maxHeight);
    
    // Limpar coluna anterior
    tft.fillRect(x, 10, barWidth - 1, maxHeight, 0x0000);
    
    // Desenhar nova barra
    if (barHeight > 0) {
      // Cor baseada na banda de frequência
      float bandFreq = map(i, 0, 5, 100, 1200);
      uint16_t barColor = frequencyToColorSimple(bandFreq, 1.0);
      
      tft.fillRect(x, 10 + maxHeight - barHeight, barWidth - 1, barHeight, barColor);
      
      // Pico brilhante no topo
      uint16_t peakColor = brightenColor(barColor);
      tft.drawLine(x, 10 + maxHeight - barHeight, x + barWidth - 1, 10 + maxHeight - barHeight, peakColor);
    }
  }
}

uint16_t frequencyToColorSimple(float freq, float intensity) {
  // Mapeamento simples de frequência para cor
  // Frequências baixas = vermelho, médias = verde, altas = azul
  
  freq = constrain(freq, 80, 1500);
  
  float hue;
  if (freq < 200) {
    // Baixas: Vermelho para laranja
    hue = map(freq, 80, 200, 0, 30);
  } else if (freq < 600) {
    // Médias: Laranja para verde
    hue = map(freq, 200, 600, 30, 120);
  } else {
    // Altas: Verde para azul/violeta
    hue = map(freq, 600, 1500, 120, 270);
  }
  
  // Converter HSV para RGB simplificado
  float h = hue / 60.0;
  float s = 0.9; // Alta saturação
  float v = intensity * 0.9; // Valor ajustado
  
  float c = v * s;
  float x = c * (1.0 - abs(fmod(h, 2.0) - 1.0));
  float m = v - c;
  
  float r, g, b;
  if (h < 1) { r = c; g = x; b = 0; }
  else if (h < 2) { r = x; g = c; b = 0; }
  else if (h < 3) { r = 0; g = c; b = x; }
  else if (h < 4) { r = 0; g = x; b = c; }
  else if (h < 5) { r = x; g = 0; b = c; }
  else { r = c; g = 0; b = x; }
  
  int red = (r + m) * 255;
  int green = (g + m) * 255;
  int blue = (b + m) * 255;
  
  return tft.color565(red, green, blue);
}

uint16_t dimColor(uint16_t color, float factor) {
  int r = ((color >> 11) & 0x1F) * factor;
  int g = ((color >> 5) & 0x3F) * factor;
  int b = (color & 0x1F) * factor;
  return tft.color565(r << 3, g << 2, b << 3);
}

uint16_t brightenColor(uint16_t color) {
  int r = min(31, ((color >> 11) & 0x1F) + 6);
  int g = min(63, ((color >> 5) & 0x3F) + 12);
  int b = min(31, (color & 0x1F) + 6);
  return (r << 11) | (g << 5) | b;
}

void clearWindingsGradually() {
  // Limpar com fade suave
  tft.fillRect(40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80, 0x0000);
  winding.pointCount = 0;
  winding.phase = 0.0;
}

void checkSilenceState(unsigned long currentTime) {
  if (currentTime - lastAudioTime < SILENCE_THRESHOLD_MS) {
    if (isInSilence) {
      isInSilence = false;
      hasShownSilenceMessage = false;
      clearSilenceMessage();
    }
  } else {
    if (!isInSilence) {
      isInSilence = true;
      silenceStartTime = currentTime;
      hasShownSilenceMessage = false;
      currentSilenceMessage = (currentTime / 1000) % NUM_SILENCE_MESSAGES;
    }
    
    if (!hasShownSilenceMessage && (currentTime - silenceStartTime > 500)) {
      showSilenceMessage();
      hasShownSilenceMessage = true;
    }
  }
}

void showSilenceMessage() {
  tft.fillRect(0, 80, SCREEN_WIDTH, 80, 0x0000);
  
  tft.setTextSize(3);
  String message = silenceMessages[currentSilenceMessage];
  int textWidth = message.length() * 18;
  int textX = (SCREEN_WIDTH - textWidth) / 2;
  
  tft.setTextColor(getAnimatedColor(0));
  tft.setCursor(textX, 110);
  tft.print(message);
}

void clearSilenceMessage() {
  tft.fillRect(0, 80, SCREEN_WIDTH, 80, 0x0000);
}

void updateSilenceAnimation(unsigned long currentTime) {
  if (currentTime - lastTextUpdate > 200) { // Mais lento para performance
    lastTextUpdate = currentTime;
    textAnimPhase += 0.3;
    if (textAnimPhase > 6.28) textAnimPhase = 0;
    
    String message = silenceMessages[currentSilenceMessage];
    int textWidth = message.length() * 18;
    int textX = (SCREEN_WIDTH - textWidth) / 2;
    
    tft.fillRect(textX - 5, 105, textWidth + 10, 30, 0x0000);
    
    tft.setTextSize(3);
    tft.setTextColor(getAnimatedColor(textAnimPhase));
    tft.setCursor(textX, 110);
    tft.print(message);
    
    // Pontos decorativos mais simples
    for (int i = 0; i < 2; i++) {
      int dotX = textX - 20 + i * (textWidth + 30);
      int dotY = 117 + sin(textAnimPhase + i * 3) * 4;
      uint16_t dotColor = getAnimatedColor(textAnimPhase + i * 2);
      tft.fillCircle(dotX, dotY, 2, dotColor);
    }
  }
}

uint16_t getAnimatedColor(float phase) {
  int r = 128 + 127 * sin(phase);
  int g = 128 + 127 * sin(phase + 2.09);
  int b = 128 + 127 * sin(phase + 4.18);
  return tft.color565(r, g, b);
}

void showWelcomeScreen() {
  tft.fillScreen(0x0000);
  
  tft.setTextSize(4);
  tft.setTextColor(0xF81F);
  tft.setCursor(60, 50);
  tft.print("MUSTEM");
  
  tft.setTextSize(2);
  tft.setTextColor(0x07FF);
  tft.setCursor(30, 100);
  tft.print("Autonomous Music Vision");
  
  tft.setTextSize(1);
  tft.setTextColor(0x07E0);
  tft.setCursor(60, 130);
  tft.print("Simple Audio Mode - No FFT");
  
  tft.setTextColor(0xFFE0);
  tft.setCursor(80, 150);
  tft.print("For hearing accessibility");
  
  tft.drawLine(50, 180, SCREEN_WIDTH - 50, 180, 0x07E0);
  
  delay(3000);
  tft.fillScreen(0x0000);
}