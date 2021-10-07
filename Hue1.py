#!python3
"""
Project: the Hue1 module
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

import logging
import json
import time
import requests

___author___ = "jpindar@jpindar.com"

# If a light is physically on and off, you can turn it virtually on and off. But you can't set it's hue etc.
LIGHT_IS_TURNED_OFF = 201
ENABLE_LOGGING = True

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    log_filename = 'Hue1.log'
    logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s')
if ENABLE_LOGGING:
    logger.setLevel(logging.INFO)


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
        logger.error("unknown error condition in request() method")
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
        return self.data

    def get_config(self):
        try:
            response = request("GET", self.url, "config")
            check_response_for_error(response)
        except HueError as e:
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
        except HueError as e:
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
        except HueError as e:
            logger.error(e.args)
            raise e
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
        except HueError as e:
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
                raise HueError(0, "Not able to parse scene data")

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
        except HueError as e:
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
                raise HueError(0, "Not able to parse light data")

    def get_data(self):
        route = self.ROUTE + "/" + str(self.index)
        try:
            response = request("GET", self.bridge.url, route)
            check_response_for_error(response)
            self.data = response[0]
            self.name = self.data['name']
            self.state = self.data['state']  # creates a reference, not a copy
        except HueError as e:
            logger.error(e.args)
            raise e


    def set(self, attr, value):
        if isinstance(value,str):
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.lstrip("-+").isdigit():  # oddly, there is no is_int() function
                value = int(value)
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


def _main():

    print("Hue Module")
    logger.info("Hue1 module")
    IP_ADDRESS = "10.0.1.3:80"
    USERNAME = "vXBlVENNfyKjfF3s"

    bridge = Bridge(IP_ADDRESS, USERNAME)
    try:
        bridge.get_all_data()
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)


if __name__ == "__main__":
    _main()

