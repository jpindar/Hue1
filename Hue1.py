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

import logging
import json
import time
import requests

___author___ = "jpindar@jpindar.com"
log_filename = 'Hue1.log'

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
        route = self.ROUTE + "/" + str(self.index) + "/state"
        msg = json.dumps({attr: value})
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


def test_bridge_commands(bridge):
    bridge.get_all_data()
    # bridge.get_lights()
    # bridge.get_scenes()
    bridge.get_whitelist()
    try:
        bridge.delete_user('3nrjWNhLKlC8SNiXnG0Jq1LT5Ht0G4ZDfmVztjvd')
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    bridge.get_whitelist()
    bridge.all_on(True)


def test_group_commands(bridge):
    group = Group(bridge, 0)  # group 0 is all lights
    group.set("hue", 0)
    group.set("sat", 255)


def test_scene_commands(bridge):
    # bridge.get_scenes()
    # could do for scene in bridge.scene_list, but that assumes bridge is populated
    # maybe bridge *should* be populated in its constructor?
    scenes = bridge.get_scenes()
    for scene in scenes:
        print(scene.name + ' ' + str(scene.lights) + ' ' + scene.id)

     # note there can be multiple scenes with the same name
    scene = bridge.get_scene_by_name("Energize")
    if scene is not None:
        scene.display()

    scene = bridge.get_scene_by_id("bad id")
    if scene is not None:
        scene.display()

    # could do this either way?
    # bridge.delete_scene(scene)
    # scene.delete()  # this could call bridge.delete_scene()


def test_light_commands(bridge):
    # light = bridge.get_light_by_name("bad name")
    # if light is None:
    #     print("Couldn't find a light with that name")
    light = bridge.get_light_by_name("L")
    if light is None:
        print("Couldn't find a light with that name")

    # this doesn't work, probably because some of the parameters in state are readonly
    # light.state['on'] = True
    # light.state['hue'] = 0
    # light.send()

    # transitiontime  uint16
    # This is given as a  multiple  of 100  ms and defaults to 4(400 ms).
    # light.set("transitiontime", 0)

    light.set("on", True)
    light.set("hue", 0000)
    light.set("sat", 255)
    # light.set("effect", "colorloop")
    # light.set("alert","select")    # turns light on and off quickly
    # light.set("alert", "lselect")

    print(light.data['state'])
    # now light.state is no longer accurate
    light.get_data()
    print(light.data['state'])
    # now it is accurate

    time.sleep(0.5)
    bridge.all_on(False)

    # can access like so
    # lights = bridge.lights()
    # light = lights[1]
    # or we could access a light without calling bridge.lights, like this:
    # light = Light(bridge, 1)
    # light.set("on",True)
    # light.set("sat", 254)
    # light.set("hue",55000)
    # I can't think of a good use case for this, though, unless you had a huge number of lights
    # if you know the index of a light, you can access a light like this:
    # But remember, the index can change, like if someone unplugged a light.


def test_bad_commands():
    bridge = Bridge(IP_ADDRESS, USERNAME)
    try:
        # this should cause an error response from the bridge
        bridge.set_all("hue", "000")
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    bridge = Bridge(IP_ADDRESS, BAD_USERNAME)
    try:
        lights = bridge.lights()
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    bridge = Bridge(IP_ADDRESS, BAD_USERNAME)
    try:
        bridge.get_all_data()
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    bridge = Bridge(BAD_IP_ADDRESS, USERNAME)
    try:
        lights = bridge.lights()
    except HueError as e:
        print("Hue Error type " + str(e.type) + e.description)
    except requests.exceptions.ConnectionError as e:
        logger.error(e.args)
        print(e.args)


def test_light_thats_off():
    """
    if a light is turned off, either physically or virtually, you can set it virtually on or off,
    but trying to set its hue etc. returns an error in the response
    """
    bridge = Bridge(IP_ADDRESS, USERNAME)

    light = bridge.get_light_by_name("badName")
    if light is None:
        print("Couldn't find a light with that name")

    light = bridge.get_light_by_name("U")
    if light is None:
        print("Couldn't find a light with that name")
        return
    light.set("on", False)
    light.set("on", True)
    light.set("on", False)
    light.set("hue", 0000)
    light.set("hue", 400)


def main():
    print("Hue Demo")

    """
     bridge = Bridge(IP_ADDRESS, BAD_USERNAME)
    try:
        bridge.get_all_data()
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)
     """

    bridge = Bridge(IP_ADDRESS, USERNAME)

    bridge.all_on(True)

    bridge.set_all('on', False)

    try:
        lights = bridge.lights()
        for light in lights:  # this won't work if lights is a dict
            print(light.index, light.name)
            light.set("hue", 0000)
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    test_bridge_commands(bridge)

    test_light_thats_off()

    test_group_commands(bridge)

    test_scene_commands(bridge)

    test_bad_commands()

    bridge.set_all("hue", 40000)


if __name__ == "__main__":
    main()
