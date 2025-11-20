# ESP32 Firmware Upload Instructions

## Problem
The ESP32 is not listening on any port, which means the firmware needs to be uploaded.

## Solution: Upload Firmware using PlatformIO

### Prerequisites
1. Install PlatformIO (if not already installed):
   - Install PlatformIO IDE extension in VS Code, OR
   - Install PlatformIO Core: https://platformio.org/install/cli

### Steps to Upload

#### Option 1: Using PlatformIO IDE (VS Code)
1. Open VS Code
2. Open the `esp_code-main` folder in VS Code
3. Connect your ESP32 to your computer via USB
4. Click on the PlatformIO icon in the left sidebar
5. Click "Upload" (→) button in the PlatformIO toolbar
6. Wait for upload to complete
7. Open Serial Monitor (plug icon) and set baud rate to 115200
8. You should see:
   ```
   Starting AP mode...
   AP IP address: 192.168.4.1
   TCP server started on port 8000
   Waiting for JSON commands...
   ```

#### Option 2: Using PlatformIO CLI
1. Open terminal/command prompt
2. Navigate to the `esp_code-main` folder:
   ```bash
   cd esp_code-main
   ```
3. Connect ESP32 via USB
4. Upload firmware:
   ```bash
   pio run --target upload
   ```
5. Monitor serial output:
   ```bash
   pio device monitor --baud 115200
   ```

### Verify Upload Success

After uploading, check Serial Monitor for:
- ✅ `AP IP address: 192.168.4.1`
- ✅ `TCP server started on port 8000`
- ✅ `Waiting for JSON commands...`

If you see errors, check:
- ESP32 is properly connected via USB
- Correct COM port is selected
- Drivers are installed for your ESP32 board

### Test Connection

After successful upload, run:
```bash
python roboCleaner/client/find_esp32_port.py
```

You should see:
```
[SUCCESS] ESP32 is listening on port 8000
```

### Troubleshooting

**Problem: Upload fails**
- Check USB cable (use data cable, not charge-only)
- Check COM port in PlatformIO
- Try pressing BOOT button on ESP32 during upload

**Problem: Server doesn't start**
- Check Serial Monitor for error messages
- Verify WiFi AP started successfully
- Check if port 8000 is already in use (unlikely)

**Problem: Still can't connect after upload**
- Make sure laptop is connected to ESP32_AP WiFi
- Run `python roboCleaner/client/test_connection.py` for diagnostics
- Check Windows Firewall isn't blocking Python

