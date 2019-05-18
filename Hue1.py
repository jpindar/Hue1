"""
Project: My First Hue Demo
File: Hue1.py
Author: jpindar@jpindar.com
"""
import requests
import json
import time

___author___ = "jpindar@jpindar.com"
ip_address = "10.0.1.3:80"
username = "d6dsl1hc-Lc0bMkkiVldUVDnwheXfzExAdrddr04"


class HueException(Exception):
    pass


class Bridge:
    def __init__(self, ip_address, username):
        self.light_list = []
        self.url = "http://" + ip_address + "/api/" + username

    def _request(self, route, data={}):
        try:
            response = requests.get(url=self.url + '/' + route)
        except Exception as e:
            raise HueException("Not able to get Hue data")
        try:
            return response.json()
        except Exception as e:
            raise HueException("Not able to parse light data")

    def get_light_data(self):
        try:
            response = self._request("lights")
        except Exception as e:
            raise HueException("Not able to get light data")

        # create lights and put them in a list
        self.light_list = [Light(self, i) for i in response.keys()]
        for light in self.light_list:
            light.data = response[str(light.index)]

        self.light_list = sorted(self.light_list, key=lambda x: x.index)
        # self.self.light_list.insert(0, Light(self, 0))  # add a dummy light so the index and the position in the list match

    def lights(self):
        self.get_light_data()
        return self.light_list

    def get_light_by_name(self, this_name):
        self.get_light_data()
        for light in self.light_list:
            if light.data['name'] == this_name:
                return light

    def all_off(self):
        self.get_light_data()
        for light in self.light_list:
            light.set("on", False)


class Light:
    def __init__(self, bridge, index):
        self.index = int(index)
        self.bridge = bridge
        self.data = None

    def _request(self):
        my_url = self.bridge.url+"/lights/"+str(self.index)
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
        try:
            self.data = response
        except Exception as e:
            raise HueException("Not able to update light data")

    def set(self, attr, value):
        cmd = {attr: value}
        self.send(cmd)

    def send(self, cmd=None):
        my_url = self.bridge.url + "/lights/" + str(self.index) + "/state"
        if cmd is None:
            msg = json.dumps(self.data['state'])   # this isn't really the right thing to do, we're trying to write to some read-only parameters
        else:
            msg = json.dumps(cmd)

        try:
            response = requests.put(url=my_url, data=msg)
            r = response.json()
            #  r should be a list of dicts, 1st element of 1st element == 'success'
        except Exception as e:
            raise HueException("Not able to send light data")
        return r




def main():
    print("Hue Demo")
    bridge = Bridge(ip_address, username)

    bridge.all_off()

    # if you know the index of a light, you can access a light like this:
    # a_light = Light(bridge, 4)
    # a_light.get_data()
    # a_light.set("on", True)
    # But the index can change, like if someone unplugged a light.

    # Better way:
    lights = bridge.lights()

    for light in lights:
        print(light.index, light.data['name'])

    light = bridge.get_light_by_name("LivingColors 1")

    light.set("on", True)
    light.set("hue", 0000)

    print(light.data['state'])
    # now light.state is no longer accurate
    light.get_data()
    print(light.data['state'])
    # now it is accurate


    time.sleep(0.5)
    light.set("on", False)

if __name__ == "__main__":
    main()

