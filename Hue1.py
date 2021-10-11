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
import requests
from typing import List, Dict, Optional, Any, Union
Response = Dict[str, Any]

___author___ = "jpindar@jpindar.com"

# If a light is physically on and off, you can turn it virtually on and off. But you can't set it's hue etc.
LIGHT_IS_TURNED_OFF = 201

ENABLE_LOGGING = True

logger = logging.getLogger(__name__)
if __name__ == "__main__":
    log_filename = 'Hue1.log'
    logging.basicConfig(filename=log_filename,  filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s')
if ENABLE_LOGGING:
    logger.setLevel(logging.INFO)


class HueError(Exception):
    """
       Exception raised for errors in the response from the bridge
       Attributes:
         type -- numeric type of error
         description -- explanation of the error
    """

    def __init__(self, type: int, description: str):
        self.type = type
        self.description = description


def check_response_for_error(result: List[Response]) -> None:
    for s in result:
        if 'error' in s:
            type: int = s['error']['type']
            description: str = (s['error']['description'])
            raise HueError(type, "error: " + description)


def request(method: str, url: str, route: str, **kwargs: Any) -> List[Response]:
    try:
        response: requests.models.Response = requests.request(method, url + '/' + route, **kwargs)
        if response.status_code != requests.codes.ok:   # should be 200
            raise HueError(0, "Got bad response status from Hue Bridge")
        # response.json() can be either a dict or a list containing a dict
        # AFAIK, the list only ever has one element, but we can't be sure of that
        # so instead of stripping the dict out of the list, let's do the opposite
        r: Union[Response, List[Response]] = response.json()
        if isinstance(r, dict):
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
        logger.error("unknown error condition")
        logger.error(e.args)
        raise e


class Bridge:

    def __init__(self, ip_address: str, username: str) -> None:
        self.light_list: List[Light] = []
        self.scene_list: List[Scene] = []
        self.group_list: List[Group] = []
        self.url: str = "http://" + ip_address + "/api/" + username
        self.data: Dict[str, Any] = {}

    def get_all_data(self) -> Dict[str, Any]:
        """ Get all data from the bridge. """
        try:
            response: List[Response] = request("GET", self.url, '')
            check_response_for_error(response)
            self.data = response[0]
        except HueError as e:
            logger.error(e.args)
            raise e
        return self.data

    def get_config(self) -> Dict[str, Any]:
        try:
            response: List[Response] = request("GET", self.url, "config")
            check_response_for_error(response)
        except HueError as e:
            logger.error(e.args)
            raise e
        return response[0]

    def get_whitelist(self) -> Dict[str, Any]:
        """ Get the bridge's whitelist of usernames """
        config: Dict[str, Any] = self.get_config()
        whitelist: Dict[str, Any] = config['whitelist']
        return whitelist

    def delete_user(self, id: str) -> None:
        route = "config/whitelist/" + str(id)
        try:
            response: List[Response] = request("DELETE", self.url, route)
            check_response_for_error(response)
        except HueError as e:
            logger.error(e.args)
            raise e

    def get_lights(self) -> List['Light']:
        """
            Get a list of the bridge's lights.
            Note that light.index starts at 1 but list positions start at 0
        """
        try:
            response: List[Response] = request("GET", self.url, Light.ROUTE)
            check_response_for_error(response)
        except HueError as e:
            logger.error("Hue Error " + str(e.args))
            raise e
        r = response[0]
        self.light_list = [Light(self, i, r[str(i)]) for i in r.keys()]
        self.light_list = sorted(self.light_list, key=lambda x: x.index)
        return self.light_list

    def get_scenes(self) -> List['Scene']:
        try:
            response: List[Response] = request("GET", self.url, Scene.ROUTE)
            check_response_for_error(response)
        except HueError as e:
            logger.error(e.args)
            raise e
        r = response[0]
        self.scene_list = [Scene(self, i, r[str(i)]) for i in r.keys()]
        self.scene_list = sorted(self.scene_list, key=lambda x: x.name)
        return self.scene_list

    def get_groups(self) -> List['Group']:
        try:
            response: List[Response] = request("GET", self.url, Group.ROUTE)
            check_response_for_error(response)
        except HueError as e:
            logger.error(e.args)
            raise e
        # note that while the keys in this look like indexes, they are not necessarily inclusive or ordered
        r = response[0]
        self.group_list = [Group(self, i, r[str(i)]) for i in r.keys()]
        self.group_list = sorted(self.group_list, key=lambda x: x.name)
        return self.group_list

    def get_scene_by_name(self, desired_name: str) -> Optional['Scene']:
        self.get_scenes()
        for scene in self.scene_list:
            if scene.name == desired_name:
                return scene
        return None

    def get_scene_by_id(self, desired_id: str) -> Optional['Scene']:
        self.get_scenes()
        for scene in self.scene_list:
            if scene.id == desired_id:
                return scene
        return None

    def delete_scene(self, scene: 'Scene') -> None:
        route = Scene.ROUTE + "/" + str(scene.id)
        try:
            response: List[Response] = request("DELETE", self.url, route)
            check_response_for_error(response)
        except HueError as e:
            logger.error(e.args)
            raise e

    def delete_group(self, group: 'Group') -> None:
        route = Group.ROUTE + "/" + str(group.id)
        try:
            response: List[Response] = request("DELETE", self.url, route)
            check_response_for_error(response)
        except HueError as e:
            logger.error(e.args)
            raise e

    def lights(self) -> List['Light']:
        # if we were going for speed at the expense of possible
        # errors (like if a light was added or removed from the bridge) we could add this:
        # note that physically turning a light off does not remove it from the bridge's list
        if self.light_list == []:
            self.get_lights()
        return self.light_list

    def get_light_by_name(self, this_name: str) -> Optional['Light']:
        self.light_list = self.get_lights()
        for light in self.light_list:
            if light.name == this_name:
                return light
        return None

    def all_on(self, on: bool) -> None:
        group: Group = Group(self, 0)  # group 0 is all lights
        group.set('on', on)

    def set_all(self, attr: str, value: Any) -> None:
        """ Set all lights
            Since you can use group 0 for all lights, this is just an example.
            value can be bool or int, not sure about str
        """
        self.get_lights()
        for light in self.light_list:
            light.set(attr, value)


class Scene:
    ROUTE = 'scenes'

    def __init__(self, bridge: Bridge, id: str, data: Optional[Dict[str, Any]] = None) -> None:
        self.id: str = id
        self.bridge: Bridge = bridge
        self.data: Dict[str, Any] = {}
        self.name: str = ""
        self.lights: List[str] = []
        if data is not None:
            try:
                self.data = data
                self.name = self.data['name']
                self.lights = self.data['lights']
            except KeyError as e:
                raise HueError(0, "Not able to parse scene data")

    def display(self) -> None:
        group: Group = Group(self.bridge, 0)  # group 0 is all lights
        group.set("scene", self.id)


class Group:
    """ A group of lights
        Note that Group 0 is all lights
    """

    ROUTE = 'groups'

    def __init__(self, bridge: Bridge, id: int, data: Optional[Dict[str, Any]] = None) -> None:
        self.id: int = id
        self.bridge: Bridge = bridge
        self.data: Dict[str, Any] = {}
        self.name: str = ""
        self.lights: List[str] = []
        if data is not None:
            try:
                self.data = data
                self.name = self.data['name']
                self.lights = self.data['lights']
            except KeyError as e:
                raise HueError(0, "Not able to parse group data")

    def set(self, attr: str, value: Any) -> None:
        route = self.ROUTE + "/" + str(self.id) + "/action"
        msg: str = json.dumps({attr: value})
        try:
            response: List[Response] = request("PUT", self.bridge.url, route, data=msg)
            #  r should be a list of dicts such as [{'success':{/lights/1/state/on':True}]
            #  1st element of 1st element == 'success'
            check_response_for_error(response)
        except HueError as e:
            logger.error(e.args)
            raise e


class Light:
    ROUTE = 'lights'

    def __init__(self, bridge: Bridge, index: int, data: Optional[Dict[str, Any]] = None) -> None:
        self.index: int = int(index)
        self.bridge: Bridge = bridge
        self.data: Dict[str, Any] = {}
        self.name: str = ""
        self.state: Dict[str, Any] = {}
        if data is not None:
            try:
                self.data = data
                self.name = self.data['name']
                self.state = self.data['state']
            except KeyError as e:
                raise HueError(0, "Not able to parse light data")

    def get_data(self) -> Response:
        route = self.ROUTE + "/" + str(self.index)
        try:
            response: List[Response] = request("GET", self.bridge.url, route)
            check_response_for_error(response)
            self.data = response[0]
            self.name = self.data['name']
            self.state = self.data['state']  # creates a reference, not a copy
            return self.data
        except HueError as e:
            logger.error(e.args)
            raise e

    def set(self, attr: str, value: Any) -> None:
        if isinstance(value, str):
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.lstrip("-+").isdigit():  # oddly, there is no is_int() function
                value = int(value)
        self.send(json.dumps({attr: value}))

    def send(self, msg: str) -> None:
        route = self.ROUTE + "/" + str(self.index) + "/state"
        try:
            response: List[Response] = request("PUT", self.bridge.url, route, data=msg)
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

