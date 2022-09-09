![pothos plant](pothos.jpg)
# pothos
This repo contains code for three separate applications that work together to generate and [upload daily timelapses](http://pothos.evanking.io) of my pothos plant. Here's what they are and how they work in brief.

## /esp8266/
This is an embedded application running on a NodeMCU ESP8266 WiFi chip with an Arducam 5MP camera attached via SPI. It runs an HTTP server that takes a picture of the plant whenever it receives a request.

## /flask/
This is a Flask app served via Passenger. It accepts password-protected uploads that meet a narrow set of requirements, maintains an archive of all past timelapses, and serves the latest timelapse to visitors.

## /pi/
These are Python scripts running on Raspberry Pi and invoked via cron jobs. One captures images by issuing requests to both the ESP8266, a few Hue smart lights (for consistent exposure), and a temperature/light level sensor. The other prepares the images with some cropping, color balancing, and a call to ffmpeg to roll them up into a nice mp4 file before uploading.
