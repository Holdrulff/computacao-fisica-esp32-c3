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

        # LED control
        self.app.route('/led')(self.handlers.get_led_status)
        self.app.route('/led/on')(self.handlers.led_on)
        self.app.route('/led/off')(self.handlers.led_off)
        self.app.route('/led/toggle')(self.handlers.led_toggle)
        self.app.route('/led/blink')(self.handlers.led_blink)

        # Morse code
        self.app.route('/morse')(self.handlers.morse_blink)

        # Display control (pragmatic approach - accepts GET for browser testing)
        self.app.get('/message')(self.handlers.message_handler)   # GET reads or sets message
        self.app.post('/message')(self.handlers.message_handler)  # POST sets message

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
