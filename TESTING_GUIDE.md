# Guia de Testes - Dispositivo IoT ESP32-C3

Guia completo para testar o projeto ESP32-C3 refatorado com configuração `.env`.

---

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Configuração](#configuração)
3. [Fluxo de Testes](#fluxo-de-testes)
4. [Testes de Componentes](#testes-de-componentes)
5. [Testes de Integração](#testes-de-integração)
6. [Testes da API HTTP](#testes-da-api-http)
7. [Resolução de Problemas](#resolução-de-problemas)
8. [Checklist de Verificação](#checklist-de-verificação)

---

## Pré-requisitos

### Requisitos de Hardware

- ESP32-C3 Supermini with integrated OLED display
- USB cable (data transfer capable)
- Computer with Python 3.x installed
- WiFi network (2.4GHz only - ESP32 doesn't support 5GHz)

### Requisitos de Software

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Required tools:**
- `esptool` - Firmware flashing
- `mpremote` - File management and REPL access
- `curl` or browser - HTTP testing

---

## Configuração

### Passo 1: Criar Arquivo .env

Create `src/.env` with your WiFi credentials:

```env
WIFI_SSID=your_network_name
WIFI_PASSWORD=your_wifi_password
HOSTNAME=dv01
```

**Important Notes:**
- Replace `your_network_name` with your actual WiFi SSID
- Replace `your_wifi_password` with your actual password
- SSID/password with spaces: `WIFI_SSID=My Network Name` (no quotes needed)
- Hostname must be alphanumeric (no spaces or special characters)
- This file is gitignored - never commit credentials!

**Example configurations:**

```env
# Home WiFi
WIFI_SSID=home_network_2.4ghz
WIFI_PASSWORD=SecurePass123!
HOSTNAME=dv01

# Office WiFi
WIFI_SSID=OfficeNet
WIFI_PASSWORD=CompanyPass2024
HOSTNAME=office-esp32

# Mobile Hotspot (2.4GHz only!)
WIFI_SSID=MyPhone
WIFI_PASSWORD=hotspot123
HOSTNAME=mobile-device
```

### Passo 2: Verificar Formato do .env

Common mistakes to avoid:

```env
# ❌ WRONG - Don't use quotes for simple values
WIFI_SSID="my_network"

# ✅ CORRECT - No quotes needed
WIFI_SSID=my_network

# ✅ ALSO CORRECT - Spaces work without quotes
WIFI_SSID=My Network Name

# ❌ WRONG - Don't use colons in hostname
HOSTNAME=dv01:5000

# ✅ CORRECT - Alphanumeric only
HOSTNAME=dv01
```

### Passo 3: Fazer Upload do .env para ESP32

```bash
# Connect to ESP32
mpremote connect COM3

# Upload .env file
mpremote connect COM3 cp src/.env :.env

# Verify upload
mpremote connect COM3 ls
```

**Expected output:**
```
ls :
    .env
    boot.py
    main.py
    config.py
    ...
```

---

## Fluxo de Testes

### Fase 1: Testes Pré-Upload

Before uploading to ESP32, verify files locally:

```bash
# Check Python syntax
python -m py_compile src/config.py
python -m py_compile src/main.py

# Verify .env exists
ls src/.env  # Linux/Mac
dir src\.env  # Windows
```

### Fase 2: Upload de Componentes

Upload all components systematically:

```bash
# 1. Create directory structure
mpremote connect COM3 mkdir core
mpremote connect COM3 mkdir hardware
mpremote connect COM3 mkdir net_manager
mpremote connect COM3 mkdir web
mpremote connect COM3 mkdir lib

# 2. Upload core modules
mpremote connect COM3 cp src/core/__init__.py :core/__init__.py
mpremote connect COM3 cp src/core/app.py :core/app.py
mpremote connect COM3 cp src/core/logger.py :core/logger.py

# 3. Upload hardware modules
mpremote connect COM3 cp src/hardware/__init__.py :hardware/__init__.py
mpremote connect COM3 cp src/hardware/led.py :hardware/led.py
mpremote connect COM3 cp src/hardware/display.py :hardware/display.py

# 4. Upload network modules
mpremote connect COM3 cp src/net_manager/__init__.py :net_manager/__init__.py
mpremote connect COM3 cp src/net_manager/wifi_manager.py :net_manager/wifi_manager.py

# 5. Upload web modules
mpremote connect COM3 cp src/web/__init__.py :web/__init__.py
mpremote connect COM3 cp src/web/server.py :web/server.py
mpremote connect COM3 cp src/web/routes.py :web/routes.py

# 6. Upload libraries
mpremote connect COM3 cp src/lib/dotenv_micro.py :lib/dotenv_micro.py
mpremote connect COM3 cp src/lib/microdot.py :lib/microdot.py
mpremote connect COM3 cp src/lib/ssd1306.mpy :lib/ssd1306.mpy
mpremote connect COM3 cp src/lib/aiorepl.mpy :lib/aiorepl.mpy

# 7. Upload configuration and entry points
mpremote connect COM3 cp src/constants.py :constants.py
mpremote connect COM3 cp src/config.py :config.py
mpremote connect COM3 cp src/.env :.env
mpremote connect COM3 cp src/boot.py :boot.py
mpremote connect COM3 cp src/main.py :main.py
mpremote connect COM3 cp src/webrepl_cfg.py :webrepl_cfg.py

# 8. Reset ESP32
mpremote connect COM3 exec "import machine; machine.reset()"
```

### Fase 3: Verificar Sequência de Boot

After reset, monitor serial output:

```bash
mpremote connect COM3
```

**Expected boot log:**

```
MicroPython v1.27.0 on ESP32-C3
>>>
[2.145] INFO  [App] === ESP32-C3 Application Starting ===
[2.234] INFO  [App] Initializing hardware...
[2.456] INFO  [LED] LED initialized on pin 8 (inverted=True)
[2.567] INFO  [Display] Display initialized successfully
[2.678] INFO  [App] Hardware initialization complete
[2.789] INFO  [App] Initializing network...
[2.890] INFO  [WiFi] Connecting to SSID: your_network_name
[3.001] INFO  [WiFi] Setting hostname: dv01
[5.123] INFO  [WiFi] WiFi connected successfully
[5.234] INFO  [WiFi] IP Address: 192.168.1.100
[5.345] INFO  [WiFi] Hostname: dv01.local
[5.456] INFO  [App] Network initialization complete
[5.567] INFO  [App] Initializing web server...
[5.678] INFO  [WebServer] Routes configured successfully
[5.789] INFO  [App] Web server initialization complete
[5.890] INFO  [App] === Application Setup Complete ===
[6.001] INFO  [App] Starting application tasks...
[6.112] INFO  [WebServer] Starting web server on port 5000
[6.223] INFO  [App] Web server and REPL started
[6.334] INFO  [App] Access web interface at: http://dv01.local:5000
[6.445] INFO  [App] Or access via IP: http://192.168.1.100:5000
```

**LED Indicators:**
- LED blinking: Attempting WiFi connection
- LED off: Successfully connected
- LED on: Connection failed or waiting for retry

**Display Status:**
```
dv01:5000
192.168.1.100
```

---

## Testes de Componentes

### Teste 1: Carregamento de Variáveis de Ambiente

Test `.env` parsing in REPL:

```python
# Enter REPL
mpremote connect COM3

# Test dotenv_micro
>>> from dotenv_micro import load_dotenv, get_env
>>> env = load_dotenv('.env')
>>> print(env)
{'WIFI_SSID': 'your_network', 'WIFI_PASSWORD': 'your_pass', 'HOSTNAME': 'dv01'}

>>> ssid = get_env('WIFI_SSID')
>>> print(ssid)
your_network

>>> hostname = get_env('HOSTNAME', 'default')
>>> print(hostname)
dv01

# Test with non-existent key
>>> test = get_env('NONEXISTENT', 'fallback_value')
>>> print(test)
fallback_value
```

**Expected behavior:**
- `.env` file is read successfully
- Variables are stored in `_environ` dictionary
- `get_env()` returns correct values
- Default values work when key doesn't exist

### Teste 2: Módulo de Configuração

Test config loader:

```python
>>> import config
>>> print(config.WIFI_SSID)
your_network

>>> print(config.WIFI_PASSWORD)
your_pass

>>> print(config.HOSTNAME)
dv01
```

**Expected behavior:**
- All config variables are loaded
- Values match `.env` file contents
- No errors on import

### Teste 3: Controle de LED

Test LED hardware abstraction:

```python
>>> from hardware.led import LED
>>> import constants

# Initialize LED
>>> led = LED(constants.LED_PIN, inverted=constants.LED_INVERTED)

# Test LED ON
>>> led.on()
# Physical LED should light up

# Check state
>>> led.is_on()
True

# Test LED OFF
>>> led.off()
# Physical LED should turn off

# Check state
>>> led.is_on()
False

# Test toggle
>>> led.toggle()
# LED should turn on

>>> led.toggle()
# LED should turn off
```

**Expected behavior:**
- `led.on()` → Physical LED lights up
- `led.off()` → Physical LED turns off
- `led.is_on()` → Returns correct state
- `led.toggle()` → Alternates state

**If LED behavior is inverted:**
- Verify `constants.LED_INVERTED = True`
- If still wrong, try `LED_INVERTED = False`

### Teste 4: Controle de Display

Test OLED display:

```python
>>> from hardware.display import Display
>>> import constants

# Initialize display
>>> display = Display(
...     constants.DISPLAY_I2C_SCL_PIN,
...     constants.DISPLAY_I2C_SDA_PIN,
...     constants.DISPLAY_I2C_ADDR
... )

# Check availability
>>> display.is_available
True

# Show message
>>> display.show_message("Hello World")
# Display should show "Hello World"

# Show status
>>> display.show_status("dv01", "192.168.1.100", 5000)
# Display should show hostname, IP, and port

# Clear display
>>> display.clear()
# Display should be blank
```

**Expected behavior:**
- Display initializes without errors
- Messages appear on physical OLED
- Text is readable and properly positioned
- Clear removes all content

**If display doesn't work:**

```python
# Check I2C connection
>>> from machine import I2C, Pin
>>> i2c = I2C(0, scl=Pin(6), sda=Pin(5))
>>> devices = i2c.scan()
>>> print([hex(d) for d in devices])
['0x3c']  # Expected: Display at address 0x3C
```

### Teste 5: Conexão WiFi

Test network connectivity:

```python
>>> from net_manager.wifi_manager import WiFiManager
>>> import config

# Initialize WiFi manager
>>> wifi = WiFiManager(
...     config.WIFI_SSID,
...     config.WIFI_PASSWORD,
...     config.HOSTNAME
... )

# Connect (without LED feedback)
>>> connected = wifi.connect()
>>> print(connected)
True

# Check connection status
>>> wifi.is_connected()
True

# Get IP address
>>> ip = wifi.get_ip_address()
>>> print(ip)
192.168.1.100

# Get network info
>>> info = wifi.get_network_info()
>>> print(info)
{'ssid': 'your_network', 'ip': '192.168.1.100', 'hostname': 'dv01'}
```

**Expected behavior:**
- Connection succeeds within timeout period
- IP address is assigned
- Hostname is set correctly
- Network info is accurate

---

## Testes de Integração

### Teste 6: Fluxo Completo da Aplicação

Test complete application startup:

```python
>>> from core.app import Application
>>> import config

# Create application instance
>>> app = Application(
...     wifi_ssid=config.WIFI_SSID,
...     wifi_password=config.WIFI_PASSWORD,
...     hostname=config.HOSTNAME
... )

# Run setup phase
>>> app.setup()
[Output shows initialization logs]

# Verify components are initialized
>>> app.led is not None
True

>>> app.display is not None
True

>>> app.wifi_manager is not None
True

>>> app.web_server is not None
True

# Check WiFi connection
>>> app.wifi_manager.is_connected()
True

# Test LED through app
>>> app.led.on()
>>> app.led.off()

# Test display through app
>>> app.display.show_message("Testing")
```

**Expected behavior:**
- All components initialize successfully
- WiFi connects automatically
- Display shows status
- LED provides visual feedback
- No errors in logs

### Teste 7: Rotas do Servidor Web

After application starts, test route registration:

```python
# Access the Microdot app instance
>>> routes = app.web_server.app.url_map
>>> for rule in routes:
...     print(rule)
/
/www/<path:path>
/hello
/health
/led
/led/on
/led/off
/led/toggle
/message
```

**Expected behavior:**
- All routes are registered
- No duplicate routes
- No missing routes

---

## Testes da API HTTP

### Método 1: Testes via Navegador

Open browser and navigate to:

```
http://dv01.local:5000
```

Or use IP address:

```
http://192.168.1.100:5000
```

**Test each endpoint:**

1. **Home page**: `http://dv01.local:5000/`
   - Should display index.html with device info

2. **Hello**: `http://dv01.local:5000/hello`
   - Expected: `{"message": "Hello from dv01.local", "status": "ok"}`

3. **Health**: `http://dv01.local:5000/health`
   - Expected: JSON with system status

4. **LED ON**: `http://dv01.local:5000/led/on`
   - Expected: `{"led": "on"}`
   - Physical LED should light up

5. **LED OFF**: `http://dv01.local:5000/led/off`
   - Expected: `{"led": "off"}`
   - Physical LED should turn off

6. **LED Status**: `http://dv01.local:5000/led`
   - Expected: `{"led": "on"}` or `{"led": "off"}`

7. **LED Toggle**: `http://dv01.local:5000/led/toggle`
   - Expected: LED state alternates
   - Response shows new state

8. **Set Message**: `http://dv01.local:5000/message?text=Hello`
   - Expected: `{"message": "Hello", "displayed": true}`
   - Display shows "Hello"

9. **Get Message**: `http://dv01.local:5000/message`
   - Expected: `{"message": "Hello"}`
   - Returns current message

### Método 2: Testes com curl

From command line:

```bash
# Replace with your device IP or hostname
export ESP_URL="http://dv01.local:5000"

# Test hello endpoint
curl $ESP_URL/hello
# Expected: {"message": "Hello from dv01.local", "status": "ok"}

# Test health check
curl $ESP_URL/health
# Expected: JSON with full system status

# Control LED
curl $ESP_URL/led/on
curl $ESP_URL/led/off
curl $ESP_URL/led/toggle

# Get LED status
curl $ESP_URL/led
# Expected: {"led": "on"} or {"led": "off"}

# Set message (GET with query parameter)
curl "$ESP_URL/message?text=Hello%20World"
# Expected: {"message": "Hello World", "displayed": true}

# Set message (POST with JSON body)
curl -X POST $ESP_URL/message \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from curl"}'
# Expected: {"message": "Hello from curl", "displayed": true}

# Get current message
curl $ESP_URL/message
# Expected: {"message": "Hello from curl"}
```

### Método 3: Testes com Python

Create test script `test_api.py`:

```python
import requests
import time

# Configuration
BASE_URL = "http://dv01.local:5000"

def test_hello():
    response = requests.get(f"{BASE_URL}/hello")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data
    print("✓ Hello endpoint working")

def test_health():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "hostname" in data
    assert "network" in data
    print("✓ Health endpoint working")

def test_led_control():
    # Turn on
    response = requests.get(f"{BASE_URL}/led/on")
    assert response.status_code == 200
    assert response.json()["led"] == "on"

    time.sleep(1)

    # Turn off
    response = requests.get(f"{BASE_URL}/led/off")
    assert response.status_code == 200
    assert response.json()["led"] == "off"

    print("✓ LED control working")

def test_message():
    # Set message
    response = requests.get(f"{BASE_URL}/message", params={"text": "Test"})
    assert response.status_code == 200
    assert response.json()["message"] == "Test"

    # Get message
    response = requests.get(f"{BASE_URL}/message")
    assert response.status_code == 200
    assert response.json()["message"] == "Test"

    print("✓ Message endpoints working")

if __name__ == "__main__":
    test_hello()
    test_health()
    test_led_control()
    test_message()
    print("\n✓ All tests passed!")
```

Run tests:

```bash
python test_api.py
```

---

## Resolução de Problemas

### Problema 1: Arquivo .env Não Encontrado

**Symptoms:**
- Config loads default values instead of .env values
- Errors like "Could not load .env file"

**Solutions:**

```bash
# Verify file exists on ESP32
mpremote connect COM3 ls

# Check file contents
mpremote connect COM3 cat .env

# Re-upload .env
mpremote connect COM3 cp src/.env :.env

# Verify format (no quotes, no extra spaces)
cat src/.env  # Linux/Mac
type src\.env  # Windows
```

### Problema 2: WiFi Não Conecta

**Symptoms:**
- LED keeps blinking indefinitely
- Connection timeout errors in log

**Solutions:**

1. **Verify credentials:**
   ```python
   >>> from dotenv_micro import load_dotenv, get_env
   >>> load_dotenv('.env')
   >>> print(get_env('WIFI_SSID'))
   >>> print(get_env('WIFI_PASSWORD'))
   # Make sure these match your network
   ```

2. **Check network compatibility:**
   - ESP32 only supports 2.4GHz WiFi
   - iPhone hotspot: Enable "Maximize Compatibility" in settings
   - Router: Ensure 2.4GHz band is enabled

3. **Scan for networks:**
   ```python
   >>> import network
   >>> wlan = network.WLAN(network.STA_IF)
   >>> wlan.active(True)
   >>> networks = wlan.scan()
   >>> for net in networks:
   ...     print(net[0].decode())  # Print SSID
   ```

4. **Manual connection test:**
   ```python
   >>> import network
   >>> wlan = network.WLAN(network.STA_IF)
   >>> wlan.active(True)
   >>> wlan.connect('your_ssid', 'your_password')
   >>> import time
   >>> time.sleep(5)
   >>> wlan.isconnected()
   True
   >>> wlan.ifconfig()
   ('192.168.1.100', '255.255.255.0', '192.168.1.1', '192.168.1.1')
   ```

### Problema 3: Comportamento do LED Invertido

**Symptoms:**
- `/led/on` turns LED off
- `/led/off` turns LED on

**Solution:**

Edit `src/constants.py`:

```python
# Change this line:
LED_INVERTED = True  # Try False

# Or:
LED_INVERTED = False  # Try True
```

Upload updated file:

```bash
mpremote connect COM3 cp src/constants.py :constants.py
mpremote connect COM3 exec "import machine; machine.reset()"
```

### Problema 4: Display Não Funciona

**Symptoms:**
- Display remains blank
- "Display not available" in logs

**Solutions:**

1. **Check I2C connection:**
   ```python
   >>> from machine import I2C, Pin
   >>> i2c = I2C(0, scl=Pin(6), sda=Pin(5))
   >>> devices = i2c.scan()
   >>> print([hex(d) for d in devices])
   ['0x3c']  # Should see 0x3c
   ```

2. **Verify I2C address:**
   ```python
   # If scan shows different address, update constants.py:
   DISPLAY_I2C_ADDR = 0x3D  # Or whatever scan returned
   ```

3. **Test display driver:**
   ```python
   >>> from machine import I2C, Pin
   >>> import ssd1306
   >>> i2c = I2C(0, scl=Pin(6), sda=Pin(5))
   >>> display = ssd1306.SSD1306_I2C(128, 64, i2c)
   >>> display.fill(0)
   >>> display.text("Test", 0, 0, 1)
   >>> display.show()
   ```

4. **Check physical connections:**
   - SCL → GPIO 6
   - SDA → GPIO 5
   - VCC → 3.3V
   - GND → GND

### Problema 5: Rotas Retornam 404

**Symptoms:**
- HTTP requests return "Not Found"
- Routes worked before but stopped

**Solutions:**

1. **Verify server is running:**
   ```python
   # In REPL (Ctrl+C to interrupt if needed)
   >>> # Check if you see "Web server and REPL started" in boot log
   ```

2. **Check route registration:**
   ```python
   >>> from core.app import Application
   >>> import config
   >>> app = Application(config.WIFI_SSID, config.WIFI_PASSWORD, config.HOSTNAME)
   >>> app.setup()
   >>> routes = app.web_server.app.url_map
   >>> for rule in routes:
   ...     print(rule)
   ```

3. **Verify port and hostname:**
   ```bash
   # Try IP address instead of hostname
   curl http://192.168.1.100:5000/hello

   # Try localhost if testing locally
   curl http://localhost:5000/hello
   ```

4. **Check firewall:**
   - Port 5000 must be open
   - Some antivirus software blocks local servers

### Problema 6: Erros de Importação

**Symptoms:**
- "ImportError: no module named 'X'"
- Module not found errors

**Solutions:**

1. **Check file structure:**
   ```bash
   mpremote connect COM3 ls
   mpremote connect COM3 ls :core
   mpremote connect COM3 ls :hardware
   mpremote connect COM3 ls :net_manager
   mpremote connect COM3 ls :web
   mpremote connect COM3 ls :lib
   ```

2. **Verify __init__.py files:**
   ```bash
   mpremote connect COM3 ls :core/__init__.py
   mpremote connect COM3 ls :hardware/__init__.py
   mpremote connect COM3 ls :net_manager/__init__.py
   mpremote connect COM3 ls :web/__init__.py
   ```

3. **Re-upload missing modules:**
   ```bash
   # Example: re-upload core module
   mpremote connect COM3 cp src/core/app.py :core/app.py
   ```

4. **Check sys.path:**
   ```python
   >>> import sys
   >>> print(sys.path)
   ['', '/', '.frozen', '/lib']
   ```

---

## Checklist de Verificação

### Checklist Pré-Upload

- [ ] `.env` file created with correct WiFi credentials
- [ ] `.env` format verified (no unnecessary quotes)
- [ ] Hostname is alphanumeric (no special characters)
- [ ] WiFi network is 2.4GHz (ESP32 doesn't support 5GHz)
- [ ] All source files have correct syntax
- [ ] Virtual environment activated
- [ ] Required tools installed (esptool, mpremote)

### Checklist de Upload

- [ ] Firmware flashed successfully (ESP32_GENERIC_C3-20251209-v1.27.0.bin)
- [ ] All directories created (core, hardware, net_manager, web, lib)
- [ ] All Python modules uploaded
- [ ] All libraries uploaded (dotenv_micro, microdot, ssd1306, aiorepl)
- [ ] Configuration files uploaded (constants, config, .env)
- [ ] Entry points uploaded (boot.py, main.py, webrepl_cfg.py)
- [ ] ESP32 reset after upload

### Checklist de Boot

- [ ] Serial monitor shows boot log without errors
- [ ] Hardware initialization completes
- [ ] WiFi connection succeeds
- [ ] IP address assigned
- [ ] Hostname set correctly
- [ ] Web server starts on port 5000
- [ ] REPL prompt appears
- [ ] LED turns off after successful connection
- [ ] Display shows hostname and IP

### Checklist de Funcionalidade

- [ ] LED control works (`/led/on`, `/led/off`, `/led/toggle`)
- [ ] LED state is correct (not inverted)
- [ ] Display shows messages (`/message?text=Test`)
- [ ] Display updates correctly
- [ ] Hello endpoint returns JSON (`/hello`)
- [ ] Health endpoint returns system status (`/health`)
- [ ] Static files serve correctly (`/`)
- [ ] Browser can access all endpoints
- [ ] curl commands work
- [ ] Multiple concurrent requests handled

### Checklist de Segurança

- [ ] `.env` file is gitignored
- [ ] No credentials in code or committed files
- [ ] WebREPL password changed from default (if using WebREPL)
- [ ] WiFi network uses WPA2/WPA3 encryption
- [ ] Device not exposed to public internet

### Checklist de Documentação

- [ ] README.md reviewed and understood
- [ ] ARCHITECTURE.md read for design patterns
- [ ] TESTING_GUIDE.md followed (this document)
- [ ] MIGRATION_GUIDE.md available for updates
- [ ] micropython-dotenv documentation accessible

---

## Testes Avançados

### Teste de Carga (Load Testing)

Test concurrent request handling:

```python
import requests
import concurrent.futures
import time

BASE_URL = "http://dv01.local:5000"

def make_request(i):
    start = time.time()
    response = requests.get(f"{BASE_URL}/hello")
    elapsed = time.time() - start
    return i, response.status_code, elapsed

# Send 10 concurrent requests
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(make_request, i) for i in range(10)]
    results = [f.result() for f in concurrent.futures.as_completed(futures)]

for i, status, elapsed in sorted(results):
    print(f"Request {i}: Status {status}, Time {elapsed:.2f}s")
```

### Monitoramento de Memória

Check memory usage:

```python
>>> import gc
>>> gc.collect()
>>> gc.mem_free()
180000  # Free memory in bytes

>>> gc.mem_alloc()
45000  # Allocated memory in bytes
```

### Profiling de Performance

Profile endpoint response times:

```python
import requests
import time
import statistics

BASE_URL = "http://dv01.local:5000"
ITERATIONS = 20

def profile_endpoint(endpoint):
    times = []
    for _ in range(ITERATIONS):
        start = time.time()
        requests.get(f"{BASE_URL}{endpoint}")
        elapsed = time.time() - start
        times.append(elapsed)

    return {
        'endpoint': endpoint,
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'min': min(times),
        'max': max(times)
    }

endpoints = ['/hello', '/health', '/led', '/message']
for endpoint in endpoints:
    stats = profile_endpoint(endpoint)
    print(f"\n{stats['endpoint']}:")
    print(f"  Mean: {stats['mean']:.3f}s")
    print(f"  Median: {stats['median']:.3f}s")
    print(f"  Min: {stats['min']:.3f}s")
    print(f"  Max: {stats['max']:.3f}s")
```

---

## Melhores Práticas de Teste

### 1. Test in Isolation

Test each component independently before integration:

```python
# Test LED alone
from hardware.led import LED
led = LED(8, inverted=True)
led.on()
# Verify physically before proceeding

# Test display alone
from hardware.display import Display
display = Display(6, 5, 0x3C)
display.show_message("Test")
# Verify physically before proceeding
```

### 2. Test with Known Good Configuration

Keep a backup of working `.env`:

```bash
# Save working configuration
cp src/.env src/.env.backup

# Test with new config
# ...

# Restore if needed
cp src/.env.backup src/.env
```

### 3. Monitor Serial Output

Always monitor REPL during testing:

```bash
# Open serial monitor
mpremote connect COM3

# In another terminal, test API
curl http://dv01.local:5000/hello

# Watch for errors in serial output
```

### 4. Test Error Handling

Deliberately cause errors to verify graceful degradation:

```python
# Test with wrong credentials
# Edit .env with invalid password
# Device should log errors but not crash

# Test without display connected
# Application should continue working

# Test with network disconnection
# Unplug router during operation
# Device should handle gracefully
```

### 5. Document Test Results

Keep a test log:

```
Test Date: 2026-03-06
Firmware: ESP32_GENERIC_C3-20251209-v1.27.0
Configuration: Home WiFi (2.4GHz)

Results:
✓ Boot successful (6.5s)
✓ WiFi connected (4.2s)
✓ LED control working
✓ Display working
✓ All API endpoints responding
✓ Concurrent requests handled (10/10)

Issues:
- None

Notes:
- LED_INVERTED=True confirmed correct
- Display address 0x3C verified
- Average response time: 45ms
```

---

## Testes Contínuos

### Verificações Diárias

- [ ] Device boots successfully
- [ ] WiFi connects automatically
- [ ] Web interface accessible
- [ ] LED and display responsive

### Verificações Semanais

- [ ] All API endpoints tested
- [ ] Memory usage checked
- [ ] Log files reviewed
- [ ] Firmware version verified

### Após Mudanças

- [ ] Full test suite run
- [ ] Integration tests passed
- [ ] Documentation updated
- [ ] Test results logged

---

## Obtendo Ajuda

Se você encontrar problemas não cobertos neste guia:

1. Verifique a saída do REPL para mensagens de erro
2. Revise ARCHITECTURE.md para detalhes de design
3. Consulte MIGRATION_GUIDE.md para procedimentos de atualização
4. Busque em issues do GitHub
5. Revise a documentação do micropython-dotenv

---

**Versão do Documento:** 1.0
**Última Atualização:** Março 2026
**Compatível com:** MicroPython v1.27.0, ESP32-C3
