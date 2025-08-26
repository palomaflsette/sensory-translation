/*
 * Sensory Music System - Arduino Mega Audio Sender
 * Captura áudio via eletreto e envia análise para Python
 * 
 * Hardware necessário:
 * - Arduino Mega
 * - Microfone eletreto
 * - Resistor 10kΩ (bias do eletreto)
 * - Capacitor 100nF (filtro)
 * - Capacitor 10µF (acoplamento AC)
 * 
 * Conexões:
 * - Eletreto VCC -> 5V via resistor 10kΩ
 * - Eletreto GND -> GND
 * - Eletreto OUT -> A0 (via capacitor 10µF)
 * - Capacitor 100nF entre A0 e GND (filtro anti-aliasing)
 */

#include <arduinoFFT.h>
#include <avr/pgmspace.h>

// ===== CONFIGURAÇÕES =====
const int AUDIO_PIN = A0;              // Pino do eletreto
const int LED_PIN = 13;                // LED indicador
const int SAMPLES = 128;               // Amostras para FFT (potência de 2)
const int SAMPLING_FREQUENCY = 10000;  // Hz - Nyquist = 5kHz
const int BAUD_RATE = 115200;          // Velocidade serial

// ===== VARIÁVEIS FFT =====
double vReal[SAMPLES];
double vImag[SAMPLES];
arduinoFFT FFT = arduinoFFT(vReal, vImag, SAMPLES, SAMPLING_FREQUENCY);

// ===== BANDAS DE FREQUÊNCIA =====
struct FrequencyBands {
  double bass;      // 20-250 Hz
  double mid;       // 250-4000 Hz  
  double treble;    // 4000+ Hz
};

// ===== DETECÇÃO DE BEAT =====
struct BeatDetector {
  double bassHistory[8];
  int historyIndex;
  double threshold;
  unsigned long lastBeatTime;
  bool beatDetected;
  
  void init() {
    for (int i = 0; i < 8; i++) bassHistory[i] = 0;
    historyIndex = 0;
    threshold = 1.3;
    lastBeatTime = 0;
    beatDetected = false;
  }
  
  bool detectBeat(double currentBass) {
    // Adicionar ao histórico
    bassHistory[historyIndex] = currentBass;
    historyIndex = (historyIndex + 1) % 8;
    
    // Calcular média histórica
    double avgBass = 0;
    for (int i = 0; i < 8; i++) {
      avgBass += bassHistory[i];
    }
    avgBass /= 8;
    
    // Detectar beat
    unsigned long currentTime = millis();
    bool beat = false;
    
    if (currentBass > avgBass * threshold && 
        currentTime - lastBeatTime > 200) { // Mínimo 200ms entre beats
      beat = true;
      lastBeatTime = currentTime;
      
      // Ajustar threshold adaptativamente
      threshold = constrain(threshold * 0.98, 1.2, 2.0);
    } else {
      threshold = constrain(threshold * 1.001, 1.2, 2.0);
    }
    
    beatDetected = beat;
    return beat;
  }
};

// ===== VARIÁVEIS GLOBAIS =====
FrequencyBands bands;
BeatDetector beatDetector;
unsigned long lastSampleTime = 0;
double maxAmplitude = 0;
int dominantFreqIndex = 0;
double dominantFreq = 440;

// ===== CALIBRAÇÃO =====
double dcOffset = 512.0;  // Offset DC do ADC
double gainFactor = 1.0;  // Fator de ganho
bool calibrationMode = false;

void setup() {
  // Inicializar comunicação serial
  Serial.begin(BAUD_RATE);
  while (!Serial) delay(10);
  
  // Configurar pinos
  pinMode(LED_PIN, OUTPUT);
  pinMode(AUDIO_PIN, INPUT);
  
  // Configurar ADC para máxima velocidade
  ADCSRA &= ~0x07;  // Limpar prescaler
  ADCSRA |= 0x04;   // Prescaler 16 (1MHz ADC clock)
  
  // Inicializar componentes
  beatDetector.init();
  
  // Calibrar DC offset
  calibrateDCOffset();
  
  // Sinal de inicialização
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(200);
    digitalWrite(LED_PIN, LOW);
    delay(200);
  }
  
  Serial.println("# Sensory Music System - Audio Sender Initialized");
  Serial.println("# Format: AMP:xxx,FREQ:xxx,BASS:xxx,MID:xxx,TREBLE:xxx,BEAT:x");
  delay(1000);
}

void loop() {
  // Capturar amostras para FFT
  captureSamples();
  
  // Processar FFT
  processFFT();
  
  // Analisar bandas de frequência
  analyzeBands();
  
  // Detectar beat
  bool beatDetected = beatDetector.detectBeat(bands.bass);
  
  // Encontrar frequência dominante
  findDominantFrequency();
  
  // Enviar dados para Python
  sendAudioData(beatDetected);
  
  // Indicador visual
  digitalWrite(LED_PIN, beatDetected ? HIGH : LOW);
  
  // Controlar taxa de amostragem (~50Hz)
  delayMicroseconds(20000 - (micros() - lastSampleTime));
}

void calibrateDCOffset() {
  Serial.println("# Calibrating DC offset...");
  
  long sum = 0;
  const int calibSamples = 1000;
  
  for (int i = 0; i < calibSamples; i++) {
    sum += analogRead(AUDIO_PIN);
    delay(1);
  }
  
  dcOffset = sum / (double)calibSamples;
  Serial.print("# DC Offset: ");
  Serial.println(dcOffset);
}

void captureSamples() {
  lastSampleTime = micros();
  unsigned int samplingPeriod = round(1000000 * (1.0 / SAMPLING_FREQUENCY));
  
  for (int i = 0; i < SAMPLES; i++) {
    unsigned long microSeconds = micros();
    
    // Ler ADC e remover DC offset
    int adcValue = analogRead(AUDIO_PIN);
    vReal[i] = (adcValue - dcOffset) * gainFactor;
    vImag[i] = 0;
    
    // Aguardar próxima amostra
    while (micros() - microSeconds < samplingPeriod) {
      // Espera ativa para timing preciso
    }
  }
}

void processFFT() {
  // Aplicar janela de Hamming para reduzir vazamento espectral
  FFT.Windowing(FFT_WIN_TYP_HAMMING, FFT_FORWARD);
  
  // Computar FFT
  FFT.Compute(FFT_FORWARD);
  
  // Converter para magnitude
  FFT.ComplexToMagnitude();
  
  // Encontrar amplitude máxima
  maxAmplitude = 0;
  for (int i = 1; i < SAMPLES/2; i++) {
    if (vReal[i] > maxAmplitude) {
      maxAmplitude = vReal[i];
    }
  }
  
  // Normalizar amplitude (0-1024 range)
  maxAmplitude = constrain(maxAmplitude, 0, 1024);
}

void analyzeBands() {
  bands.bass = 0;
  bands.mid = 0;
  bands.treble = 0;
  
  // Calcular largura de bin de frequência
  double binWidth = (double)SAMPLING_FREQUENCY / SAMPLES;
  
  for (int i = 1; i < SAMPLES/2; i++) {
    double frequency = i * binWidth;
    double magnitude = vReal[i];
    
    // Classificar em bandas
    if (frequency >= 20 && frequency <= 250) {
      bands.bass += magnitude;
    } else if (frequency > 250 && frequency <= 4000) {
      bands.mid += magnitude;
    } else if (frequency > 4000) {
      bands.treble += magnitude;
    }
  }
  
  // Normalizar bandas
  bands.bass = constrain(bands.bass / 8, 0, 1024);    // 8 bins aproximadamente
  bands.mid = constrain(bands.mid / 30, 0, 1024);     // 30 bins aproximadamente  
  bands.treble = constrain(bands.treble / 25, 0, 1024); // 25 bins aproximadamente
}

void findDominantFrequency() {
  double maxMagnitude = 0;
  dominantFreqIndex = 1;
  
  // Procurar pico mais alto (ignorar DC - bin 0)
  for (int i = 1; i < SAMPLES/2; i++) {
    if (vReal[i] > maxMagnitude) {
      maxMagnitude = vReal[i];
      dominantFreqIndex = i;
    }
  }
  
  // Converter bin para frequência
  dominantFreq = (dominantFreqIndex * SAMPLING_FREQUENCY) / SAMPLES;
  
  // Filtro simples para evitar mudanças bruscas
  static double lastDominantFreq = 440;
  dominantFreq = (dominantFreq * 0.3) + (lastDominantFreq * 0.7);
  lastDominantFreq = dominantFreq;
}

void sendAudioData(bool beat) {
  // Formato: AMP:xxx,FREQ:xxx,BASS:xxx,MID:xxx,TREBLE:xxx,BEAT:x
  
  Serial.print("AMP:");
  Serial.print((int)maxAmplitude);
  Serial.print(",FREQ:");
  Serial.print((int)dominantFreq);
  Serial.print(",BASS:");
  Serial.print((int)bands.bass);
  Serial.print(",MID:");
  Serial.print((int)bands.mid);
  Serial.print(",TREBLE:");
  Serial.print((int)bands.treble);
  Serial.print(",BEAT:");
  Serial.println(beat ? 1 : 0);
}

// ===== COMANDOS SERIAIS (OPCIONAL) =====
void serialEvent() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    if (command == "CALIBRATE") {
      calibrateDCOffset();
    } else if (command.startsWith("GAIN:")) {
      gainFactor = command.substring(5).toDouble();
      Serial.print("# Gain set to: ");
      Serial.println(gainFactor);
    } else if (command == "STATUS") {
      printStatus();
    } else if (command == "HELP") {
      printHelp();
    }
  }
}

void printStatus() {
  Serial.println("# === SYSTEM STATUS ===");
  Serial.print("# Sampling Freq: "); Serial.print(SAMPLING_FREQUENCY); Serial.println(" Hz");
  Serial.print("# DC Offset: "); Serial.println(dcOffset);
  Serial.print("# Gain Factor: "); Serial.println(gainFactor);
  Serial.print("# Beat Threshold: "); Serial.println(beatDetector.threshold);
  Serial.print("# Dominant Freq: "); Serial.print(dominantFreq); Serial.println(" Hz");
  Serial.println("# =====================");
}

void printHelp() {
  Serial.println("# === COMMANDS ===");
  Serial.println("# CALIBRATE - Recalibrate DC offset");
  Serial.println("# GAIN:x.x - Set gain factor");
  Serial.println("# STATUS - Show system status");  
  Serial.println("# HELP - Show this help");
  Serial.println("# =================");
}

// ===== FUNÇÕES DE DEBUG (OPCIONAL) =====
#ifdef DEBUG_MODE
void debugFFT() {
  Serial.println("# FFT Debug Data:");
  for (int i = 0; i < SAMPLES/2; i++) {
    double frequency = (i * SAMPLING_FREQUENCY) / SAMPLES;
    Serial.print(frequency); Serial.print(" Hz: ");
    Serial.println(vReal[i]);
  }
}

void debugBands() {
  Serial.print("# Bands - Bass: "); Serial.print(bands.bass);
  Serial.print(", Mid: "); Serial.print(bands.mid);
  Serial.print(", Treble: "); Serial.println(bands.treble);
}
#endif

/*
 * NOTAS DE IMPLEMENTAÇÃO:
 * 
 * 1. O código usa a biblioteca arduinoFFT para análise espectral
 * 2. Implementa detecção adaptativa de beat baseada em energia dos graves
 * 3. Calibra automaticamente o offset DC do eletreto
 * 4. Envia dados a ~50Hz para evitar overflow do buffer serial
 * 5. Suporta comandos seriais para calibração e ajustes
 * 
 * MELHORIAS POSSÍVEIS:
 * - Filtro passa-alta para remover ruído de 50/60Hz
 * - AGC (Automatic Gain Control) baseado no nível médio
 * - Detecção de onset mais sofisticada
 * - Análise de pitch mais precisa
 * - Compressão de dados para maior taxa de transmissão
 */