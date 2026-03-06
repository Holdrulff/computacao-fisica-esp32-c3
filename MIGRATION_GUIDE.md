# Guia de Migração - ESP32-C3 Edição Refatorada

Guia completo passo a passo para migrar da base de código ESP32-C3 original para a arquitetura refatorada de nível sênior.

---

## Índice

1. [Visão Geral](#visão-geral)
2. [Checklist Pré-Migração](#checklist-pré-migração)
3. [Procedimentos de Backup](#procedimentos-de-backup)
4. [Passos da Migração](#passos-da-migração)
5. [Migração de Configuração](#migração-de-configuração)
6. [Mudanças na Estrutura de Arquivos](#mudanças-na-estrutura-de-arquivos)
7. [Resumo das Mudanças no Código](#resumo-das-mudanças-no-código)
8. [Testes Pós-Migração](#testes-pós-migração)
9. [Procedimentos de Rollback](#procedimentos-de-rollback)
10. [Resolução de Problemas de Migração](#resolução-de-problemas-de-migração)

---

## Visão Geral

### O que Mudou?

A versão refatorada introduz:

- **Padrão de Injeção de Dependências** - Sem mais estado global
- **Arquitetura em Camadas** - Core → Hardware → Rede → Web
- **Variáveis de Ambiente** - Gerenciamento seguro de credenciais com `.env`
- **Logging Estruturado** - Substituiu `print()` por logging profissional
- **Abstração de Hardware** - LED e display com degradação graciosa
- **Tratamento de Erros** - Blocos try-catch em toda parte
- **Type Hints** - Melhor documentação do código
- **Separação de Responsabilidades** - Cada módulo tem responsabilidade única

### Por que Migrar?

**Antes (Original):**
```python
# Hardcoded credentials (INSECURE!)
WIFI_SSID = "my_network"
WIFI_PASSWORD = "password123"

# Global state (HARD TO TEST!)
import config
config.led.on()

# No error handling (CRASHES!)
display.show("Hello")
```

**Depois (Refatorado):**
```python
# Secure .env configuration
from dotenv_micro import get_env
WIFI_SSID = get_env('WIFI_SSID')

# Dependency injection (TESTABLE!)
class App:
    def __init__(self, led, display):
        self.led = led
        self.display = display

# Graceful degradation (RESILIENT!)
try:
    display.show("Hello")
except Exception as e:
    logger.error(f"Display failed: {e}")
    # App continues without display
```

### Tempo de Migração

- **Projeto pequeno** (< 500 linhas): 30-60 minutos
- **Projeto médio** (500-2000 linhas): 1-2 horas
- **Projeto grande** (> 2000 linhas): 2-4 horas

---

## Checklist Pré-Migração

### 1. Verificar Hardware

- [ ] ESP32-C3 is functional and accessible
- [ ] USB cable supports data transfer (not charge-only)
- [ ] Display is working (if present)
- [ ] LED is functional
- [ ] Serial port is accessible (Windows: COM3, Linux: /dev/ttyACM0)

### 2. Requisitos de Software

```bash
# Check Python version (3.7+ required)
python --version

# Create virtual environment
python -m venv venv

# Activate environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install esptool mpremote requests
```

### 3. Informações de Rede

Gather the following information:

- [ ] WiFi SSID (network name)
- [ ] WiFi Password
- [ ] Desired hostname for device
- [ ] Verify network is 2.4GHz (ESP32 requirement)

Example:
```
SSID: home_network_2.4ghz
Password: SecurePass123!
Hostname: dv01
Frequency: 2.4GHz ✓
```

### 4. Fazer Backup da Configuração Atual

Document your current setup:

```bash
# Windows
mpremote connect COM3 ls > backup_file_list.txt
mpremote connect COM3 cat boot.py > backup_boot.py
mpremote connect COM3 cat main.py > backup_main.py

# Linux/Mac
mpremote connect /dev/ttyACM0 ls > backup_file_list.txt
mpremote connect /dev/ttyACM0 cat boot.py > backup_boot.py
mpremote connect /dev/ttyACM0 cat main.py > backup_main.py
```

---

## Procedimentos de Backup

### Opção 1: Backup Completo do Sistema de Arquivos (Recomendado)

```bash
# Create backup directory
mkdir esp32_backup_$(date +%Y%m%d)
cd esp32_backup_$(date +%Y%m%d)

# Download all files
mpremote connect COM3 cat boot.py > boot.py
mpremote connect COM3 cat main.py > main.py
mpremote connect COM3 cat config.py > config.py

# List all files and backup each
mpremote connect COM3 ls

# For each file shown, download it:
mpremote connect COM3 cat filename.py > filename.py
```

### Opção 2: Backup via Repositório Git

If you have the original code in a git repository:

```bash
# Create backup branch
git checkout -b backup/pre-refactor-$(date +%Y%m%d)
git add .
git commit -m "Backup before refactor migration"
git push origin backup/pre-refactor-$(date +%Y%m%d)

# Return to main branch
git checkout main
```

### Opção 3: Backup Manual de Arquivos

1. Create folder: `esp32_backup/`
2. Copy all files from ESP32 to backup folder
3. Document the file structure:

```
esp32_backup/
├── boot.py
├── main.py
├── config.py
├── webrepl_cfg.py
└── lib/
    ├── microdot.py
    └── ssd1306.mpy
```

---

## Passos da Migração

### Passo 1: Gravar Firmware MicroPython Mais Recente

```bash
# Erase existing flash
esptool --port COM3 erase_flash

# Flash new firmware
esptool --port COM3 write_flash 0 firmware/ESP32_GENERIC_C3-20251209-v1.27.0.bin

# Wait for completion (~30 seconds)
# Reset ESP32 (press physical reset button or power cycle)
```

**Expected output:**
```
Chip is ESP32-C3 (revision v0.3)
Features: WiFi, BLE
Erasing flash (this may take a while)...
Chip erase completed successfully
Writing at 0x00000000... (100 %)
Wrote 1638400 bytes
Hash of data verified.
Leaving...
Hard resetting via RTS pin...
```

### Passo 2: Clonar Repositório Refatorado

```bash
# Clone the repository
git clone https://github.com/Holdrulff/computacao-fisica-esp32-c3.git
cd computacao-fisica-esp32-c3

# Or download ZIP and extract
# https://github.com/Holdrulff/computacao-fisica-esp32-c3/archive/refs/heads/main.zip
```

### Passo 3: Configurar Variáveis de Ambiente

Create `src/.env` with your credentials:

```bash
# Navigate to src directory
cd src

# Create .env file (Windows)
echo WIFI_SSID=your_network_name > .env
echo WIFI_PASSWORD=your_wifi_password >> .env
echo HOSTNAME=dv01 >> .env

# Create .env file (Linux/Mac)
cat > .env << EOF
WIFI_SSID=your_network_name
WIFI_PASSWORD=your_wifi_password
HOSTNAME=dv01
EOF
```

**Important:** Replace `your_network_name` and `your_wifi_password` with actual values.

**Example:**
```env
WIFI_SSID=home_network
WIFI_PASSWORD=SecurePass123!
HOSTNAME=dv01
```

### Passo 4: Criar Estrutura de Diretórios no ESP32

```bash
# Create all required directories
mpremote connect COM3 mkdir core
mpremote connect COM3 mkdir hardware
mpremote connect COM3 mkdir net_manager
mpremote connect COM3 mkdir web
mpremote connect COM3 mkdir lib

# Verify directories were created
mpremote connect COM3 ls
```

**Expected output:**
```
ls :
    core/
    hardware/
    net_manager/
    web/
    lib/
```

### Passo 5: Fazer Upload dos Módulos Core

```bash
# Upload __init__.py files (create empty packages)
mpremote connect COM3 cp src/core/__init__.py :core/__init__.py
mpremote connect COM3 cp src/hardware/__init__.py :hardware/__init__.py
mpremote connect COM3 cp src/net_manager/__init__.py :net_manager/__init__.py
mpremote connect COM3 cp src/web/__init__.py :web/__init__.py

# Upload core modules
mpremote connect COM3 cp src/core/app.py :core/app.py
mpremote connect COM3 cp src/core/logger.py :core/logger.py
```

### Passo 6: Fazer Upload dos Módulos de Hardware

```bash
mpremote connect COM3 cp src/hardware/led.py :hardware/led.py
mpremote connect COM3 cp src/hardware/display.py :hardware/display.py
```

### Passo 7: Fazer Upload dos Módulos de Rede

```bash
mpremote connect COM3 cp src/net_manager/wifi_manager.py :net_manager/wifi_manager.py
```

### Passo 8: Fazer Upload dos Módulos do Servidor Web

```bash
mpremote connect COM3 cp src/web/server.py :web/server.py
mpremote connect COM3 cp src/web/routes.py :web/routes.py
```

### Passo 9: Fazer Upload das Bibliotecas

```bash
mpremote connect COM3 cp src/lib/dotenv_micro.py :lib/dotenv_micro.py
mpremote connect COM3 cp src/lib/microdot.py :lib/microdot.py
mpremote connect COM3 cp src/lib/ssd1306.mpy :lib/ssd1306.mpy
mpremote connect COM3 cp src/lib/aiorepl.mpy :lib/aiorepl.mpy
```

### Passo 10: Fazer Upload dos Arquivos de Configuração

```bash
mpremote connect COM3 cp src/constants.py :constants.py
mpremote connect COM3 cp src/config.py :config.py
mpremote connect COM3 cp src/.env :.env
```

### Passo 11: Fazer Upload dos Pontos de Entrada

```bash
mpremote connect COM3 cp src/boot.py :boot.py
mpremote connect COM3 cp src/main.py :main.py
mpremote connect COM3 cp src/webrepl_cfg.py :webrepl_cfg.py
```

### Passo 12: Fazer Upload dos Arquivos Web Estáticos (Opcional)

If you have a web interface:

```bash
mpremote connect COM3 mkdir www
mpremote connect COM3 cp src/www/index.html :www/index.html
mpremote connect COM3 cp src/www/index.css :www/index.css

# If using WebREPL client
mpremote connect COM3 mkdir www/webrepl
mpremote connect COM3 cp src/www/webrepl/webrepl.html :www/webrepl/webrepl.html
# ... upload other WebREPL files
```

### Passo 13: Verificar Estrutura de Arquivos

```bash
# Check all files are present
mpremote connect COM3 ls
mpremote connect COM3 ls :core
mpremote connect COM3 ls :hardware
mpremote connect COM3 ls :net_manager
mpremote connect COM3 ls :web
mpremote connect COM3 ls :lib
```

**Expected structure:**
```
/
├── boot.py
├── main.py
├── config.py
├── constants.py
├── .env
├── webrepl_cfg.py
├── core/
│   ├── __init__.py
│   ├── app.py
│   └── logger.py
├── hardware/
│   ├── __init__.py
│   ├── led.py
│   └── display.py
├── net_manager/
│   ├── __init__.py
│   └── wifi_manager.py
├── web/
│   ├── __init__.py
│   ├── server.py
│   └── routes.py
└── lib/
    ├── dotenv_micro.py
    ├── microdot.py
    ├── ssd1306.mpy
    └── aiorepl.mpy
```

### Passo 14: Resetar e Testar

```bash
# Reset ESP32
mpremote connect COM3 exec "import machine; machine.reset()"

# Monitor boot sequence
mpremote connect COM3

# Watch for successful boot logs
```

**Expected output:**
```
[2.145] INFO  [App] === ESP32-C3 Application Starting ===
[2.234] INFO  [App] Initializing hardware...
[2.456] INFO  [LED] LED initialized on pin 8 (inverted=True)
[2.567] INFO  [Display] Display initialized successfully
[2.678] INFO  [App] Hardware initialization complete
[5.123] INFO  [WiFi] WiFi connected successfully
[5.234] INFO  [WiFi] IP Address: 192.168.1.100
[6.334] INFO  [App] Access web interface at: http://dv01.local:5000
```

---

## Migração de Configuração

### Configuração Antiga (config.py)

```python
# Old approach - Hardcoded credentials
WIFI_SSID = "my_network"
WIFI_PASSWORD = "password123"
HOSTNAME = "esp32"

# Global hardware instances
from machine import Pin
led = Pin(8, Pin.OUT)
```

### Nova Configuração (.env + config.py)

**src/.env** (gitignored):
```env
WIFI_SSID=my_network
WIFI_PASSWORD=password123
HOSTNAME=dv01
```

**src/config.py** (loads from .env):
```python
from dotenv_micro import load_dotenv, get_env

load_dotenv('.env')

WIFI_SSID = get_env('WIFI_SSID', 'default_network')
WIFI_PASSWORD = get_env('WIFI_PASSWORD', 'default_password')
HOSTNAME = get_env('HOSTNAME', 'esp32')
```

### Mapeamento de Migração

| Arquivo Antigo | Arquivo(s) Novo(s) | Mudanças |
|----------|-------------|---------|
| `config.py` | `config.py` + `.env` | Credentials moved to .env |
| `main.py` | `main.py` | Now uses Application class |
| `boot.py` | `boot.py` | Starts WebREPL, no logic change |
| `led_control.py` | `hardware/led.py` | Hardware abstraction added |
| `display_control.py` | `hardware/display.py` | Error handling added |
| `wifi_setup.py` | `net_manager/wifi_manager.py` | Retry logic + LED feedback |
| `web_server.py` | `web/server.py` + `web/routes.py` | Separated routes from server |
| N/A | `core/app.py` | New orchestrator class |
| N/A | `core/logger.py` | New logging system |
| N/A | `constants.py` | Centralized configuration |

---

## Mudanças na Estrutura de Arquivos

### Estrutura Antiga (Plana)

```
/
├── boot.py
├── main.py
├── config.py
├── led_control.py
├── display_control.py
├── wifi_setup.py
├── web_server.py
├── webrepl_cfg.py
└── lib/
    ├── microdot.py
    └── ssd1306.mpy
```

**Problemas:**
- Todos os arquivos no diretório raiz (desorganizado)
- Sem organização clara
- Difícil encontrar funcionalidades específicas
- Difícil de manter

### Nova Estrutura (Em Camadas)

```
/
├── boot.py                 # Entry: WebREPL start
├── main.py                 # Entry: Application start
├── config.py               # Configuration loader
├── constants.py            # System constants
├── .env                    # Credentials (gitignored)
├── webrepl_cfg.py          # WebREPL config
│
├── core/                   # Core application logic
│   ├── __init__.py
│   ├── app.py             # Application orchestrator
│   └── logger.py          # Structured logging
│
├── hardware/               # Hardware abstraction
│   ├── __init__.py
│   ├── led.py             # LED control
│   └── display.py         # Display control
│
├── net_manager/            # Network management
│   ├── __init__.py
│   └── wifi_manager.py    # WiFi connectivity
│
├── web/                    # Web server
│   ├── __init__.py
│   ├── server.py          # Microdot server
│   └── routes.py          # HTTP handlers
│
└── lib/                    # Third-party libraries
    ├── dotenv_micro.py    # Environment variables
    ├── microdot.py        # Web framework
    ├── ssd1306.mpy        # Display driver
    └── aiorepl.mpy        # Async REPL
```

**Benefícios:**
- Separação clara de responsabilidades
- Fácil de navegar
- Estrutura escalável
- Organização profissional

---

## Resumo das Mudanças no Código

### 1. Migração do Controle de LED

**Antes:**
```python
# main.py
from machine import Pin
led = Pin(8, Pin.OUT)

def led_on():
    led.on()  # Wrong for active-low hardware!

def led_off():
    led.off()  # Wrong for active-low hardware!
```

**After:**
```python
# hardware/led.py
class LED:
    def __init__(self, pin: int, inverted: bool = False):
        self._pin = Pin(pin, Pin.OUT)
        self._inverted = inverted

    def on(self):
        if self._inverted:
            self._pin.off()  # Active-low: LOW = ON
        else:
            self._pin.on()

# main.py
from hardware.led import LED
import constants

led = LED(constants.LED_PIN, inverted=constants.LED_INVERTED)
led.on()  # Works correctly regardless of hardware
```

### 2. Migração do Controle de Display

**Before:**
```python
# main.py
from machine import I2C, Pin
import ssd1306

i2c = I2C(0, scl=Pin(6), sda=Pin(5))
display = ssd1306.SSD1306_I2C(128, 64, i2c)

def show_message(text):
    display.fill(0)
    display.text(text, 0, 0, 1)
    display.show()  # Crashes if display not connected!
```

**After:**
```python
# hardware/display.py
class Display:
    def __init__(self, scl_pin: int, sda_pin: int, i2c_addr: int):
        self._available = False
        try:
            i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
            self._driver = ssd1306.SSD1306_I2C(128, 64, i2c)
            self._available = True
        except Exception as e:
            logger.error(f"Display init failed: {e}")
            # App continues without display!

    def show_message(self, text: str):
        if not self._available:
            return  # Graceful degradation

        try:
            self._driver.fill(0)
            self._driver.text(text, 0, 0, 1)
            self._driver.show()
        except Exception as e:
            logger.error(f"Display error: {e}")
```

### 3. Migração da Conexão WiFi

**Before:**
```python
# wifi_setup.py
import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

# No retry logic!
# No feedback!
# Blocks forever if fails!
```

**After:**
```python
# net_manager/wifi_manager.py
class WiFiManager:
    def connect(self, led=None) -> bool:
        self._wlan = network.WLAN(network.STA_IF)
        self._wlan.active(True)
        self._wlan.config(hostname=self.hostname)
        self._wlan.connect(self.ssid, self.password)

        attempts = 0
        while not self._wlan.isconnected():
            if attempts >= constants.WIFI_MAX_RETRIES:
                logger.error("WiFi connection failed")
                return False

            if led:
                led.on()  # Visual feedback

            time.sleep(constants.WIFI_CONNECT_RETRY_INTERVAL_SEC)
            attempts += 1

        if led:
            led.off()  # Success indicator

        logger.info("WiFi connected successfully")
        return True
```

### 4. Migração do Servidor Web

**Before:**
```python
# web_server.py
from microdot import Microdot
app = Microdot()

@app.route('/led/on')
def led_on(request):
    led.on()
    return {'led': 'on'}

# No dependency injection!
# Uses global 'led' variable!
```

**After:**
```python
# web/routes.py
class RouteHandlers:
    def __init__(self, led, display, wifi_manager, hostname):
        self.led = led  # Injected dependency
        self.display = display
        self.wifi_manager = wifi_manager
        self.hostname = hostname

    async def led_on(self, request):
        try:
            self.led.on()
            return {'led': 'on'}
        except Exception as e:
            logger.error(f"LED control error: {e}")
            return {'error': str(e)}, 500

# web/server.py
class WebServer:
    def __init__(self, led, display, wifi_manager, hostname):
        self.app = Microdot()
        self.handlers = RouteHandlers(led, display, wifi_manager, hostname)
        self._setup_routes()

    def _setup_routes(self):
        self.app.route('/led/on')(self.handlers.led_on)
```

### 5. Migração da Aplicação Principal

**Before:**
```python
# main.py
import config
from wifi_setup import connect_wifi
from web_server import app

# Initialize everything globally
connect_wifi()
led.off()

# Start server (blocks forever)
app.run(host='0.0.0.0', port=5000)
```

**After:**
```python
# main.py
from core.app import Application
import config

if __name__ == '__main__':
    app = Application(
        wifi_ssid=config.WIFI_SSID,
        wifi_password=config.WIFI_PASSWORD,
        hostname=config.HOSTNAME
    )
    app.start()  # Sets up and runs async event loop
```

---

## Testes Pós-Migração

### Teste 1: Sequência de Boot

```bash
mpremote connect COM3
```

**Verificar:**
- [ ] Sem erros de importação
- [ ] Hardware inicializa
- [ ] WiFi conecta
- [ ] Servidor web inicia
- [ ] Prompt REPL aparece

### Teste 2: Variáveis de Ambiente

```python
>>> from dotenv_micro import load_dotenv, get_env
>>> env = load_dotenv('.env')
>>> print(env)
{'WIFI_SSID': 'my_network', 'WIFI_PASSWORD': 'mypass', 'HOSTNAME': 'dv01'}
```

### Teste 3: Controle de LED

```python
>>> from hardware.led import LED
>>> import constants
>>> led = LED(constants.LED_PIN, inverted=constants.LED_INVERTED)
>>> led.on()  # LED should light up
>>> led.off()  # LED should turn off
```

### Teste 4: Controle de Display

```python
>>> from hardware.display import Display
>>> import constants
>>> display = Display(constants.DISPLAY_I2C_SCL_PIN, constants.DISPLAY_I2C_SDA_PIN, constants.DISPLAY_I2C_ADDR)
>>> display.show_message("Migration OK")
```

### Teste 5: Endpoints HTTP

```bash
# Test hello endpoint
curl http://dv01.local:5000/hello

# Test LED control
curl http://dv01.local:5000/led/on
curl http://dv01.local:5000/led/off

# Test message display
curl "http://dv01.local:5000/message?text=Test"
```

### Teste 6: Requisições Concorrentes

```bash
# Send multiple requests simultaneously
curl http://dv01.local:5000/hello & \
curl http://dv01.local:5000/health & \
curl http://dv01.local:5000/led & \
wait
```

### Teste 7: Tratamento de Erros

```python
# Disconnect display physically
# Device should continue working

>>> display.show_message("This should not crash")
# No crash, error logged gracefully
```

---

## Procedimentos de Rollback

### Opção 1: Rollback Rápido (Restaurar Backup)

```bash
# Navigate to backup directory
cd esp32_backup_YYYYMMDD

# Upload old files back
mpremote connect COM3 cp boot.py :boot.py
mpremote connect COM3 cp main.py :main.py
mpremote connect COM3 cp config.py :config.py
# ... upload all backed up files

# Reset ESP32
mpremote connect COM3 exec "import machine; machine.reset()"
```

### Opção 2: Rollback via Git

```bash
# Return to backup branch
git checkout backup/pre-refactor-YYYYMMDD

# Re-upload from backup branch
# Follow upload procedures with old code
```

### Opção 3: Gravação Fresh do Firmware

```bash
# Erase everything
esptool --port COM3 erase_flash

# Flash firmware
esptool --port COM3 write_flash 0 firmware/ESP32_GENERIC_C3-20251209-v1.27.0.bin

# Upload old code from backup
# ... manual upload
```

---

## Resolução de Problemas de Migração

### Problema: ImportError após migração

**Sintoma:**
```
ImportError: no module named 'core.app'
```

**Solution:**
```bash
# Verify directory structure
mpremote connect COM3 ls :core

# Check __init__.py exists
mpremote connect COM3 ls :core/__init__.py

# Re-upload if missing
mpremote connect COM3 cp src/core/__init__.py :core/__init__.py
mpremote connect COM3 cp src/core/app.py :core/app.py
```

### Problema: Arquivo .env não encontrado

**Sintoma:**
```
Warning: Could not load .env file
```

**Solution:**
```bash
# Check if .env exists
mpremote connect COM3 ls :.env

# Re-upload if missing
mpremote connect COM3 cp src/.env :.env

# Verify contents
mpremote connect COM3 cat .env
```

### Problema: WiFi não conecta após migração

**Sintoma:**
- LED continua piscando
- Timeout de conexão

**Solução:**
```bash
# Verify .env credentials
mpremote connect COM3 cat .env

# Test credentials manually
mpremote connect COM3
>>> import network
>>> wlan = network.WLAN(network.STA_IF)
>>> wlan.active(True)
>>> wlan.connect('your_ssid', 'your_password')
>>> import time; time.sleep(5)
>>> wlan.isconnected()
```

### Problema: Comportamento do LED invertido

**Sintoma:**
- `/led/on` apaga o LED
- `/led/off` acende o LED

**Solução:**
```bash
# Edit constants.py
# Change LED_INVERTED value

# Windows
notepad src\constants.py

# Change this line:
LED_INVERTED = True  # Try False instead

# Re-upload
mpremote connect COM3 cp src/constants.py :constants.py
mpremote connect COM3 exec "import machine; machine.reset()"
```

### Problema: Display não funciona após migração

**Sintoma:**
- Display permanece em branco
- "Display not available" nos logs

**Solução:**
```python
# Test I2C connection in REPL
>>> from machine import I2C, Pin
>>> i2c = I2C(0, scl=Pin(6), sda=Pin(5))
>>> devices = i2c.scan()
>>> print([hex(d) for d in devices])
['0x3c']  # Should see display address

# If address is different, update constants.py:
DISPLAY_I2C_ADDR = 0x3D  # Use address from scan
```

### Problema: Servidor web não inicia

**Sintoma:**
```
OSError: [Errno 98] Address already in use
```

**Solution:**
```python
# Check if another process is using port 5000
>>> import socket
>>> s = socket.socket()
>>> s.bind(('0.0.0.0', 5000))  # Will fail if port in use

# Reset ESP32 to clear port
import machine
machine.reset()
```

### Problema: Upload de arquivo falha no meio

**Sintoma:**
```
OSError: [Errno 28] No space left on device
```

**Solution:**
```bash
# Check free space
mpremote connect COM3 exec "import os; print(os.statvfs('/'))"

# Delete unnecessary files
mpremote connect COM3 rm :old_file.py

# Or erase and start fresh
esptool --port COM3 erase_flash
# Then re-flash firmware and re-upload
```

---

## Checklist de Migração

### Pré-Migração

- [ ] Hardware verified and functional
- [ ] Software requirements installed
- [ ] Network information gathered
- [ ] Current configuration backed up
- [ ] Git repository backed up (if applicable)

### Durante a Migração

- [ ] Firmware flashed successfully
- [ ] Directory structure created
- [ ] All modules uploaded
- [ ] Configuration files uploaded
- [ ] .env file created and uploaded
- [ ] File structure verified

### Pós-Migração

- [ ] ESP32 boots without errors
- [ ] Environment variables loaded
- [ ] Hardware initialized
- [ ] WiFi connected
- [ ] Web server started
- [ ] LED control tested
- [ ] Display tested
- [ ] HTTP endpoints tested
- [ ] Concurrent requests handled
- [ ] Error handling verified
- [ ] Documentation updated
- [ ] Rollback procedure documented

---

## Melhores Práticas

### 1. Testar Antes da Migração Completa

Test refactored code on a separate device or branch first:

```bash
# Clone to test directory
git clone https://github.com/Holdrulff/computacao-fisica-esp32-c3.git test-migration
cd test-migration

# Test upload and functionality
# ...

# If successful, proceed with production device
```

### 2. Migrar Durante Período de Baixo Uso

Schedule migration when device downtime is acceptable:

- **Development devices**: Anytime
- **Demo devices**: Outside class hours
- **Production devices**: Scheduled maintenance window

### 3. Documentar Mudanças Personalizadas

If you've customized the original code, document differences:

```bash
# Create custom_changes.md
echo "# Custom Changes" > custom_changes.md
echo "- Modified LED pin to GPIO 9" >> custom_changes.md
echo "- Added custom /status endpoint" >> custom_changes.md
echo "- Changed WiFi timeout to 60s" >> custom_changes.md
```

### 4. Controle de Versão

Tag successful migrations:

```bash
git tag -a v2.0-migrated -m "Successfully migrated to refactored architecture"
git push origin v2.0-migrated
```

### 5. Manter Backup Acessível

Maintain backup for at least 30 days after migration:

```bash
# Don't delete backup immediately!
# Keep for rollback if issues arise

# After 30 days of stable operation:
rm -rf esp32_backup_YYYYMMDD
```

---

## Critérios de Sucesso

A migração é bem-sucedida quando:

- [ ] Device boots reliably
- [ ] WiFi connects automatically
- [ ] All hardware functions correctly
- [ ] HTTP API responds as expected
- [ ] No errors in logs
- [ ] Performance is acceptable
- [ ] No regression in functionality
- [ ] Code is maintainable and testable
- [ ] Documentation is complete
- [ ] Team is trained on new structure

---

## Obtendo Ajuda

Se você encontrar problemas durante a migração:

1. **Verifique este guia** para passos de resolução de problemas
2. **Revise ARCHITECTURE.md** para detalhes de design
3. **Consulte TESTING_GUIDE.md** para procedimentos de verificação
4. **Busque issues no GitHub** por problemas similares
5. **Revise a documentação do MicroPython** para questões específicas da plataforma
6. **Pergunte em fóruns**: MicroPython Forum, ESP32 Forum, Stack Overflow

---

## Próximos Passos

Após migração bem-sucedida:

1. Revise [ARCHITECTURE.md](ARCHITECTURE.md) para entender os padrões de design
2. Leia [TESTING_GUIDE.md](TESTING_GUIDE.md) para procedimentos de teste
3. Explore [README.md](README.md) para documentação de uso
4. Verifique [micropython-dotenv/](micropython-dotenv/) para detalhes da biblioteca
5. Comece a desenvolver novos recursos com confiança!

---

**Versão do Documento:** 1.0
**Última Atualização:** Março 2026
**Compatível com:** MicroPython v1.27.0, ESP32-C3
