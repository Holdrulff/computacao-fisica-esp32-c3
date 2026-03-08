# ESP32-C3 Deployment Guide

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
```

### 2. Check Web Interface

Visit `http://dv01.local:5000/` and verify:
- [ ] Page loads without errors
- [ ] LED Control card shows 3 items: LED ON, LED OFF, BLINK
- [ ] Display OLED card shows: Morse Code
- [ ] Animated background circles moving right
- [ ] All buttons/links functional

## Troubleshooting

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
python deploy.py && curl http://dv01.local:5000/hello

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
