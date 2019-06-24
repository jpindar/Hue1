#!python3
"""
Project: My First Hue Demo
File: Hue1.py
Author: jpindar@jpindar.com
Requires: https://pypi.org/project/requests/2.7.0/
"""
import sys
import json
import argparse
import requests

___author___ = "jpindar@jpindar.com"
IP_ADDRESS = "10.0.1.3:80"
USERNAME = "vXBlVENNfyKjfF3s"


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
            raise HueException("Not able to get Hue data")
        try:
            return response.json()
        except Exception as e:
            raise HueException("Not able to parse light data")

    def get_all_data(self):
        """ get all data from bridge """
        try:
            response = self._request('')
            self.data = response
        except Exception as e:
            raise HueException("Not able to get data")
        return response

    def get_config(self):
        try:
            response = self._request('config')
        except Exception as e:
            raise HueException("Not able to get data")
        return response

    def get_whitelist(self):
        config = self.get_config()
        whitelist = config['whitelist']
        return whitelist

    def delete_user(self, userid):
        my_url = self.url + "/config/whitelist/" + str(userid)
        try:
            response = requests.delete(url=my_url)
            r = response.json()
        except Exception as e:
            raise HueException("Not able to delete user")
        if any('error' in s for s in r):
            raise HueException("got error response")
        return r

    def get_lights(self):
        """ get a list of lights """
        try:
            response = self._request(Light.ROUTE)
        except Exception as e:
            raise HueException("Not able to get light data")
        # index starts at 1 not 0
        self.light_list = [Light(self, i) for i in response.keys()]
        for light in self.light_list:
            light.data = response[str(light.index)]
        self.light_list = sorted(self.light_list, key=lambda x: x.index)

    def get_scenes(self):
        try:
            response = self._request(Scene.ROUTE)
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

    def get_scene_by_index(self, i):
        self.get_scenes()
        scene = self.scene_list[i]
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
            if light.data['name'] == this_name:
                return light

    def get_light_by_index(self, this_index):
        self.get_lights()
        for light in self.light_list:
            if light.index == this_index:
                return light

    def all_on(self, on):
        group = Group(self, 0)  # group 0 is all lights
        group.set('on', on)

    def print_scene_names(self):
        self.get_scenes()
        i = 0
        for scene in self.scene_list:
            i += 1
            print(i, scene.data['name'])

    def print_light_names(self):
        self.get_lights()
        for light in self.light_list:
            print(light.index, light.data['name'])


class Scene:
    ROUTE = 'scenes'

    def __init__(self, bridge, userid):
        self.id = userid
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
    ROUTE = 'groups'

    def __init__(self, bridge, userid):
        self.id = userid
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
        except Exception as e:
            raise HueException("Not able to get light data")
        self.data = response

    def set(self, attr, value):
        try:
            msg = json.dumps({attr: value})
            self.send(msg)
        except HueException as e:  # usually means the light is turned off (logicly, not physically)
            pass

    def send(self, msg):
        my_url = self.bridge.url + "/" + self.ROUTE + "/" + str(self.index) + "/state"
        try:
            response = requests.put(url=my_url, data=msg)
            r = response.json()
            #  r is a list of dicts such as [{'success':{/lights/1/state/on':True}]
            #  1st element of 1st element should be 'success'
        except Exception as e:
            raise HueException("Not able to send light data")
        if any('error' in s for s in r):
            raise HueException("got error response")  # could just mean the light is turned off
        return r


def main():
    parser = argparse.ArgumentParser(description='controls Hue lights')
    parser.add_argument("-l", "--lights", help="list lights", action="store_true")  # boolean flag
    parser.add_argument("-off", "--off", help="all lights off", action="store_true")  # boolean flag
    parser.add_argument("-scenes", "--scenes", help="list scenes", action="store_true")  # boolean flag
    parser.add_argument("-scene", "--scene", type=int, default=0, help="activate scene")
    # args = parser.parse_args()
    args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])
    # print(args)
    print("Hue Demo")

    bridge = Bridge(IP_ADDRESS, USERNAME)

    if args.lights:
        bridge.print_light_names()

    if args.scenes:
        bridge.print_scene_names()

    if args.off:
        bridge.all_on(False)

    if args.scene:
        scene = bridge.get_scene_by_index(args.scene)
        scene.display()

if __name__ == "__main__":
    main()

