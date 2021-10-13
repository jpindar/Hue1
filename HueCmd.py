#!python3
"""
HueCmd, a script that calls the Hue1 module from the command line

Author: jpindar@jpindar.com

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
import argparse
from Hue1 import *

___author___ = "jpindar@jpindar.com"
script_name = 'HueCmd.py'
# It's OK to leave the credentials here for now because my bridge is not accessible from outside my LAN
# TODO read these from a config file
BAD_IP_ADDRESS = "10.0.1.99:80"
IP_ADDRESS = "10.0.1.3:80"
USERNAME = "vXBlVENNfyKjfF3s"
BAD_USERNAME = "invalid_username"

enable_logging = False
log_filename = 'HueCmd.log'
logger = logging.getLogger("HueCmd")
if enable_logging:
    logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s')
    logger.setLevel(logging.INFO)
logger.info("HueCmd  starting")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='controls Hue lights')
    parser.add_argument("-lights", "--lights", help="list lights", action="store_true")  # boolean flag
    parser.add_argument("-off", "--off", help="all lights off", action="store_true")  # boolean flag
    parser.add_argument("-scenes", "--scenes", help="list scenes", action="store_true")  # boolean flag
    parser.add_argument("-scene", "--scene", type=str, default=0, help="activate scene")
    parser.add_argument("-light", "--light", nargs='+', help="send either a json string or a parameter and a value to one light")
    return parser


def test_parser(parser: argparse.ArgumentParser) -> argparse.Namespace:
    # args = parser.parse_args()  # no output, which I think is correct
    # args = parser.parse_args(["--lights"])   # works
    # args = parser.parse_args(["--light", "badname", '{"on": true, "bri":100}'])  # works as expected
    # args = parser.parse_args(["--light", "U", '{"on": true, "bri":100}'])  # works
    # args = parser.parse_args(["--scenes"])  # works, could use some output formatting #TODO
    # args = parser.parse_args(["-scene", 'ac637e2f0-on-0'])  # works
    # args = parser.parse_args(["-scene", 'bad id'])  # works as expected
    # args = parser.parse_args(["-off"])  # works
    # args = parser.parse_args(["-light", "U"])  # works as expected
    # args = parser.parse_args(["-light", "U", '{"on": true}'])       # this works from here, however...
    # args = parser.parse_args(["-light", "U", '{\"on\": false}'])  # you need to escape the " when doing this on the command line
    # args = parser.parse_args(["-light", "U", "hue", "9000"]) # works
    args: argparse.Namespace = parser.parse_args(["-light", "U", "on", "false"])  # works
    return args


def main() -> None:
    parser = create_parser()
    TEST_PARSER = False
    if TEST_PARSER:
        # INJECTING ARGS FOR TESTING
        args = test_parser(parser)
    else:
        # NORMAL PARSING
        args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    bridge = Bridge(IP_ADDRESS, USERNAME)

    if args.light: # OK
        # command format is  {'parameter':value,'parameter':value}
        # any quotes within a command line argument must be escaped
        #light = bridge.get_light_by_index(int(args.light[0]))
        light = bridge.get_light_by_name(args.light[0])
        if light is None:
            print(script_name + " did not find any light by that name")
        else:
            if len(args.light) == 2:
                print(script_name + ' sending', args.light[1], 'to', light.data['name'])
                light.send(args.light[1])
            else:
                light.set(args.light[1], args.light[2])

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

