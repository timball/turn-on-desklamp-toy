#!/usr/bin/env python
#
# Script to set lights in home assistant when osx camera turns on
#   make this an app w/ automator and have it start at startup
#
# --timball@gmail.com
#
# Mon Nov 17 21:14:27 EST 2025

import cattrs
import json
import logging
import os
import requests
import subprocess
import sys
import threading
import time
import yaml

import pprint

from dataclasses import dataclass
from datetime import datetime
from time import sleep
from typing import Dict, List, Optional

# setup some logging stuff
LOG = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)


## global variables
CAMERA_OFF = False
CAMERA_ON  = True

# read from config
class CONFIG:
    AUTH_KEY = None
    LIGHTS = list()
    SERVER = None
c = CONFIG()

@dataclass
class CameraState:
    camera: bool
    service: str
    entity: str
    method: str
    brightness: Optional[int] = 255
CAM_ST = list()

@dataclass
class LightStateConfig:
    name: str
    service: str
    entity: str
    on_level: Optional[int] = 255
    off_level: Optional[int] = 0


def debounce(wait_time):
    """
    Decorator that will postpone a function's execution until after
    'wait_time' seconds have elapsed since the last time it was invoked.
        # Example usage:
        @debounce(1)  # Debounce for 1 second
        def my_function(message):
            print(f"Function executed with: {message}")

        ## how to debounce
        # Simulate rapid calls
        my_function("Call 1")
        time.sleep(0.1)
        my_function("Call 2")
        time.sleep(0.3)
        my_function("Call 3")
        time.sleep(1.2) # Wait longer than debounce time
        my_function("Call 4")
    """
    def decorator(func):
        last_call_time = 0
        timer = None

        def debounced(*args, **kwargs):
            nonlocal last_call_time, timer

            def call_it():
                nonlocal last_call_time, timer
                last_call_time = time.time()
                timer = None
                return func(*args, **kwargs)

            current_time = time.time()
            if timer:
                timer.cancel()  # Cancel previous timer if still active

            # Schedule a new call after 'wait_time'
            timer = threading.Timer(wait_time, call_it)
            timer.start()

        return debounced
    return decorator


#@debounce
def set_LightLevel(state: bool):
    """ why do I need to put a line here? """
    LOG.debug("in set_lightLevel")
    sleep (0.8)

    base_url = ''
    payload = dict()
    headers = {
      'Content-Type': 'application/json',
      'Authorization': f"Bearer {c.AUTH_KEY}"
    }

    for l in CAM_ST:
        if l.camera == state:
            base_url = f"http://{c.SERVER}/api/services/{l.service}/{l.method}"
            payload = {"entity_id": f"{l.service}.{l.entity}"}
            if l.service == "light":
                payload['brightness'] = f"{l.brightness}"
            LOG.debug(base_url)
            LOG.debug(payload)
            LOG.debug(headers)
            resp = requests.request("POST", base_url, headers=headers, data=json.dumps(payload))
    return True


def watch_camera_state():
    """
    okay here's what we have to do:
    1. Use subprocess.Popen to read `log` command output
        a. Buffering:
            If you need truly unbuffered output (byte-by-byte), you might need to set bufsize=0 and read using process.stdout.read(1). For line-buffered output, bufsize=1 and text=True is often sufficient.
    2. Use requests to send request to endpoint
    """

    cmd = r"log stream --predicate"
    arg = r'subsystem == "com.apple.UVCExtension" and composedMessage contains "Post PowerLog"'
    cmd_list = cmd.split()
    cmd_list.append(arg)

    # Set PYTHONUNBUFFERED=1 to potentially unbuffer output from Python child processes
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'

    process = subprocess.Popen(
        cmd_list,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1, # Line-buffered output
        env=env
    )

    LOG.info("Monitoring Camera State")
    while True:
        output_line = process.stdout.readline()
        if output_line == '' and process.poll() is not None:
            break
        if "VDCAssistant_Power_State" in output_line:
            if "Off" in output_line:
                # send the off camera state
                set_LightLevel(CAMERA_OFF)
            elif "On" in output_line:
                # send the on camera state
                set_LightLevel(CAMERA_ON)
            else:
                LOG.warning(f"state is unknown: {outputline}")
    return True


def read_configs():
    """ read the yaml and set the LightStateConfig
    """

    try:
        with open(sys.argv[1]) as file:
            data = yaml.safe_load(file)
    except FileNotFoundError:
        log.critical("Error: config.yaml not found.")
        os.exit(1)
    except yaml.YAMLError as exc:
        log.critical(f"Error parsing YAML file: {exc}")
        os.exit(1)

    for i in (data):
        if list(i.keys())[0] == 'hass_auth':
            c.AUTH_KEY = i['hass_auth']
            continue
        if list(i.keys())[0] == 'hass_server':
            c.SERVER = i['hass_server']
            continue
        try:
            c.LIGHTS.append(cattrs.structure(i, LightStateConfig))
        except ClassValidationError:
            log.critical("Error in config file")
            os.exit(1)
    return True


def create_CameraStates():
    """ This does stuff via globals bc I'm a bad person and idgaf
    """

    #LOG.info ("items in c.LIGHTS")
    for i in c.LIGHTS:
        if i.service == "light":
            #LOG.info("we have a light")
            # create on
            CAM_ST.append(CameraState(camera=CAMERA_ON, service=i.service, entity=i.entity, method="turn_on", brightness=i.on_level))
            # create off
            CAM_ST.append(CameraState(camera=CAMERA_OFF, service=i.service, entity=i.entity, method="turn_on", brightness=i.off_level))
        elif i.service == "switch":
            # create on
            CAM_ST.append(CameraState(camera=CAMERA_ON, service=i.service, entity=i.entity, method="turn_on", brightness=None))
            # create off
            CAM_ST.append(CameraState(camera=CAMERA_OFF, service=i.service, entity=i.entity, method="turn_off", brightness=None))
        else:
            LOG.warning("how did you get here?")
    return True


if __name__ ==  "__main__":
    # first import configs
    read_configs()
    LOG.debug(pprint.pformat(c.LIGHTS))
    LOG.debug(f"auth_key: {c.AUTH_KEY}")
    LOG.debug(f"server: {c.SERVER}")

    # second setup the list of CameraStates
    create_CameraStates()
    LOG.debug(pprint.pformat(CAM_ST))

    LOG.debug("---- simulate camera off")
    #set_LightLevel(False)

    #LOG.info("---- simulate camera on")
    #set_LightLevel(True)

    # third watch the camera state and activate lights
    watch_camera_state()

