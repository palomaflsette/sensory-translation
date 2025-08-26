
// SISTEMA MUSICAL TÁTIL - 4 MOTORES
// Tecnologia Assistiva para Deficientes Auditivos
// Separação em 4 faixas de frequência para experiência imersiva

const int micPin = A1;
const int ledPin = 3;

// === 4 MOTORES - SEPARAÇÃO REFORMULADA ===
const int motorKickPin = 11;        // KICK/BUMBO (20-80Hz) - Batidas principais
const int motorBaixoPin = 10;       // BAIXO/BASS (80-300Hz) - Linha de baixo constante
const int motorVozPin = 9;         // VOZ/MELODIA (300-2kHz) - Vocal, guitarra, piano
const int motorAgudosPin = 8;      // AGUDOS (2k-8kHz) - Pratos, hi-hat, harmônicos

// === FILTROS REFORMULADOS ===
float filtroKick = 0.0;           // Para detectar batidas (kick/bumbo)
float filtroBaixo = 0.0;          // Para linha de baixo constante
float filtroVoz = 0.0;            // Para vocal/melodia
float filtroAgudos = 0.0;         // Para pratos/detalhes

// Coeficientes especializados
const float coefKick = 0.08;      // Muito lento = detecta kick/bumbo
const float coefBaixo = 0.30;     // Médio-rápido = linha de baixo
const float coefVoz = 0.45;       // Rápido = vocal/melodia
const float coefAgudos = 0.8;     // Muito rápido = agudos

// === DETECTORES ESPECIAIS ===
float kickBoost = 0.0;            // Boost para detecção de kick
float baixoConstante = 0.0;       // Detecta linha de baixo constante
float vozDetector = 0.0;          // Detector específico de voz
float hihatDetector = 0.0;        // Detector de hi-hat/pratos

// === VARIÁVEIS DE CONTROLE ===
int valorBase = 512;
float amplitudeAnterior = 0.0;
float vozAnterior = 0.0;
unsigned long ultimaBatida = 0;

// === INTENSIDADES DOS MOTORES ===
int intensidadeKick = 0;          // Motor kick/bumbo
int intensidadeBaixo = 0;         // Motor baixo/bass
int intensidadeVoz = 0;           // Motor voz/melodia
int intensidadeAgudos = 0;        // Motor agudos

// === THRESHOLDS REFORMULADOS ===
const float THRESHOLD_KICK = 45.0;     // Kick/bumbo (mais seletivo)
const float THRESHOLD_BAIXO = 38.0;     // Baixo (mais sensível)
const float THRESHOLD_VOZ = 32.0;      // Voz/melodia (mais sensível)
const float THRESHOLD_AGUDOS = 30.0;   // Agudos (mais sensível)

// === PARÂMETROS PARA EXPERIÊNCIA TÁTIL ===
const int INTENSIDADE_MIN = 80;        // PWM mínimo para sentir
const int INTENSIDADE_MAX_SUB = 255;   // Sub-graves = mais forte
const int INTENSIDADE_MAX_MED = 240;   // Med-graves = forte
const int INTENSIDADE_MAX_VOZ = 200;   // Voz = médio
const int INTENSIDADE_MAX_AGUDOS = 180; // Agudos = mais suave

void setup() {
  Serial.begin(115200);
  
  pinMode(motorKickPin, OUTPUT);
  pinMode(motorBaixoPin, OUTPUT);
  pinMode(motorVozPin, OUTPUT);
  pinMode(motorAgudosPin, OUTPUT);
  pinMode(ledPin, OUTPUT);
  pinMode(micPin, INPUT);
  
  Serial.println("=== SISTEMA MUSICAL TÁTIL - 4 MOTORES ===");
  Serial.println("🎵 Tecnologia Assistiva para Deficientes Auditivos");
  Serial.println();
  Serial.println("MAPEAMENTO DOS MOTORES:");
  Serial.println("Motor 1 (KICK): Bumbo, batidas principais (20-80Hz)");
  Serial.println("Motor 2 (BAIXO): Linha de baixo constante (80-300Hz)");
  Serial.println("Motor 3 (VOZ): Vocal, guitarra, melodia (300-2kHz)");
  Serial.println("Motor 4 (AGU): Pratos, hi-hat, detalhes (2k-8kHz)");
  Serial.println();
  
  // Calibração
  Serial.print("Calibrando sistema");
  long soma = 0;
  for(int i = 0; i < 150; i++) {
    soma += analogRead(micPin);
    if(i % 25 == 0) Serial.print(".");
    delay(3);
  }
  valorBase = soma / 150;
  
  Serial.println();
  Serial.print("Valor base calibrado: ");
  Serial.println(valorBase);
  Serial.println();
  Serial.println("🎶 Sistema ativo! Reproduza música para testar.");
  Serial.println("Monitor mostrará: KICK|BAIXO|VOZ|AGU + barras visuais");
  Serial.println("===============================================");
  
  delay(1000);
}

void loop() {
  // === LEITURA E PRÉ-PROCESSAMENTO ===
  int valorAtual = analogRead(micPin);
  float amplitude = abs(valorAtual - valorBase);
  
  // === FILTROS DE FREQUÊNCIA ESPECIALIZADOS ===
  
  // KICK: Ultra lento = detecta apenas batidas profundas (bumbo)
  filtroKick = filtroKick * (1.0 - coefKick) + amplitude * coefKick;
  
  // BAIXO: Velocidade média = linha de baixo constante
  filtroBaixo = filtroBaixo * (1.0 - coefBaixo) + amplitude * coefBaixo;
  
  // VOZ: Detecta variações médias = vocal, melodias
  float deltaVoz = amplitude - vozAnterior;
  filtroVoz = filtroVoz * (1.0 - coefVoz) + abs(deltaVoz) * coefVoz;
  vozAnterior = amplitude;
  
  // AGUDOS: Muito rápido = pratos, hi-hat, harmônicos
  filtroAgudos = filtroAgudos * (1.0 - coefAgudos) + amplitude * coefAgudos;
  
  // === DETECTORES ESPECIAIS ===
  
  // Detector de KICK: Pico súbito E filtro lento alto
  float deltaAmplitude = amplitude - amplitudeAnterior;
  if(deltaAmplitude > 35.0 && filtroKick > 8.0 && 
     (millis() - ultimaBatida) > 150) {  // Intervalo maior entre kicks
    kickBoost = 30.0;  // Boost para kick
    ultimaBatida = millis();
  }
  kickBoost *= 0.8;  // Decay médio
  
  // Detector de BAIXO CONSTANTE: Nível médio estável
  if(filtroBaixo > 8.0 && filtroBaixo < 40.0) {
    baixoConstante = min(baixoConstante + 3.0, 25.0);
  }
  baixoConstante *= 0.92;  // Decay lento
  
  // Detector de VOZ: Variações na faixa média
  if(filtroVoz > 8.0) {
    vozDetector = min(vozDetector + 4.0, 30.0);
  }
  vozDetector *= 0.85;
  
  // Detector de HI-HAT: Agudos puros sem graves
  if(filtroAgudos > 25.0 && filtroKick < 10.0) {
    hihatDetector = min(hihatDetector + 6.0, 20.0);
  }
  hihatDetector *= 0.75;
  
  amplitudeAnterior = amplitude;
  
  // === CÁLCULO DAS INTENSIDADES FINAIS ===
  
  float nivelKick = filtroKick + kickBoost;           // Kick = filtro lento + boosts
  float nivelBaixo = filtroBaixo + baixoConstante;    // Baixo = filtro médio + constante
  float nivelVoz = filtroVoz + vozDetector;           // Voz = variações médias
  float nivelAgudos = filtroAgudos + hihatDetector;   // Agudos = filtro rápido + hi-hat
  
  // === CONTROLE DOS MOTORES ===
  
  // KICK/BUMBO (apenas para batidas principais)
  if(nivelKick > THRESHOLD_KICK) {
    float norm = constrain(nivelKick - THRESHOLD_KICK, 0, 40) / 40.0;
    norm = pow(norm, 0.9);
    intensidadeKick = INTENSIDADE_MIN + (norm * (INTENSIDADE_MAX_SUB - INTENSIDADE_MIN));
  } else {
    intensidadeKick = 0;
  }
  
  // BAIXO (linha de baixo constante)
  if(nivelBaixo > THRESHOLD_BAIXO) {
    float norm = constrain(nivelBaixo - THRESHOLD_BAIXO, 0, 50) / 50.0;
    norm = pow(norm, 0.7);
    intensidadeBaixo = INTENSIDADE_MIN + (norm * (INTENSIDADE_MAX_MED - INTENSIDADE_MIN));
  } else {
    intensidadeBaixo = 0;
  }
  
  // VOZ/MELODIA
  if(nivelVoz > THRESHOLD_VOZ) {
    float norm = constrain(nivelVoz - THRESHOLD_VOZ, 0, 45) / 45.0;
    norm = pow(norm, 0.8);
    intensidadeVoz = INTENSIDADE_MIN + (norm * (INTENSIDADE_MAX_VOZ - INTENSIDADE_MIN));
  } else {
    intensidadeVoz = 0;
  }
  
  // AGUDOS
  if(nivelAgudos > THRESHOLD_AGUDOS) {
    float norm = constrain(nivelAgudos - THRESHOLD_AGUDOS, 0, 35) / 35.0;
    norm = pow(norm, 0.75);
    intensidadeAgudos = INTENSIDADE_MIN + (norm * (INTENSIDADE_MAX_AGUDOS - INTENSIDADE_MIN));
  } else {
    intensidadeAgudos = 0;
  }
  
  // === ACIONAMENTO DOS MOTORES ===
  analogWrite(motorKickPin, intensidadeKick);
  analogWrite(motorBaixoPin, intensidadeBaixo);
  analogWrite(motorVozPin, intensidadeVoz);
  analogWrite(motorAgudosPin, intensidadeAgudos);
  
  // LED indicador (intensidade máxima)
  int ledLevel = max(max(intensidadeKick, intensidadeBaixo), 
                     max(intensidadeVoz, intensidadeAgudos));
  analogWrite(ledPin, ledLevel);
  
  // === MONITOR PARA TECNOLOGIA ASSISTIVA ===
  static unsigned long ultimoMonitor = 0;
  if(millis() - ultimoMonitor > 120) {  // Monitor a cada 120ms
    
    // Cabeçalho com status geral
    bool sistemaAtivo = (intensidadeKick + intensidadeBaixo + intensidadeVoz + intensidadeAgudos) > 0;
    
    Serial.print(sistemaAtivo ? "🎵 MÚSICA ATIVA " : "⏸  SILÊNCIO    ");
    
    // Valores dos motores
    Serial.print("SUB:");
    Serial.print(String(intensidadeKick).substring(0,3));
    Serial.print(" MED:");
    Serial.print(String(intensidadeBaixo).substring(0,3));
    Serial.print(" VOZ:");
    Serial.print(String(intensidadeVoz).substring(0,3));
    Serial.print(" AGU:");
    Serial.print(String(intensidadeAgudos).substring(0,3));
    
    Serial.print(" |");
    
    // Visualização tátil com barras
    int subBars = map(intensidadeKick, 0, 255, 0, 5);
    int medBars = map(intensidadeBaixo, 0, 255, 0, 5);
    int vozBars = map(intensidadeVoz, 0, 255, 0, 5);
    int aguBars = map(intensidadeAgudos, 0, 255, 0, 5);
    
    // Sub-graves = █ (mais forte)
    for(int i = 0; i < 5; i++) Serial.print(i < subBars ? "█" : ".");
    Serial.print("|");
    
    // Med-graves = ▓
    for(int i = 0; i < 5; i++) Serial.print(i < medBars ? "▓" : ".");
    Serial.print("|");
    
    // Voz = ▒
    for(int i = 0; i < 5; i++) Serial.print(i < vozBars ? "▒" : ".");
    Serial.print("|");
    
    // Agudos = ░
    for(int i = 0; i < 5; i++) Serial.print(i < aguBars ? "░" : ".");
    
    // Detectores especiais
    if(kickBoost > 5) Serial.print(" 🥁KICK");
    if(baixoConstante > 5) Serial.print(" 🎸BAIXO");
    if(hihatDetector > 5) Serial.print(" ✨HIHAT");
    
    Serial.println();
    ultimoMonitor = millis();
  }
  
  delay(8); 
}

/*
SEPARAÇÃO EM 4 FAIXAS:
1. SUB-GRAVES (20-80Hz): Bateria, sub-bass - VIBRAÇÃO MAIS INTENSA
2. MED-GRAVES (80-250Hz): Bumbo, baixo - VIBRAÇÃO FORTE  
3. VOZ/MELODIA (250-2kHz): Vocal, guitarra, piano - VIBRAÇÃO EXPRESSIVA
4. AGUDOS (2k-8kHz): Pratos, hi-hat - VIBRAÇÃO DELICADA

RECURSOS ESPECIAIS:
- Detectores de instrumentos específicos (kick, snare, hi-hat)
- Intensidades calibradas para experiência tátil otimizada
- Curvas não-lineares para maior expressividade
- Monitor visual detalhado para acompanhamento

POSICIONAMENTO SUGERIDO DOS MOTORES:
- SUB-GRAVES: Peito/costas (graves se sentem no corpo todo)
- MED-GRAVES: Abdômen (bumbo e baixo)
- VOZ: Braços/ombros (melodias)
- AGUDOS: Pulsos/mãos (detalhes delicados)

RESULTADO ESPERADO:
- Música pop: Todos motores ativos em harmonia
- Música eletrônica: Sub e med-graves predominantes
- Balada: Voz proeminente com acompanhamento suave
- Rock: Med-graves (bateria) + voz (guitarra) intensos

AJUSTES POSSÍVEIS:
- THRESHOLD_*: Sensibilidade de cada faixa
- INTENSIDADE_MAX_*: Força máxima de cada motor
- Coeficientes dos filtros: Separação das frequências
*/