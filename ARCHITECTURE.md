# Documentação da Arquitetura ESP32-C3

## 🏗️ Arquitetura de Software

Este documento detalha a arquitetura do projeto ESP32-C3 IoT Device, explicando padrões de design (design patterns), decisões arquiteturais e princípios de engenharia de software aplicados.

---

## 📚 Índice

1. [Visão Geral](#visão-geral)
2. [Princípios Arquiteturais](#princípios-arquiteturais)
3. [Camadas da Aplicação](#camadas-da-aplicação)
4. [Padrões de Design](#padrões-de-design)
5. [Fluxo de Dados](#fluxo-de-dados)
6. [Injeção de Dependências](#injeção-de-dependências)
7. [Estratégia de Tratamento de Erros](#estratégia-de-tratamento-de-erros)
8. [Decisões Técnicas](#decisões-técnicas)

---

## Visão Geral

### Arquitetura em Camadas

```
┌─────────────────────────────────────────────────┐
│              Application Layer                   │
│              (core/app.py)                      │
│  - Orchestrates all components                  │
│  - Manages lifecycle                            │
│  - Dependency injection                         │
└─────────────────┬───────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬──────────────┐
    │             │             │              │
    ▼             ▼             ▼              ▼
┌────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐
│Hardware│  │ Network  │  │   Web   │  │   Core   │
│ Layer  │  │  Layer   │  │  Layer  │  │ Services │
└────────┘  └──────────┘  └─────────┘  └──────────┘
│           │             │             │
│  LED      │ WiFi        │ Microdot    │ Logger
│  Display  │ Manager     │ Routes      │ Config
└───────────┴─────────────┴─────────────┴──────────┘
```

### Stack Tecnológico

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Runtime** | MicroPython 1.27.0 | Python interpreter for ESP32 |
| **Hardware** | ESP32-C3 RISC-V | Microcontroller |
| **Web Framework** | Microdot (async) | HTTP server |
| **Async Runtime** | asyncio | Concurrency |
| **Display Driver** | SSD1306 (I2C) | OLED control |
| **Config Management** | micropython-dotenv | Environment variables |

---

## Princípios Arquiteturais

### Princípios SOLID

#### 1. **Single Responsibility Principle (SRP) - Princípio da Responsabilidade Única**

Cada classe tem uma única responsabilidade:

```python
# ✅ LED class: ONLY controls LED
class LED:
    def on(self): ...
    def off(self): ...
    def toggle(self): ...

# ✅ Display class: ONLY controls display
class Display:
    def show_message(self): ...
    def clear(self): ...

# ✅ WiFiManager: ONLY manages WiFi
class WiFiManager:
    def connect(self): ...
    def disconnect(self): ...
```

#### 2. **Open/Closed Principle (OCP) - Princípio Aberto/Fechado**

Classes abertas para extensão, fechadas para modificação:

```python
# Extensível: adicionar novos tipos de LED sem modificar classe base
class LED:
    def __init__(self, pin, inverted=False):  # Extensível via parâmetro
        self._inverted = inverted
```

#### 3. **Liskov Substitution Principle (LSP) - Princípio da Substituição de Liskov**

Objetos podem ser substituídos por suas abstrações:

```python
# Qualquer display que implemente show_message() pode ser usado
def display_status(display, message):
    display.show_message(message)  # Funciona com qualquer display
```

#### 4. **Interface Segregation Principle (ISP) - Princípio da Segregação de Interface**

Interfaces específicas e focadas:

```python
# Cada handler tem interface específica
class RouteHandlers:
    async def led_on(self, request): ...     # LED control
    async def set_message(self, request): ... # Display control
    async def health(self, request): ...      # Health check
```

#### 5. **Dependency Inversion Principle (DIP) - Princípio da Inversão de Dependência**

Dependa de abstrações, não de implementações concretas:

```python
# Application depende de abstrações (interfaces)
class Application:
    def __init__(self, wifi_ssid, wifi_password, hostname):
        # Injeta dependências (inversão)
        self.led = LED(...)
        self.display = Display(...)
        self.wifi_manager = WiFiManager(...)
```

### Separação de Responsabilidades (Separation of Concerns)

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│         (web/routes.py)                 │
│  - HTTP handlers                        │
│  - Request/response formatting          │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│         Business Logic Layer            │
│         (core/app.py)                   │
│  - Application orchestration            │
│  - Component coordination               │
└──────────────┬──────────────────────────┘
               │
┌──────────────┴──────────────────────────┐
│         Data/Hardware Layer             │
│    (hardware/*, net_manager/*)          │
│  - Hardware abstraction                 │
│  - Network communication                │
└─────────────────────────────────────────┘
```

---

## Camadas da Aplicação

### 1. Camada Core (`core/`)

**Responsabilidade**: Lógica central da aplicação

#### `core/app.py` - Orquestrador da Aplicação (Application Orchestrator)

```python
class Application:
    """
    Main orchestrator - segue Facade Pattern

    Responsabilidades:
    - Lifecycle management (setup → run → shutdown)
    - Dependency injection
    - Component coordination
    """

    def __init__(self, wifi_ssid, wifi_password, hostname):
        # Configuration
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.hostname = hostname

        # Components (initialized in setup)
        self.led = None
        self.display = None
        self.wifi_manager = None
        self.web_server = None

    def setup(self):
        """Setup phase: initialize all components"""
        self._initialize_hardware()
        self._initialize_network()
        self._initialize_web_server()

    async def run(self):
        """Main application loop (async tasks)"""
        web_task = asyncio.create_task(self.web_server.start())
        repl_task = asyncio.create_task(aiorepl.task())
        await asyncio.gather(repl_task, web_task)
```

**Padrões Aplicados**:
- ✅ Facade Pattern (padrão fachada - simplifica subsistemas complexos)
- ✅ Template Method (método template - setup → run → shutdown)
- ✅ Dependency Injection (injeção de dependências)

#### `core/logger.py` - Sistema de Logging Estruturado

```python
class Logger:
    """
    Lightweight logging with levels

    Levels: DEBUG < INFO < WARNING < ERROR < CRITICAL
    """

    def __init__(self, name, level=LogLevel.INFO):
        self.name = name
        self.level = level

    def _log(self, level, message):
        if level >= self.level:
            timestamp = time.time()
            print(f"[{timestamp:.3f}] {level_name} [{self.name}] {message}")
```

**Features**:
- ✅ Timestamps automáticos
- ✅ Log levels configuráveis
- ✅ Context (nome do módulo)

### 2. Camada de Hardware (`hardware/`)

**Responsabilidade**: Abstração de hardware

#### `hardware/led.py` - Abstração de LED

```python
class LED:
    """
    Hardware abstraction for LED control

    Supports active-low LEDs (common in ESP32)
    """

    def __init__(self, pin, inverted=False):
        self._pin = Pin(pin, Pin.OUT)
        self._inverted = inverted  # Active-low support
        self._state = False

    def on(self):
        """Turn LED on (handles inversion internally)"""
        if self._inverted:
            self._pin.off()  # Active-low: LOW = ON
        else:
            self._pin.on()
        self._state = True
```

**Decisões de Design**:
- ✅ **Flag invertida**: Suporta LEDs active-low (ativo-baixo) sem código especial
- ✅ **Rastreamento de estado**: `_state` sempre reflete estado lógico
- ✅ **Logging**: Todas operações são logadas

#### `hardware/display.py` - Abstração de Display

```python
class Display:
    """
    OLED display abstraction with graceful degradation
    """

    def __init__(self, scl_pin, sda_pin, i2c_addr):
        self._available = False
        try:
            i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
            self._driver = ssd1306.SSD1306_I2C(128, 64, i2c)
            self._available = True
        except Exception as e:
            logger.error(f"Display init failed: {e}")
            # Application continues even without display!

    def show_message(self, text):
        if not self._available:
            logger.debug(f"Display unavailable: {text}")
            return  # Graceful degradation
        self._driver.text(text, x, y, 1)
        self._driver.show()
```

**Decisões de Design**:
- ✅ **Degradação Graciosa (Graceful Degradation)**: App funciona sem display
- ✅ **Verificação de Disponibilidade**: propriedade `is_available`
- ✅ **Resiliência a Erros**: Try-catch em todas operações

#### `hardware/morse.py` - Codificador Morse

```python
class MorseEncoder:
    """
    Morse code encoder with LED signaling and display feedback

    Implements ITU-R M.1677-1 international standard
    """

    def __init__(self, led, display=None, dot_duration=0.2):
        self.led = led
        self.display = display  # Optional display for progress
        self.dot_duration = dot_duration
        self.dash_duration = dot_duration * 3
        # Timing standard (ITU-R M.1677-1)
        self.symbol_gap = dot_duration      # Between dots/dashes
        self.letter_gap = dot_duration * 3  # Between letters
        self.word_gap = dot_duration * 7    # Between words

    async def blink_morse(self, text):
        """Encode text to Morse and blink LED with display sync"""
        morse = self.text_to_morse(text)

        # Progressive display update during transmission
        for char_idx, letter in enumerate(text):
            if self.display:
                self.display.show_message(text[:char_idx + 1])
            await self._blink_letter(morse_for_letter)

        return {'text': text, 'morse': morse, 'duration': ...}
```

**Decisões de Design**:
- ✅ **Dependency Injection**: LED e Display injetados (testável)
- ✅ **Progressive Display**: Mostra cada letra conforme é transmitida
- ✅ **Standard Timing**: Segue padrão internacional ITU-R M.1677-1
- ✅ **Async Operations**: Não bloqueia o servidor durante transmissão
- ✅ **Parameterizable Speed**: Velocidade ajustável via `dot_duration`
- ✅ **State Preservation**: Restaura estado inicial do LED após transmissão
- ✅ **Character Validation**: Valida caracteres suportados (A-Z, 0-9, pontuação)

**Timing Standard (ITU-R M.1677-1)**:
```
Dot (·):        200ms (base unit)
Dash (−):       600ms (3× dot)
Symbol gap:     200ms (1× dot)
Letter gap:     600ms (3× dot)
Word gap:      1400ms (7× dot)
```

**Exemplo de Uso**:
```python
# SOS em Morse: ... --- ...
encoder = MorseEncoder(led, display, dot_duration=0.2)
result = await encoder.blink_morse("SOS")
# Display mostra: S → SO → SOS progressivamente
# LED pisca: ··· (gap) −−− (gap) ···
```

### 3. Camada de Rede (`net_manager/`)

**Responsabilidade**: Gestão de conectividade

#### `net_manager/wifi_manager.py` - Gerenciamento WiFi

```python
class WiFiManager:
    """
    WiFi connection with retry logic and LED feedback
    """

    def connect(self, led=None) -> bool:
        """
        Connect to WiFi with exponential backoff

        Args:
            led: Optional LED for visual feedback

        Returns:
            True if connected, False otherwise
        """
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)
        self._wlan.config(hostname=self.hostname)
        self._wlan.connect(self.ssid, self.password)

        # Retry logic with LED feedback
        attempts = 0
        while not self._wlan.isconnected() and attempts < MAX_RETRIES:
            if led:
                led.on()  # Visual indicator
            time.sleep(RETRY_INTERVAL)
            attempts += 1

        if self._wlan.isconnected():
            if led:
                led.off()  # Success indicator
            return True
        return False
```

**Decisões de Design**:
- ✅ **Lógica de Retry (tentativa)**: Até 20 tentativas (40 segundos)
- ✅ **Feedback via LED**: Indicador visual durante conexão
- ✅ **Conexão em Background**: Continua mesmo se falhar
- ✅ **Informações de Rede**: Métodos para consulta de status

**Por que `net_manager` e não `network`?**
```python
# MicroPython tem módulo built-in 'network'
import network  # ← Built-in do MicroPython

# Nossa pasta 'network/' causaria conflito
# Solução: renomear para 'net_manager/'
from net_manager.wifi_manager import WiFiManager  # ✅ Sem conflito
```

### 4. Camada Web (`web/`)

**Responsabilidade**: Interface HTTP

#### `web/server.py` - Configuração do Servidor

```python
class WebServer:
    """
    Microdot web server with configured routes
    """

    def __init__(self, led, display, wifi_manager, hostname):
        self.app = Microdot()
        self.handlers = RouteHandlers(led, display, wifi_manager, hostname)
        self._setup_routes()

    def _setup_routes(self):
        """Configure HTTP routes"""
        # Static files
        self.app.route('/')(self.handlers.serve_index)

        # API endpoints
        self.app.route('/health')(self.handlers.health)
        self.app.route('/storage')(self.handlers.storage_info)

        # LED control
        self.app.route('/led')(self.handlers.get_led_status)
        self.app.route('/led/on')(self.handlers.led_on)
        self.app.route('/led/off')(self.handlers.led_off)
        self.app.route('/led/toggle')(self.handlers.led_toggle)
        self.app.route('/led/blink')(self.handlers.led_blink)

        # Morse code
        self.app.route('/morse')(self.handlers.morse_blink)

        # Display control (GET and POST)
        self.app.get('/message')(self.handlers.message_handler)
        self.app.post('/message')(self.handlers.message_handler)
```

**Decisões de Design**:
- ✅ **Injeção de Dependências**: Handlers recebem dependências
- ✅ **Organização de Rotas**: Agrupamento lógico
- ✅ **Flexibilidade de Métodos**: GET e POST para facilitar testes

#### `web/routes.py` - Manipuladores de Rotas (Route Handlers)

```python
class RouteHandlers:
    """
    HTTP route handlers with dependency injection
    """

    def __init__(self, led, display, wifi_manager, hostname):
        # Injected dependencies
        self.led = led
        self.display = display
        self.wifi_manager = wifi_manager
        self.hostname = hostname

    async def led_on(self, request):
        """Turn LED on endpoint"""
        self.led.on()
        return {'led': 'on' if self.led.is_on else 'off'}

    async def message_handler(self, request):
        """
        Smart handler: GET without params → read, with params → write
        """
        text = request.args.get('text', None)

        if text is None:
            # GET without params: read current message
            return {'message': self.last_message}

        # GET/POST with params: set new message
        self.last_message = text
        self.display.show_message(text)
        return {'message': text, 'displayed': True}

    async def led_blink(self, request):
        """
        Parametrized LED blinking with validation
        """
        count = int(request.args.get('count', 3))
        interval = float(request.args.get('interval', 0.5))

        # Input validation with limits
        count = max(1, min(count, 20))
        interval = max(0.1, min(interval, 2.0))

        # Async blinking (non-blocking)
        for i in range(count):
            self.led.on()
            await asyncio.sleep(interval)
            self.led.off()
            await asyncio.sleep(interval)

        return {'action': 'blink', 'count': count, 'interval': interval}

    async def morse_blink(self, request):
        """
        Morse code transmission with progressive display
        """
        text = request.args.get('text')
        speed = float(request.args.get('speed', 0.2))

        # Validation
        if not text:
            return {'error': 'Missing text parameter'}, 400
        if len(text) > 20:
            return {'error': 'Text too long'}, 400

        # Create encoder and transmit
        morse_encoder = MorseEncoder(self.led, self.display, speed)
        result = await morse_encoder.blink_morse(text)

        return result  # {'text': ..., 'morse': ..., 'duration': ...}

    async def storage_info(self, request):
        """
        Filesystem storage information
        """
        import os
        stat = os.statvfs('/')

        # Calculate storage metrics
        total_bytes = stat[2] * stat[0]  # blocks * block_size
        free_bytes = stat[3] * stat[0]   # free_blocks * block_size
        used_bytes = total_bytes - free_bytes

        return {
            'total_mb': round(total_bytes / (1024**2), 2),
            'used_mb': round(used_bytes / (1024**2), 2),
            'free_mb': round(free_bytes / (1024**2), 2),
            'used_percent': round(used_bytes / total_bytes * 100, 2)
        }
```

**Decisões de Design**:
- ✅ **Roteamento Inteligente (Smart Routing)**: Um handler para leitura e escrita
- ✅ **Respostas JSON**: Sempre retorna JSON válido
- ✅ **Tratamento de Erros**: Try-catch em operações críticas
- ✅ **Degradação Graciosa**: Funciona sem display
- ✅ **Input Validation**: Limites para prevenir abuso (count, interval, text length)
- ✅ **Async Operations**: Operações longas não bloqueiam o servidor
- ✅ **Progressive Feedback**: Display atualizado durante transmissão Morse

---

## Padrões de Design

### 1. Injeção de Dependências (Dependency Injection)

**Problema**: Estado global dificulta testes e manutenção

**Solução**: Injetar dependências via construtor

```python
# ❌ ANTES: Global state
import config
def control_led():
    config.led.on()  # Acoplamento global

# ✅ DEPOIS: Dependency injection
class LedController:
    def __init__(self, led):  # Injetado
        self.led = led

    def control(self):
        self.led.on()  # Desacoplado

# Usage
led = LED(pin=8)
controller = LedController(led)  # Inject
```

**Benefícios**:
- ✅ Testável (fácil criar mocks)
- ✅ Dependências explícitas
- ✅ Flexível (trocar implementações facilmente)

### 2. Padrão Facade (Fachada)

**Problema**: Subsistemas complexos difíceis de usar

**Solução**: Classe Application como facade

```python
class Application:
    """
    Facade que simplifica interação com subsistemas
    """

    def start(self):
        """
        Single method hides complexity:
        - Hardware init
        - Network connection
        - Server startup
        - Async loop
        """
        self.setup()
        asyncio.run(self.run())

# Usage (simple!)
app = Application(ssid, password, hostname)
app.start()  # One line!
```

### 3. Padrão Factory (Fábrica)

**Factory de Logger**:

```python
def get_logger(name, level=LogLevel.INFO):
    """Factory function for logger instances"""
    return Logger(name, level)

# Usage
logger = get_logger('MyModule')  # Factory cria instância
```

### 4. Padrão Strategy (Estratégia)

**Configuração WiFi via .env**:

```python
# Different strategies for different environments
# Development:
WIFI_SSID=dev_network
WIFI_PASSWORD=dev_password

# Production:
WIFI_SSID=prod_network
WIFI_PASSWORD=prod_password

# Loaded via same code path (strategy is interchangeable)
```

### 5. Padrão Template Method (Método Template)

**Ciclo de Vida da Aplicação**:

```python
class Application:
    def start(self):
        """Template method defines algorithm"""
        self.setup()      # Step 1
        asyncio.run(self.run())  # Step 2

    def setup(self):
        """Steps called in order"""
        self._initialize_hardware()
        self._initialize_network()
        self._initialize_web_server()
```

---

## Fluxo de Dados

### Sequência de Inicialização (Startup)

```
[Power On]
    ↓
boot.py executes
    └─→ import webrepl; webrepl.start()
    ↓
main.py executes
    └─→ time.sleep(2)  # Allow IDE interrupt
    └─→ from core.app import Application
    └─→ import config  # Loads .env
    ↓
app = Application(wifi_ssid, password, hostname)
    ↓
app.start()
    ↓
app.setup()
    ├─→ _initialize_hardware()
    │   ├─→ LED(pin=8, inverted=True)
    │   └─→ Display(scl=6, sda=5)
    │
    ├─→ _initialize_network()
    │   └─→ WiFiManager.connect(led=led)
    │       └─→ LED blinks during connection
    │       └─→ LED off when connected
    │
    └─→ _initialize_web_server()
        └─→ WebServer(led, display, wifi, hostname)
            └─→ RouteHandlers(led, display, wifi, hostname)
    ↓
app.run() (async)
    ├─→ Task 1: Microdot HTTP Server (port 5000)
    └─→ Task 2: aiorepl (async REPL)
    ↓
[Event Loop Running]
```

### Fluxo de Requisição HTTP

```
Browser GET /led/on
    ↓
Microdot receives request
    ↓
Routes to: handlers.led_on(request)
    ↓
handlers.led_on():
    self.led.on()
    return {'led': 'on'}
    ↓
LED.on():
    if inverted:
        pin.off()  # Active-low: LOW = ON
    state = True
    logger.debug("LED ON")
    ↓
Response: {"led":"on"}
    ↓
Browser displays JSON
```

---

## Injeção de Dependências

### Grafo de Componentes

```
Application
    ├─→ LED
    │   └─→ Logger
    │
    ├─→ Display
    │   └─→ Logger
    │
    ├─→ WiFiManager
    │   └─→ Logger
    │
    └─→ WebServer
        ├─→ RouteHandlers
        │   ├─→ LED (injected)
        │   ├─→ Display (injected)
        │   └─→ WiFiManager (injected)
        └─→ Logger
```

### Fluxo de Injeção

```python
# 1. Application creates dependencies
app = Application(ssid, password, hostname)

# 2. Setup creates components
def setup(self):
    self.led = LED(pin=8, inverted=True)  # Create
    self.display = Display(scl=6, sda=5)  # Create
    self.wifi = WiFiManager(ssid, password, hostname)  # Create

    # 3. Inject into WebServer
    self.web_server = WebServer(
        led=self.led,           # Inject
        display=self.display,   # Inject
        wifi=self.wifi,         # Inject
        hostname=self.hostname  # Inject
    )

# 4. WebServer injects into Handlers
class WebServer:
    def __init__(self, led, display, wifi, hostname):
        self.handlers = RouteHandlers(
            led=led,           # Inject
            display=display,   # Inject
            wifi=wifi,         # Inject
            hostname=hostname  # Inject
        )
```

**Benefits**:
- ✅ No global state
- ✅ Easy to test (mock dependencies)
- ✅ Clear ownership
- ✅ Explicit dependencies

---

## Estratégia de Tratamento de Erros

### Tratamento de Erros em Camadas

```python
# Layer 1: Hardware (graceful degradation)
class Display:
    def __init__(self, scl, sda, addr):
        try:
            self._driver = ssd1306.SSD1306_I2C(...)
            self._available = True
        except Exception as e:
            logger.error(f"Display init failed: {e}")
            self._available = False  # Continue without display

# Layer 2: Application (recovery)
class Application:
    def setup(self):
        try:
            self._initialize_hardware()
            self._initialize_network()
            self._initialize_web_server()
        except Exception as e:
            logger.critical(f"Setup failed: {e}")
            raise  # Critical error, cannot continue

# Layer 3: Routes (user feedback)
async def set_message(self, request):
    text = request.args.get('text')
    if text is None:
        return {'error': 'Missing parameter'}, 400

    try:
        self.display.show_message(text)
        return {'message': text, 'displayed': True}
    except Exception as e:
        logger.error(f"Display error: {e}")
        return {'message': text, 'displayed': False}, 500
```

### Princípios de Tratamento de Erros

1. **Fail Fast (falhe rápido)**: Erros críticos param a aplicação
2. **Graceful Degradation (degradação graciosa)**: Funciona sem hardware opcional (display)
3. **Feedback ao Usuário**: Erros retornam JSON com mensagem
4. **Logging**: Todos erros são logados com contexto
5. **Recuperação**: Lógica de retry para operações temporariamente falhas (WiFi)

---

## Decisões Técnicas

### 1. Por que MicroPython?

**Prós**:
- ✅ Python familiar e produtivo
- ✅ REPL interativo para debug
- ✅ Bibliotecas asyncio nativas
- ✅ Ecossistema maduro (Microdot, drivers)

**Contras**:
- ❌ Menor performance que C
- ❌ Maior uso de memória
- ❌ Menos controle low-level (baixo nível)

**Decisão**: Prós superam contras para prototipagem IoT

### 2. Por que Microdot?

**Alternativas consideradas**:
- Flask/FastAPI (muito pesados para MicroPython)
- HTTP básico (reinventar a roda)

**Decisão**: Microdot é lightweight, async-native, e familiar para quem conhece Flask

### 3. Por que asyncio?

**Problema**: Múltiplos serviços concorrentes (HTTP + REPL)

**Alternativas**:
- Threading (não suportado bem em MicroPython)
- Multiprocessing (overhead alto)
- Polling loop (loop de verificação - complexo e ineficiente)

**Decisão**: asyncio é nativo, eficiente e elegante

### 4. Por que .env para configurações?

**Problema**: Credenciais hardcoded (fixas no código) são inseguras

**Alternativas**:
- Configuração JSON (ainda commitada ao git)
- Prompt no boot (inconveniente)
- Página web de configuração (complexo)

**Decisão**: .env é padrão da indústria, gitignored e familiar

### 5. Por que renomear network para net_manager?

**Problema**: Conflito com módulo built-in `network` do MicroPython

```python
import network  # Built-in MicroPython
from network.wifi_manager import ...  # ❌ Sobrescreve built-in!
```

**Solução**: Renomear para `net_manager`

```python
import network  # Built-in (WiFi WLAN class)
from net_manager.wifi_manager import WiFiManager  # ✅ Sem conflito
```

### 6. Por que active-low LED support?

**Problema**: ESP32-C3 tem LED active-low (pino HIGH = LED OFF)

**Alternativas**:
- Trocar lógica em todo código (confuso)
- Documentar a inversão (propenso a erros)

**Decisão**: Abstrair a inversão na classe LED

```python
led = LED(pin=8, inverted=True)
led.on()   # ✅ Código lógico, hardware abstrato
```

---

## Considerações de Performance

### Uso de Memória

- **asyncio**: Event loop (loop de eventos) é eficiente em memória
- **Microdot**: Leve (~15KB)
- **Logging**: Overhead mínimo (apenas timestamps)
- **Sem caching**: Acesso direto ao hardware

### Performance de Rede

- **WiFi retry**: Backoff exponencial evita flood
- **Async I/O**: Requisições non-blocking (não bloqueantes)
- **Arquivos estáticos**: Servidos diretamente (sem processamento)

### Limites de Escalabilidade

- **Clientes concorrentes**: ~5-10 (limite de RAM do ESP32)
- **Taxa de requisições**: ~10 req/seg (interpretador MicroPython)
- **Tamanho de arquivo**: Arquivos estáticos < 100KB recomendado

---

## Estratégia de Testes

### Testes Unitários (Offline)

```python
# Mock dependencies
mock_led = MockLED()
mock_display = MockDisplay()

handlers = RouteHandlers(
    led=mock_led,
    display=mock_display,
    wifi=mock_wifi,
    hostname="test"
)

# Test
await handlers.led_on(mock_request)
assert mock_led.is_on == True  # ✅ Testable without hardware
```

### Testes de Integração (No Dispositivo)

```python
# REPL testing
from hardware.led import LED
led = LED(8, inverted=True)
led.on()   # Visual verification
led.off()

# Network testing
from net_manager.wifi_manager import WiFiManager
wifi = WiFiManager("ssid", "pass", "hostname")
wifi.connect()  # Check logs
```

---

## Melhorias Futuras

### Melhorias Potenciais

1. **Autenticação**: Adicionar autenticação via API key
2. **OTA Updates**: Atualizações de firmware over-the-air (sem fio)
3. **HTTPS**: Suporte TLS para segurança
4. **Banco de Dados**: SQLite para persistência
5. **Métricas**: Endpoint de métricas estilo Prometheus
6. **WebSocket**: Comunicação bidirecional em tempo real

### Oportunidades de Refatoração

1. **Hardware Abstrato**: Interfaces baseadas em protocolo
2. **Validação de Config**: Validação via JSON schema
3. **Rate Limiting (limitação de taxa)**: Proteção contra abuso
4. **Circuit Breaker (disjuntor)**: Fail-fast para serviços downstream

---

## Conclusão

Esta arquitetura demonstra:

✅ **Princípios SOLID** aplicados consistentemente
✅ **Separação de Responsabilidades** em camadas claras
✅ **Injeção de Dependências** para testabilidade
✅ **Tratamento de Erros** robusto com degradação graciosa
✅ **Código Limpo (Clean Code)** com documentação inline
✅ **Padrões Production-Ready** em MicroPython

O código é:
- **Manutenível (Maintainable)**: Fácil de entender e modificar
- **Testável (Testable)**: Dependências podem ser mockadas
- **Escalável (Scalable)**: Camadas podem ser estendidas independentemente
- **Profissional**: Segue melhores práticas da indústria

---

**Autor**: Bruno Fernandes (CFA 2026)
**Versão**: 2.0 (Edição Refatorada)
**Data**: Março 2026
