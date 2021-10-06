"""
HueTest, a script for exercising the HUe1 module
Author: jpindar@jpindar.com

"""
import logging
from Hue1 import *

# It's OK to leave the credentials here for now
# because my bridge is not accessible from outside my LAN
#TODO read these from a config file
BAD_IP_ADDRESS = "10.0.1.99:80"
IP_ADDRESS = "10.0.1.3:80"
USERNAME = "vXBlVENNfyKjfF3s"
BAD_USERNAME = "invalid_username"

ENABLE_LOGGING = True

log_filename = 'Hue1.log'
logger = logging.getLogger(__name__)
if __name__ == "__main__":
    logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s')
if ENABLE_LOGGING:
    logger.setLevel(logging.INFO)
logger.info("Hue1 demo")


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

    # time.sleep(0.5)
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

    bridge = Bridge(IP_ADDRESS, BAD_USERNAME)
    try:
        bridge.get_all_data()
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

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

    # test_bad_commands()

    bridge.set_all("hue", 40000)


if __name__ == "__main__":
    main()
