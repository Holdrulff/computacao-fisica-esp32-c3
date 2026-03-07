"""
HTTP route handlers for the web server.
"""
from microdot import send_file
from core.logger import get_logger
from hardware.morse import MorseEncoder
import asyncio
import gc

logger = get_logger('Routes')

class RouteHandlers:
    """Collection of HTTP route handlers with dependency injection."""

    def __init__(self, led, display, wifi_manager, hostname):
        """
        Initialize route handlers with dependencies.

        Args:
            led: LED instance for control
            display: Display instance for messages
            wifi_manager: WiFiManager instance for network info
            hostname: Device hostname
        """
        self.led = led
        self.display = display
        self.wifi_manager = wifi_manager
        self.hostname = hostname
        self.last_message = None

        # Request counter for periodic GC
        self._request_count = 0

        # Cache static health data to avoid creating dict on every request
        self._static_health = {
            'hostname': self.hostname,
            'hardware': {'led': 'Built-in GPIO8'}
        }

    # Static files
    async def serve_index(self, request):
        """Serve main index page."""
        return send_file('www/index.html')

    async def serve_static(self, request, path):
        """
        Serve static files from www directory.

        Args:
            request: HTTP request object
            path: Requested file path
        """
        if '..' in path:
            logger.warning(f"Directory traversal attempt blocked: {path}")
            return {'error': 'Not found'}, 404
        return send_file('www/' + path)

    # API routes
    async def hello(self, request):
        """Simple hello endpoint."""
        return {'message': f"Hello from {self.hostname}.local", 'status': 'ok'}

    async def health(self, request):
        """
        Health check endpoint with system status.

        Returns detailed system health information.
        """
        # Periodic GC every 10 requests
        self._request_count += 1
        if self._request_count % 10 == 0:
            gc.collect()
            logger.info(f"GC triggered at request #{self._request_count}")

        network_info = self.wifi_manager.get_network_info()

        # Use cached static data, only add dynamic fields
        # MicroPython doesn't support ** unpacking, use update() instead
        health_data = {
            'hostname': self.hostname,
            'status': 'healthy',
            'network': network_info,
            'hardware': {
                'led': {
                    'available': True,
                    'state': 'on' if self.led.is_on else 'off'
                }
            }
        }

        return health_data

    async def storage_info(self, request):
        """
        Get filesystem storage information.

        Returns:
            JSON with storage statistics:
            - total: Total storage in bytes
            - used: Used storage in bytes
            - free: Free storage in bytes
            - used_percent: Percentage of storage used
            - total_mb: Total storage in MB
            - used_mb: Used storage in MB
            - free_mb: Free storage in MB
        """
        import os

        # Periodic GC every 10 requests
        self._request_count += 1
        if self._request_count % 10 == 0:
            gc.collect()

        try:
            # Get filesystem statistics
            stat = os.statvfs('/')

            # Calculate sizes (in bytes)
            block_size = stat[0]  # f_bsize
            total_blocks = stat[2]  # f_blocks
            free_blocks = stat[3]  # f_bfree

            total_bytes = total_blocks * block_size
            free_bytes = free_blocks * block_size
            used_bytes = total_bytes - free_bytes

            # Calculate percentages
            used_percent = (used_bytes / total_bytes * 100) if total_bytes > 0 else 0

            # Convert to MB for readability
            total_mb = total_bytes / (1024 * 1024)
            used_mb = used_bytes / (1024 * 1024)
            free_mb = free_bytes / (1024 * 1024)

            logger.info(f"Storage: {used_mb:.2f}MB used / {total_mb:.2f}MB total ({used_percent:.1f}%)")

            return {
                'total': total_bytes,
                'used': used_bytes,
                'free': free_bytes,
                'used_percent': round(used_percent, 2),
                'total_mb': round(total_mb, 2),
                'used_mb': round(used_mb, 2),
                'free_mb': round(free_mb, 2)
            }

        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return {'error': 'Failed to get storage information'}, 500

    # LED control
    def _led_state_response(self) -> str:
        """Get LED state as string."""
        return 'on' if self.led.is_on else 'off'

    async def get_led_status(self, request):
        """Get current LED status."""
        return {'led': self._led_state_response()}

    async def led_on(self, request):
        """Turn LED on."""
        self.led.on()
        logger.info("LED turned on via HTTP request")
        return {'led': self._led_state_response()}

    async def led_off(self, request):
        """Turn LED off."""
        self.led.off()
        logger.info("LED turned off via HTTP request")
        return {'led': self._led_state_response()}

    async def led_toggle(self, request):
        """Toggle LED state."""
        self.led.toggle()
        logger.info("LED toggled via HTTP request")
        return {'led': self._led_state_response()}
    
    async def led_blink(self, request):
        """
        Blink LED multiple times (non-blocking).

        Query parameters:
            count: Number of blinks (default: 3, max: 20)
            interval: Interval between blinks in seconds (default 0.5, max: 2.0)

        example:
            GET /led/blink?count=5&interval=0.3 → Blinks LED 5 times with 0.3s interval

        Returns immediately while LED blinks in background.
        """
        try:
            count = int(request.args.get('count', 3))
            interval = float(request.args.get('interval', 0.5))
        except ValueError:
            return {'error': 'Invalid count or interval'}, 400

        count = max(1, min(count, 20))
        interval = max(0.1, min(interval, 2.0))

        logger.info(f"Starting LED blink: {count} times with {interval}s interval (non-blocking)")

        # Start blink in background, return immediately
        asyncio.create_task(self._blink_background(count, interval))

        return {
            'message': 'Blink started',
            'count': count,
            'interval': interval
        }

    async def _blink_background(self, count, interval):
        """
        Background task for LED blinking.

        Args:
            count: Number of blinks
            interval: Interval between blinks in seconds
        """
        initial_state = self.led.is_on

        for i in range(count):
            self.led.on()
            await asyncio.sleep(interval)
            self.led.off()
            await asyncio.sleep(interval)

        # Restore initial state
        if initial_state:
            self.led.on()

        logger.info(f"LED blink completed: {count} times")

    async def morse_blink(self, request):
        """
        Blink LED in Morse code.

        Query/POST parameters:
            text: Text to encode (required, max 20 chars)
            speed: Dot duration in seconds (optional, default 0.2, range 0.1-0.5)

        Examples:
            GET /morse?text=SOS
            GET /morse?text=HELP&speed=0.3
            POST /morse with {"text": "OK"}

        Returns:
            JSON with morse code and duration

        Errors:
            400 - Missing text parameter
            400 - Text too long (>20 chars)
            400 - Invalid characters
            400 - Invalid speed value
        """
        # Extract text from query params or JSON body
        text = None
        try:
            if request.json:
                text = request.json.get('text')
        except:
            pass

        if text is None:
            text = request.args.get('text', None)

        # Validate text parameter
        if not text:
            return {'error': 'Missing text parameter'}, 400

        text = text.strip()
        if len(text) > 20:
            return {'error': 'Text too long (max 20 characters)'}, 400

        # Extract and validate speed parameter
        try:
            speed = float(request.args.get('speed', 0.2))
            speed = max(0.1, min(speed, 0.5))  # Limit between 0.1 and 0.5
        except ValueError:
            return {'error': 'Invalid speed value'}, 400

        # Encode and blink
        try:
            morse_encoder = MorseEncoder(self.led, display=self.display, dot_duration=speed)
            result = await morse_encoder.blink_morse(text)

            logger.info(f"Morse code sent: {text} -> {result['morse']}")
            return result

        except ValueError as e:
            logger.warning(f"Morse encoding error: {e}")
            return {'error': str(e)}, 400
        except Exception as e:
            logger.error(f"Morse error: {e}")
            return {'error': 'Internal error'}, 500

    async def message_handler(self, request):
        """Display a message on the OLED screen."""
        try:
            text = request.args.get('text', 'Hello ESP32!')

            # Validate text length
            if len(text) > 100:
                return {'error': 'Text too long (max 100 chars)'}, 400

            if self.display and self.display.is_available:
                self.display.show_message(text)
                logger.info(f"Displayed message via HTTP: {text}")
                return {
                    'success': True,
                    'message': text,
                    'displayed': True
                }
            else:
                logger.warning(f"Display unavailable, message not shown: {text}")
                return {
                    'success': False,
                    'message': text,
                    'displayed': False,
                    'reason': 'Display hardware not detected'
                }, 503  # Service Unavailable (not 410 Gone)
        except Exception as e:
            logger.error(f"Message display error: {e}")
            return {'error': str(e)}, 500

    # Snake game leaderboard
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

    # Tic-Tac-Toe game
    async def tictactoe_game_state(self, request):
        """Get current Tic-Tac-Toe game state."""
        from games.tictactoe import get_game_state
        return get_game_state()

    async def tictactoe_make_move(self, request):
        """
        Make a move in Tic-Tac-Toe game.

        Expects JSON body:
            {
                "position": 0-8,
                "player": "X" or "O"
            }
        """
        from games.tictactoe import make_move

        # Periodic GC every 10 requests
        self._request_count += 1
        if self._request_count % 10 == 0:
            gc.collect()

        try:
            data = request.json
            position = data.get('position')
            player = data.get('player', 'X')

            if position is None:
                return {'success': False, 'error': 'Missing position'}, 400

            result = make_move(position, player)

            if not result.get('success'):
                return result, 400

            return result

        except Exception as e:
            logger.error(f"Error making move: {e}")
            return {'success': False, 'error': 'Failed to make move'}, 500

    async def tictactoe_reset(self, request):
        """Reset Tic-Tac-Toe game to initial state."""
        from games.tictactoe import reset_game
        return reset_game()

    async def tictactoe_computer_move(self, request):
        """Get and execute computer's move."""
        from games.tictactoe import get_computer_move

        try:
            result = get_computer_move()

            if not result.get('success'):
                return result, 400

            return result

        except Exception as e:
            logger.error(f"Error getting computer move: {e}")
            return {'success': False, 'error': 'Failed to get computer move'}, 500
