// ArduCAM Mini demo (C) 2016 Lee, modified 2022 King
// web: http://www.ArduCAM.com

// This program requires the ArduCAM V4.0.0 (or later) library and ArduCAM ESP8266 5MP camera
// and use Arduino IDE 1.5.8 compiler or above
#include <ESP8266WiFi.h>
#include <WiFiClient.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>

#include <Wire.h>
#include <ArduCAM.h>
#include <SPI.h>
#include "memorysaver.h"

// includes AP SSID, gateway and static IP addresses
#include "headers/myap.h"

#if !(defined ESP8266)
  #error Please select the ArduCAM ESP8266 UNO board in the Tools/Board
#endif

// This demo can only work on OV5642_MINI_5MP or OV5642_MINI_5MP_BIT_ROTATION_FIXED
// or OV5640_MINI_5MP_PLUS or ARDUCAM_SHIELD_V2 platform.
#if !(defined (OV5642_MINI_5MP) || defined (OV5642_MINI_5MP_BIT_ROTATION_FIXED) || defined (OV5642_MINI_5MP_PLUS) || (defined (ARDUCAM_SHIELD_V2) && defined (OV5642_CAM)))
  #error Please select the hardware platform and camera module in the ../libraries/ArduCAM/memorysaver.h file
#endif

// set GPIO16 as the slave select:
const int CS = 16;

ESP8266WebServer server(80);
ArduCAM myCAM(OV5642, CS);

void start_capture() {
  myCAM.clear_fifo_flag();
  myCAM.start_capture();
}

void camCapture(ArduCAM myCAM) {
  WiFiClient client = server.client();
  
  size_t len = myCAM.read_fifo_length();
  
  if (len >= MAX_FIFO_SIZE) {
    Serial.println("Over size.");
    return;
  } 
  else if (len == 0 ) {
    Serial.println("Size is 0.");
    return;
  }
  
  myCAM.CS_LOW();
  myCAM.set_fifo_burst();
  
  #if !(defined (OV5642_MINI_5MP_PLUS) ||(defined (ARDUCAM_SHIELD_V2) && defined (OV5642_CAM)))
    SPI.transfer(0xFF);
  #endif
  
  if (!client.connected()) 
    return;

  String response = "HTTP/1.1 200 OK\r\n";
  response += "Content-Type: image/jpeg\r\n";
  response += "Content-Length: " + String(len) + "\r\n\r\n";
  server.sendContent(response);
  static const size_t bufferSize = 4096;
  static uint8_t buffer[bufferSize] = {0xFF};
  while (len) {
      size_t will_copy = (len < bufferSize) ? len : bufferSize;
      myCAM.transferBytes(&buffer[0], &buffer[0], will_copy);
      
      if (!client.connected()) 
        break;
      
      client.write(&buffer[0], will_copy);
      len -= will_copy;
  }
  
  myCAM.CS_HIGH();
}

void serverCapture() {
  if (server.hasArg("resolution")) {
    int resolution = server.arg("resolution").toInt();

    if (resolution < 0 || resolution > 6) {
      Serial.println("Invalid resolution given (" + server.arg("resolution") +"), ignorning");
    }
    else {
      myCAM.OV5642_set_JPEG_size(resolution);
      delay(1000);
      Serial.println("Capture resolution set to: " + server.arg("resolution"));
    }
  }
  
  start_capture();
  Serial.println("CAM Capturing");

  int total_time = 0;
  total_time = millis();
  while (!myCAM.get_bit(ARDUCHIP_TRIG, CAP_DONE_MASK));
  total_time = millis() - total_time;
  Serial.print("capture total_time used (in miliseconds):");
  Serial.println(total_time, DEC);
  total_time = 0;
  Serial.println("CAM Capture Done!");
  total_time = millis();
  camCapture(myCAM);
  total_time = millis() - total_time;
  Serial.print("send total_time used (in miliseconds):");
  Serial.println(total_time, DEC);
  Serial.println("CAM send Done!");
}

void handleNotFound() {
  String message = "Server is running!\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET)?"GET":"POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";
  server.send(200, "text/plain", message);
}

void connectToAP() {
  Serial.println("Attempting connection to WiFi AP.");
  
  if (!strcmp(AP_SSID, "SSID")) {
    Serial.println("Please set your SSID");
    while(1);
  }
  if (!strcmp(AP_PASS, "PASSWORD")) {
   Serial.println("Please set your PASSWORD");
   while(1);
  }

  // Configures static IP address
  if (!WiFi.config(local_IP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("Failed to set static IP.");
  }
  else {
    Serial.println("Set static IP.");
  }
 
  // Connect to WiFi network
  Serial.print("Connecting to ");
  Serial.println(AP_SSID);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(AP_SSID, AP_PASS);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println(" WiFi connected.");
  Serial.println("My IP address:");
  Serial.println(WiFi.localIP());
}

void setup() {
  uint8_t vid, pid;
  uint8_t temp;
  
  #if defined(__SAM3X8E__)
    Wire1.begin();
  #else
    Wire.begin();
  #endif
  
  Serial.begin(115200);

  connectToAP();

  // Start the server
  server.on("/capture", HTTP_GET, serverCapture);
  server.onNotFound(handleNotFound);
  server.begin();
  Serial.println("HTTP server started.");

  Serial.println("Initializing SPI to ArduCAM");

  // set the CS as an output:
  pinMode(CS, OUTPUT);

  // initialize SPI:
  SPI.begin();
  SPI.setFrequency(4000000); // 4MHz

  // Check if the ArduCAM SPI bus is OK
  myCAM.write_reg(ARDUCHIP_TEST1, 0x55);
  temp = myCAM.read_reg(ARDUCHIP_TEST1);
  
  if (temp != 0x55) {
    Serial.println("SPI1 interface Error!");
    while(1);
  }
  
  // Check if the camera module type is OV5642
  myCAM.wrSensorReg16_8(0xff, 0x01);
  myCAM.rdSensorReg16_8(OV5642_CHIPID_HIGH, &vid);
  myCAM.rdSensorReg16_8(OV5642_CHIPID_LOW, &pid);
  
  if ((vid != 0x56) || (pid != 0x42)) {
    Serial.println("Can't find OV5642 module!");
    while(1);
  }
  else
    Serial.println("OV5642 detected.");
 
  // Change to JPEG capture mode and initialize the OV5642 module
  myCAM.set_format(JPEG);
  myCAM.InitCAM();
  myCAM.write_reg(ARDUCHIP_TIM, VSYNC_LEVEL_MASK);   // VSYNC is active HIGH
  myCAM.OV5642_set_JPEG_size(OV5642_1024x768);
  delay(1000);
}

void loop() {
  server.handleClient();
}