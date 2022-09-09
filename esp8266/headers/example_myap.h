#include <ESP8266WiFi.h>

// your access point SSID and password
#define AP_SSID ""
#define AP_PASS ""

// static IP address
IPAddress local_IP(0, 0, 0, 0);

// gateway IP address
IPAddress gateway(0, 0, 0, 0);

IPAddress subnet(0, 0, 0, 0);
IPAddress primaryDNS(0, 0, 0, 0);   // optional
IPAddress secondaryDNS(0, 0, 0, 0); // optional