#!python3
"""
Project: My First Hue Demo
File: Hue1.py
Author: jpindar@jpindar.com
Requires: https://pypi.org/project/requests/2.7.0/

Hue API documentation is here:
https://developers.meethue.com/develop/hue-api/

some error types
201 device (light) is turned off (logically)
7   invalid value
1 unauthorized user
3 resource not available

"""

import sys
import logging
import json
import time
import argparse
import requests

___author___ = "jpindar@jpindar.com"
log_filename = 'Hue1.log'
script_name = 'Hue1.py'
# It's OK to leave the credentials here for now
# because my bridge is not accessible from outside my LAN
BAD_IP_ADDRESS = "10.0.1.99:80"
IP_ADDRESS = "10.0.1.3:80"
USERNAME = "vXBlVENNfyKjfF3s"
BAD_USERNAME = "invalid_username"

# If a light is physically on and off, you can turn it virtually on and off. But you can't set it's hue etc.
LIGHT_IS_TURNED_OFF = 201
ENABLE_LOGGING = True

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s')
if ENABLE_LOGGING:
    logger.setLevel(logging.INFO)
logger.info("Hue1 demo")


class HueError(Exception):
    """Exception raised for errors in the response from the bridge
    Attributes:
        type -- numeric type of error
        description -- explanation of the error
    """
    def __init__(self, type, description):
        self.type = type
        self.description = description


def check_response_for_error(result):
    for s in result:
        if 'error' in s:
            type = s['error']['type']
            description = (s['error']['description'])
            raise HueError(type, "error: " + description)


def request(method, url, route, **kwargs):
    try:
        response = requests.request(method, url + '/' + route, **kwargs)
        if response.status_code != requests.codes.ok:   # should be 200
            raise HueError(0, "Got bad response status from Hue Bridge")
        # response.json() can be either a dict or a list containing a dict
        # AFAIK, the list only ever has one element, but we can't be sure of that
        # so instead of stripping the dict out of the list, let's do the opposite
        r = response.json()
        if isinstance(r,dict):
            r = [r]
        return r
    except ConnectionError as e:  # doesn't happen?
        logger.error(e.args)
        raise e
    except requests.exceptions.ConnectionError as e:  # this happens when no response
        logger.error(e.args)
        raise e
    except (requests.Timeout, requests.exceptions.RequestException) as e:
        logger.error(e.args)
        raise e
    except Exception as e:
        logger.error(e.args)
        raise e


class Bridge:

    def __init__(self, ip_address, username):
        self.light_list = []
        self.scene_list = []
        self.url = "http://" + ip_address + "/api/" + username
        self.data = {}

    def get_all_data(self):
        """ Get all data from the bridge. """
        try:
            response = request("GET", self.url, '')
            check_response_for_error(response)
            self.data = response[0]
        except HueError as e:
            logger.error(e.args)
            raise e
        except Exception as e:
            logger.error(e.args)
            raise e
        return self.data

    def get_config(self):
        try:
            response = request("GET", self.url, "config")
            check_response_for_error(response)
        except HueError as e:
            logger.error(e.args)
            raise e
        except Exception as e:
            logger.error(e.args)
            raise e
        return response[0]

    def get_whitelist(self):
        """ Get the bridge's whitelist of usernames """
        config = self.get_config()
        whitelist = config['whitelist']
        return whitelist

    def delete_user(self, id):
        route = "config/whitelist/" + str(id)
        try:
            response = request("DELETE", self.url, route)
            check_response_for_error(response)
        except Exception as e:
            logger.error(e.args)
            raise e

    def get_lights(self):
        """
            Get a list of the bridge's lights.
            Note that light.index starts at 1 but list positions start at 0
        """
        try:
            response = request("GET", self.url, Light.ROUTE)
            check_response_for_error(response)
        except HueError as e:
            logger.error("Hue Error " + str(e.args))
            raise e
        r = response[0]
        self.light_list = [Light(self, i, r[str(i)]) for i in r.keys()]
        self.light_list = sorted(self.light_list, key=lambda x: x.index)
        return self.light_list

    def get_scenes(self):
        try:
            response = request("GET", self.url, Scene.ROUTE)
            check_response_for_error(response)
        except Exception as e:
            raise HueError(0, "Not able to get scene data")
        r = response[0]
        self.scene_list = [Scene(self, i, r[str(i)]) for i in r.keys()]
        self.scene_list = sorted(self.scene_list, key=lambda x: x.name)
        return self.scene_list

    def get_scene_by_name(self, desired_name):
        self.get_scenes()
        for scene in self.scene_list:
            if scene.name == desired_name:
                return scene
        return None

    def get_scene_by_id(self, desired_id):
        self.get_scenes()
        for scene in self.scene_list:
            if scene.id == desired_id:
                return scene
        return None

    def delete_scene(self, scene):
        route = Scene.ROUTE + "/" + str(scene.id)
        try:
            response = request("DELETE", self.url, route)
            check_response_for_error(response)
        except Exception as e:
            logger.error(e.args)
            raise e

    def lights(self):
        # if we were going for speed at the expense of possible
        # errors (like if a light was added or removed from the bridge) we could add this:
        # if self.light_list == {}:
        # note that physically turning a light off does not remove it from the bridge's list
        self.get_lights()
        return self.light_list


    def get_light_by_name(self, this_name):
        self.light_list = self.get_lights()
        for light in self.light_list:
            if light.name == this_name:
                return light
        return None


    def all_on(self, on):
        group = Group(self, 0)  # group 0 is all lights
        group.set('on', on)

    def set_all(self, attr, value):
        """ Set all lights
            Since you can use group 0 for all lights, this is just an example.
        """
        self.get_lights()
        for light in self.light_list:
            light.set(attr, value)


class Scene:
    ROUTE = 'scenes'

    def __init__(self, bridge, id, data = None):
        self.id = id
        self.bridge = bridge
        self.data = {}
        self.name = ""
        self.lights = []
        if data is not None:
            try:
                self.data = data
                self.name = self.data['name']
                self.lights = self.data['lights']
            except KeyError as e:
                raise HueError(0, "Not able to update scene data")
            except Exception as e:
                raise e

    def display(self):
        group = Group(self.bridge, 0)  # group 0 is all lights
        group.set("scene", self.id)

    def delete(self):
        self.bridge.delete_scene(self)
        # delete this object now?


class Group:
    """ A group of lights
        Note that Group 0 is all lights
    """

    ROUTE = 'groups'

    def __init__(self, bridge, id):
        self.id = id
        self.bridge = bridge

    def set(self, attr, value):
        route = self.ROUTE + "/" + str(self.id) + "/action"
        msg = json.dumps({attr: value})
        try:
            response = request("PUT", self.bridge.url, route, data=msg)
            #  r should be a list of dicts such as [{'success':{/lights/1/state/on':True}]
            #  1st element of 1st element == 'success'
            check_response_for_error(response)
        except Exception as e:
            logger.error(e.args)
            raise e


class Light:
    ROUTE = 'lights'

    def __init__(self, bridge, index, data = None):
        self.index = int(index)
        self.bridge = bridge
        self.data = {}
        self.name = ""
        self.state = {}
        if data is not None:
            try:
                self.data = data
                self.name = self.data['name']
                self.state = self.data['state'] # creates a reference, not a copy
            except KeyError as e:
                raise HueError(0, "Not able to update light data")
            except Exception as e:
                raise e

    def get_data(self):
        route = self.ROUTE + "/" + str(self.index)
        try:
            response = request("GET", self.bridge.url, route)
            check_response_for_error(response)
            self.data = response[0]
            self.name = self.data['name']
            self.state = self.data['state']  # creates a reference, not a copy
        except Exception as e:
            raise HueError(0, "Not able to get light data")



    def set(self, attr, value):
        self.send(json.dumps({attr: value}))


    def send(self, msg):
        route = self.ROUTE + "/" + str(self.index) + "/state"
        try:
            response = request("PUT", self.bridge.url, route, data=msg)
            #  r is a list of dicts such as [{'success':{/lights/1/state/on':True}]
            #  1st element of 1st element should be 'success'
            # it will be 'success' if the light is physically turned off
            check_response_for_error(response)
        except HueError as e:
            logger.warning(e.args)
            if e.type == LIGHT_IS_TURNED_OFF:
                pass
            else:
                raise e
        except Exception as e:
            logger.warning(e.args)
            raise e


def main():
    # region parse arguments
    parser = argparse.ArgumentParser(description='controls Hue lights')
    # parser.add_argument("-l", "--lights", help="list lights", action="store_true")  # boolean flag
    parser.add_argument("-lights", "--lights", help="list lights", action="store_true")  # boolean flag
    parser.add_argument("-off", "--off", help="all lights off", action="store_true")  # boolean flag
    parser.add_argument("-scenes", "--scenes", help="list scenes", action="store_true")  # boolean flag
    # parser.add_argument("-s", "--scene", type=int, default=0, help="activate scene")
    parser.add_argument("-scene", "--scene", type=str, default=0, help="activate scene")
    parser.add_argument("-light", "--light", nargs=2, type=str, help="send JSON string to one light")
    # NORMAL PARSING
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    # INJECTING ARGS FOR TESTING
    # args = parser.parse_args()  # no output, which I think is correct
    # args = parser.parse_args(["--lights"])   # works
    # args = parser.parse_args(["--light", "badname", '{"on": true, "bri":100}'])  # works as expected
    # args = parser.parse_args(["--light", "U", '{"on": true, "bri":100}'])  # works
    # args = parser.parse_args(["--scenes"])  # works, could use some output formatting #TODO
    # args = parser.parse_args(["-scene", 'ac637e2f0-on-0'])  # works
    # args = parser.parse_args(["-scene", 'bad id'])  # works as expected
    # args = parser.parse_args(["-off"])  # works


    # print(args)
    # endregion
    # print("Hue Demo")
    bridge = Bridge(IP_ADDRESS, USERNAME)

    if args.light: # OK
        # command format is  {'parameter':value,'parameter':value}
        # any quotes within a command line argument must be escaped
        #light = bridge.get_light_by_index(int(args.light[0]))
        light = bridge.get_light_by_name(args.light[0])
        if light is None:
            print(script_name + " did not find any light by that name")
        else:
            print(script_name + 'sending', args.light[1], 'to', light.data['name'])
            light.send(args.light[1])

    if args.lights:  # OK
        bridge.get_lights()
        print(script_name + " found these lights")
        for light in bridge.light_list:
            print(light.index, light.name)


    if args.scenes:
        scenes = bridge.get_scenes()
        print(script_name + " found these scenes")
        i = 1
        for scene in scenes:
            print(i, scene.data['name'], ' ', scene.data['lights'], ' ', scene.id)
            i = i + 1

    if args.off:
        bridge.all_on(False)

    if args.scene:
        scene = bridge.get_scene_by_id(args.scene)
        if scene is not None:
            scene.display()
        else:
            print(script_name + " did not find a scene by that name")

if __name__ == "__main__":
    main()

