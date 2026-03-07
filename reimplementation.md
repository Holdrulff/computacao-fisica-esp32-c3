# Plano de Reimplementação Completo - ESP32-C3 WebServer

## Context

O projeto sofreu perda de arquivos e reversão para versões antigas. Este plano documenta **TODAS** as funcionalidades implementadas que precisam ser restauradas:

### O que foi perdido:

1. **Correção do WebREPL** - WebREPL condicional para evitar travamento do HTTP server
2. **Display 128x64 configuração** - Configuração correta para display landscape
3. **Homepage Neobrutalism** - Interface moderna mobile-first com design neobrutalism
4. **Páginas HTML interativas**:
   - `snake.html` - Jogo da cobrinha 30x30 com leaderboard
   - `led.html` - Interface de controle do LED
   - `message.html` - Interface para enviar mensagens ao display
   - `morse.html` - Interface de código Morse interativa
   - `tictactoe.html` - Jogo da velha vs IA (confirmar se existia)
5. **Backend Snake Game**:
   - `src/games/snake_leaderboard.py` - Sistema de leaderboard com idempotência
6. **Correções de bugs**:
   - High score Snake sincronizado com servidor
   - Mensagens rápidas no message.html

---

## Arquivos Críticos a Restaurar

### 1. Arquivos de Configuração

#### `src/constants.py`
**Estado atual**: Faltam flags de performance/debug e configuração do display

**Código a adicionar**:
```python
"""
Application constants and configuration values.
"""

# Performance / Debug
DEBUG = False  # Enable development features (IDE interrupt delay, verbose logging)
ENABLE_AIOREPL = False  # Enable async REPL (can be disabled for faster boot)
ENABLE_WEBREPL = False  # Enable WebREPL (conflicts with HTTP server event loop)

# Hardware pins
LED_PIN = 8
LED_INVERTED = True  # True for active-low LEDs (common in ESP32 boards)
DISPLAY_I2C_SCL_PIN = 6
DISPLAY_I2C_SDA_PIN = 5
DISPLAY_I2C_ADDR = 0x3C
DISPLAY_WIDTH = 128   # Landscape mode (standard)
DISPLAY_HEIGHT = 64

# Network
WIFI_CONNECT_TIMEOUT_SEC = 40
WIFI_CONNECT_RETRY_INTERVAL_SEC = 2
WIFI_MAX_RETRIES = 20

# Web server
HTTP_PORT = 5000
HTTP_HOST = '0.0.0.0'

# Display (landscape mode: 128x64)
DISPLAY_CHARS_PER_LINE = 21   # ~128px / 6px per char
DISPLAY_LINE_HEIGHT = 10      # Extra spacing between lines
DISPLAY_START_Y = 0           # Start from top
```

#### `src/boot.py`
**Estado atual**: WebREPL ativo sem condicional (causa travamento)

**Código correto**:
```python
# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

# WebREPL (disabled by default - conflicts with HTTP server asyncio loop)
# To enable: set ENABLE_WEBREPL = True in constants.py
import constants
if constants.ENABLE_WEBREPL:
    import webrepl
    webrepl.start()
    print("WebREPL started on port 8266")

# Note: User code should not be placed in boot.py
# See: https://docs.micropython.org/en/latest/reference/reset_boot.html#id4
# Use main.py for application startup instead
```

---

### 2. Backend - Snake Leaderboard

#### `src/games/snake_leaderboard.py` (CRIAR)
Sistema de leaderboard com top 10, persistência JSON e idempotência.

```python
"""
Snake game leaderboard management with JSON persistence.
"""
import json
from core.logger import get_logger

logger = get_logger('SnakeLeaderboard')

LEADERBOARD_FILE = 'snake_scores.json'
MAX_ENTRIES = 10

def load_leaderboard():
    """Load leaderboard from JSON file."""
    try:
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    except:
        logger.info("Creating new leaderboard file")
        return []

def save_leaderboard(leaderboard):
    """Save leaderboard to JSON file."""
    try:
        with open(LEADERBOARD_FILE, 'w') as f:
            json.dump(leaderboard, f)
        logger.info(f"Leaderboard saved ({len(leaderboard)} entries)")
    except Exception as e:
        logger.error(f"Failed to save leaderboard: {e}")

def get_leaderboard():
    """Get current leaderboard."""
    leaderboard = load_leaderboard()
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    return {
        'success': True,
        'leaderboard': leaderboard[:MAX_ENTRIES]
    }

def add_score(name, score):
    """
    Add score to leaderboard with idempotency check.

    Args:
        name: Player name (max 20 chars)
        score: Score value

    Returns:
        dict with success, rank, and updated leaderboard
    """
    leaderboard = load_leaderboard()
    normalized_name = name[:20].strip()

    # Check if this exact entry already exists (idempotency)
    if any(entry['name'] == normalized_name and entry['score'] == score
           for entry in leaderboard):
        logger.info(f"Score already exists: {normalized_name} - {score} (idempotent)")
        # Find rank without adding duplicate
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        rank = next((i+1 for i, e in enumerate(leaderboard)
                     if e['name'] == normalized_name and e['score'] == score), None)
        return {
            'success': True,
            'rank': rank,
            'leaderboard': leaderboard[:MAX_ENTRIES],
            'duplicate': True
        }

    # Add new entry
    new_entry = {'name': normalized_name, 'score': score}
    leaderboard.append(new_entry)
    leaderboard.sort(key=lambda x: x['score'], reverse=True)
    leaderboard = leaderboard[:MAX_ENTRIES]

    # Find rank
    rank = next((i+1 for i, e in enumerate(leaderboard)
                 if e['name'] == normalized_name and e['score'] == score), None)

    save_leaderboard(leaderboard)
    logger.info(f"New score added: {normalized_name} - {score} (rank #{rank})")

    return {
        'success': True,
        'rank': rank,
        'leaderboard': leaderboard,
        'duplicate': False
    }
```

**Integração em `src/web/routes.py`**:
```python
# Adicionar estes métodos na classe RouteHandlers:

async def snake_leaderboard(self, request):
    """Get Snake game leaderboard."""
    from games.snake_leaderboard import get_leaderboard
    data = get_leaderboard()
    return data

async def snake_add_score(self, request):
    """Add score to Snake leaderboard."""
    from games.snake_leaderboard import add_score

    try:
        data = request.json
        name = data.get('name', 'Anonymous')
        score = int(data.get('score', 0))

        if score < 0:
            return {'error': 'Invalid score'}, 400

        result = add_score(name, score)
        return result

    except Exception as e:
        logger.error(f"Error adding score: {e}")
        return {'error': 'Failed to add score'}, 500
```

**Integração em `src/web/server.py`**:
```python
# Adicionar no método _setup_routes():

# Snake game leaderboard
self.app.get('/snake/leaderboard')(self.handlers.snake_leaderboard)
self.app.post('/snake/score')(self.handlers.snake_add_score)
```

---

### 3. Frontend - Homepage Neobrutalism

#### `src/www/index.html`
**Design**: Mobile-first, neobrutalism, responsivo, max-width 900px

```html
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32-C3 WebServer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial Black', 'Arial Bold', sans-serif;
            background: #fffef0;
            padding: 16px;
            line-height: 1.6;
        }

        header {
            background: #ff6b35;
            border: 5px solid #000;
            padding: 24px;
            margin: 0 auto 24px;
            max-width: 900px;
            box-shadow: 8px 8px 0 #000;
            transform: rotate(-1deg);
        }

        header h1 {
            color: #fff;
            font-size: 28px;
            text-transform: uppercase;
            text-shadow: 3px 3px 0 #000;
            transform: rotate(1deg);
        }

        .subtitle {
            color: #000;
            background: #ffeb3b;
            padding: 8px 12px;
            display: inline-block;
            border: 3px solid #000;
            margin-top: 12px;
            font-size: 14px;
            font-weight: bold;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }

        .card {
            background: #fff;
            border: 5px solid #000;
            padding: 20px;
            box-shadow: 6px 6px 0 #000;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .card:hover {
            transform: translate(-2px, -2px);
            box-shadow: 8px 8px 0 #000;
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 4px solid #000;
        }

        .card-icon {
            font-size: 36px;
            line-height: 1;
        }

        .card-title {
            font-size: 22px;
            text-transform: uppercase;
            color: #000;
        }

        .card.led { background: #4caf50; }
        .card.display { background: #00bcd4; }
        .card.games { background: #ff4081; }
        .card.system { background: #ffeb3b; }

        .link-list {
            list-style: none;
        }

        .link-item {
            margin-bottom: 12px;
        }

        .link-item a {
            display: block;
            background: #fff;
            color: #000;
            text-decoration: none;
            padding: 12px 16px;
            border: 4px solid #000;
            font-weight: bold;
            transition: all 0.2s;
            position: relative;
        }

        .link-item a:hover {
            background: #000;
            color: #fff;
            transform: translate(2px, 2px);
        }

        .link-item a:active {
            transform: translate(4px, 4px);
        }

        .description {
            font-size: 12px;
            font-family: Arial, sans-serif;
            margin-top: 6px;
            padding-left: 8px;
            font-weight: normal;
        }

        .big-button {
            display: block;
            background: #9c27b0;
            color: #fff;
            text-decoration: none;
            padding: 20px;
            border: 5px solid #000;
            font-size: 24px;
            text-align: center;
            text-transform: uppercase;
            box-shadow: 6px 6px 0 #000;
            margin-bottom: 20px;
            transition: all 0.2s;
            font-weight: bold;
        }

        .big-button:hover {
            transform: translate(-2px, -2px);
            box-shadow: 8px 8px 0 #000;
        }

        .big-button:active {
            transform: translate(2px, 2px);
            box-shadow: 4px 4px 0 #000;
        }

        footer {
            margin-top: 40px;
            padding: 20px;
            background: #000;
            color: #fff;
            border: 5px solid #000;
            text-align: center;
            font-size: 12px;
        }

        footer a {
            color: #ffeb3b;
            font-weight: bold;
        }

        @media (min-width: 640px) {
            body {
                padding: 24px;
            }

            header h1 {
                font-size: 36px;
            }

            .grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .card-title {
                font-size: 24px;
            }
        }

        @media (min-width: 1024px) {
            body {
                padding: 32px;
            }

            header {
                padding: 32px;
            }

            header h1 {
                font-size: 48px;
            }

            .grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>ESP32-C3 WEBSERVER</h1>
        <div class="subtitle">MicroPython + OLED Display + IoT Power</div>
    </header>

    <div class="container">
        <a href="/www/snake.html" class="big-button">🐍 JOGAR SNAKE →</a>
        <a href="/www/tictactoe.html" class="big-button" style="background: #f44336;">⭕ JOGO DA VELHA →</a>

        <div class="grid">
            <div class="card led">
                <div class="card-header">
                    <span class="card-icon">💡</span>
                    <h2 class="card-title">LED Control</h2>
                </div>
                <ul class="link-list">
                    <li class="link-item">
                        <a href="/led/on">LED ON</a>
                        <div class="description">Acende o LED da placa</div>
                    </li>
                    <li class="link-item">
                        <a href="/led/off">LED OFF</a>
                        <div class="description">Apaga o LED da placa</div>
                    </li>
                    <li class="link-item">
                        <a href="/led/blink?count=5&interval=0.3">BLINK</a>
                        <div class="description">Pisca LED 5x (count=1-20, interval=0.1-2.0s)</div>
                    </li>
                    <li class="link-item">
                        <a href="/morse?text=SOS">MORSE CODE</a>
                        <div class="description">LED em código Morse + Display (text=1-20 chars)</div>
                    </li>
                </ul>
            </div>

            <div class="card display">
                <div class="card-header">
                    <span class="card-icon">📺</span>
                    <h2 class="card-title">Display OLED</h2>
                </div>
                <ul class="link-list">
                    <li class="link-item">
                        <a href="/www/message.html">Message Panel</a>
                        <div class="description">Interface para enviar mensagens ao display</div>
                    </li>
                    <li class="link-item">
                        <a href="/www/morse.html">Morse Code</a>
                        <div class="description">Transmitir código Morse via LED + Display</div>
                    </li>
                </ul>
            </div>

            <div class="card games">
                <div class="card-header">
                    <span class="card-icon">🎮</span>
                    <h2 class="card-title">Games</h2>
                </div>
                <ul class="link-list">
                    <li class="link-item">
                        <a href="/www/snake.html">Snake Game</a>
                        <div class="description">Cobrinha 30x30 com leaderboard online</div>
                    </li>
                    <li class="link-item">
                        <a href="/snake/leaderboard">Snake Leaderboard</a>
                        <div class="description">Top 10 melhores pontuações (JSON)</div>
                    </li>
                    <li class="link-item">
                        <a href="/www/tictactoe.html">Tic-Tac-Toe</a>
                        <div class="description">Jogo da Velha vs IA</div>
                    </li>
                    <li class="link-item">
                        <a href="/game/tictactoe">Game State</a>
                        <div class="description">Estado do jogo (JSON)</div>
                    </li>
                </ul>
            </div>

            <div class="card system">
                <div class="card-header">
                    <span class="card-icon">⚙️</span>
                    <h2 class="card-title">System Info</h2>
                </div>
                <ul class="link-list">
                    <li class="link-item">
                        <a href="/hello">Hello</a>
                        <div class="description">Teste de conexão</div>
                    </li>
                    <li class="link-item">
                        <a href="/storage">Storage Info</a>
                        <div class="description">Armazenamento (total, usado, livre)</div>
                    </li>
                    <li class="link-item">
                        <a href="#" onclick="openWebREPL(); return false;">WebREPL</a>
                        <div class="description">Console Python (porta 8266, senha: star) - Desabilitado por padrão. Habilite em constants.py</div>
                    </li>
                </ul>
            </div>
        </div>

        <footer>
            <p>ESP32-C3 Supermini + MicroPython v1.27.0</p>
            <p>Projeto: <a href="https://github.com/FNakano/ProjetoBasico-CFA" target="_blank">github.com/FNakano/ProjetoBasico-CFA</a></p>
        </footer>
    </div>

    <script>
        function openWebREPL() {
            const currentUrl = new URL(window.location.href);
            currentUrl.port = '8266';
            currentUrl.pathname = '/www/webrepl/webrepl.html';
            window.open(currentUrl.toString(), '_blank');
        }
    </script>
</body>
</html>
```

---

### 4. Frontend - Páginas Interativas

#### `src/www/snake.html` (CRIAR)
Jogo Snake 30x30 com leaderboard, high score sincronizado com servidor.

**Características**:
- Grid 30x30, canvas 600x600px
- Velocidade progressiva (2% por comida)
- Controles: Arrow keys ou WASD, Spacebar para pause
- Idempotência na submissão (botão desabilita após envio)
- High score sincroniza com servidor (usa max do leaderboard[0].score)
- Gradiente no corpo da cobra
- Olhos na cabeça da cobra

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Snake Game - ESP32</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
        }

        h1 {
            margin-bottom: 10px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .game-container {
            display: flex;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }

        .game-area {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .info-panel {
            background: rgba(255, 255, 255, 0.15);
            padding: 20px;
            border-radius: 15px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            display: flex;
            gap: 30px;
            justify-content: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .info-item {
            text-align: center;
        }

        .info-label {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }

        .info-value {
            font-size: 32px;
            font-weight: bold;
        }

        #gameCanvas {
            border: 4px solid white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            background: #2a2a2a;
        }

        .controls {
            display: flex;
            gap: 15px;
            margin-top: 20px;
        }

        button {
            padding: 15px 30px;
            font-size: 18px;
            font-weight: bold;
            background: white;
            color: #667eea;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        button:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }

        button:active {
            transform: translateY(0);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .leaderboard {
            background: rgba(255, 255, 255, 0.15);
            padding: 25px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            min-width: 300px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .leaderboard h2 {
            margin-bottom: 15px;
            font-size: 1.5em;
            text-align: center;
        }

        .leaderboard-list {
            list-style: none;
        }

        .leaderboard-item {
            display: flex;
            justify-content: space-between;
            padding: 12px;
            margin: 8px 0;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            font-size: 16px;
            transition: background 0.3s;
        }

        .leaderboard-item:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .rank {
            font-weight: bold;
            margin-right: 10px;
            color: #ffd700;
        }

        .player-name {
            flex: 1;
        }

        .player-score {
            font-weight: bold;
        }

        .game-over-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal-content {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 10px 50px rgba(0, 0, 0, 0.5);
            max-width: 400px;
        }

        .modal-content h2 {
            font-size: 2.5em;
            margin-bottom: 20px;
        }

        .modal-content p {
            font-size: 1.5em;
            margin-bottom: 30px;
        }

        .modal-content input {
            width: 100%;
            padding: 15px;
            font-size: 18px;
            border: none;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }

        .modal-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
        }

        a {
            display: inline-block;
            margin-top: 30px;
            padding: 12px 25px;
            background: rgba(255, 255, 255, 0.2);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            transition: background 0.3s;
        }

        a:hover {
            background: rgba(255, 255, 255, 0.3);
        }

        @media (max-width: 768px) {
            .game-container {
                flex-direction: column;
            }

            h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <h1>🐍 Snake Game</h1>

    <div class="game-container">
        <div class="game-area">
            <div class="info-panel">
                <div class="info-item">
                    <div class="info-label">Score</div>
                    <div class="info-value" id="score">0</div>
                </div>
                <div class="info-item">
                    <div class="info-label">High Score</div>
                    <div class="info-value" id="highScore">0</div>
                </div>
            </div>

            <canvas id="gameCanvas" width="600" height="600"></canvas>

            <div class="controls">
                <button id="startBtn" onclick="startGame()">▶ Start Game</button>
                <button id="pauseBtn" onclick="togglePause()" disabled>⏸ Pause</button>
                <button onclick="location.href='/'">🏠 Home</button>
            </div>
        </div>

        <div class="leaderboard">
            <h2>🏆 Leaderboard</h2>
            <ul class="leaderboard-list" id="leaderboardList">
                <li class="leaderboard-item">Loading...</li>
            </ul>
        </div>
    </div>

    <a href="/">← Back to Home</a>

    <!-- Game Over Modal -->
    <div id="gameOverModal" class="game-over-modal">
        <div class="modal-content">
            <h2>Game Over!</h2>
            <p>Your Score: <span id="finalScore">0</span></p>
            <input type="text" id="playerName" placeholder="Enter your name" maxlength="20">
            <div class="modal-buttons">
                <button id="submitBtn" onclick="submitScore()">Submit Score</button>
                <button onclick="closeModal()">Close</button>
            </div>
        </div>
    </div>

    <script>
        // Game constants
        const GRID_SIZE = 30;
        const CELL_SIZE = 600 / GRID_SIZE; // 20px per cell
        const INITIAL_SPEED = 150; // ms per frame
        const SPEED_INCREASE = 0.02; // Speed increases over time

        // Game state
        let canvas, ctx;
        let snake = [];
        let food = {};
        let direction = 'RIGHT';
        let nextDirection = 'RIGHT';
        let score = 0;
        let highScore = 0;
        let gameLoop = null;
        let isPaused = false;
        let gameSpeed = INITIAL_SPEED;

        // Initialize game
        async function init() {
            canvas = document.getElementById('gameCanvas');
            ctx = canvas.getContext('2d');

            // Load leaderboard (which also updates high score)
            await loadLeaderboard();

            // Setup keyboard controls
            document.addEventListener('keydown', handleKeyPress);
        }

        function startGame() {
            // Reset game state
            snake = [
                {x: 15, y: 15},
                {x: 14, y: 15},
                {x: 13, y: 15}
            ];
            direction = 'RIGHT';
            nextDirection = 'RIGHT';
            score = 0;
            gameSpeed = INITIAL_SPEED;
            isPaused = false;

            updateScore();
            spawnFood();

            // Update UI
            document.getElementById('startBtn').disabled = true;
            document.getElementById('pauseBtn').disabled = false;

            // Start game loop
            if (gameLoop) clearInterval(gameLoop);
            gameLoop = setInterval(update, gameSpeed);
        }

        function update() {
            if (isPaused) return;

            // Update direction
            direction = nextDirection;

            // Calculate new head position
            const head = {...snake[0]};

            switch(direction) {
                case 'UP': head.y--; break;
                case 'DOWN': head.y++; break;
                case 'LEFT': head.x--; break;
                case 'RIGHT': head.x++; break;
            }

            // Check wall collision
            if (head.x < 0 || head.x >= GRID_SIZE || head.y < 0 || head.y >= GRID_SIZE) {
                gameOver();
                return;
            }

            // Check self collision
            if (snake.some(segment => segment.x === head.x && segment.y === head.y)) {
                gameOver();
                return;
            }

            // Add new head
            snake.unshift(head);

            // Check food collision
            if (head.x === food.x && head.y === food.y) {
                score++;
                updateScore();
                spawnFood();

                // Increase speed slightly
                gameSpeed = Math.max(50, gameSpeed * (1 - SPEED_INCREASE));
                clearInterval(gameLoop);
                gameLoop = setInterval(update, gameSpeed);
            } else {
                // Remove tail
                snake.pop();
            }

            draw();
        }

        function draw() {
            // Clear canvas
            ctx.fillStyle = '#2a2a2a';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw grid lines (subtle)
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 1;
            for (let i = 0; i <= GRID_SIZE; i++) {
                ctx.beginPath();
                ctx.moveTo(i * CELL_SIZE, 0);
                ctx.lineTo(i * CELL_SIZE, canvas.height);
                ctx.stroke();

                ctx.beginPath();
                ctx.moveTo(0, i * CELL_SIZE);
                ctx.lineTo(canvas.width, i * CELL_SIZE);
                ctx.stroke();
            }

            // Draw snake
            snake.forEach((segment, index) => {
                if (index === 0) {
                    // Head - brighter green
                    ctx.fillStyle = '#4ade80';
                } else {
                    // Body - gradient green
                    const opacity = 1 - (index / snake.length) * 0.3;
                    ctx.fillStyle = `rgba(34, 197, 94, ${opacity})`;
                }

                ctx.fillRect(
                    segment.x * CELL_SIZE + 1,
                    segment.y * CELL_SIZE + 1,
                    CELL_SIZE - 2,
                    CELL_SIZE - 2
                );

                // Add eye to head
                if (index === 0) {
                    ctx.fillStyle = 'white';
                    const eyeSize = CELL_SIZE / 6;
                    const eyeOffset = CELL_SIZE / 3;

                    if (direction === 'UP' || direction === 'DOWN') {
                        ctx.fillRect(segment.x * CELL_SIZE + eyeOffset,
                                   segment.y * CELL_SIZE + CELL_SIZE/2 - eyeSize/2,
                                   eyeSize, eyeSize);
                        ctx.fillRect(segment.x * CELL_SIZE + CELL_SIZE - eyeOffset - eyeSize,
                                   segment.y * CELL_SIZE + CELL_SIZE/2 - eyeSize/2,
                                   eyeSize, eyeSize);
                    } else {
                        ctx.fillRect(segment.x * CELL_SIZE + CELL_SIZE/2 - eyeSize/2,
                                   segment.y * CELL_SIZE + eyeOffset,
                                   eyeSize, eyeSize);
                        ctx.fillRect(segment.x * CELL_SIZE + CELL_SIZE/2 - eyeSize/2,
                                   segment.y * CELL_SIZE + CELL_SIZE - eyeOffset - eyeSize,
                                   eyeSize, eyeSize);
                    }
                }
            });

            // Draw food
            ctx.fillStyle = '#ef4444';
            ctx.beginPath();
            ctx.arc(
                food.x * CELL_SIZE + CELL_SIZE / 2,
                food.y * CELL_SIZE + CELL_SIZE / 2,
                CELL_SIZE / 2 - 2,
                0,
                Math.PI * 2
            );
            ctx.fill();
        }

        function spawnFood() {
            do {
                food = {
                    x: Math.floor(Math.random() * GRID_SIZE),
                    y: Math.floor(Math.random() * GRID_SIZE)
                };
            } while (snake.some(segment => segment.x === food.x && segment.y === food.y));
        }

        function handleKeyPress(e) {
            // Prevent arrow keys from scrolling
            if(['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(e.key)) {
                e.preventDefault();
            }

            switch(e.key) {
                case 'ArrowUp':
                case 'w':
                case 'W':
                    if (direction !== 'DOWN') nextDirection = 'UP';
                    break;
                case 'ArrowDown':
                case 's':
                case 'S':
                    if (direction !== 'UP') nextDirection = 'DOWN';
                    break;
                case 'ArrowLeft':
                case 'a':
                case 'A':
                    if (direction !== 'RIGHT') nextDirection = 'LEFT';
                    break;
                case 'ArrowRight':
                case 'd':
                case 'D':
                    if (direction !== 'LEFT') nextDirection = 'RIGHT';
                    break;
                case ' ':
                    togglePause();
                    break;
            }
        }

        function togglePause() {
            if (!gameLoop) return;

            isPaused = !isPaused;
            document.getElementById('pauseBtn').textContent = isPaused ? '▶ Resume' : '⏸ Pause';
        }

        function updateScore() {
            document.getElementById('score').textContent = score;

            if (score > highScore) {
                highScore = score;
                document.getElementById('highScore').textContent = highScore;
                localStorage.setItem('snakeHighScore', highScore);
            }
        }


        function gameOver() {
            clearInterval(gameLoop);
            gameLoop = null;

            // Update UI
            document.getElementById('startBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;

            // Show game over modal
            document.getElementById('finalScore').textContent = score;
            document.getElementById('gameOverModal').style.display = 'flex';
        }

        function closeModal() {
            document.getElementById('gameOverModal').style.display = 'none';
            document.getElementById('playerName').value = '';

            // Reset submit button state
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit Score';
        }

        async function submitScore() {
            const playerName = document.getElementById('playerName').value.trim();
            const submitBtn = document.getElementById('submitBtn');

            if (!playerName) {
                alert('Please enter your name!');
                return;
            }

            // Prevent multiple submissions
            if (submitBtn.disabled) {
                return;
            }

            // Disable button and show loading state
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            try {
                const response = await fetch('/snake/score', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: playerName,
                        score: score
                    })
                });

                if (response.ok) {
                    closeModal();
                    loadLeaderboard();
                } else {
                    alert('Failed to submit score. Please try again.');
                    // Re-enable button on error
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Submit Score';
                }
            } catch (error) {
                console.error('Error submitting score:', error);
                alert('Network error. Please check your connection.');
                // Re-enable button on error
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Score';
            }
        }

        async function loadLeaderboard() {
            try {
                const response = await fetch('/snake/leaderboard');
                const data = await response.json();

                const list = document.getElementById('leaderboardList');

                if (data.leaderboard && data.leaderboard.length > 0) {
                    // Update leaderboard list
                    list.innerHTML = data.leaderboard.map((entry, index) => `
                        <li class="leaderboard-item">
                            <span class="rank">#${index + 1}</span>
                            <span class="player-name">${entry.name}</span>
                            <span class="player-score">${entry.score}</span>
                        </li>
                    `).join('');

                    // Update high score from leaderboard (server is authoritative)
                    const serverHighScore = data.leaderboard[0].score;

                    // Always use server as source of truth when leaderboard exists
                    highScore = serverHighScore;
                    document.getElementById('highScore').textContent = highScore;

                    // Update localStorage to match server
                    localStorage.setItem('snakeHighScore', serverHighScore);
                } else {
                    list.innerHTML = '<li class="leaderboard-item">No scores yet. Be the first!</li>';

                    // No server scores, use local high score
                    const localHighScore = parseInt(localStorage.getItem('snakeHighScore')) || 0;
                    highScore = localHighScore;
                    document.getElementById('highScore').textContent = highScore;
                }
            } catch (error) {
                console.error('Error loading leaderboard:', error);
                document.getElementById('leaderboardList').innerHTML =
                    '<li class="leaderboard-item">Failed to load leaderboard</li>';

                // Fallback to localStorage on network error
                const localHighScore = parseInt(localStorage.getItem('snakeHighScore')) || 0;
                highScore = localHighScore;
                document.getElementById('highScore').textContent = highScore;
            }
        }

        // Initialize on page load
        window.onload = init;
    </script>
</body>
</html>
```

---

#### `src/www/message.html` (CRIAR)
Interface para enviar mensagens ao display OLED.

**Características**:
- Preview da mensagem atual
- Mensagens rápidas (botões) apenas preenchem campo (não enviam automaticamente)
- Contador de caracteres (200 max)
- Botão limpar display

```html
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Display Message - ESP32-C3</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial Black', 'Arial Bold', sans-serif;
            background: #fffef0;
            padding: 16px;
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: #00bcd4;
            border: 5px solid #000;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 8px 8px 0 #000;
            transform: rotate(-1deg);
        }

        header h1 {
            color: #fff;
            font-size: 28px;
            text-transform: uppercase;
            text-shadow: 3px 3px 0 #000;
            transform: rotate(1deg);
        }

        .container {
            max-width: 600px;
            margin: 0 auto;
            flex: 1;
        }

        .control-panel {
            background: #fff;
            border: 5px solid #000;
            padding: 30px;
            box-shadow: 8px 8px 0 #000;
            margin-bottom: 20px;
        }

        .display-preview {
            background: #000;
            color: #00ff00;
            border: 5px solid #000;
            padding: 20px;
            min-height: 150px;
            margin-bottom: 30px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            white-space: pre-wrap;
            word-break: break-all;
        }

        .input-group {
            margin-bottom: 20px;
        }

        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
        }

        .input-group textarea {
            width: 100%;
            padding: 15px;
            border: 4px solid #000;
            font-size: 16px;
            font-family: 'Courier New', monospace;
            resize: vertical;
            min-height: 120px;
        }

        .char-counter {
            text-align: right;
            font-size: 12px;
            margin-top: 5px;
            color: #666;
        }

        button {
            width: 100%;
            padding: 20px;
            font-size: 18px;
            font-weight: bold;
            border: 5px solid #000;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
            font-family: 'Arial Black', sans-serif;
            background: #00bcd4;
            color: #fff;
            margin-bottom: 15px;
        }

        button:hover {
            transform: translate(-2px, -2px);
            box-shadow: 6px 6px 0 #000;
        }

        button:active {
            transform: translate(2px, 2px);
            box-shadow: 2px 2px 0 #000;
        }

        .btn-clear {
            background: #f44336;
        }

        .quick-messages {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }

        .quick-btn {
            padding: 12px;
            font-size: 14px;
            background: #ffeb3b;
            color: #000;
        }

        .back-button {
            display: block;
            background: #000;
            color: #fff;
            text-decoration: none;
            padding: 15px;
            border: 5px solid #000;
            text-align: center;
            font-size: 16px;
            text-transform: uppercase;
            transition: all 0.2s;
        }

        .back-button:hover {
            background: #fff;
            color: #000;
            transform: translate(-2px, -2px);
            box-shadow: 6px 6px 0 #000;
        }

        @media (min-width: 640px) {
            header h1 {
                font-size: 36px;
            }

            body {
                padding: 24px;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>📺 DISPLAY MESSAGE</h1>
    </header>

    <div class="container">
        <div class="control-panel">
            <h2 style="margin-bottom: 15px; font-size: 18px;">MENSAGEM ATUAL:</h2>
            <div class="display-preview" id="preview">Carregando...</div>

            <h2 style="margin-bottom: 15px; font-size: 18px;">MENSAGENS RÁPIDAS:</h2>
            <div class="quick-messages">
                <button class="quick-btn" onclick="setQuickMessage('Hello ESP32!')">Hello ESP32!</button>
                <button class="quick-btn" onclick="setQuickMessage('IoT Power')">IoT Power</button>
                <button class="quick-btn" onclick="setQuickMessage('MicroPython')">MicroPython</button>
                <button class="quick-btn" onclick="setQuickMessage('ESP32-C3')">ESP32-C3</button>
            </div>

            <hr style="border: 2px solid #000; margin: 30px 0;">

            <div class="input-group">
                <label>NOVA MENSAGEM:</label>
                <textarea id="messageInput" maxlength="200" oninput="updateCounter()"></textarea>
                <div class="char-counter" id="charCounter">0 / 200 caracteres</div>
            </div>

            <button onclick="sendMessage()">ENVIAR</button>
            <button class="btn-clear" onclick="clearMessage()">LIMPAR DISPLAY</button>
        </div>

        <a href="/" class="back-button">← VOLTAR</a>
    </div>

    <script>
        async function loadCurrentMessage() {
            try {
                const response = await fetch('/message');
                const message = await response.text();
                document.getElementById('preview').textContent = message || '(vazio)';
            } catch (error) {
                console.error('Erro ao carregar mensagem:', error);
                document.getElementById('preview').textContent = 'Erro ao carregar';
            }
        }

        async function sendMessage() {
            const message = document.getElementById('messageInput').value.trim();

            if (!message) {
                alert('Digite uma mensagem primeiro!');
                return;
            }

            try {
                const response = await fetch(`/message?text=${encodeURIComponent(message)}`);

                if (response.ok) {
                    await loadCurrentMessage();
                    document.getElementById('messageInput').value = '';
                    updateCounter();
                } else {
                    alert('Erro ao enviar mensagem');
                }
            } catch (error) {
                alert('Erro de conexão');
            }
        }

        function setQuickMessage(message) {
            document.getElementById('messageInput').value = message;
            updateCounter();
        }

        async function clearMessage() {
            try {
                await fetch('/message?text= ');
                await loadCurrentMessage();
            } catch (error) {
                alert('Erro ao limpar display');
            }
        }

        function updateCounter() {
            const textarea = document.getElementById('messageInput');
            const counter = document.getElementById('charCounter');
            counter.textContent = `${textarea.value.length} / 200 caracteres`;
        }

        // Carrega mensagem atual ao iniciar
        loadCurrentMessage();
    </script>
</body>
</html>
```

---

#### `src/www/morse.html` (CRIAR)
Interface de código Morse com conversão em tempo real.

**Características**:
- Conversão texto → Morse em tempo real
- Mensagens rápidas (SOS, HELP, OK, HI, HELLO, TEST)
- Controle de velocidade (0.1-0.5s slider)
- Dicionário completo A-Z, 0-9, pontuação
- Display mostra código Morse gerado

```html
<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Morse Code - ESP32-C3</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial Black', 'Arial Bold', sans-serif;
            background: #fffef0;
            padding: 16px;
            line-height: 1.6;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: #ff9800;
            border: 5px solid #000;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 8px 8px 0 #000;
            transform: rotate(-1deg);
        }

        header h1 {
            color: #fff;
            font-size: 28px;
            text-transform: uppercase;
            text-shadow: 3px 3px 0 #000;
            transform: rotate(1deg);
        }

        .container {
            max-width: 600px;
            margin: 0 auto;
            flex: 1;
        }

        .control-panel {
            background: #fff;
            border: 5px solid #000;
            padding: 30px;
            box-shadow: 8px 8px 0 #000;
            margin-bottom: 20px;
        }

        .morse-display {
            background: #000;
            color: #ff9800;
            border: 5px solid #000;
            padding: 20px;
            min-height: 80px;
            margin-bottom: 20px;
            font-family: 'Courier New', monospace;
            font-size: 24px;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .input-group {
            margin-bottom: 20px;
        }

        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-size: 14px;
        }

        .input-group input {
            width: 100%;
            padding: 15px;
            border: 4px solid #000;
            font-size: 18px;
            font-family: 'Courier New', monospace;
            text-transform: uppercase;
        }

        .char-counter {
            text-align: right;
            font-size: 12px;
            margin-top: 5px;
            color: #666;
        }

        button {
            width: 100%;
            padding: 20px;
            font-size: 18px;
            font-weight: bold;
            border: 5px solid #000;
            cursor: pointer;
            transition: all 0.2s;
            text-transform: uppercase;
            font-family: 'Arial Black', sans-serif;
            background: #ff9800;
            color: #fff;
            margin-bottom: 15px;
        }

        button:hover {
            transform: translate(-2px, -2px);
            box-shadow: 6px 6px 0 #000;
        }

        button:active {
            transform: translate(2px, 2px);
            box-shadow: 2px 2px 0 #000;
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }

        .quick-messages {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 10px;
            margin-bottom: 20px;
        }

        .quick-btn {
            padding: 12px;
            font-size: 14px;
            background: #ffeb3b;
            color: #000;
        }

        .info-box {
            background: #e3f2fd;
            border: 4px solid #000;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 12px;
            font-family: Arial, sans-serif;
        }

        .info-box strong {
            display: block;
            margin-bottom: 5px;
        }

        .back-button {
            display: block;
            background: #000;
            color: #fff;
            text-decoration: none;
            padding: 15px;
            border: 5px solid #000;
            text-align: center;
            font-size: 16px;
            text-transform: uppercase;
            transition: all 0.2s;
        }

        .back-button:hover {
            background: #fff;
            color: #000;
            transform: translate(-2px, -2px);
            box-shadow: 6px 6px 0 #000;
        }

        @media (min-width: 640px) {
            header h1 {
                font-size: 36px;
            }

            body {
                padding: 24px;
            }
        }
    </style>
</head>
<body>
    <header>
        <h1>📡 MORSE CODE</h1>
    </header>

    <div class="container">
        <div class="control-panel">
            <div class="info-box">
                <strong>Como funciona:</strong>
                Digite uma mensagem (até 20 caracteres) e ela será transmitida via LED em código Morse internacional.
                O display OLED mostrará cada letra durante a transmissão.
            </div>

            <h2 style="margin-bottom: 15px; font-size: 18px;">CÓDIGO MORSE:</h2>
            <div class="morse-display" id="morseDisplay">...</div>

            <h2 style="margin-bottom: 15px; font-size: 18px;">MENSAGENS RÁPIDAS:</h2>
            <div class="quick-messages">
                <button class="quick-btn" onclick="setQuickMessage('SOS')">SOS</button>
                <button class="quick-btn" onclick="setQuickMessage('HELP')">HELP</button>
                <button class="quick-btn" onclick="setQuickMessage('OK')">OK</button>
                <button class="quick-btn" onclick="setQuickMessage('HI')">HI</button>
                <button class="quick-btn" onclick="setQuickMessage('HELLO')">HELLO</button>
                <button class="quick-btn" onclick="setQuickMessage('TEST')">TEST</button>
            </div>

            <hr style="border: 2px solid #000; margin: 30px 0;">

            <div class="input-group">
                <label>MENSAGEM (A-Z, 0-9, pontuação básica):</label>
                <input type="text" id="messageInput" maxlength="20" oninput="updateMorse()" placeholder="Digite sua mensagem">
                <div class="char-counter" id="charCounter">0 / 20 caracteres</div>
            </div>

            <div class="input-group">
                <label>VELOCIDADE (0.1-0.5 segundos/ponto):</label>
                <input type="range" id="speedInput" min="0.1" max="0.5" step="0.05" value="0.2" oninput="updateSpeedLabel()" style="width: 100%;">
                <div style="text-align: center; margin-top: 5px;">
                    <strong id="speedLabel">0.2s</strong> (Normal)
                </div>
            </div>

            <button id="sendBtn" onclick="sendMorse()">TRANSMITIR MORSE</button>
        </div>

        <a href="/" class="back-button">← VOLTAR</a>
    </div>

    <script>
        const MORSE_CODE = {
            'A': '.-',    'B': '-...',  'C': '-.-.',  'D': '-..',   'E': '.',
            'F': '..-.',  'G': '--.',   'H': '....',  'I': '..',    'J': '.---',
            'K': '-.-',   'L': '.-..',  'M': '--',    'N': '-.',    'O': '---',
            'P': '.--.',  'Q': '--.-',  'R': '.-.',   'S': '...',   'T': '-',
            'U': '..-',   'V': '...-',  'W': '.--',   'X': '-..-',  'Y': '-.--',
            'Z': '--..',
            '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
            '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
            '.': '.-.-.-', ',': '--..--', '?': '..--..', '!': '-.-.--', '-': '-....-',
            ' ': '/'
        };

        function textToMorse(text) {
            return text.toUpperCase()
                .split('')
                .map(char => MORSE_CODE[char] || '')
                .filter(code => code)
                .join(' ');
        }

        function updateMorse() {
            const text = document.getElementById('messageInput').value;
            const morse = textToMorse(text);
            document.getElementById('morseDisplay').textContent = morse || '...';
            document.getElementById('charCounter').textContent = `${text.length} / 20 caracteres`;
        }

        function updateSpeedLabel() {
            const speed = document.getElementById('speedInput').value;
            const speedLabel = document.getElementById('speedLabel');
            speedLabel.textContent = `${speed}s`;
        }

        function setQuickMessage(message) {
            document.getElementById('messageInput').value = message;
            updateMorse();
        }

        async function sendMorse() {
            const text = document.getElementById('messageInput').value.trim();
            const speed = document.getElementById('speedInput').value;

            if (!text) {
                alert('Digite uma mensagem primeiro!');
                return;
            }

            const sendBtn = document.getElementById('sendBtn');
            sendBtn.disabled = true;
            sendBtn.textContent = 'TRANSMITINDO...';

            try {
                const response = await fetch(`/morse?text=${encodeURIComponent(text)}&speed=${speed}`);
                const data = await response.json();

                if (data.error) {
                    alert(`Erro: ${data.error}`);
                } else {
                    // Aguarda duração estimada da transmissão
                    setTimeout(() => {
                        sendBtn.disabled = false;
                        sendBtn.textContent = 'TRANSMITIR MORSE';
                    }, (data.duration || 5) * 1000);
                }
            } catch (error) {
                alert('Erro de conexão');
                sendBtn.disabled = false;
                sendBtn.textContent = 'TRANSMITIR MORSE';
            }
        }

        // Inicializa
        updateMorse();
        updateSpeedLabel();
    </script>
</body>
</html>
```

---

#### `src/www/led.html` (CRIAR)
Interface de controle do LED (OPCIONAL - verificar se foi criado anteriormente).

---

### 5. Correções de Hardware

#### `src/hardware/display.py`
**Estado atual**: Implementação diferente

**Código correto da função `show_message()`**:
```python
def show_message(self, message: str):
    """
    Display multi-line message with automatic text wrapping.

    Args:
        message: Message to display (supports \n for line breaks)
    """
    if not self._available:
        self.logger.debug(f"Display unavailable, would show message: {message}")
        return

    try:
        self.clear()
        line_num = 0

        # Split by newlines first, then wrap long lines
        lines = message.split('\n')
        max_lines = constants.DISPLAY_HEIGHT // constants.DISPLAY_LINE_HEIGHT

        for line in lines:
            if line_num >= max_lines:
                break

            # Break long lines into chunks
            if len(line) <= constants.DISPLAY_CHARS_PER_LINE:
                chunks = [line]
            else:
                chunks = [line[i:i + constants.DISPLAY_CHARS_PER_LINE]
                         for i in range(0, len(line), constants.DISPLAY_CHARS_PER_LINE)]

            for chunk in chunks:
                if line_num >= max_lines:
                    break

                y_pos = constants.DISPLAY_START_Y + (line_num * constants.DISPLAY_LINE_HEIGHT)

                # Center text horizontally
                text_width = len(chunk) * 6  # Approximate char width
                x_pos = max(0, (constants.DISPLAY_WIDTH - text_width) // 2)

                self._driver.text(chunk, x_pos, y_pos, 1)
                line_num += 1

        self._driver.show()
        self.logger.debug(f"Displayed message: {message}")

    except Exception as e:
        self.logger.error(f"Failed to display message: {e}")
```

---

## Implementação Paralela com 3 Agents

**IMPORTANTE**: Estas 3 tarefas são **totalmente independentes** e devem ser executadas **EM PARALELO** por 3 agents diferentes. Nenhuma tarefa depende da outra.

---

### 🟦 AGENT 1: Backend Core + Snake Leaderboard

**Responsabilidade**: Corrigir arquivos de configuração, display e implementar sistema completo de leaderboard Snake.

**Arquivos a modificar**:
1. ✅ `src/constants.py` - Adicionar flags DEBUG, ENABLE_AIOREPL, ENABLE_WEBREPL e config display 128x64
2. ✅ `src/boot.py` - Condicionalizar WebREPL (import constants + if)
3. ✅ `src/hardware/display.py` - Corrigir função show_message() com suporte a \n e centralização
4. ✅ `src/games/snake_leaderboard.py` - **CRIAR** sistema de leaderboard com idempotência
5. ✅ `src/web/routes.py` - Adicionar métodos snake_leaderboard() e snake_add_score()
6. ✅ `src/web/server.py` - Registrar rotas GET /snake/leaderboard e POST /snake/score

**Código completo**: Ver seções "1. Arquivos de Configuração", "2. Backend - Snake Leaderboard", "5. Correções de Hardware" deste documento.

**Dependências**: Nenhuma (totalmente independente).

**Validação**:
- [ ] constants.py tem todas as flags (DEBUG, ENABLE_AIOREPL, ENABLE_WEBREPL)
- [ ] boot.py só inicia WebREPL se ENABLE_WEBREPL = True
- [ ] display.py show_message() suporta \n e centraliza texto
- [ ] snake_leaderboard.py existe e tem funções load/save/get/add_score
- [ ] routes.py tem handlers snake_leaderboard e snake_add_score
- [ ] server.py registra /snake/leaderboard e /snake/score

---

### 🟩 AGENT 2: Frontend - Homepage + Snake Game

**Responsabilidade**: Reimplementar homepage neobrutalism e jogo Snake completo com leaderboard.

**Arquivos a modificar**:
1. ✅ `src/www/index.html` - Homepage neobrutalism mobile-first responsivo
2. ✅ `src/www/snake.html` - **CRIAR** jogo Snake 30x30 completo com leaderboard

**Código completo**: Ver seção "3. Frontend - Homepage Neobrutalism" e "4. Frontend - Páginas Interativas (snake.html)" deste documento.

**Características homepage**:
- Design neobrutalism (bordas grossas, sombras duras, cores vibrantes)
- Mobile-first responsivo (1 coluna mobile → 2 colunas desktop)
- Max-width 900px
- 4 cards coloridos (LED verde, Display ciano, Games rosa, System amarelo)
- Botões grandes para Snake e Tic-Tac-Toe
- WebREPL com redirecionamento automático porta 8266

**Características Snake**:
- Grid 30x30, canvas 600x600px
- Velocidade progressiva (2% por comida)
- Controles: Arrow keys ou WASD, Spacebar pause
- High score sincronizado com servidor (source of truth)
- Idempotência na submissão (botão desabilita)
- Gradiente no corpo da cobra, olhos na cabeça

**Dependências**: Nenhuma (HTML puro, JavaScript fetch para /snake/leaderboard e /snake/score).

**Validação**:
- [ ] index.html tem design neobrutalism responsivo
- [ ] index.html max-width 900px
- [ ] snake.html grid 30x30 funciona
- [ ] snake.html high score usa servidor como source of truth
- [ ] snake.html botão Submit desabilita após click

---

### 🟨 AGENT 3: Frontend - Interfaces Auxiliares

**Responsabilidade**: Criar interfaces HTML interativas para Message (display OLED) e Morse Code.

**Arquivos a criar**:
1. ✅ `src/www/message.html` - **CRIAR** interface para enviar mensagens ao display
2. ✅ `src/www/morse.html` - **CRIAR** interface de código Morse interativa

**Código completo**: Ver seção "4. Frontend - Páginas Interativas (message.html e morse.html)" deste documento.

**Características message.html**:
- Preview da mensagem atual (busca GET /message)
- Mensagens rápidas (botões) apenas preenchem campo (não enviam automaticamente)
- Textarea com contador 200 caracteres
- Botões: Enviar, Limpar Display
- Estilo neobrutalism ciano

**Características morse.html**:
- Conversão texto → Morse em tempo real (dicionário JavaScript)
- Display mostra código Morse gerado
- Mensagens rápidas (SOS, HELP, OK, HI, HELLO, TEST)
- Slider de velocidade (0.1-0.5s)
- Contador 20 caracteres
- Estilo neobrutalism laranja

**Dependências**: Nenhuma (HTML puro, JavaScript fetch para /message e /morse).

**Validação**:
- [ ] message.html mensagens rápidas não enviam automaticamente
- [ ] message.html contador de caracteres funciona
- [ ] morse.html converte texto→Morse em tempo real
- [ ] morse.html slider de velocidade funciona

---

## Comandos de Deploy (Após Implementação)

**Executar DEPOIS que os 3 agents terminarem**:

```bash
cd c:\Users\bruno\Documents\codes\computacao-fisica-esp32-c3

# Backend (Agent 1)
venv/Scripts/python.exe -m mpremote cp src/constants.py :constants.py
venv/Scripts/python.exe -m mpremote cp src/boot.py :boot.py
venv/Scripts/python.exe -m mpremote cp src/hardware/display.py :hardware/display.py
venv/Scripts/python.exe -m mpremote cp src/games/snake_leaderboard.py :games/snake_leaderboard.py
venv/Scripts/python.exe -m mpremote cp src/web/routes.py :web/routes.py
venv/Scripts/python.exe -m mpremote cp src/web/server.py :web/server.py

# Frontend (Agent 2 + Agent 3)
venv/Scripts/python.exe -m mpremote cp src/www/index.html :www/index.html
venv/Scripts/python.exe -m mpremote cp src/www/snake.html :www/snake.html
venv/Scripts/python.exe -m mpremote cp src/www/message.html :www/message.html
venv/Scripts/python.exe -m mpremote cp src/www/morse.html :www/morse.html

# Reiniciar
venv/Scripts/python.exe -m mpremote reset
```

---

## Checklist de Verificação

### Arquivos Backend
- [ ] `src/constants.py` - Flags e display config restaurados
- [ ] `src/boot.py` - WebREPL condicional
- [ ] `src/hardware/display.py` - show_message() corrigido
- [ ] `src/games/snake_leaderboard.py` - Criado
- [ ] `src/web/routes.py` - Handlers Snake adicionados
- [ ] `src/web/server.py` - Rotas Snake registradas

### Arquivos Frontend
- [ ] `src/www/index.html` - Homepage neobrutalism
- [ ] `src/www/snake.html` - Snake game completo
- [ ] `src/www/message.html` - Interface mensagens
- [ ] `src/www/morse.html` - Interface Morse

### Funcionalidades
- [ ] WebREPL não trava (desabilitado por padrão)
- [ ] Display 128x64 funcionando
- [ ] Snake com leaderboard e idempotência
- [ ] High score sincronizado com servidor
- [ ] Mensagens rápidas não enviam automaticamente
- [ ] Código Morse converte em tempo real

---

## Comandos para Copiar ao ESP32

```bash
cd c:\Users\bruno\Documents\codes\computacao-fisica-esp32-c3

# Backend
venv/Scripts/python.exe -m mpremote cp src/constants.py :constants.py
venv/Scripts/python.exe -m mpremote cp src/boot.py :boot.py
venv/Scripts/python.exe -m mpremote cp src/hardware/display.py :hardware/display.py
venv/Scripts/python.exe -m mpremote cp src/games/snake_leaderboard.py :games/snake_leaderboard.py
venv/Scripts/python.exe -m mpremote cp src/web/routes.py :web/routes.py
venv/Scripts/python.exe -m mpremote cp src/web/server.py :web/server.py

# Frontend
venv/Scripts/python.exe -m mpremote cp src/www/index.html :www/index.html
venv/Scripts/python.exe -m mpremote cp src/www/snake.html :www/snake.html
venv/Scripts/python.exe -m mpremote cp src/www/message.html :www/message.html
venv/Scripts/python.exe -m mpremote cp src/www/morse.html :www/morse.html

# Reiniciar
venv/Scripts/python.exe -m mpremote reset
```

---

## Referências

- **Plano WebREPL**: `C:\Users\bruno\.claude\plans\tidy-nibbling-biscuit.md`
- **Summary anterior**: Contexto completo no início da conversa
- **Git log**: `a1b30bf add morse code and word print on display while morse code is under emission`

---

## Notas Importantes

1. **WebREPL desabilitado por padrão** - Evita conflito com HTTP server asyncio loop
2. **High score autoritativo** - Sempre usa servidor como source of truth
3. **Idempotência** - Backend verifica duplicatas, frontend desabilita botão
4. **Mobile-first** - Todos componentes responsivos
5. **Neobrutalism** - Bordas grossas, cores vibrantes, sombras duras
6. **Display 128x64 landscape** - Configuração padrão restaurada

---

**Status**: Plano completo de reimplementação pronto para execução ✅
