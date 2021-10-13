"""
HueTest, a script for exercising the Hue1 module
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

enable_logging = False
log_filename = 'HueTest.log'
logger = logging.getLogger("HueTest")
if enable_logging:
    logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s')
    logger.setLevel(logging.INFO)
logger.info("HueTest demo starting")


def test_bridge_commands(bridge:Bridge) -> None:
    data = bridge.get_all_data()
    print(data)
    lights = bridge.get_lights()
    print(lights)
    scenes = bridge.get_scenes()
    print(scenes)
    whitelist = bridge.get_whitelist()
    print(whitelist)
    bridge.all_on(True)
    bridge.set_all('on', False)
    light = bridge.get_light_by_name("bad name")
    if light is None:
        print("Couldn't find a light with that name")
    light = bridge.get_light_by_name("L")
    if light is None:
        print("Couldn't find a light with that name")
    else:
       light.set('hue', 000)

    # this should raise a Hueerror exception since this user doesn't exist
    # in a real application this should probably fail silently
    try:
        bridge.delete_user('3nrjWNhLKlC8SNiXnG0Jq1LT5Ht0G4ZDfmVztjvd')
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    bridge.all_on(True)


def test_group_commands(bridge:Bridge) -> None:
    groups = bridge.get_groups()
    for group in groups:
       print(group.id)
       print(group.data)
    group = Group(bridge, 0)  # group 0 is all lights
    group.set("hue", 0)
    group.set("sat", 255)
    bridge.get_all_data()
    # group = Group(bridge,"9") # note this is the index, not the name
    group = Group(bridge,9) # note this is the index, not the name
    bridge.delete_group(group) # trying to delete a not-existant group gives an appropriate error
    bridge.get_all_data()


def test_scene_commands(bridge:Bridge) -> None:
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


def test_light_commands(bridge:Bridge) -> None:

    try:
        lights = bridge.get_lights()
        for light in lights:  # this won't work if lights is a dict
            print(light.index, light.name)
            light.set("hue", 0000)
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    light = bridge.get_light_by_name("L")
    if light is None:
        print("Couldn't find a light with that name")
    else:
        light.set('on', True)
        # transitiontime  uint16
        # This is given as a  multiple  of 100  ms and defaults to 4(400 ms).
        light.set("transitiontime", 0)
        light.set("on", True)
        light.set("sat", 255)
        try:
            for h in range(0, 65537, 4096):
                light.set("hue", h)
        except HueError as e:   # you get an error if you go over 65535, althugh logically it could just wrap
            print("Hue Error type " + str(e.type) + " " + e.description)

        try:
            # ct 	uint16 	The Mired Color temperature of the light. 2012 connected lights are capable of 153 (6500K) to 500 (2000K).
            for t in range(153, 501, 50):
                light.set("ct",t)
        except HueError as e:
            print("Hue Error type " + str(e.type) + " " + e.description)

        light.set("hue",16000)  # yellow
        light.set("sat", 255)
        light.set("effect", "colorloop")
        light.set("effect", "none")
        # note that setting a hue etc. doesn't stop the color loop
        light.set("effect", "none")
        light.set("alert","select")    # turns light on and off quickly
        light.set("alert", "lselect")  # turns light on and off quickly several times
        light.set("alert", "none")
        print(light.data['state'])
        # now light.state is no longer accurate
        light.get_data()
        print(light.data['state'])
        # now it is accurate
        bridge.all_on(False)


def test_bad_commands() -> None:
    bridge = Bridge(IP_ADDRESS, USERNAME)
    try:
        # this should cause an error response from the bridge
        bridge.set_all("hue", "000")
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    bridge = Bridge(IP_ADDRESS, BAD_USERNAME)
    try:
        lights = bridge.get_lights()
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    bridge = Bridge(IP_ADDRESS, BAD_USERNAME)
    try:
        bridge.get_all_data()
    except HueError as e:
        print("Hue Error type " + str(e.type) + " " + e.description)

    bridge = Bridge(BAD_IP_ADDRESS, USERNAME)
    try:
        lights = bridge.get_lights()
        print(lights)
    except HueError as e:
        print("Hue Error type " + str(e.type) + e.description)


def test_light_thats_off() -> None:
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


def main() -> None:
    print("Hue Demo")
    # typical access is like
    # lights = bridge.get_lights()
    # or
    # light = bridge.get_light_by_name(name)
    # (which calls bridge.get_lights())
    #
    # or we could access a light without calling bridge.lights, like this:
    # light = Light(bridge, 1)
    # This might be slightly faster
    # I can't think of a good use case for this, though, unless you had a huge number of lights
    # if you know the index of a light, you can access a light like this:
    # But remember, the index can change, like if someone unplugged a light.
    bridge = Bridge(IP_ADDRESS, USERNAME)
    test_bridge_commands(bridge)
    test_light_commands(bridge)
    test_light_thats_off()
    test_group_commands(bridge)
    test_scene_commands(bridge)
    test_bad_commands()
    bridge.all_on(False)

if __name__ == "__main__":
    main()
