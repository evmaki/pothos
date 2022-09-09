import requests
import shutil
from datetime import datetime
import time
import json
import logging

from os import path

# contains API keys, IP addresses, etc.
import settings

# absolute path (refer to everything from abs path so it works in a cron job)
abs_path = path.abspath(path.dirname(__file__))

cam_ip = settings.CAMERA_IP
hue_ip = settings.HUE_IP
hue_username = settings.HUE_USERNAME

def capture_image(resolution, output_name):
    """ Captures an image of the given resolution from the esp8266 cam and 
    saves it to a file with the given name.

    Resolutions:
        0 "320x240"
        1 "640x480"
        2 "1024x768"
        3 "1280x960"
        4 "1600x1200"
        5 "2048x1536"
        6 "2592x1944"
    """
    response = requests.get(f'http://{cam_ip}/capture?resolution={resolution}', stream=True)

    output_path = f'{abs_path}/frames/{output_name}.jpg'

    with open(output_path, 'wb') as out_file:
        logging.info(f'capture_image: saving image to to {output_path}')
        shutil.copyfileobj(response.raw, out_file)
    del response

def get_sensor_state(sensor_id):
    logging.debug(f'get_sensor_state: {sensor_id}')
    r = requests.get(f'http://{hue_ip}/api/{hue_username}/sensors/{sensor_id}')
    logging.debug(f'get_sensor_state: {r}')

    return r.json()

def set_light_state(light_id, state):
    logging.debug(f'set_light_state: light_id = {light_id}, state = {state}')
    r = requests.put(f'http://{hue_ip}/api/{hue_username}/lights/{light_id}/state', json=state)
    logging.debug(f'set_light_state: {r}')

def get_light_state(light_id):
    logging.debug(f'get_light_state: {light_id}')
    r = requests.get(f'http://{hue_ip}/api/{hue_username}/lights/{light_id}')
    logging.debug(f'get_light_state: {r}')

    return r.json()

def log_sensor_state(t, state):
    output_path = f'{abs_path}/data.json'

    # the new entry to add to the log
    entry = {f'{t}': state}

    # create the file if it doesn't exist and dump the json
    if not path.exists(output_path):
        with open(output_path, 'w') as f:
            json.dump(entry, f)
    else:
        logging.info(f'log_sensor_state: logging sensor state to {output_path}')

        # load up the existing json so we can update it
        with open(output_path) as f:
            data = json.load(f)

        # update the json with the new state
        data.update(entry)

        # write the updated json to the file
        with open(output_path, 'w') as f:
            json.dump(data, f)

logging.basicConfig(level=logging.INFO)

now = datetime.now().strftime('%m-%d-%Y_%H:%M')

clamp_lamp = 4
plant_lamp = 5

light_sensor = 14
temp_sensor = 15

# gather the sensor info before messing with the lights
lightlevel = get_sensor_state(light_sensor)['state']['lightlevel']
temperature = get_sensor_state(temp_sensor)['state']['temperature']

# log the sensor state in the json file
log_sensor_state(now, {
    'lightlevel': lightlevel,
    'temperature': temperature
})

# see if the clamp lamp is on and turn it off if so (cleans up the shot)
clamp_lamp_on = get_light_state(clamp_lamp)['state']['on']

if clamp_lamp_on:
    set_light_state(clamp_lamp, {'on': False})

# turn on the overhead pothos lamp
set_light_state(plant_lamp, {'bri': 250, 'ct': 300, 'on': True})

# wait for it to fade on
time.sleep(1)

# take a picture
capture_image(3, now)

# wait for the picture to finish capturing
time.sleep(2)

# turn off the overhead lamp
set_light_state(plant_lamp, {'on': False})

# if the clamp lamp was on, turn it back on
if clamp_lamp_on:
    set_light_state(clamp_lamp, {'on': True})