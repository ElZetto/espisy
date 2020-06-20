

import os
import sys
import ipaddress
from pathlib import Path

import yaml

espisy_path = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), os.pardir)
sys.path.append(espisy_path)

from espisy.constants import config, config_file_name
from espisy.core import ESP

config.get("DEFAULT", "file_dir")
positive_answer = ["y", "yes", "j", "ja"]


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def check_file_dir():
    file_dir = config.get("USER_SETTINGS", "file_dir")
    new_dir = os.path.join(Path.home(), ".espisy")
    if file_dir == "default":
        done = False
        # Dialog ask for standard directory
        while not done:
            msg = f"""{bcolors.BOLD}Do you want to change the directory for files that espisy will save? 
    Current directory is {new_dir}{bcolors.ENDC}"""
            if input(msg).lower() in positive_answer:
                new_dir = input(f"{bcolors.BOLD}Please enter new directory.\n{bcolors.ENDC}")
            if not os.path.isdir(new_dir):
                if input(f"{bcolors.BOLD}Create directory {new_dir}?\n{bcolors.ENDC}").lower() in positive_answer:
                    os.mkdir(new_dir)
                    done = True
            else:
                done = True
    else:
        # accept standard directory
        pass
    config.set("USER_SETTINGS", "file_dir", new_dir)
    with open(config_file_name, "w") as config_file:
        config.write(config_file)
    return new_dir


def create_esp_settings():
    settings_file_name = os.path.join(config.get(
        "USER_SETTINGS", "file_dir"), "esp.yaml")
    try:
        with open(settings_file_name, "r") as settings_file:
            settings = yaml.safe_load(settings_file)
    except Exception as e:
        print(f"{bcolors.WARNING}An error occured: {e}{bcolors.ENDC}")
    if settings.get("ipv4network", None) != None:
        if input(f"{bcolors.BOLD}Do you want to keep the current config {settings.get('ipv4network',None)}?\n >>{bcolors.ENDC}").lower() in positive_answer:
            return settings.get("ipv4network", "ERROR")
    msg = f"""{bcolors.BOLD}Do you want to set a subnet that will be used for the scanning?
If you do not set one, the scanning function will not work.\n >>{bcolors.ENDC}"""
    if input(msg).lower() in positive_answer:
        ipv4network = input(
            f"{bcolors.BOLD}Please enter new subnet like this: 192.0.0.0/24\n >>{bcolors.ENDC}")
        try:
            ipaddress.IPv4Network(ipv4network)
        except Exception as e:
            print(
                f"{bcolors.WARNING}That did not work. Wrong syntax in '{ipv4network}'?\nException: {e}{bcolors.ENDC}")
        settings.update({"ipv4network": ipv4network})

    with open(settings_file_name, "w") as settings_file:
        yaml.dump(settings, settings_file)
    return ipv4network


def perform_scan():
    if input(f"{bcolors.BOLD}Do you want to perform a scan for ESPs now?\n >>{bcolors.ENDC}").lower() in positive_answer:
        ESP.scan_network()
        msg_length = len(f"| ESP | {' ':20} | {' ':20}|")
        line = "+" + "-"*(msg_length-2) + "+"
        print(f"\n{bcolors.BOLD}Found the following ESPEasy devices.{bcolors.ENDC}")
        print(line)
        for ip, esp in ESP._device_register.items():
            message = f"| ESP | {bcolors.OKBLUE}{esp.name:^20}{bcolors.ENDC} | {bcolors.OKBLUE}{ip:^20}{bcolors.ENDC}|"
            print(message)
            print(line)
        return [(device.ip, device.name) for device in ESP._device_register.values()]
    else:
        return "not performed"


def last_check(**kwargs):
    print(f"{bcolors.BOLD}Please take a look if the settings are correct:{bcolors.ENDC}")
    for arg in kwargs:
        if isinstance(kwargs[arg], (list, dict, type({}.items()))):
            print(f"{arg:15}: ")
            for result in kwargs[arg]:
                print(f"{' ':15}  {str(result):90}")
        else:
            print(f"{arg:15}: {str(kwargs[arg]):90}")
    return input(f">> [y/n]")

if __name__ == "__main__":
    file_dir = check_file_dir()
    esp_settings = create_esp_settings()
    scan = perform_scan()
    if last_check(file_dir=file_dir, ipv4network=esp_settings, scan=scan) in positive_answer:
        msg = f"{bcolors.BOLD}{bcolors.OKGREEN}Looks like everything is set up and running. Have fun with espisy and ESPEasy{bcolors.ENDC}"
    else:
         msg = f"{bcolors.BOLD}{bcolors.FAIL}Huh... That should not have happened. Try running the script again or \
reach out for help on github{bcolors.ENDC}" 
    print(f"\n{msg:^150}\n")      