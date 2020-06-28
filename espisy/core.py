"""ESP Module to virtualize ESPEasy devices"""

import os
from pathlib import Path
import json
import logging
import ipaddress
import threading
from typing import Union

import requests
import yaml

from .devices import Device
from .errors import ESPNotFoundError, NoGPIOError
from .constants import test_ip, test_name, test_state, test_gpio, config


logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(name)s.%(funcName)s, line %(lineno)s \t %(levelname)s: %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)

# Extract the filename for settings from the config. Set to Home directory on default
settings_dir = config.get("USER_SETTINGS", "file_dir")
if settings_dir == "default":
    settings_dir = os.path.join(Path.home(), ".espisy")
settings_file_name = os.path.join(settings_dir, "esp.yaml")


class ESP():
    """ESP class that can be used to access the state and control ESP devices within your network"""

    _device_register = {}
    _name_ip_map = {}

    def __init__(self, ip: str):
        """Initializing the ESP

        Parameters
        ----------
        ip : str
            The local ip where the ESP is reachable.
        """

        self.ip = ip
        self._state = None
        self.devices = []
        self.refresh()
        self.name = self._state["System"]["Unit Name"]

    def refresh(self):
        """Refreshes the state of the esp by requesting http://<self.ip>/json."""

        self._state = requests.get(f"http://{self.ip}/json").json()

    @property
    def state(self) -> dict:
        """Returns the state of the device.

        The method does not refresh via http request, but uses the stored information

        Returns
        -------
        dict
            self._state
        """
        return self._state

    @property
    def devices(self):
        """Returns all devices of an ESP"""
        return self.devices

    @state.setter
    def state(self, value):
        """A refresh is triggered"""
        logger.error("Setting not permitted. Refresh triggered")
        self.refresh()

    def gpio_on(self, gpio: int) -> dict:
        """Turn a GPIO on. This is a very basic function. If you want to access an ESPEasy switch use on, off or toggle instead.

        Parameters
        ----------
        gpio : int
            GPIO number of the ESP to turn on

        Returns
        -------
        dict
            Answer of the ESP as json.
        """

        if gpio == None:
            raise NoGPIOError
        cmd_url = f"http://{self.ip}/control?cmd=GPIO,{gpio},1"
        answer = requests.get(cmd_url)
        try:
            answer = answer.json()
            return answer["state"]
        except json.decoder.JSONDecodeError as e:
            print(f"An error occured. Could not verify json data: {e}")
            answer = answer.text
            return answer

    def gpio_off(self, gpio: int) -> dict:
        """Turn a GPIO off. This is a very basic function. If you want to access an ESPEasy switch use on, off or toggle instead.

        Parameters
        ----------
        gpio : int
            GPIO number of the ESP to turn off

        Returns
        -------
        str
            Answer of the ESP as json.
        """

        if gpio == None:
            raise NoGPIOError
        cmd_url = f"http://{self.ip}/control?cmd=GPIO,{gpio},0"
        answer = requests.get(cmd_url)
        try:
            answer = answer.json()
            return answer["state"]
        except json.decoder.JSONDecodeError as e:
            print(f"An error occured. Could not verify json data: {e}")
            answer = answer.text
            return answer

    def gpio_state(self, gpio: int) -> dict:
        """Returns the state of the given GPIO

        Normally returns dict. At the moment (V0.3.0) the JSON answer from ESPEasy is broken. Will return str instead

        Parameters
        ----------
        gpio : int
            GPIO number

        Returns
        -------
        dict
            JSON answer from ESPEasy

        Raises
        ------
        NoGPIOError
            If no GPIO is given
        """

        if gpio == None:
            raise NoGPIOError
        cmd_url = f"http://{self.ip}/control?cmd=status,gpio,{gpio}"
        answer = requests.get(cmd_url)
        try:
            answer = answer.json()
            return answer["state"]
        except json.decoder.JSONDecodeError as e:
            print(f"An error occured. Could not verify json data: {e}")
            answer = answer.text
            start = answer.find('"state": ')+9
            return answer[start:start+1]

    def _toggle(self, gpio: int) -> dict:
        """Toggles a switch or GPIO

        You can pass the name of the switch or the number of the GPIO

        Parameters
        ----------
        switch : Union[str, int]
            pass the switch name as str or the number of the GPIO as int

        Returns
        -------
        dict
            JSON answer from ESPEasy. (If JSON answer from ESPEasy is broken, returns string)

        Raises
        ------
        NoGPIOError
            If no GPIO was mapped to the switch
        """

        if gpio == None:
            raise NoGPIOError(f"No GPIO mapped to the switch {switch}")
        else:
            cmd_url = f"http://{self.ip}/control?cmd=gpiotoggle,{gpio}"
            answer = requests.get(cmd_url)
            try:
                answer = answer.json()
                return answer
            except json.JSONDecoder.JSONDecodeError as e:
                logger.info(f"Could not encode answer to json. ({e})")
                answer = answer.text
                return answer

    def device(self, device_name: str, **kwargs) -> Device:
        """Create a device

        Fire and forget. The esp keeps track of the device. You can always access it with its name afterwards.
        The first call of device("led") will create a device with name led. The second call will return this device again.
        This means that you cannot create two devices with the same name. (Not recommended in ESPEasy as well)

        Parameters
        ----------
        device_name : str
            Name of the device
        **kwargs : dict, str
            You can (and sometimes need to) pass further arguments
            like device_type="<type>" or settings={"<name>":<value>}

        Returns
        -------
        Device
            Returns the device that was created
        """

        for device in self.devices:
            if device_name == device["name"]:
                return device["instance"]
        device = Device(name=device_name, parent=self, **kwargs)
        self.devices.append({"name": device_name, "device_class": device.device_class,
                             "settings": device.settings, "instance": device})
        return device

    def save_settings(self):
        """Save the settings to the esp.yaml configuration file

        The path where the settings should be stored can be defined in esp.ini.
        The standard behaviour for all save files is  ~home/.espisy/
        This method overwrites the old settings.
        """

        filename = os.path.join(config.get(
            "USER_SETTINGS", "file_dir"), "esp.yaml")
        with open(filename, "r") as save_file:
            settings = yaml.safe_load(save_file)
        if "esps" not in settings:
            settings.update({"esps": []})
        # Check if the settings have already been saved and update or append the current settings
        saved_esp_setting = next(((i, dictionary) for i, dictionary in enumerate(
            settings["esps"]) if self.ip in dictionary), None)
        if saved_esp_setting == None:

            settings["esps"].append({self.ip: {"devices": [{key: value for key, value in device.items(
            ) if key != "instance"} for device in self.devices]}})
        else:
            settings["esps"][saved_esp_setting[0]].update(
                {self.ip: {"devices": [{key: value for key, value in device.items() if key != "instance"} for device in self.devices]}})
        with open(filename, "w") as save_file:
            yaml.dump(settings, save_file)

    def event(self, event: str) -> str:
        """Triggers a event that can be fetched by a rule defined in ESPEasy

        Parameters
        ----------
        event : str
            Name of the event to trigger

        Returns
        -------
        str
            HTML response
        """

        cmd_url = f"http://{self.ip}/control?cmd=event,{event}"
        answer = requests.get(cmd_url)
        return answer

    def send_command(self, cmd: str) -> str:
        """Send a command to the ESPEasy device

        Any command that is not covered within the ESP class can be send via this function.
        It provides the address of the ESP.

        Parameters
        ----------
        cmd : str
            The command string that comes behind http://ip/

        Returns
        -------
        str
            Returns the answer of the ESPEasy device
        """

        cmd_url = f"http://{self.ip}/{cmd}"
        answer = requests.get(cmd_url)
        try:
            answer = answer.json()
            return answer
        except json.JSONDecoder.JSONDecodeError as e:
            logger.info(f"Could not encode answer to json. ({e})")
            answer = answer.text
            return answer

    def load_settings(self):
        """Try to load settings from esp.yaml

        If you created devices, they will be automatically generated with this method.
        This method is automatically invoked by the scan_network method
        """

        filename = os.path.join(config.get(
            "USER_SETTINGS", "file_dir"), "esp.yaml")
        with open(filename, "r") as save_file:
            settings = yaml.safe_load(save_file)
        for esp in settings["esps"]:
            for ip, details in esp.items():
                if ip == self.ip:
                    for device in details["devices"]:
                        self.device(
                            device["name"], device_type=device["device_class"], settings=device["settings"])

    @ classmethod
    def get(cls, ip):
        """Classmethod. Search for a specific ESP with the IP address <ip>

        Parameters
        ----------
        ip : str
            IP address that the ESP was mapped to

        Returns
        -------
        ESP
            The ESP that was found

        Raises
        ------
        ESPNotFoundError
            Raised when no ESP was found
        """

        if ip in cls._name_ip_map:  # if the name of the ESPEasy device is passed instead of the ip,
            ip = cls._name_ip_map[ip]  # get the ip address from the map
        esp_found = cls._device_register.get(ip, None)
        if esp_found == None:
            raise ESPNotFoundError
        return esp_found

    @ classmethod
    def remove(cls, ip):
        """Classmethod. Simple wrapper to pop the ESP with ip

        Parameters
        ----------
        ip : str
            IP to look for

        Returns
        -------
        ESP
            The ESP that was poppped
        """

        esp_deleted = cls._device_register.pop(ip)
        print(cls._name_ip_map.pop(esp_deleted.name))
        return esp_deleted

    @ classmethod
    def add(cls, ip):
        """Classmethod. Should always be used.

        Especially necessary if the function of the device register is used.

        Parameters
        ----------
        ip : str
            ip address of the ESP device
        """

        lock = threading.Lock()
        lock.acquire()
        name = requests.get(
            f"http://{ip}/json").json()["System"]["Unit Name"]
        cls._name_ip_map.update({name: ip})
        esp = ESP(ip)
        cls._device_register.update({ip: esp})
        lock.release()

    @ classmethod
    def scan_network(cls, network: ipaddress.IPv4Network = None, timeout=3):
        """Scans the network for any ESPEasy device and creates ESP instances

        The method scans all hosts in the given ipaddress.IPv4Network.
        You can pass the network as argument or define it in the esp.yaml configuration file.
        E.g. ipv4network: 192.168.0.0/24
        **If you do not pass the network as an argument and do not have it defined in the .yaml file, this method does
        not work.**
        Be sure to use the right network. The method does not perform any checks on the network!

        Parameters
        ----------
        network : ipaddress.IPv4Network, optional
            Pass the network or leave it as None and configure it in esp.yaml, by default None
        timeout : int, optional
            the time for the request to wait for an answer, by default 1
        """

        # if no network is passed, try to find the network in the configuration file.
        # log and return if not possible.
        if network == None:
            try:
                with open(settings_file_name, "r") as f:
                    ipv4network_string = yaml.safe_load(f)["ipv4network"]
                if ipv4network_string == None:
                    logger.error("No subnet is set in the config file.")
                    return
                network = ipaddress.ip_network(ipv4network_string)
            except FileNotFoundError as fnferror:
                logger.error(f"File {settings_file_name} does not exist")
                return
            except KeyError as kerror:
                logger.error("ipv4network not defined")
                return

        # start a single thread for each ip address in the network and validate the answer on <ip>:80/json
        threads = []
        try:
            with open(settings_file_name) as settings_file:
                settings = yaml.safe_load(settings_file)
        except Exception as e:
            logger.error(e, exc_info=1)
        for host in network:
            t = threading.Thread(
                target=cls.__connect_validate_ipv4_address, args=(host, timeout, settings))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    @ classmethod
    def __connect_validate_ipv4_address(cls, host: ipaddress.IPv4Address, timeout: int, settings=None):
        """Internal function to knock at port 80 and check if the answer is ESPEasy-like"""
        try:
            response = requests.get(
                f"http://{host}/json", timeout=timeout).json()
            name = response["System"]["Unit Name"]
            if name:
                if name in cls._name_ip_map:
                    logger.info(
                        f"{name} already exists. Please rename the ESPEasy device at {host.exploded} and scan again.")
                else:
                    ESP.add(host.exploded)
                    # Try to find old settings and apply
                    esp = ESP.get(host.exploded)
                    # Check if the settings have already been saved and update or append the current settings
                    try:
                        esp.load_settings()
                    except Exception as e:
                        logger.exception(f"An Exception occured: {e}")

        except (json.JSONDecodeError, requests.ConnectTimeout, KeyError, requests.ConnectionError) as error:
            pass  # logger.debug(f"did not find a device at {host}")
