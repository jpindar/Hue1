"""
Project: My First Hue Demo
File: Hue1.py
Author: jpindar@jpindar.com
Requires: https://pypi.org/project/requests/2.7.0/
"""
import logging
import json
import time
import requests

___author___ = "jpindar@jpindar.com"
log_filename = 'Hue1.log'

IP_ADDRESS = "10.0.1.3:80"
USERNAME = "vXBlVENNfyKjfF3s"

# IP_ADDRESS = "75.67.104.223:4200"
# USERNAME = "d6dsl1hc-Lc0bMkkiVldUVDnwheXfzExAdrddr04"

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s', level=logging.INFO)


class HueException(Exception):
    pass


class Bridge:
    def __init__(self, ip_address, username):
        self.light_list = []
        self.scene_list = []
        self.url = "http://" + ip_address + "/api/" + username
        self.data = []

    def _request(self, route):
        try:
            response = requests.get(url=self.url + '/' + route)
        except Exception as e:
            raise HueException("Not able to get data")
        try:
            return response.json() # response is of type response, but we're only returning the json (which is a dict)
        except Exception as e:
            raise HueException("Not able to parse data")

    def check_for_error(self, result):
        for s in result:
            if 'error' in s:
                s = (s['error']['description'])
                raise HueException("error: " +s)

    """ get all data from bridge """
    def get_all_data(self):
        try:
            response = self._request('')
            self.check_for_error(response)
            self.data = response
        except Exception as e:
            raise HueException("Not able to get data")
        return response

    def get_config(self):
        try:
            response = self._request('config')
            self.check_for_error(response)
        except Exception as e:
            raise HueException("Not able to get data")
        return response

    def get_whitelist(self):
        """ get bridge's whitelist of usernames """
        config = self.get_config()
        whitelist = config['whitelist']
        return whitelist

    def delete_user(self, id):
        my_url = self.url + "/config/whitelist/" + str(id)
        try:
            response = requests.delete(url=my_url)
            self.check_for_error(response)
        except Exception as e:
            raise HueException("Not able to delete user")

    """ get a list of lights """
    def get_lights(self):
        try:
            response = self._request(Light.ROUTE)
            self.check_for_error(response)
        except Exception as e:
            raise HueException("Not able to get light data")
        # create lights and put them in a list
        self.light_list = [Light(self, i) for i in response.keys()]
        for light in self.light_list:
            light.populate(response[str(light.index)])
        self.light_list = sorted(self.light_list, key=lambda x: x.index)

    def get_scenes(self):
        try:
            response = self._request(Scene.ROUTE)
            self.check_for_error(response)
        except Exception as e:
            raise HueException("Not able to get scene data")

        # create scenes and put them in a list
        self.scene_list = [Scene(self, i) for i in response.keys()]
        for scene in self.scene_list:
            scene.data = response[str(scene.id)]
        self.scene_list = sorted(self.scene_list, key=lambda x: x.data['name'])

    def get_scene_by_name(self, this_name):
        self.get_scenes()
        for scene in self.scene_list:
            if scene.data['name'] == this_name:
                return scene

    def lights(self):
        self.get_lights()
        return self.light_list

    def scenes(self):
        self.get_scenes()
        return self.scene_list

    def get_light_by_name(self, this_name):
        self.get_lights()
        for light in self.light_list:
            if light.name == this_name:
                return light

    def all_on(self, on):
        group = Group(self, 0)  # group 0 is all lights
        group.set('on', on)

    def set_all(self, attr, value):
        self.get_lights()
        for light in self.light_list:
            light.set(attr, value)


class Scene:
    ROUTE = 'scenes'

    def __init__(self, bridge, id):
        self.id = id
        self.bridge = bridge
        self.data = {}

    def display(self):
        group = Group(self.bridge, 0)  # group 0 is all lights
        group.set("scene", self.id)

    def delete(self):
        my_url = self.bridge.url + "/" + self.ROUTE + "/" + str(self.id)
        try:
            response = requests.delete(url=my_url)
            r = response.json()
        except Exception as e:
            raise HueException("Not able to delete scene")
        if any('error' in s for s in r):
            raise HueException("got error response")
        return r


class Group:
    """  Group 0 is all lights """
    ROUTE = 'groups'

    def __init__(self, bridge, id):
        self.id = id
        self.bridge = bridge

    def set(self, attr, value):
        self.send({attr: value})

    def send(self, cmd=None):
        my_url = self.bridge.url + "/" + self.ROUTE + "/" + str(self.id) + "/action"
        msg = json.dumps(cmd)
        try:
            response = requests.put(url=my_url, data=msg)
            r = response.json()
            #  r should be a list of dicts such as [{'success':{/lights/1/state/on':True}]
            #  1st element of 1st element == 'success'
        except Exception as e:
            raise HueException("Not able to send light data")
        for s in r:
            if 'error' in s:
                error_msg = s['error']['description']
                print(error_msg)
                raise HueException("got error response")
        return r


class Light:
    ROUTE = 'lights'

    def __init__(self, bridge, index):
        self.index = int(index)
        self.bridge = bridge
        self.data = None
        self.name = None
        self.state = None

    def _request(self):
        my_url = self.bridge.url + "/" + self.ROUTE + "/" + str(self.index)
        try:
            response = requests.get(url=my_url)
        except Exception as e:
            raise HueException("Not able to get light data")
        return response.json()

    def get_data(self):
        try:
            response = self._request()
            self.data = response
            self.name = self.data['name']
            self.state = self.data['state']  # creates a reference, not a copy
        except Exception as e:
            raise HueException("Not able to get light data")

    def populate(self, dict_data):
        try:
            self.data = dict_data
            self.name = self.data['name']
            self.state = self.data['state']  # creates a reference, not a copy
        except Exception as e:
            raise HueException("Not able to update light data")

    def set(self, attr, value):
        try:
            self.send({attr: value})
        except HueException as e:  # usually means the light is turned off (logicly, not physically)
            pass

    def send(self, cmd=None):
        my_url = self.bridge.url + "/" + self.ROUTE + "/" + str(self.index) + "/state"
        if cmd is None:
            msg = json.dumps(self.state)
        else:
            msg = json.dumps(cmd)

        try:
            response = requests.put(url=my_url, data=msg)
            r = response.json()
            #  r is a list of dicts such as [{'success':{/lights/1/state/on':True}]
            #  1st element of 1st element should be 'success'
        except Exception as e:
            logger.warning(e.args)
            raise HueException("Not able to send light data")
        if any('error' in s for s in r):
            raise HueException("got error response")  # could just mean the light is turned off
        return r


def test_group_commands(bridge):
    group = Group(bridge, 0)  # group 0 is all lights
    group.set("hue", 0)
    group.set("sat", 255)


def test_scene_commands(bridge):
    # scene = bridge.get_scene_by_name("Energize")
    # if scene is not None:
    #    scene.display()
    pass

def test_light_commands(bridge):
    # light = bridge.get_light_by_name("LivingColors 1")
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



def main():
    print("Hue Demo")
    bridge = Bridge(IP_ADDRESS, USERNAME)

    lights = bridge.lights()
    for light in lights:  # this won't work if lights is a dict
        print(light.index, light.name)

    bridge.all_on(True)

    test_group_commands(bridge)




if __name__ == "__main__":
    main()

