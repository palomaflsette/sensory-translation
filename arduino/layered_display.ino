#include <MCUFRIEND_kbv.h>
#include <Adafruit_GFX.h>

MCUFRIEND_kbv tft;

#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240

// Estados de cada camada
struct LayerState {
  int prevX;
  int prevY;
  bool isActive;
};

LayerState windingLayer = {-1, -1, true};
LayerState waveLayer = {-1, -1, true};
LayerState spectrumLayer = {-1, -1, true};

// Buffers para diferentes elementos
struct WindingPoint {
  int x, y;
  uint16_t color;
  unsigned long timestamp;
};

const int MAX_WINDING_POINTS = 800;
WindingPoint windingBuffer[MAX_WINDING_POINTS];
int windingIndex = 0;

// Variáveis para ondas senoidais
float currentWaveAmplitude = 0.0;
float currentDominantFreq = 440.0;
float currentTempoMultiplier = 1.0;
float currentBeatStrength = 0.0;
float wavePhase = 0.0;
unsigned long lastWaveUpdate = 0;

// Variáveis para ritmo
float currentBPM = 120.0;
unsigned long lastBeatTime = 0;

// Variáveis para espectro com transição suave
int spectrumBars[10] = {0};          // Valores atuais (alvo)
int currentSpectrumBars[10] = {0};   // Valores sendo exibidos (atual)
int previousSpectrumBars[10] = {0};  // Valores anteriores para comparação
unsigned long lastSpectrumUpdate = 0;
const int SPECTRUM_UPDATE_INTERVAL = 30; // Atualizar a cada 30ms
const float SPECTRUM_LERP_SPEED = 0.15;   // Velocidade da interpolação (0.1 = lento, 0.5 = rápido)

String inputBuffer = "";

// Declarações das funções
void clearAll();
void clearWindings();
void resetAllLayers();
void redrawWaveLayer();
void redrawSpectrumLayer();
void processCommand();
void drawWindingPoint(String pointStr);
void updateWaveLayer(String waveData);
void updateRhythmData(String rhythmData);
void drawSineWave(float amplitude, uint16_t color = 0x07E0);
void updateSpectrumLayer(String spectrumData);
void drawSpectrum();
void updateSpectrumAnimation();
void updateWavePhase();

void setup() {
  Serial.begin(115200);

  uint16_t ID = tft.readID();
  if (ID == 0xD3D3) ID = 0x9481;
  tft.begin(ID);
  tft.setRotation(1);
  tft.fillScreen(0x0000); // Preto

  Serial.println("ARDUINO_LAYERED_READY");
}

void loop() {
  // Atualizar fase da onda continuamente para movimento suave
  updateWavePhase();
  
  // Atualizar animação do espectro
  updateSpectrumAnimation();
  
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      processCommand();
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }
}

void processCommand() {
  if (inputBuffer.startsWith("WINDING:")) {
    drawWindingPoint(inputBuffer.substring(8));
  }
  else if (inputBuffer == "CLEAR") {
    clearAll();
  }
  else if (inputBuffer == "CLEAR_WINDINGS") {
    clearWindings();
  }
  else if (inputBuffer == "CLEAR_ALL") {
    clearAll();
  }
  else if (inputBuffer.startsWith("WAVE:")) {
    updateWaveLayer(inputBuffer.substring(5));
  }
  else if (inputBuffer.startsWith("RHYTHM:")) {
    updateRhythmData(inputBuffer.substring(7));
  }
  else if (inputBuffer.startsWith("SPECTRUM:")) {
    updateSpectrumLayer(inputBuffer.substring(9));
  }
  else if (inputBuffer == "LAYER_WINDING_OFF") {
    windingLayer.isActive = false;
  }
  else if (inputBuffer == "LAYER_WINDING_ON") {
    windingLayer.isActive = true;
  }
  else if (inputBuffer == "LAYER_WAVE_OFF") {
    waveLayer.isActive = false;
  }
  else if (inputBuffer == "LAYER_WAVE_ON") {
    waveLayer.isActive = true;
  }
  else if (inputBuffer == "LAYER_SPECTRUM_OFF") {
    spectrumLayer.isActive = false;
  }
  else if (inputBuffer == "LAYER_SPECTRUM_ON") {
    spectrumLayer.isActive = true;
  }
}

void clearAll() {
  tft.fillScreen(0x0000);
  resetAllLayers();
}

void clearWindings() {
  // Limpar apenas a área das windings (método simples: redesenhar fundo)
  tft.fillScreen(0x0000);
  
  // Redesenhar ondas e espectro se estiverem ativos
  redrawWaveLayer();
  redrawSpectrumLayer();
  
  // Reset do estado das windings
  windingLayer.prevX = -1;
  windingLayer.prevY = -1;
  windingIndex = 0;
}

void resetAllLayers() {
  windingLayer.prevX = -1;
  windingLayer.prevY = -1;
  waveLayer.prevX = -1;
  waveLayer.prevY = -1;
  spectrumLayer.prevX = -1;
  spectrumLayer.prevY = -1;
  windingIndex = 0;
  wavePhase = 0.0;
  currentWaveAmplitude = 0.0;
  currentDominantFreq = 440.0;
  currentTempoMultiplier = 1.0;
  currentBeatStrength = 0.0;
  currentBPM = 120.0;
  lastWaveUpdate = 0;
  lastBeatTime = 0;
  lastSpectrumUpdate = 0;
  for (int i = 0; i < 10; i++) {
    spectrumBars[i] = 0;
    currentSpectrumBars[i] = 0;
    previousSpectrumBars[i] = 0;
  }
}

void redrawWaveLayer() {
  if (!waveLayer.isActive || currentWaveAmplitude == 0.0) return;
  
  // Redesenhar a onda senoidal atual
  drawSineWave(currentWaveAmplitude*5);
}

void redrawSpectrumLayer() {
  if (!spectrumLayer.isActive) return;
  
  // Redesenhar as barras do espectro
  drawSpectrum();
}

void drawWindingPoint(String pointStr) {
  if (!windingLayer.isActive) return;
  
  int i1 = pointStr.indexOf(',');
  int i2 = pointStr.indexOf(',', i1 + 1);
  int i3 = pointStr.indexOf(',', i2 + 1);
  int i4 = pointStr.indexOf(',', i3 + 1);

  if (i1 <= 0 || i2 <= i1 || i3 <= i2 || i4 <= i3) return;

  int x = pointStr.substring(0, i1).toInt();
  int y = pointStr.substring(i1 + 1, i2).toInt();
  int r = pointStr.substring(i2 + 1, i3).toInt();
  int g = pointStr.substring(i3 + 1, i4).toInt();
  int b = pointStr.substring(i4 + 1).toInt();

  uint16_t color = tft.color565(r, g, b);

  x = constrain(x, 0, SCREEN_WIDTH - 1);
  y = constrain(y, 0, SCREEN_HEIGHT - 1);

  if (windingLayer.prevX >= 0 && windingLayer.prevY >= 0) {
    tft.drawLine(windingLayer.prevX, windingLayer.prevY, x, y, color);
  } else {
    tft.drawPixel(x, y, color);
  }

  windingLayer.prevX = x;
  windingLayer.prevY = y;
}

void updateWaveLayer(String waveData) {
  if (!waveLayer.isActive) return;
  
  // Parse: amplitude,frequencia_dominante,tempo_multiplier,beat_strength
  int i1 = waveData.indexOf(',');
  int i2 = waveData.indexOf(',', i1 + 1);
  int i3 = waveData.indexOf(',', i2 + 1);
  
  if (i1 > 0 && i2 > i1 && i3 > i2) {
    currentWaveAmplitude = waveData.substring(0, i1).toFloat();
    currentDominantFreq = waveData.substring(i1 + 1, i2).toFloat();
    currentTempoMultiplier = waveData.substring(i2 + 1, i3).toFloat();
    currentBeatStrength = waveData.substring(i3 + 1).toFloat();
  } else {
    // Fallback para formato antigo (só amplitude)
    currentWaveAmplitude = waveData.toFloat();
  }
}

void updateRhythmData(String rhythmData) {
  // Parse: bpm,beat_strength,tempo_multiplier
  int i1 = rhythmData.indexOf(',');
  int i2 = rhythmData.indexOf(',', i1 + 1);
  
  if (i1 > 0 && i2 > i1) {
    currentBPM = rhythmData.substring(0, i1).toFloat();
    float beatStrength = rhythmData.substring(i1 + 1, i2).toFloat();
    currentTempoMultiplier = rhythmData.substring(i2 + 1).toFloat();
    
    // Se há uma batida forte, marcar o tempo
    if (beatStrength > 0.7) {
      lastBeatTime = millis();
    }
  }
}

void updateWavePhase() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastWaveUpdate > 20) { // Atualizar a cada 20ms (50 FPS)
    lastWaveUpdate = currentTime;
    
    if (waveLayer.isActive && currentWaveAmplitude > 0.01) {
      // Limpar onda anterior
      drawSineWave(currentWaveAmplitude*5, 0x0011); // Preto para apagar
      
      // Calcular nova fase baseada no tempo e BPM
      float phaseSpeed = currentTempoMultiplier * 0.15; // Velocidade base
      
      // Acelerar na batida forte
      unsigned long timeSinceBeat = currentTime - lastBeatTime;
      if (timeSinceBeat < 200) { // 200ms após a batida
        float beatEffect = 1.0 + currentBeatStrength * 2.0;
        phaseSpeed *= beatEffect;
      }
      
      wavePhase += phaseSpeed;
      if (wavePhase > 2 * PI * 10) { // Reset para evitar overflow
        wavePhase = 0;
      }
      
      // Desenhar nova onda
      drawSineWave(currentWaveAmplitude*5);
    }
  }
}

void drawSineWave(float amplitude, uint16_t color) {
  int centerY = SCREEN_HEIGHT - 30; // Parte inferior da tela
  int waveWidth = SCREEN_WIDTH;
  
  // Calcular frequência da onda baseada na frequência dominante
  float waveFrequency = map(currentDominantFreq, 80, 2000, 30, 100); // Mapear para freq visual
  waveFrequency = constrain(waveFrequency, 20, 120);
  
  // Amplitude com efeito de batida
  float finalAmplitude = amplitude * 30; // Amplitude base maior
  unsigned long timeSinceBeat = millis() - lastBeatTime;
  if (timeSinceBeat < 300) { // Efeito por 300ms
    float beatEffect = 1.0 + (currentBeatStrength * 0.5 * (1.0 - timeSinceBeat / 300.0));
    finalAmplitude *= beatEffect;
  }
  
  finalAmplitude = constrain(finalAmplitude, 0, 40);
  
  for (int x = 0; x < waveWidth - 1; x++) {
    // Onda principal
    int y1 = centerY + (int)(finalAmplitude * sin(2 * PI * x / waveFrequency + wavePhase));
    int y2 = centerY + (int)(finalAmplitude * sin(2 * PI * (x + 1) / waveFrequency + wavePhase));
    
    y1 = constrain(y1, 0, SCREEN_HEIGHT - 1);
    y2 = constrain(y2, 0, SCREEN_HEIGHT - 1);
    
    // Cor que varia com a frequência (se não for para apagar)
    uint16_t finalColor = color;
    if (color != 0x0000) {
      // Variar cor baseada na frequência dominante
      int hue = map(currentDominantFreq, 80, 2000, 0, 255);
      // Converter para RGB simplificado
      if (hue < 85) {
        finalColor = tft.color565(255 - hue * 3, hue * 3, 0);
      } else if (hue < 170) {
        hue -= 85;
        finalColor = tft.color565(0, 255 - hue * 3, hue * 3);
      } else {
        hue -= 170;
        finalColor = tft.color565(hue * 3, 0, 255 - hue * 3);
      }
    }
    
    tft.drawLine(x, y1, x + 1, y2, finalColor);
    
    // Adicionar harmônicos sutis para música complexa
    if (color != 0x0000 && amplitude > 0.3) {
      int y1_harm = centerY + (int)(finalAmplitude * 0.3 * sin(2 * PI * x / (waveFrequency * 0.5) + wavePhase * 1.5));
      y1_harm = constrain(y1_harm, 0, SCREEN_HEIGHT - 1);
      uint16_t harmColor = tft.color565(
        (finalColor >> 11) * 0.5,
        ((finalColor >> 5) & 0x3F) * 0.5,
        (finalColor & 0x1F) * 0.5
      );
      tft.drawPixel(x, y1_harm, harmColor);
    }
  }
}

void updateSpectrumLayer(String spectrumData) {
  if (!spectrumLayer.isActive) return;
  
  // Parse dos dados do espectro (valores separados por vírgula)
  int barIndex = 0;
  int startPos = 0;
  int commaPos = 0;
  
  // Atualizar apenas os valores alvo, sem redesenhar imediatamente
  while (barIndex < 10 && commaPos >= 0) {
    commaPos = spectrumData.indexOf(',', startPos);
    String valueStr;
    
    if (commaPos > 0) {
      valueStr = spectrumData.substring(startPos, commaPos);
    } else {
      valueStr = spectrumData.substring(startPos);
    }
    
    spectrumBars[barIndex] = valueStr.toInt();
    barIndex++;
    startPos = commaPos + 1;
  }
  
  // A animação será tratada pela função updateSpectrumAnimation()
}

void updateSpectrumAnimation() {
  if (!spectrumLayer.isActive) return;
  
  unsigned long currentTime = millis();
  
  if (currentTime - lastSpectrumUpdate > SPECTRUM_UPDATE_INTERVAL) {
    lastSpectrumUpdate = currentTime;
    
    // Verificar se há mudanças a fazer
    bool needsUpdate = false;
    
    for (int i = 0; i < 10; i++) {
      // Interpolação linear (lerp) entre valor atual e valor alvo
      float target = (float)spectrumBars[i];
      float current = (float)currentSpectrumBars[i];
      
      if (abs(target - current) > 1) { // Só atualizar se a diferença for significativa
        float newValue = current + (target - current) * SPECTRUM_LERP_SPEED;
        int newIntValue = (int)newValue;
        
        if (newIntValue != currentSpectrumBars[i]) {
          previousSpectrumBars[i] = currentSpectrumBars[i];
          currentSpectrumBars[i] = newIntValue;
          needsUpdate = true;
        }
      }
    }
    
    if (needsUpdate) {
      drawSpectrum();
    }
  }
}

void drawSpectrum() {
  int barWidth = SCREEN_WIDTH / 10;
  int maxHeight = 60; // Aumentei um pouco para ficar mais visível
  
  for (int i = 0; i < 10; i++) {
    int newBarHeight = map(currentSpectrumBars[i], 0, 255, 0, maxHeight);
    int oldBarHeight = map(previousSpectrumBars[i], 0, 255, 0, maxHeight);
    
    int x = i * barWidth;
    
    // Se a nova barra é menor que a anterior, limpar a parte superior
    if (newBarHeight < oldBarHeight) {
      int clearStart = SCREEN_HEIGHT - oldBarHeight;
      int clearEnd = SCREEN_HEIGHT - newBarHeight;
      
      for (int j = 0; j < barWidth - 2; j++) {
        tft.drawLine(x + j, clearStart, x + j, clearEnd, 0x0000); // Preto para apagar
      }
    }
    
    // Desenhar a nova parte da barra (se necessário)
    if (newBarHeight > 0) {
      int barStart = SCREEN_HEIGHT - newBarHeight;
      int barEnd = SCREEN_HEIGHT - 1;
      
      // Cor baseada na altura da barra e posição (frequência)
      uint16_t color;
      if (i < 3) {
        // Graves - vermelho para laranja
        color = tft.color565(255, i * 40, 0);
      } else if (i < 7) {
        // Médios - laranja para amarelo
        color = tft.color565(255, 150 + (i-3) * 25, 0);
      } else {
        // Agudos - amarelo para branco
        int brightness = 200 + (i-7) * 15;
        color = tft.color565(255, brightness, brightness/2);
      }
      
      // Ajustar intensidade baseada na altura
      float intensity = (float)newBarHeight / maxHeight;
      int r = ((color >> 11) & 0x1F) * intensity;
      int g = ((color >> 5) & 0x3F) * intensity;
      int b = (color & 0x1F) * intensity;
      
      color = tft.color565(r * 8, g * 4, b * 8); // Converter de volta para RGB565
      
      for (int j = 1; j < barWidth - 1; j++) { // Deixar 1 pixel de espaço entre barras
        tft.drawLine(x + j, barStart, x + j, barEnd, color);
      }
    }
    
    previousSpectrumBars[i] = currentSpectrumBars[i];
  }
}