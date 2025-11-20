/*
 * ESP32 Robotic Arm Controller Firmware
 * 
 * This firmware receives commands from Python controllers (PoseController.py, KeyboardController.py)
 * Supports JSON protocol for servo control.
 * 
 * DATA FLOW:
 * Python Controller → TCP (192.168.4.1:8000) → ESP32 → Servos
 * 
 * PROTOCOL (JSON):
 * - Receives JSON commands: {"type": "servo", "servo1": angle, "servo2": angle, "servo3": angle, "servo4": angle}
 * - servo1: Base left/right (0-180 degrees)
 * - servo2: Forward/backward (0-180 degrees)
 * - servo3: Up/down (0-180 degrees)
 * - servo4: Grip open/close (0-180 degrees)
 * 
 * SERVO MAPPING:
 * - servo1 → Base (left/right rotation) - Channel 0
 * - servo2 → Shoulder (forward/backward motion) - Channel 1
 * - servo3 → Elbow (up/down motion) - Channel 2
 * - servo4 → Claw/Gripper (open/close) - Channel 3
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiAP.h>

// Servo pin configuration - EDIT THESE PINS AS NEEDED
// These pins connect to the 4 servos: base, shoulder, elbow, claw
const int SERVO_PINS[4] = {14, 12, 13, 15};  // Pins for servo 0, 1, 2, 3

// PWM configuration for LEDC
const int PWM_FREQ = 50;  // 50Hz for standard servos
const int PWM_RESOLUTION = 16;  // 16-bit resolution
const int SERVO_CHANNELS[4] = {0, 1, 2, 3};  // LEDC channels for each servo

// Duty cycle limits - TUNE THESE FOR YOUR SERVOS (min=40, max=115 as default)
const int minDuty = 40;   // Minimum duty cycle (0 degrees)
const int maxDuty = 115;  // Maximum duty cycle (180 degrees)

// WiFi AP configuration
const char* AP_SSID = "ESP32_AP";
const char* AP_PASSWORD = "12345678";

// TCP server configuration - Changed to port 8000 for JSON protocol
WiFiServer server(8000);

// Function to set servo angle
void setServoAngle(int channel, int angle) {
  if (channel < 0 || channel >= 4) {
    return;
  }
  
  // Clamp angle to 0-180 range
  angle = constrain(angle, 0, 180);
  
  // Map angle (0-180) to duty cycle (minDuty-maxDuty)
  int duty = map(angle, 0, 180, minDuty, maxDuty);
  
  // Convert to LEDC duty value (0-65535 for 16-bit)
  uint32_t dutyValue = map(duty, 0, 255, 0, 65535);
  
  // Set duty cycle
  ledcWrite(SERVO_CHANNELS[channel], dutyValue);
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Initialize LEDC channels for servos
  for (int i = 0; i < 4; i++) {
    ledcSetup(SERVO_CHANNELS[i], PWM_FREQ, PWM_RESOLUTION);
    ledcAttachPin(SERVO_PINS[i], SERVO_CHANNELS[i]);
    ledcWrite(SERVO_CHANNELS[i], 0);  // Initialize to 0
  }
  
  // Start WiFi AP mode
  Serial.println("Starting AP mode...");
  bool ap_started = WiFi.softAP(AP_SSID, AP_PASSWORD);
  
  if (ap_started) {
    IPAddress IP = WiFi.softAPIP();
    Serial.print("AP IP address: ");
    Serial.println(IP);
  } else {
    Serial.println("Failed to start AP!");
    return;
  }
  
  // Start TCP server
  server.begin();
  Serial.println("TCP server started on port 8000");
  Serial.println("Waiting for JSON commands: {\"type\":\"servo\",\"servo1\":angle,\"servo2\":angle,\"servo3\":angle,\"servo4\":angle}");
}

// Simple JSON parser to extract servo values
// Parses: {"type":"servo","servo1":90,"servo2":90,"servo3":90,"servo4":90}
bool parseJSONCommand(String json, int& servo1, int& servo2, int& servo3, int& servo4) {
  servo1 = servo2 = servo3 = servo4 = -1;
  
  // Find servo values in JSON string
  int idx1 = json.indexOf("\"servo1\":");
  int idx2 = json.indexOf("\"servo2\":");
  int idx3 = json.indexOf("\"servo3\":");
  int idx4 = json.indexOf("\"servo4\":");
  
  if (idx1 >= 0) {
    int start = idx1 + 9; // After "servo1":
    int end = json.indexOf(',', start);
    if (end < 0) end = json.indexOf('}', start);
    if (end > start) {
      servo1 = json.substring(start, end).toInt();
    }
  }
  
  if (idx2 >= 0) {
    int start = idx2 + 9;
    int end = json.indexOf(',', start);
    if (end < 0) end = json.indexOf('}', start);
    if (end > start) {
      servo2 = json.substring(start, end).toInt();
    }
  }
  
  if (idx3 >= 0) {
    int start = idx3 + 9;
    int end = json.indexOf(',', start);
    if (end < 0) end = json.indexOf('}', start);
    if (end > start) {
      servo3 = json.substring(start, end).toInt();
    }
  }
  
  if (idx4 >= 0) {
    int start = idx4 + 9;
    int end = json.indexOf(',', start);
    if (end < 0) end = json.indexOf('}', start);
    if (end > start) {
      servo4 = json.substring(start, end).toInt();
    }
  }
  
  return (servo1 >= 0 || servo2 >= 0 || servo3 >= 0 || servo4 >= 0);
}

void loop() {
  // Check for incoming client connections
  WiFiClient client = server.available();
  
  if (client) {
    Serial.println("Client connected");
    
    String buffer = "";
    unsigned long lastDataTime = millis();
    const unsigned long TIMEOUT = 5000; // 5 second timeout
    
    while (client.connected()) {
      // Check for timeout
      if (millis() - lastDataTime > TIMEOUT) {
        Serial.println("Connection timeout");
        break;
      }
      
      // Read available data
      while (client.available() > 0) {
        char c = client.read();
        lastDataTime = millis();
        
        if (c == '\n' || c == '\r') {
          // End of command, process JSON
          if (buffer.length() > 0) {
            buffer.trim();
            
            // Check if it's a servo command
            if (buffer.indexOf("\"type\":\"servo\"") >= 0 || buffer.indexOf("\"type\": \"servo\"") >= 0) {
              int servo1, servo2, servo3, servo4;
              
              if (parseJSONCommand(buffer, servo1, servo2, servo3, servo4)) {
                // Update servos with new angles
                if (servo1 >= 0) {
                  setServoAngle(0, servo1); // Base
                  Serial.print("Servo1 (Base): ");
                  Serial.println(servo1);
                }
                if (servo2 >= 0) {
                  setServoAngle(1, servo2); // Shoulder
                  Serial.print("Servo2 (Shoulder): ");
                  Serial.println(servo2);
                }
                if (servo3 >= 0) {
                  setServoAngle(2, servo3); // Elbow
                  Serial.print("Servo3 (Elbow): ");
                  Serial.println(servo3);
                }
                if (servo4 >= 0) {
                  setServoAngle(3, servo4); // Claw
                  Serial.print("Servo4 (Claw): ");
                  Serial.println(servo4);
                }
              } else {
                Serial.println("ERROR: Failed to parse JSON command");
              }
            }
            
            buffer = ""; // Clear buffer for next command
          }
        } else if (c >= 32) { // Printable character
          buffer += c;
          // Prevent buffer overflow
          if (buffer.length() > 512) {
            buffer = "";
            Serial.println("ERROR: Buffer overflow");
          }
        }
      }
      
      delay(10); // Small delay to prevent CPU spinning
    }
    
    Serial.println("Client disconnected");
    client.stop();
  }
  
  delay(10);  // Small delay to prevent watchdog issues
}
