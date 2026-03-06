"""
HTTP route handlers for the web server.
"""
from microdot import send_file
from core.logger import get_logger

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
        network_info = self.wifi_manager.get_network_info()

        health_data = {
            'status': 'healthy',
            'hostname': self.hostname,
            'network': network_info,
            'hardware': {
                'led': {
                    'available': True,
                    'state': 'on' if self.led.is_on else 'off'
                },
                'display': {
                    'available': self.display.is_available
                }
            }
        }

        return health_data

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

    # Display control
    async def message_handler(self, request):
        """
        Handle display messages - GET or SET.

        GET without params: Returns current message
        - GET /message → {"message": "current text"}

        GET/POST with text: Sets new message
        - GET /message?text=Hello → Sets and displays "Hello"
        - POST /message with {"text": "Hello"} → Sets and displays "Hello"

        Returns:
            JSON with message and status
        """
        # Try JSON body first (POST), then query param (GET)
        text = None
        try:
            if request.json:
                text = request.json.get('text')
        except:
            pass

        if text is None:
            text = request.args.get('text', None)

        # If no text parameter, return current message (GET without params)
        if text is None:
            return {'message': self.last_message}

        # Set new message
        self.last_message = text

        if self.display.is_available:
            self.display.show_message(text)
            logger.info(f"Displayed message via HTTP: {text}")
            return {'message': text, 'displayed': True}
        else:
            logger.warning(f"Display unavailable, message not shown: {text}")
            return {'message': text, 'displayed': False, 'reason': 'Display not available'}
