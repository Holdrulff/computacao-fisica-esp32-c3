# ESP32-C3 Deployment Guide

## Current Status

### Message.html Endpoint Fix

The `/www/message.html` endpoint was showing an error message:
```json
{"error": "Display feature has been removed", "message": "OLED display is no longer available"}
```

**This error is from old code.** The issue was fixed in commit `a6cc3f5` where the `message_handler` in `src/web/routes.py` was restored with proper display availability checking.

**If you're still seeing this error**, your ESP32-C3 device is running an older version of the code from commit `d98d9fd`. You need to deploy the latest code.

## Deployment Methods

### Method 1: Using deploy.py (Recommended)

```bash
# Auto-detect port and deploy
python deploy.py

# Or specify port explicitly
python deploy.py COM3  # Windows
python deploy.py /dev/ttyUSB0  # Linux
python deploy.py /dev/tty.usbserial-*  # macOS
```

The deploy script will:
1. Auto-detect your ESP32-C3 device
2. Copy all files from `src/` to the device
3. Restart the device
4. Verify deployment

### Method 2: Using deploy.sh

```bash
# Make executable (first time only)
chmod +x deploy.sh

# Deploy
./deploy.sh
```

### Method 3: Using mpremote directly

```bash
# Install mpremote if not already installed
pip install mpremote

# Deploy all files
python -m mpremote cp -r src/* :

# Or deploy specific files
python -m mpremote cp src/web/routes.py :web/routes.py
python -m mpremote cp src/www/index.html :www/index.html

# Soft reset the device
python -m mpremote soft-reset
```

### Method 4: Using Thonny IDE

1. Open Thonny IDE
2. Connect to ESP32-C3 (bottom right: Select interpreter)
3. Navigate to `src/` folder in local filesystem
4. Right-click files → Upload to /
5. Reset device: Tools → Restart backend

## Verification Steps

### 1. Check Device is Running Latest Code

```bash
# Connect to device REPL
python -m mpremote

# Or use screen (Linux/macOS)
screen /dev/ttyUSB0 115200

# Check for updated message_handler in routes.py
# The handler should check display.is_available, not return 410 error
```

### 2. Test Message Endpoint

```bash
# Test via curl
curl http://dv01.local:5000/message?text=Hello

# Expected successful response:
{
    "success": true,
    "message": "Hello",
    "displayed": true
}

# If display hardware is unavailable (but code is correct):
{
    "success": false,
    "message": "Hello",
    "displayed": false,
    "error": "Display unavailable"
}
# HTTP Status: 503 Service Unavailable

# OLD ERROR (means device has old code):
{
    "error": "Display feature has been removed",
    "message": "OLED display is no longer available"
}
# HTTP Status: 410 Gone
```

### 3. Test Message.html Interface

1. Open browser to `http://dv01.local:5000/www/message.html`
2. Should see message panel UI (not error message)
3. Type a test message and click "Send Message"
4. Should get success response
5. If display hardware is connected, text appears on OLED

### 4. Check Web Interface

Visit `http://dv01.local:5000/` and verify:
- [ ] Page loads without errors
- [ ] LED Control card shows 3 items: LED ON, LED OFF, BLINK
- [ ] Display OLED card shows: Message Panel, Morse Code
- [ ] Animated background circles moving right
- [ ] All buttons/links functional

## Troubleshooting

### Error: 410 Gone - "Display feature has been removed"

**Cause**: Device is running old code from commit d98d9fd

**Solution**:
1. Deploy latest code using Method 1 or 2 above
2. Verify deployment with curl test
3. Hard refresh browser (Ctrl+F5)

### Error: 503 Service Unavailable - "Display unavailable"

**Cause**: Code is correct, but display hardware not detected

**Solutions**:
- Check I2C connections (SCL=GPIO6, SDA=GPIO5)
- Verify SSD1306 OLED is powered (3.3V, GND)
- Check I2C address is 0x3C
- Run I2C scan in REPL to detect devices
- Display functionality is optional - other features still work

### Browser Shows Old Version

**Cause**: Browser cache

**Solutions**:
- Hard refresh: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (macOS)
- Clear browser cache
- Add cache-busting parameter: `?v=123` or `?nocache=timestamp`
- Incognito/Private browsing mode

### Device Not Found / Port Detection Fails

**Solutions**:
1. Check USB connection
2. Install CP210x drivers (ESP32-C3 USB-to-UART)
3. Check device manager (Windows) or `ls /dev/tty*` (Linux/macOS)
4. Try different USB cable (data cable, not power-only)
5. Specify port manually: `python deploy.py COM3`

### Deploy Fails - Permission Denied

**Solutions**:
- Close other serial connections (Arduino IDE, Thonny, PuTTY, screen)
- Run as administrator (Windows) or use `sudo` (Linux)
- Check user is in `dialout` group (Linux): `sudo usermod -a -G dialout $USER`

### Deploy Succeeds but Changes Not Visible

**Solutions**:
1. Verify files were actually uploaded:
   ```bash
   python -m mpremote ls :web/
   python -m mpremote cat :web/routes.py
   ```
2. Soft reset device:
   ```bash
   python -m mpremote soft-reset
   ```
3. Hard reset: Press physical RESET button on ESP32-C3
4. Power cycle: Unplug and replug USB

## Testing Checklist

After deployment, verify all features work:

### Core Functionality
- [ ] Device boots and connects to WiFi
- [ ] Web server accessible at `http://dv01.local:5000/`
- [ ] Health endpoint works: `/health`

### LED Control
- [ ] LED ON button works
- [ ] LED OFF button works
- [ ] BLINK function works (5x default)

### Display Features
- [ ] Message endpoint: `/message?text=Test`
- [ ] Message.html page loads
- [ ] Can send messages to display (if hardware available)
- [ ] Graceful degradation if display unavailable

### Morse Code
- [ ] Accessible from Display OLED card only
- [ ] morse.html page loads
- [ ] Can send morse code text
- [ ] LED blinks in correct pattern
- [ ] Display shows progress (if available)

### Web Interface
- [ ] index.html loads with all cards
- [ ] Animated circles background works
- [ ] Responsive on mobile/tablet/desktop
- [ ] No JavaScript errors in console
- [ ] All links functional

### Games (if applicable)
- [ ] Snake game works
- [ ] Tic-tac-toe game works
- [ ] Leaderboards functional

## Quick Deploy Command Reference

```bash
# Full deployment with verification
python deploy.py && curl http://dv01.local:5000/message?text=DeployTest

# Deploy and watch logs
python deploy.py && python -m mpremote

# Deploy specific files only
python -m mpremote cp src/web/routes.py :web/routes.py
python -m mpremote cp src/www/index.html :www/index.html
python -m mpremote soft-reset

# Check what's on device
python -m mpremote ls :
python -m mpremote ls :web/
python -m mpremote ls :www/

# Read file from device
python -m mpremote cat :web/routes.py | head -50
```

## Network Configuration

Device hostname: `dv01.local` (mDNS)

If mDNS doesn't work:
1. Find IP address in serial logs during boot
2. Or check router DHCP leases
3. Or connect via serial and run: `import network; print(network.WLAN(network.STA_IF).ifconfig())`
4. Access via IP: `http://192.168.1.xxx:5000/`

## Support

If issues persist:
1. Check serial logs during boot for errors
2. Verify MicroPython version compatibility
3. Check free memory: `import gc; gc.collect(); gc.mem_free()`
4. Review commit history for recent changes
5. Check [README.md](README.md) for additional documentation
