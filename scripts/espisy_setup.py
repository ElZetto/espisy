import os
import sys
import ipaddress
from pathlib import Path

import yaml
import colorama
from colorama import Fore, Back, Style
from colorama import init as colorama_init
colorama_init()

espisy_path = os.path.join(os.path.abspath(
os.path.dirname(__file__)), os.pardir)
sys.path.append(espisy_path)

from espisy.constants import config, config_file_name
from espisy.core import ESP

config.get("DEFAULT", "file_dir")
positive_answer = ["y", "yes", "j", "ja"]

def check_file_dir():
    file_dir = config.get("USER_SETTINGS", "file_dir")
    new_dir = os.path.join(Path.home(), ".espisy")
    if file_dir == "default":
        done = False
        # Dialog ask for standard directory
        while not done:
            msg = f"""{Style.BRIGHT}Do you want to change the directory for files that espisy will save? 
    Current directory is {new_dir}\n[y/n]{Style.RESET_ALL}\n (You need to restart the script afterwards)."""
            print(msg)
            if input(">>> ").lower() in positive_answer:
                print(f"{Style.BRIGHT}Please enter new directory.{Style.RESET_ALL}")
                new_dir = input(">>> ")
                if not os.path.isdir(new_dir):
                    print(f"{Style.BRIGHT}Create directory {new_dir}?\n[y/n]{Style.RESET_ALL}")
                    if input(">>> ").lower() in positive_answer:
                        os.mkdir(new_dir)
                config.set("USER_SETTINGS", "file_dir", new_dir)
                with open(config_file_name, "w") as config_file:
                    config.write(config_file)
                print(f"{Fore.LIGHTGREEN_EX}Directory created. Please restart the script.{Style.RESET_ALL}")
                sys.exit(0)
            else:
                done = True
    else:
        new_dir = file_dir
        pass
    if not os.path.isdir(new_dir):
        print(f"{Style.BRIGHT}Create directory {new_dir}?\n[y/n]{Style.RESET_ALL}")
        if input(">>> ").lower() in positive_answer:
            os.mkdir(new_dir)
    config.set("USER_SETTINGS", "file_dir", new_dir)
    with open(config_file_name, "w") as config_file:
        config.write(config_file)
    return new_dir
#! /usr/bin/env python3



def create_esp_settings():
    settings_file_name = os.path.join(config.get(
        "USER_SETTINGS", "file_dir"), "esp.yaml")
    try:
        with open(settings_file_name, "r") as settings_file:
            settings = yaml.safe_load(settings_file)
            if settings == None:
                settings = {}
    except FileNotFoundError as e:
        print(f"{Fore.YELLOW}Info: Could not finde file {settings_file_name} {e}{Style.RESET_ALL}")
        settings = {}
# Check if a ipv4network settings already exists and ask if it should be kept. Returns the ipv4network
    if settings.get("ipv4network", None) != None:
        print(f"{Style.BRIGHT}Do you want to keep the current config {settings.get('ipv4network',None)}?\n[y/n]{Style.RESET_ALL}")
        if input(">>> ").lower() in positive_answer:
            return settings.get("ipv4network", "ERROR")
# Setup network if there was no network before
    msg = f"""{Style.BRIGHT}Do you want to set a subnet that will be used for the scanning?
If you do not set one, the scanning function will not work.\n[y/n]{Style.RESET_ALL}"""
    print(msg)
    if input(">>> ").lower() in positive_answer:
        print(
            f"{Style.BRIGHT}Please enter new subnet like this: 192.0.0.0/24{Style.RESET_ALL}")
        ipv4network = input(">>> ")
        try:
            ipaddress.IPv4Network(ipv4network)
        except Exception as e:
            print(
                f"{Fore.RED}That did not work. Wrong syntax in '{ipv4network}'?\nException: {e}{Style.RESET_ALL}")
        settings.update({"ipv4network": ipv4network})
    else:
        ipv4network = "not set"
# write the new settings to esp.yaml
    with open(settings_file_name, "w") as settings_file:
        yaml.dump(settings, settings_file)
    return ipv4network


def perform_scan():
    print(f"{Style.BRIGHT}Do you want to perform a scan for ESPs now?\n[y/n]{Style.RESET_ALL}")
    if input(">>> ").lower() in positive_answer:
        ESP.scan_network()
        msg_length = len(f"| ESP | {' ':20} | {' ':20}|")
        line = "+" + "-"*(msg_length-2) + "+"
        print(
            f"\n{Style.BRIGHT}Found the following ESPEasy devices.{Style.RESET_ALL}")
        print(line)
        for ip, esp in ESP._device_register.items():
            message = f"| ESP | {Fore.BLUE}{esp.name:^20}{Style.RESET_ALL} | {Fore.BLUE}{ip:^20}{Style.RESET_ALL}|"
            print(message)
            print(line)
        return [(device.ip, device.name) for device in ESP._device_register.values()]
    else:
        return "not performed"


def last_check(**kwargs):
    print(f"{Style.BRIGHT}Please take a look if the settings are correct:\n[y/n]{Style.RESET_ALL}")
    for arg in kwargs:
        if isinstance(kwargs[arg], (list, dict, type({}.items()))):
            print(f"{arg:15}: ")
            for result in kwargs[arg]:
                print(f"{' ':15}  {str(result):90}")
        else:
            print(f"{arg:15}: {str(kwargs[arg]):90}")
    return input(">>> ")


if __name__ == "__main__":
    file_dir = check_file_dir()
    esp_settings = create_esp_settings()
    scan = perform_scan()
    if last_check(file_dir=file_dir, ipv4network=esp_settings, scan=scan) in positive_answer:
        msg = f"{Style.BRIGHT}{Fore.GREEN}Looks like everything is set up and running. Have fun with espisy and ESPEasy{Style.RESET_ALL}"
    else:
        msg = f"{Style.BRIGHT}{Fore.RED}Huh... That should not have happened. Try running the script again or \
reach out for help on github{Style.RESET_ALL}"
    print(f"\n{msg:^150}\n")
    t = input()
