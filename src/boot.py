# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

# Note: User code should not be placed in boot.py
# See: https://docs.micropython.org/en/latest/reference/reset_boot.html#id4
# Use main.py for application startup instead