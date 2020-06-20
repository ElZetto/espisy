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

from .sensor import Sensor
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
    settings_dir = Path.home()
settings_file_name = os.path.join(settings_dir, "esp.yaml")


class ESP():
    """ESP class that can be used to access the state and control ESP devices within your network"""

    _device_register = {}
    _name_ip_map = {}

    def __init__(self, ip: str, dummy=False):
        """Initializing the ESP

        Parameters
        ----------
        ip : str
            The local ip where the ESP is reachable.
        dummy : bool, optional
            If set to True, a dummy ESP will be set up. Used for testing, by default False
        """

        if dummy == True:
            self.__set_up_dummy()
        else:
            self.ip = ip
            self._is_dummy = False
            self._state = None
            self._switches = {}
            self.refresh()
            self._initialize_switches()
            self.name = self._state["System"]["Unit Name"]

    def __set_up_dummy(self):
        """Sets all properties to dummy values. Used with testing"""
        self.ip = test_ip
        self.name = test_name
        self._is_dummy = True
        self._switches = {}
        self._state = test_state
        self._initialize_switches()

    def refresh(self):
        """Refreshes the state of the esp by requesting http://<self.ip>/json."""

        if self._is_dummy:
            logger.debug("Instance is a dummy. Test_state will be returned")
            return 0
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
    def sensors(self) -> list:
        """Returns a list of all sensors read from self._state.

        Returns
        -------
        list
            List of all sensors read at the last refresh.
        """
        sensors = [sensor["TaskName"]for sensor in self._state["Sensors"]]
        return sensors

    @state.setter
    def state(self, value):
        """The state of an ESP can only be set if it is a dummy. Otherwise a refresh is triggered"""
        logger.error("Setting not permitted. Refresh triggered")
        if self._is_dummy:
            self._state = value
        else:
            self.refresh()

    def gpio_on(self, gpio) -> dict:
        """Turn a GPIO on. This is a very basic function. If you want to access an ESPEasy switch use on, off or toggle instead.

        Parameters
        ----------
        gpio : int
            GPIO number of the ESP to turn on

        Returns
        -------
        dict
            Answer of the ESP as json. Returns the cmd_url if instance is a dummy
        """

        if gpio == None:
            raise NoGPIOError
        cmd_url = f"http://{self.ip}/control?cmd=GPIO,{gpio},1"
        if self._is_dummy:
            return cmd_url
        answer = requests.get(cmd_url).json()
        return answer

    def gpio_off(self, gpio) -> dict:
        """Turn a GPIO off. This is a very basic function. If you want to access an ESPEasy switch use on, off or toggle instead.

        Parameters
        ----------
        gpio : int
            GPIO number of the ESP to turn off

        Returns
        -------
        str
            Answer of the ESP as json. Returns the cmd_url if instance is a dummy
        """

        if gpio == None:
            raise NoGPIOError
        cmd_url = f"http://{self.ip}/control?cmd=GPIO,{gpio},0"
        if self._is_dummy:
            return cmd_url
        answer = requests.get(cmd_url).json()
        return answer

    def _initialize_switches(self) -> dict:
        """The function initializes all switches.

        It looks for all Sensors in the ESP state that have "switch" in Type and
        appends them to self._switches. Needed for the easier access via on(switchname) off(switchname) and toggle(switchname)

        Returns
        -------
        dict
            The only time self._switches is returned
        """

        for sensor in self.state["Sensors"]:
            if "switch" in sensor["Type"].lower():
                self._switches.update(
                    {sensor["TaskName"]: {"GPIO": None}})
        return self._switches

    def delete_switch(self, name) -> dict:
        """Simple wrapper to pop the switch with <name> from the _switches dictionary.

        Parameters
        ----------
        name : str
            name of the switch to pop

        Returns
        -------
        dict
            returns the values of the popped item
        """

        switch = self._switches.pop(name)
        return switch

    def map_gpio_to_switch(self, switch, gpio):
        """This function needs to be called in order to map a GPIO to the switch.

        Since it is not possible to find out the GPIO pin of a task via ESPEasy, you need to
        map the GPIO pin to the switch on your own, if you want to manipulate it.
        Reading the switch state is possible without mapping a GPIO to it.

        Parameters
        ----------
        switch : str
            name of the switch that the GPIO should be mapped to (The name that you gave it in ESPEasy)
        gpio : int
            GPIO that should be mapped to it (was also set in ESPEasy)
        """

        self._switches[switch]["GPIO"] = gpio

    def on(self, switch) -> dict:
        """Turns a specific switch on

        Parameters
        ----------
        switch : str
            Name of the switch

        Returns
        -------
        dict
            JSON answer from ESP

        Raises
        ------
        NoGPIOError
            If no GPIO was mapped to the switch
        """

        gpio = self._switches[switch]["GPIO"]
        if gpio == None:
            raise NoGPIOError(f"No GPIO mapped to the switch {switch}")
        answer = self.gpio_on(gpio)
        return answer

    def off(self, switch) -> dict:
        """Turns a specific switch off

        Parameters
        ----------
        switch : str
            Name of the switch

        Returns
        -------
        dict
            JSON answer from ESP

        Raises
        ------
        NoGPIOError
            If no GPIO was mapped to the switch
        """

        gpio = self._switches[switch]["GPIO"]
        if gpio == None:
            raise NoGPIOError(f"No GPIO mapped to the switch {switch}")
        answer = self.gpio_off(gpio)
        return answer

    def toggle(self, switch: Union[str, int]) -> dict:
        """Toggles a switch or GPIO

        You can pass the name of the switch or the number of the GPIO

        Parameters
        ----------
        switch : Union[str, int]
            pass the switch name as str or the number of the GPIO as int

        Returns
        -------
        dict
            JSON answer from ESPEasy

        Raises
        ------
        NoGPIOError
            If no GPIO was mapped to the switch
        """
        if switch in self._switches:
            gpio = self._switches.get(switch, None)["GPIO"]
        elif isinstance(switch, int):
            gpio = switch
        if gpio == None:
            raise NoGPIOError(f"No GPIO mapped to the switch {switch}")
        else:
            cmd_url = f"http://{self.ip}/control?cmd=gpiotoggle,{gpio}"
            answer = requests.get(cmd_url).json()
            return answer

    def switch_state(self, switch) -> dict:
        """Sends a get request to the esp and returns the status of the switch.

        Parameters
        ----------
        switch : str
            name of the switch

        Returns
        -------
        dict
            the json answer from ESPEasy

        Raises
        ------
        NoGPIOError
            Raised if no GPIO is mapped to the switch
        """

        gpio = self._switches[switch]['GPIO']
        if gpio == None:
            raise NoGPIOError
        if self._is_dummy:
            return f"http://{self.ip}/control?cmd=status,gpio,{gpio}"
        answer = requests.get(
            f"http://{self.ip}/control?cmd=status,gpio,{gpio}").json()
        return answer

    def sensor_state(self, sensor_name, refresh=True) -> dict:
        """Returns a sensor state from self._state

        In standard behaviour the function refreshes self._state before the sensor state is returned

        Parameters
        ----------
        sensor_name : str
            name of the sensor to be looked up
        refresh : bool, optional
            defines if a refresh should be done first, by default True

        Returns
        -------
        dict
            the sensor dictionary
        """

        if refresh == True:
            self.refresh()
        for sensor in self._state["Sensors"]:
            if sensor["TaskName"] == sensor_name:
                return sensor["TaskValues"]

    def sensor(self, sensor_name, refresh=False) -> Sensor:
        """Returns a sensor object of the given sensor name.

        Calls sensor_state with refresh=False internally.
        In standard behaviour, the function DOES NOT refresh self._state

        Parameters
        ----------
        sensor_name : str
            name of the sensor to look for
        refresh : bool, optional
            defines if a refresh should be done first, by default False

        Returns
        -------
        Sensor
            Returns an object of class Sensor (see sensor.py)
        """

        sens = Sensor(sensor_name, self.sensor_state(sensor_name, refresh))
        return sens

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
            settings["esps"].append({self.ip: {"switches": self._switches}})
        else:
            settings["esps"][saved_esp_setting[0]].update(
                {self.ip: {"switches": self._switches}})
        with open(filename, "w") as save_file:
            yaml.dump(settings, save_file)

    def event(self, event: str) -> str:
        cmd_url = f"http://{self.ip}/control?cmd=event,{event}"
        answer = requests.get(cmd_url)
        return answer

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
    def add(cls, ip, dummy=False):
        """Classmethod. Should always be used.

        Especially necessary if the function of the device register is used.

        Parameters
        ----------
        ip : str
            ip address of the ESP device
        dummy : bool, optional
            If set to True, a dummy ESP will be set up. Used for testing, by default False
        """
        name = requests.get(
            f"http://{ip}/json").json()["System"]["Unit Name"]
        cls._name_ip_map.update({name: ip})
        cls._device_register.update({ip: ESP(ip, dummy)})

    @ classmethod
    def scan_network(cls, network: ipaddress.IPv4Network = None, timeout=1):
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
                    saved_esp_setting = next(
                        (d for d in settings["esps"] if esp.ip in d), None)
                    if saved_esp_setting == None:
                        return
                    else:
                        for switch in esp._switches:
                            try:
                                esp.map_gpio_to_switch(switch, saved_esp_setting[host.exploded].get(
                                    "switches").get(switch, None).get("GPIO", None))
                            except AttributeError:
                                logger.info(
                                    f"Did not find any information for {switch} at {esp.ip} in the config file")

        except (json.JSONDecodeError, requests.ConnectTimeout, KeyError, requests.ConnectionError) as error:
            pass  # logger.debug(f"did not find a device at {host}")
