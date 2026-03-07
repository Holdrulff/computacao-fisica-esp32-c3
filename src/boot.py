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