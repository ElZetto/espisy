"""ESP Module to virtualize ESPEasy devices"""

import os
import json
import logging
import ipaddress

import requests

from .sensor import Sensor
from .errors import ESPNotFoundError, NoGPIOError
from .constants import test_ip, test_name, test_state, test_gpio


logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(name)s.%(funcName)s, line %(lineno)s \t %(levelname)s: %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)


class ESP():
    """ESP class that can be used to access the state and control ESP devices within your network"""

    _device_register = {}

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
            self.name = test_name
            self._is_dummy = False
            self._state = None
            self._switches = {}
            self.refresh()
            self._initialize_switches()

    def __set_up_dummy(self):
        """Sets all properties to dummy values. Used with testing"""
        self.ip = test_ip
        self.name = test_name
        self._is_dummy = True
        self._switches = {}
        self._state = test_state
        self._initialize_switches()

    def refresh(self):
        """Refreshes the state of the esp by requesting http://<self.ip>/json.

        Returns
        -------
        int
            0 if ESP is a dummy, 1 if not
        """

        if self._is_dummy:
            logger.debug("Instance is a dummy. Test_state will be returned")
            return 0
        self._state = requests.get(f"http://{self.ip}/json").json()
        return self.state

    @property
    def state(self):
        """Returns the state of the ESP"""
        return self._state

    @property
    def sensors(self):
        """Returns a dictionary of all sensors."""
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

    def gpio_on(self, gpio):
        """Turn a GPIO on. This is a very basic function. If you want to access an ESPEasy switch use on, off or toggle instead.

        Parameters
        ----------
        gpio : int
            GPIO number of the ESP to turn on

        Returns
        -------
        str
            answer of the ESP. "dummy" if instance is a dummy
        """

        if gpio == None:
            raise NoGPIOError
        cmd_url = f"http://{self.ip}/control?cmd=GPIO,{gpio},1"
        if self._is_dummy:
            return cmd_url
        answer = requests.get(cmd_url).json()
        return answer

    def gpio_off(self, gpio):
        """Turn a GPIO off. This is a very basic function. If you want to access an ESPEasy switch use on, off or toggle instead.

        Parameters
        ----------
        gpio : int
            GPIO number of the ESP to turn off

        Returns
        -------
        str
            answer of the ESP. "dummy" if instance is a dummy
        """

        if gpio == None:
            raise NoGPIOError
        cmd_url = f"http://{self.ip}/control?cmd=GPIO,{gpio},0"
        if self._is_dummy:
            return cmd_url
        answer = requests.get(cmd_url).json()
        return answer

    def _initialize_switches(self):
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

    def delete_switch(self, name):
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

    def on(self, switch):
        """Turns a specific switch on

        Parameters
        ----------
        switch : str
            name of the switch to be turned on
        """

        gpio = self._switches[switch]["GPIO"]
        answer = self.gpio_on(gpio)
        return answer

    def off(self, switch):
        """Turns a specific switch off

        Parameters
        ----------
        switch : str
            name of the switch to be turned off
        """

        gpio = self._switches[switch]["GPIO"]
        answer = self.gpio_off(gpio)
        return answer

    def toggle(self, switch):
        """Toggles a specific switch

        Parameters
        ----------
        switch : str
            name of the switch to be toggled
        """

        state = self.switch_state(switch)
        if state["state"] == 0:
            answer = self.on(switch)
        else:
            answer = self.off(switch)
        return answer

    def switch_state(self, switch):
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

    def sensor_state(self, sensor_name, refresh=True):
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

    def sensor(self, sensor_name, refresh=False):
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

    @classmethod
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

        esp_found = cls._device_register.get(ip, None)
        if esp_found == None:
            raise ESPNotFoundError
        return esp_found

    @classmethod
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
        return esp_deleted

    @classmethod
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

        cls._device_register.update({ip: ESP(ip, dummy)})

    @classmethod
    def scan_network(cls, network: ipaddress.IPv4Network=None, timeout=1):
        if network == None:
            network = ipaddress.ip_network("192.168.178.0/23")
        
        for host in network:
            try:
                response = requests.get(
                    f"http://{host}/json", timeout=timeout).json()
                if response["System"]["Unit Name"]:
                    print(f"found {response['System']['Unit Name']} at {host}")
            except (json.JSONDecodeError, KeyError, requests.ConnectTimeout, KeyboardInterrupt) as error:
                logger.error(f"no ESPEasy device at {host}")