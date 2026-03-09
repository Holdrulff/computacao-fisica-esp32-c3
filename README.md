# ESP32-C3 IoT Device

![MicroPython](https://img.shields.io/badge/MicroPython-v1.27.0-blue)
![ESP32-C3](https://img.shields.io/badge/ESP32--C3-Supermini-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

Dispositivo IoT baseado em ESP32-C3 com display OLED integrado, servidor web assíncrono e API REST completa.

![ESP32-C3 Device](./mdImageAssets/4929270778520341423.jpg)

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#️-arquitetura)
- [Hardware](#-hardware)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [API Endpoints](#-api-endpoints)
- [Desenvolvimento](#-desenvolvimento)
- [Troubleshooting](#️-troubleshooting)
- [Licença](#-licença)

## ✨ Funcionalidades

- ✅ **Servidor Web Assíncrono** - Interface web responsiva na porta 5000
- ✅ **API REST** - Controle via HTTP com respostas JSON
- ✅ **Controle de LED** - Ligar/desligar/toggle/piscar com parâmetros
- ✅ **Código Morse** - Transmissão via LED com display progressivo
- ✅ **Display OLED** - Mensagens customizáveis (72x40px)
- ✅ **Monitoramento** - Informações de sistema, rede e armazenamento
- ✅ **Jogos** - Snake e Tic-Tac-Toe via web
- ✅ **Configuração Segura** - Credenciais via .env (não no código)
- ✅ **Multi-cliente** - Suporte a múltiplos acessos simultâneos

## 🏗️ Arquitetura

### Padrões de Design

- **Dependency Injection** - Componentes desacoplados e testáveis
- **Separation of Concerns** - Camadas bem definidas (hardware, rede, web)
- **SOLID Principles** - Single responsibility, Open-closed, Dependency inversion
- **Error Handling** - Try-catch abrangente com graceful degradation
- **Structured Logging** - Sistema de logs com níveis e timestamps
- **Configuration Management** - Variáveis de ambiente (.env)

### Estrutura do Projeto

```
src/
├── boot.py                 # MicroPython boot script
├── main.py                 # Application entry point
├── config.py               # Configuration loader (.env)
├── constants.py            # System constants
├── .env                    # Credentials (gitignored)
│
├── core/                   # Core application logic
│   ├── app.py             # Main Application orchestrator
│   └── logger.py          # Structured logging
│
├── hardware/               # Hardware abstraction layer
│   ├── led.py             # LED control (supports active-low)
│   ├── display.py         # OLED display (SSD1306)
│   └── morse.py           # Morse code encoder
│
├── net_manager/            # Network management
│   └── wifi_manager.py    # WiFi with retry logic
│
├── web/                    # Web server
│   ├── server.py          # Microdot server setup
│   └── routes.py          # HTTP route handlers
│
├── games/                  # Game logic
│   ├── snake_leaderboard.py
│   └── tictactoe.py
│
├── lib/                    # Third-party libraries
│   ├── dotenv_micro.py    # micropython-dotenv
│   ├── microdot.py        # Async web framework
│   ├── ssd1306.mpy        # Display driver
│   └── aiorepl.mpy        # Async REPL
│
└── www/                    # Static web assets
    ├── index.html
    ├── index.css
    ├── snake.html
    ├── tictactoe.html
    └── morse.html
```

## 🔧 Hardware

### Especificações

- **Microcontrolador**: ESP32-C3 Supermini
- **Display**: OLED 0.42" SSD1306 (72x40px, I2C)
  - SCL: GPIO 6
  - SDA: GPIO 5
  - Endereço: 0x3C
- **LED**: GPIO 8 (active-low)
- **WiFi**: 2.4GHz apenas (802.11 b/g/n)

### Pinagem

| Componente | Pino | Observações |
|------------|------|-------------|
| LED integrado | GPIO 8 | Active-low (invertido) |
| Display SCL | GPIO 6 | I2C Clock |
| Display SDA | GPIO 5 | I2C Data |

## 📦 Instalação

### Pré-requisitos

- Python 3.7+
- ESP32-C3 Supermini com display OLED
- Cabo USB para dados

### Passo 1: Clone e Configure o Ambiente

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/computacao-fisica-esp32-c3.git
cd computacao-fisica-esp32-c3

# Crie ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

### Passo 2: Flash do Firmware MicroPython

```bash
# Windows
esptool --port COM3 erase_flash
esptool --port COM3 write_flash 0 firmware/ESP32_GENERIC_C3-20251209-v1.27.0.bin

# Linux/Mac
esptool.py --port /dev/ttyUSB0 erase_flash
esptool.py --port /dev/ttyUSB0 write_flash 0 firmware/ESP32_GENERIC_C3-20251209-v1.27.0.bin
```

### Passo 3: Configure Credenciais WiFi

Crie o arquivo `src/.env`:

```env
WIFI_SSID=sua_rede_wifi
WIFI_PASSWORD=sua_senha
HOSTNAME=dv01
```

### Passo 4: Deploy do Código

```bash
# Windows
deploy.bat COM3

# Linux/Mac
./deploy.sh /dev/ttyUSB0

# Ou com Python (auto-detecta porta)
python deploy.py
```

## 🚀 Uso

### Acesso via Web

1. Conecte o ESP32 via USB
2. Aguarde o LED parar de piscar (conectado ao WiFi)
3. O display mostrará o IP e hostname
4. Acesse no navegador:
   - `http://dv01.local:5000` (via mDNS)
   - `http://192.168.x.x:5000` (via IP mostrado no display)

### Acesso via REPL Serial

Para desenvolvimento e debugging, use o REPL via serial:

```bash
# Conectar ao REPL
mpremote connect COM3

# No REPL, você pode:
>>> import machine
>>> machine.freq()
160000000

>>> import os
>>> os.listdir()
['.env', 'boot.py', 'main.py', 'core', 'hardware', ...]

>>> from hardware.led import LED
>>> led = LED(8, inverted=True)
>>> led.toggle()

# Ctrl+] para sair
```

### Comandos Úteis

```bash
# Resetar o dispositivo
mpremote connect COM3 exec "import machine; machine.reset()"

# Listar arquivos
mpremote connect COM3 fs ls

# Ver conteúdo de arquivo
mpremote connect COM3 fs cat boot.py

# Copiar arquivo individual
mpremote connect COM3 fs cp src/config.py :config.py
```

## 📡 API Endpoints

### Status & Health

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/hello` | GET | Ping simples |
| `/health` | GET | Status do sistema (rede, hardware) |
| `/storage` | GET | Informações de armazenamento |

**Exemplo `/health`:**
```bash
curl http://dv01.local:5000/health
```
```json
{
  "status": "healthy",
  "hostname": "dv01",
  "network": {
    "connected": true,
    "ssid": "sua_rede",
    "ip": "192.168.1.100"
  },
  "hardware": {
    "led": {"available": true, "state": "off"}
  }
}
```

### Controle de LED

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/led` | GET | Status atual |
| `/led/on` | GET | Liga o LED |
| `/led/off` | GET | Desliga o LED |
| `/led/toggle` | GET | Alterna estado |
| `/led/blink?count=5&interval=0.3` | GET | Pisca N vezes |

**Exemplo:**
```bash
# Piscar 5 vezes com intervalo de 0.3s
curl "http://dv01.local:5000/led/blink?count=5&interval=0.3"
```

### Código Morse

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/morse?text=SOS&speed=0.2` | GET/POST | Transmite texto em Morse via LED |

**Exemplo:**
```bash
curl "http://dv01.local:5000/morse?text=HELP"
```
```json
{
  "text": "HELP",
  "morse": ".... . .-.. .--.",
  "duration": 8.5,
  "led": "off"
}
```

**Suportado**: A-Z, 0-9, pontuação (`.`, `,`, `?`, `!`, `-`)

### Jogos

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/snake/leaderboard` | GET | Placar do Snake |
| `/snake/score` | POST | Adicionar pontuação |
| `/game/tictactoe` | GET | Estado do jogo |
| `/game/tictactoe/move` | POST | Fazer jogada |
| `/game/tictactoe/reset` | POST | Reiniciar jogo |

## 👨‍💻 Desenvolvimento

### Estrutura de Logs

```python
from core.logger import get_logger

logger = get_logger('ModuleName')
logger.info("Informação")
logger.warning("Aviso")
logger.error("Erro")
```

**Output:**
```
[123.456] INFO  [WiFi] Connected successfully
[124.789] ERROR [Display] Failed to initialize
```

### Dependency Injection Pattern

```python
# hardware/led.py
class LED:
    def __init__(self, pin, inverted=False):
        self.pin = Pin(pin, Pin.OUT)
        self.inverted = inverted

# core/app.py
class Application:
    def __init__(self, led, display, wifi_manager):
        self.led = led  # Injected dependency
        self.display = display
        self.wifi = wifi_manager
```

### Adicionar Novo Endpoint

```python
# web/routes.py
class RouteHandlers:
    async def my_new_endpoint(self, request):
        return {'message': 'Hello!', 'status': 'ok'}

# web/server.py
def _setup_routes(self):
    self.app.route('/my-endpoint')(self.handlers.my_new_endpoint)
```

## 🛠️ Troubleshooting

### LED funciona invertido

**Sintoma**: `/led/on` apaga o LED.

**Solução**: LED é active-low. Verifique `src/constants.py`:
```python
LED_INVERTED = True  # ✅ Já configurado
```

### Display não funciona

**Diagnóstico**:
```python
# No REPL (mpremote connect COM3)
from machine import I2C, Pin
i2c = I2C(0, scl=Pin(6), sda=Pin(5))
i2c.scan()  # Deve retornar [60] (0x3C)
```

**Solução**: Verifique conexões físicas (SCL=6, SDA=5).

### WiFi não conecta

**Sintomas**: LED piscando indefinidamente.

**Checklist**:
- ✅ Rede é 2.4GHz (ESP32-C3 não suporta 5GHz)
- ✅ Credenciais corretas no `src/.env`
- ✅ SSID visível e alcançável
- ✅ Senha sem caracteres especiais problemáticos

**Debug**:
```python
# No REPL
import network
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.scan()  # Lista redes disponíveis
```

### Porta serial não detectada (Linux)

```bash
# Adicionar usuário ao grupo dialout
sudo usermod -a -G dialout $USER
# Fazer logout e login novamente
```

### Deploy falha com "Device busy"

1. Feche Thonny ou outros programas usando a porta serial
2. Desconecte e reconecte o cabo USB
3. Pressione o botão RESET no ESP32

## 📄 Licença

Este projeto é open-source e está disponível sob a [Licença MIT](LICENSE).

## 👨‍💻 Autor

- **Wesley Fernandes** - [@Holdrulff](https://github.com/Holdrulff)
- **Instituição**: EACH-USP
- **Curso**: Sistemas de Informação
- **Disciplina**: Computação Física Aplicada (CFA)

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma feature branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Add: nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

**📌 Versão**: 3.0.0
**📅 Última atualização**: Março 2026
**⭐ Star este repositório se foi útil!**
