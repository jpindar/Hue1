"""
Project: My First Hue Demo
File: Hue1.py
Author: jpindar@jpindar.com
Requires: https://pypi.org/project/requests/2.7.0/
"""
import json
import time
import requests

___author___ = "jpindar@jpindar.com"
IP_ADDRESS = "10.0.1.3:80"
USERNAME = "d6dsl1hc-Lc0bMkkiVldUVDnwheXfzExAdrddr04"


class HueException(Exception):
    pass


class Bridge:
    def __init__(self, ip_address, username):
        self.light_list = []
        self.url = "http://" + ip_address + "/api/" + username

    def _request(self, route):
        try:
            response = requests.get(url=self.url + '/' + route)
        except Exception as e:
            raise HueException("Not able to get Hue data")
        try:
            return response.json()
        except Exception as e:
            raise HueException("Not able to parse light data")

    """ get all data from bridge """
    def get_all_data(self):
        try:
            response = self._request('')
        except Exception as e:
            raise HueException("Not able to get data")
        return response

    """"" get a list of lights """
    def get_lights(self):
        try:
            response = self._request(Light.ROUTE)
        except Exception as e:
            raise HueException("Not able to get light data")
        # create lights and put them in a list
        self.light_list = [Light(self, i) for i in response.keys()]
        for light in self.light_list:
            light.data = response[str(light.index)]
        self.light_list = sorted(self.light_list, key=lambda x: x.index)

    def lights(self):
        self.get_lights()
        return self.light_list

    def get_light_by_name(self, this_name):
        self.get_lights()
        for light in self.light_list:
            if light.data['name'] == this_name:
                return light

    def all_on(self, on):
        group = Group(self, 0)  # group 0 is all lights
        group.set('on', on)


class Group:
    ROUTE = 'groups'

    def __init__(self, bridge, id):
        self.id = id
        self.bridge=bridge

    def set(self, attr, value):
        self.send({attr: value})

    def send(self, cmd=None):
        my_url = self.bridge.url+"/"+self.ROUTE+"/"+str(self.id)+ "/action"  # /api/<username>/groups/<id>/action
        msg = json.dumps(cmd)
        try:
            response = requests.put(url=my_url, data=msg)
            r = response.json()
            #  r should be a list of dicts such as [{'success':{/lights/1/state/on':True}]
            #  1st element of 1st element == 'success'
        except Exception as e:
            raise HueException("Not able to send light data")
        if any('error' in s for s in r):
            raise HueException("got error response")  # could just mean the light is turned off
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
            self.send({attr: value})
        except HueException as e:  # usually means the light is turned off (logicly, not physically)
            pass

    def send(self, cmd=None):
        my_url = self.bridge.url + "/" + self.ROUTE + "/" + str(self.index) + "/state"
        msg = json.dumps(cmd)
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
    print("Hue Demo")
    bridge = Bridge(IP_ADDRESS, USERNAME)

    bridge.get_all_data()

    bridge.all_on(True)

    group = Group(bridge, 0)  # group 0 is all lights
    group.set("hue", 9000)

    # Better way:
    lights = bridge.lights()

    for light in lights:
        print(light.index, light.data['name'])

    light = bridge.get_light_by_name("LivingColors 1")
    if light is None:
        print("Couldn't find a light with that name")

    # transitiontime  uint16
    # This is given as a  multiple  of 100  ms and defaults to 4(400 ms).

    light.set("transitiontime", 0)
    light.set("on", True)
    light.set("hue", 0000)

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

if __name__ == "__main__":
    main()

