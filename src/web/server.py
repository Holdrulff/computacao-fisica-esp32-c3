"""
Web server configuration and setup.
"""
from microdot import Microdot
from core.logger import get_logger
from web.routes import RouteHandlers
import constants

class WebServer:
    """Microdot web server with configured routes."""

    def __init__(self, led, display, wifi_manager, hostname):
        """
        Initialize web server with dependencies.

        Args:
            led: LED instance
            display: Display instance
            wifi_manager: WiFiManager instance
            hostname: Device hostname
        """
        self.logger = get_logger('WebServer')
        self.app = Microdot()
        self.handlers = RouteHandlers(led, display, wifi_manager, hostname)
        self._setup_routes()

    def _setup_routes(self):
        """Configure all HTTP routes."""
        # Static files
        self.app.route('/')(self.handlers.serve_index)
        self.app.route('/www/<path:path>')(self.handlers.serve_static)

        # API endpoints
        self.app.route('/hello')(self.handlers.hello)
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

        # I2C diagnostics
        self.app.get('/i2c/scan')(self.handlers.i2c_scan_handler)

        # Snake game leaderboard
        self.app.get('/snake/leaderboard')(self.handlers.snake_leaderboard)
        self.app.post('/snake/score')(self.handlers.snake_add_score)

        # Tic-Tac-Toe game
        self.app.get('/game/tictactoe')(self.handlers.tictactoe_game_state)
        self.app.post('/game/tictactoe/move')(self.handlers.tictactoe_make_move)
        self.app.post('/game/tictactoe/reset')(self.handlers.tictactoe_reset)
        self.app.post('/game/tictactoe/computer-move')(self.handlers.tictactoe_computer_move)

        self.logger.info("Routes configured successfully")

    async def start(self):
        """Start the web server."""
        self.logger.info(f"Starting web server on port {constants.HTTP_PORT}")
        await self.app.start_server(
            host=constants.HTTP_HOST,
            port=constants.HTTP_PORT
        )

    def get_app(self):
        """Get the Microdot application instance."""
        return self.app
