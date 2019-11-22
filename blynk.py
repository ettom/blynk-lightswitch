#!/usr/bin/env python3
"""Small python script to interact with the blynk HTTP api."""
import sys
import requests

# If you are hosting your own blynk-server, add the url here.

server = "http://blynk-cloud.com"

# Configure your devices here.
# If your devices are wired so that a pin value of LOW is the "on" state,
# change the "default" field in the dict for that device from 0 to 1.
# This might happen if your relays are wired as normally closed.

all_devices = {
    "bedroom_light": {"pin": "V3", "auth": "<auth_token>", "default":  0, "group": "bedroom"},
    "kitchen_light": {"pin": "d2", "auth": "<auth_token>", "default":  1, "group": "kitchen"},
    "temperature":   {"pin": "V6", "auth": "<auth_token>"},
    "humidity":      {"pin": "V5", "auth": "<auth_token>"}}


# Add the names of devices that are not supposed to be toggled on/off here.
# If a device is not listed here it must have a 0/1 in its "default" field.
exclude = ("temperature", "humidity")

# Add the names of device groups/rooms here. All devices that have the name of
# the group in the corresponding field will respond
groups = ("bedroom", "kitchen")

help = """Usage: blynk.py [DEVICE(S)] [ACTION]

Small python script to interact with the blynk HTTP api.

Actions:
  on         Turn the device(s) on
  of(f)      Turn the device(s) off
  f(lip)     Flip the device(s)
  j(ust)     Turn the device(s) on and turn off every other device in the same group
  p(rint)    Print the status of the device(s) as a table
  s(tatus)   Print the status of the device(s) in dict/json format
  any int/float for setting a pin to an arbitrary value"""


def process_pin(value, default_state=0):
    """Modify a pin value according to its default state."""
    value = float(value)
    if value.is_integer():
        value = int(value) ^ default_state
    return value


def set_to_state(device, value):
    """Set a device to the required state."""
    value = process_pin(value, all_devices[device]["default"])
    pin, auth_token = all_devices[device]["pin"], all_devices[device]["auth"]
    requests.get(f"{server}/{auth_token}/update/{pin}?value={value}")


def get_state(device):
    """Get device state."""
    pin, auth_token = all_devices[device]["pin"], all_devices[device]["auth"]
    r = requests.get(f"{server}/{auth_token}/get/{pin}")
    state = process_pin(r.json()[0])

    return (state if state not in (0, 1) or device in exclude
            else process_pin(state, all_devices[device]["default"]))


def flip_state(device):
    """Invert device state."""
    set_to_state(device, get_state(device) ^ 1)


def apply_function(devices, func, *args):
    """Given a function as an argument, apply function to all given devices.

    Extra arguments, if given, are passed to the function.
    """
    for device in devices:
        func(device, *args)


def get_status_as_dict(devices):
    """Return status of given devices in dict format."""
    status = {}
    for device in devices:
        status[device] = get_state(device)

    return status


def print_status(devices):
    """Prettyprint status of devices."""
    status_dict = get_status_as_dict(devices)
    table = ""
    max_len = max(len(x) for x in status_dict) + 1
    for device, status in status_dict.items():
        table += f"{device: <{max_len}}: {status: <{3}} \n"
    table = table[:-1:]
    return table


def choose_devices(action, *args):
    """Choose which devices to modify."""
    if args[0] in ("all", "a"):
        devices_to_modify = filter(lambda x: x not in exclude
                                   or action[:1] in ("s", "p"), all_devices.keys())
    elif args[0] in groups:
        devices_to_modify = filter(lambda x: args[0] == all_devices[x].get("group")
                                   and (x not in exclude or action[:1] in ("s", "p")), all_devices.keys())
    else:
        devices_to_modify = args

    return list(devices_to_modify)


def take_action(action, *args):
    """Take action on given devices."""
    if action[:1] == "f":          # flip
        apply_function(args, flip_state)
    elif action[:2] == "of":       # off
        apply_function(args, set_to_state, 0)
    elif action == "on":           # on
        apply_function(args, set_to_state, 1)
    elif action[:1] == "j":        # just
        apply_function(args, set_to_state, 1)
        devices_to_turn_off = [device for device in all_devices.keys()
                               if device not in exclude
                               and all_devices[device]["group"] in [all_devices[device]["group"] for device in args]
                               and device not in args]
        apply_function(devices_to_turn_off, set_to_state, 0)
    elif action[:1] == "p":        # print
        print(print_status(args))
    elif action[:1] == "s":        # status
        print(get_status_as_dict(args) if len(args) != 1 else get_state(*args))
    else:                          # set
        action = float(action)
        apply_function(args, set_to_state, action)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(help)
    else:
        *args, action = sys.argv[1:]

        devices_to_modify = choose_devices(action, *args)
        take_action(action, *devices_to_modify)
