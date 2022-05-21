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
ip_address: str = ""
username: str = ""
BAD_IP_ADDRESS = "10.0.1.99:80"
BAD_USERNAME = "invalid_username"
config_filename = ".hueconfig"

enable_logging = False
log_filename = 'HueCmd.log'
logger = logging.getLogger("HueCmd")
if enable_logging:
    logging.basicConfig(filename=log_filename, filemode='w', format='%(levelname)-8s:%(asctime)s %(name)s: %(message)s')
    logger.setLevel(logging.INFO)
logger.info("HueCmd  starting")


def read_config_file() -> None:
    global ip_address
    global username
    configFile = open(config_filename, 'r')
    with configFile as f:
        ip_address = f.readline()
        username = f.readline()
        ip_address = ip_address.strip("\r\n\'\"")
        username = username.strip("\r\n\'\"")


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
    # args = parser.parse_args(["-scene", 'bad id'])  # fails as expected
    # args = parser.parse_args(["-off"])  # works
    # args = parser.parse_args(["-light", "U"])  # fails as expected
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

    read_config_file()
    bridge = Bridge(ip_address, username)

    if args.light: # OK
        # command format is  {'parameter':value,'parameter':value}
        # args.light[0] is the lights name, args.light[1] is the dict of settings
        light = bridge.get_light_by_name(args.light[0])
        if light is None:
            print(script_name + " did not find any light by that name")
        else:
            n = len(args.light)
            if n == 2: # 0 and 1
                print(script_name + ' sending', args.light[1], 'to', light.data['name'])
                light.send(args.light[1])
            elif n == 3:
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

