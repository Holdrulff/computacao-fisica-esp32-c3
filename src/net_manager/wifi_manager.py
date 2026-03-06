"""
WiFi network management with robust error handling.
"""
import network
import time
from core.logger import get_logger
import constants

class WiFiManager:
    """Manages WiFi connectivity with automatic retry and error handling."""

    def __init__(self, ssid: str, password: str, hostname: str):
        """
        Initialize WiFi manager.

        Args:
            ssid: WiFi network SSID
            password: WiFi network password
            hostname: Device hostname
        """
        self.logger = get_logger('WiFi')
        self.ssid = ssid
        self.password = password
        self.hostname = hostname
        self._wlan = None
        self._connected = False

    def connect(self, led=None) -> bool:
        """
        Connect to WiFi network with retry logic.

        Args:
            led: Optional LED instance for visual feedback during connection

        Returns:
            True if connected successfully, False otherwise
        """
        self.logger.info(f"Connecting to WiFi network: {self.ssid}")

        try:
            # Initialize WLAN interface
            self._wlan = network.WLAN(network.STA_IF)
            self._wlan.active(True)
            self._wlan.config(hostname=self.hostname)

            # Attempt connection
            self._wlan.connect(self.ssid, self.password)

            # Retry logic with timeout
            attempts = 0
            while not self._wlan.isconnected() and attempts < constants.WIFI_MAX_RETRIES:
                if led:
                    led.on()  # Visual indicator of connection attempt

                self.logger.debug(f"Connection attempt {attempts + 1}/{constants.WIFI_MAX_RETRIES}")
                time.sleep(constants.WIFI_CONNECT_RETRY_INTERVAL_SEC)
                attempts += 1

            if self._wlan.isconnected():
                if led:
                    led.off()  # Turn off indicator when connected

                self._connected = True
                ifconfig = self._wlan.ifconfig()
                self.logger.info(f"WiFi connected successfully")
                self.logger.info(f"IP Address: {ifconfig[0]}")
                self.logger.info(f"Subnet Mask: {ifconfig[1]}")
                self.logger.info(f"Gateway: {ifconfig[2]}")
                self.logger.info(f"DNS: {ifconfig[3]}")
                return True
            else:
                self.logger.warning("Failed to connect to WiFi within timeout")
                self.logger.info("Connection may succeed in background")
                return False

        except Exception as e:
            self.logger.error(f"WiFi connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect from WiFi network."""
        if self._wlan:
            self.logger.info("Disconnecting from WiFi")
            self._wlan.disconnect()
            self._wlan.active(False)
            self._connected = False

    def is_connected(self) -> bool:
        """
        Check if currently connected to WiFi.

        Returns:
            True if connected, False otherwise
        """
        if self._wlan:
            self._connected = self._wlan.isconnected()
        return self._connected

    def get_ip_address(self) -> str:
        """
        Get current IP address.

        Returns:
            IP address string, or None if not connected
        """
        if self.is_connected():
            return self._wlan.ifconfig()[0]
        return None

    def get_network_info(self) -> dict:
        """
        Get detailed network information.

        Returns:
            Dictionary with network configuration details
        """
        if not self.is_connected():
            return {"connected": False}

        ifconfig = self._wlan.ifconfig()
        return {
            "connected": True,
            "ssid": self.ssid,
            "hostname": self.hostname,
            "ip": ifconfig[0],
            "subnet": ifconfig[1],
            "gateway": ifconfig[2],
            "dns": ifconfig[3]
        }

    def scan_networks(self) -> list:
        """
        Scan for available WiFi networks.

        Returns:
            List of tuples containing network information
        """
        if not self._wlan:
            self._wlan = network.WLAN(network.STA_IF)
            self._wlan.active(True)

        self.logger.info("Scanning for WiFi networks...")
        networks = self._wlan.scan()
        self.logger.info(f"Found {len(networks)} networks")

        return networks
