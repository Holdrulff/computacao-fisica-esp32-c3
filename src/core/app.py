"""
Main application class that orchestrates all components.
"""
import asyncio
import gc
from core.logger import get_logger, LogLevel
from hardware.led import LED
from hardware.display import Display
from net_manager.wifi_manager import WiFiManager
from web.server import WebServer
import constants

class Application:
    """
    Main application class with dependency injection pattern.

    Orchestrates hardware initialization, network connectivity,
    and web server startup.
    """

    def __init__(self, wifi_ssid: str, wifi_password: str, hostname: str):
        """
        Initialize application with configuration.

        Args:
            wifi_ssid: WiFi network SSID
            wifi_password: WiFi password
            hostname: Device hostname
        """
        self.logger = get_logger('App', LogLevel.INFO)
        self.logger.info("=== ESP32-C3 Application Starting ===")

        # Configuration
        self.wifi_ssid = wifi_ssid
        self.wifi_password = wifi_password
        self.hostname = hostname

        # Components (initialized in setup)
        self.led = None
        self.display = None
        self.wifi_manager = None
        self.web_server = None

    def _initialize_hardware(self):
        """Initialize hardware components (LED and Display)."""
        self.logger.info("Initializing hardware...")

        # Initialize LED with inverted flag for active-low hardware
        self.led = LED(constants.LED_PIN, inverted=constants.LED_INVERTED)

        # Initialize Display
        self.display = Display(
            constants.DISPLAY_I2C_SCL_PIN,
            constants.DISPLAY_I2C_SDA_PIN,
            constants.DISPLAY_I2C_ADDR
        )

        self.logger.info("Hardware initialization complete")

    def _initialize_network(self) -> bool:
        """
        Initialize network connectivity.

        Returns:
            True if connected, False otherwise
        """
        self.logger.info("Initializing network...")

        self.wifi_manager = WiFiManager(
            self.wifi_ssid,
            self.wifi_password,
            self.hostname
        )

        # Connect with LED feedback
        connected = self.wifi_manager.connect(led=self.led)

        if connected:
            self.logger.info("Network initialization complete")
            # Show status on display
            if self.display and self.display.is_available:
                ip = self.wifi_manager.get_ip_address()
                self.display.show_status(self.hostname, ip, constants.HTTP_PORT)
        else:
            self.logger.warning("Network initialization incomplete (may connect later)")

        return connected

    def _initialize_web_server(self):
        """Initialize web server with route handlers."""
        self.logger.info("Initializing web server...")

        self.web_server = WebServer(
            self.led,
            self.display,
            self.wifi_manager,
            self.hostname
        )

        self.logger.info("Web server initialization complete")

    def setup(self):
        """
        Setup phase: initialize all components.

        This method initializes hardware, connects to WiFi,
        and prepares the web server.
        """
        try:
            self._initialize_hardware()
            connected = self._initialize_network()
            self._initialize_web_server()

            if connected:
                self.led.off()  # Indicate successful setup

            self.logger.info("=== Application Setup Complete ===")

        except Exception as e:
            self.logger.critical(f"Setup failed: {e}")
            raise

    async def run(self):
        """
        Main application loop.

        Runs web server and async REPL concurrently.
        """
        self.logger.info("Starting application tasks...")

        try:
            # Import aiorepl here (only when running)
            import aiorepl

            # Create concurrent tasks
            web_server_task = asyncio.create_task(self.web_server.start())
            repl_task = asyncio.create_task(aiorepl.task())

            self.logger.info("Web server and REPL started")
            self.logger.info(f"Access web interface at: http://{self.hostname}.local:{constants.HTTP_PORT}")

            if self.wifi_manager.is_connected():
                ip = self.wifi_manager.get_ip_address()
                self.logger.info(f"Or access via IP: http://{ip}:{constants.HTTP_PORT}")

            # Run both tasks concurrently
            await asyncio.gather(repl_task, web_server_task)

        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
        finally:
            self.logger.info("Application shutting down")

    def start(self):
        """
        Start the application.

        Performs setup and then runs the async event loop.
        """
        # Trigger GC before starting server
        gc.collect()
        try:
            mem_free = gc.mem_free()
            self.logger.info(f"Memory before start: {mem_free} bytes free")
        except AttributeError:
            self.logger.info("Memory monitoring not available on this platform")

        self.setup()
        asyncio.run(self.run())
