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

String inputBuffer = "";

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

// Variáveis para espectro
unsigned long lastSpectrumUpdate = 0;
const int SPECTRUM_UPDATE_INTERVAL = 30;
const float SPECTRUM_LERP_SPEED = 0.15;

// Variáveis para detecção de silêncio e mensagens
unsigned long lastAudioTime = 0;
bool isInSilence = false;
bool hasShownSilenceMessage = false;
bool hasShownWelcome = false;
unsigned long silenceStartTime = 0;
const unsigned long SILENCE_THRESHOLD = 2000; // 2 segundos de silêncio
int currentSilenceMessage = 0;

// Mensagens de silêncio artísticas
const char* silenceMessages[] = {
  "So quiet...",
  "~ Silence ~",
  "Listen...",
  "Shh...",
  "Peaceful...",
  "Waiting...",
  "~ ~ ~",
  "Breathe...",
  "Stillness...",
  "Zen..."
};
const int NUM_SILENCE_MESSAGES = 10;

// Variáveis para animação de texto
float textAnimPhase = 0.0;
unsigned long lastTextUpdate = 0;

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
void showWelcomeScreen();
void checkSilenceState();
void showSilenceMessage();
void clearSilenceMessage();
void updateSilenceAnimation();
uint16_t getAnimatedColor(float phase);

void setup() {
  Serial.begin(115200);

  uint16_t ID = tft.readID();
  if (ID == 0xD3D3) ID = 0x9481;
  tft.begin(ID);
  tft.setRotation(1);
  
  // Mostrar tela de boas-vindas
  showWelcomeScreen();
  
  Serial.println("ARDUINO_LAYERED_READY");
}

void loop() {
  // Verificar estado de silêncio
  checkSilenceState();
  
  // Atualizar fase da onda continuamente para movimento suave
  updateWavePhase();
  
  // Atualizar animação do espectro
  updateSpectrumAnimation();
  
  // Atualizar animação de silêncio se necessário
  if (isInSilence && hasShownSilenceMessage) {
    updateSilenceAnimation();
  }
  
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

void showWelcomeScreen() {
  tft.fillScreen(0x0000); // Fundo preto
  
  // Título principal "MUSTEM"
  tft.setTextSize(4);
  tft.setTextColor(0xF81F); // Magenta
  int titleWidth = 6 * 5 * 4; // 6 chars * 5 pixels * scale 4
  int titleX = (SCREEN_WIDTH - titleWidth) / 2;
  tft.setCursor(titleX, 60);
  tft.print("MUSTEM");
  
  // Subtítulo
  tft.setTextSize(2);
  tft.setTextColor(0x07FF); // Ciano
  String subtitle = "Music Visualization";
  int subtitleWidth = subtitle.length() * 6 * 2;
  int subtitleX = (SCREEN_WIDTH - subtitleWidth) / 2;
  tft.setCursor(subtitleX, 120);
  tft.print(subtitle);
  
  // Linha decorativa
  tft.drawLine(50, 160, SCREEN_WIDTH - 50, 160, 0x07E0); // Verde
  
  // Aguardar um momento
  delay(3000);
  
  // Limpar tela
  tft.fillScreen(0x0000);
  hasShownWelcome = true;
}

void checkSilenceState() {
  unsigned long currentTime = millis();
  
  // Se recebeu áudio recentemente, não está em silêncio
  if (currentTime - lastAudioTime < SILENCE_THRESHOLD) {
    if (isInSilence) {
      // Saindo do silêncio
      isInSilence = false;
      hasShownSilenceMessage = false;
      clearSilenceMessage();
    }
  } else {
    // Está em silêncio
    if (!isInSilence) {
      // Entrando em silêncio
      isInSilence = true;
      silenceStartTime = currentTime;
      hasShownSilenceMessage = false;
      // Escolher uma mensagem aleatória
      currentSilenceMessage = (currentTime / 1000) % NUM_SILENCE_MESSAGES;
    }
    
    // Mostrar mensagem de silêncio se ainda não mostrou
    if (!hasShownSilenceMessage && (currentTime - silenceStartTime > 500)) {
      showSilenceMessage();
      hasShownSilenceMessage = true;
    }
  }
}

void showSilenceMessage() {
  // Limpar área central
  tft.fillRect(0, 80, SCREEN_WIDTH, 80, 0x0000);
  
  // Configurar texto
  tft.setTextSize(3);
  
  // Calcular posição centralizada
  String message = silenceMessages[currentSilenceMessage];
  int textWidth = message.length() * 6 * 3; // chars * 6 pixels * scale 3
  int textX = (SCREEN_WIDTH - textWidth) / 2;
  int textY = 110;
  
  // Cor inicial
  tft.setTextColor(getAnimatedColor(0));
  tft.setCursor(textX, textY);
  tft.print(message);
}

void clearSilenceMessage() {
  // Limpar área da mensagem
  tft.fillRect(0, 80, SCREEN_WIDTH, 80, 0x0000);
}

void updateSilenceAnimation() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastTextUpdate > 150) { // Atualizar a cada 150ms
    lastTextUpdate = currentTime;
    
    // Atualizar fase da animação
    textAnimPhase += 0.3;
    if (textAnimPhase > 6.28) { // 2 * PI
      textAnimPhase = 0;
    }
    
    // Redesenhar texto com nova cor
    String message = silenceMessages[currentSilenceMessage];
    int textWidth = message.length() * 6 * 3;
    int textX = (SCREEN_WIDTH - textWidth) / 2;
    int textY = 110;
    
    // Limpar área do texto
    tft.fillRect(textX - 5, textY - 5, textWidth + 10, 30, 0x0000);
    
    // Desenhar com cor animada
    tft.setTextSize(3);
    tft.setTextColor(getAnimatedColor(textAnimPhase));
    tft.setCursor(textX, textY);
    tft.print(message);
    
    // Adicionar pontos decorativos animados
    for (int i = 0; i < 3; i++) {
      int dotX = textX - 30 + i * 15;
      int dotY = textY + 15 + sin(textAnimPhase + i * 2) * 5;
      uint16_t dotColor = getAnimatedColor(textAnimPhase + i * 1.5);
      tft.fillCircle(dotX, dotY, 2, dotColor);
    }
    
    for (int i = 0; i < 3; i++) {
      int dotX = textX + textWidth + 15 + i * 15;
      int dotY = textY + 15 + sin(textAnimPhase + i * 2 + 3.14) * 5;
      uint16_t dotColor = getAnimatedColor(textAnimPhase + i * 1.5 + 3.14);
      tft.fillCircle(dotX, dotY, 2, dotColor);
    }
  }
}

uint16_t getAnimatedColor(float phase) {
  // Criar um ciclo de cores suaves
  int r = 128 + 127 * sin(phase);
  int g = 128 + 127 * sin(phase + 2.09); // +120 graus
  int b = 128 + 127 * sin(phase + 4.18); // +240 graus
  
  // Converter para RGB565
  return tft.color565(r, g, b);
}

void processCommand() {
  // Marcar que recebeu áudio
  lastAudioTime = millis();
  
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
  tft.fillScreen(0x0000);
  redrawWaveLayer();
  redrawSpectrumLayer();
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
}

void redrawWaveLayer() {
  if (!waveLayer.isActive || currentWaveAmplitude == 0.0) return;
  drawSineWave(currentWaveAmplitude*5);
}

void redrawSpectrumLayer() {
  if (!spectrumLayer.isActive) return;
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
  
  int i1 = waveData.indexOf(',');
  int i2 = waveData.indexOf(',', i1 + 1);
  int i3 = waveData.indexOf(',', i2 + 1);
  
  if (i1 > 0 && i2 > i1 && i3 > i2) {
    currentWaveAmplitude = waveData.substring(0, i1).toFloat();
    currentDominantFreq = waveData.substring(i1 + 1, i2).toFloat();
    currentTempoMultiplier = waveData.substring(i2 + 1, i3).toFloat();
    currentBeatStrength = waveData.substring(i3 + 1).toFloat();
  } else {
    currentWaveAmplitude = waveData.toFloat();
  }
}

void updateRhythmData(String rhythmData) {
  int i1 = rhythmData.indexOf(',');
  int i2 = rhythmData.indexOf(',', i1 + 1);
  
  if (i1 > 0 && i2 > i1) {
    currentBPM = rhythmData.substring(0, i1).toFloat();
    float beatStrength = rhythmData.substring(i1 + 1, i2).toFloat();
    currentTempoMultiplier = rhythmData.substring(i2 + 1).toFloat();
    
    if (beatStrength > 0.7) {
      lastBeatTime = millis();
    }
  }
}

void updateWavePhase() {
  unsigned long currentTime = millis();
  
  if (currentTime - lastWaveUpdate > 20) {
    lastWaveUpdate = currentTime;
    
    if (waveLayer.isActive && currentWaveAmplitude > 0.01) {
      drawSineWave(currentWaveAmplitude*5, 0x0000);
      
      float phaseSpeed = currentTempoMultiplier * 0.15;
      
      unsigned long timeSinceBeat = currentTime - lastBeatTime;
      if (timeSinceBeat < 200) {
        float beatEffect = 1.0 + currentBeatStrength * 2.0;
        phaseSpeed *= beatEffect;
      }
      
      wavePhase += phaseSpeed;
      if (wavePhase > 2 * PI * 10) {
        wavePhase = 0;
      }
      
      drawSineWave(currentWaveAmplitude*5);
    }
  }
}

void drawSineWave(float amplitude, uint16_t color) {
  int centerY = SCREEN_HEIGHT - 30;
  int waveWidth = SCREEN_WIDTH;
  
  float waveFrequency = map(currentDominantFreq, 80, 2000, 30, 100);
  waveFrequency = constrain(waveFrequency, 20, 120);
  
  float finalAmplitude = amplitude * 30;
  unsigned long timeSinceBeat = millis() - lastBeatTime;
  if (timeSinceBeat < 300) {
    float beatEffect = 1.0 + (currentBeatStrength * 0.5 * (1.0 - timeSinceBeat / 300.0));
    finalAmplitude *= beatEffect;
  }
  
  finalAmplitude = constrain(finalAmplitude, 0, 40);
  
  for (int x = 0; x < waveWidth - 1; x++) {
    int y1 = centerY + (int)(finalAmplitude * sin(2 * PI * x / waveFrequency + wavePhase));
    int y2 = centerY + (int)(finalAmplitude * sin(2 * PI * (x + 1) / waveFrequency + wavePhase));
    
    y1 = constrain(y1, 0, SCREEN_HEIGHT - 1);
    y2 = constrain(y2, 0, SCREEN_HEIGHT - 1);
    
    uint16_t finalColor = color;
    if (color != 0x0000) {
      int hue = map(currentDominantFreq, 80, 2000, 0, 255);
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
}

void updateSpectrumAnimation() {
  if (!spectrumLayer.isActive) return;
}

void drawSpectrum() {
  // Barras do espectro ainda desabilitadas
}