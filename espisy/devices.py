value_names = {"Thermometer": "Temperature",
               "Barometer": "Pressure",
               "Hygrometer": "Humidity",
               "Rotary": "Counter"}


class Device():
    """Standard Device class that implements basic properties.

    The Device class implements basic properties, like name, parent or settings
    """

    def __new__(cls, name, parent, device_type="auto", *args, **kwargs):
        if device_type == "auto":
            for task in parent.state["Sensors"]:
                if task["TaskName"].lower() == name.lower():
                    if task["Type"] in device_name_class_map:
                        return object.__new__(device_name_class_map[task["Type"]])
                    else:
                        print(f"found no device of type {task['Type']}")
        else:
            return object.__new__(device_name_class_map[device_type])

    def __init__(self, name, parent, *args, **kwargs):
        self.name = name
        self.parent = parent
        self.settings = {}

    @property
    def device_class(self):
        """Returns the names of all classes the device inherits"""
        return type(self).__name__

    @property
    def state(self):
        """Returns the (static) state of the device taken from the esp json output"""
        for state in self.parent.state["Sensors"]:
            if state["TaskName"] == self.name:
                return state
        return None

    def refresh(self):
        """Refreshes the parent ESP device.

        The function only reads the json output again. The ESP Easy device will only refresh on its set interval
        """
        self.parent.refresh()


class Thermometer(Device):
    """Thermometer class

    Implements property temperature
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @ property
    def temperature(self):
        """Returns the value of the temperature"""
        for task in self.state["TaskValues"]:
            if task["Name"] == value_names["Thermometer"]:
                return task["Value"]


class Hygrometer(Device):
    """Hygrometer class

    Implements property humidity
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @ property
    def humidity(self):
        """Returns the value of the humidity"""
        for task in self.state["TaskValues"]:
            if task["Name"] == value_names["Hygrometer"]:
                return task["Value"]


class Barometer(Device):
    """Barometer class

    Implements property pressure
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @ property
    def pressure(self):
        """Returns the value of the pressure"""
        for task in self.state["TaskValues"]:
            if task["Name"] == value_names["Barometer"]:
                return task["Value"]


class DS18b20(Thermometer, Device):
    """DS18b20 class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DHT(Thermometer, Hygrometer, Device):
    """DHT class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MLX90614(Thermometer, Device):
    """MLX90614 class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BMP085(Thermometer, Barometer, Device):
    """BMP085 class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BMx280(Thermometer, Barometer, Hygrometer, Device):
    """BMx280 class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MS5611(Thermometer, Barometer, Device):
    """MS5611 class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Switch(Device):
    """Generic switch class

    Used to track input switches that were setup in the ESPEasy
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def pinstate(self):
        """Returns the pinstate of the switch"""
        return self.state["TaskValues"][0]["Value"]


class GPIO(Device):
    """Generic GPIO class to control GPIO output.

    This class differs from switch, because GPIOs pinstate function will always be the updated state.
    This class cannot be generated automatically. In order to create a GPIO, you have to call the Device constructor manually.
    Device(<name>, <parent>, device_type="GPIO",settings={"pin":<gpio>}) where <name>, <parent> and <gpio> must be correct will
    give you a GPIO device.
    If you call the device method of an espisy.ESP instance, you do not need to pass the parent.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings.update(kwargs["settings"])

    def on(self):
        """Set GPIO high"""
        self.parent.gpio_on(self.settings["pin"])

    def off(self):
        """Set GPIO low"""
        self.parent.gpio_off(self.settings["pin"])

    def toggle(self):
        """Toggle GPIO state"""
        self.parent._toggle(self.settings["pin"])

    @property
    def pinstate(self):
        """Returns the current GPIO state

        This call always gets the current state from your ESPEasy device.
        """
        return self.parent.gpio_state(self.settings["pin"])


class Display(Device):
    """Class for a Display with 2004 driver or OLED display"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def text(self, row: int, column: int, text: str):
        """Sets the Displays text

        Parameters
        ----------
        row : int
            row to start the text, starting at 1
        column : int
            column to start the text, starting at 1
        text : str
            Text to display
        """
        cmd = f"control?cmd=LCD,{row},{column},{text}"
        self.parent.send_command(cmd)

    def clear(self):
        """Clears the display"""
        cmd = f"control?cmd=LCDCMD,clear"
        self.parent.send_command(cmd)

    def on(self):
        """Switches the Display light on"""
        cmd = f"control?cmd=LCDCMD,on"
        self.parent.send_command(cmd)

    def off(self):
        """Switches the Display light off"""
        cmd = f"control?cmd=LCDCMD,off"
        self.parent.send_command(cmd)


class Rotary(Device):
    """Class for rotary encoders"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def counter(self):
        """Returns the counter value of the device"""
        for task in self.state["TaskValues"]:
            if task["Name"] == value_names["Rotary"]:
                return task["Value"]


class MQTT(Device):
    """Class for generig MQTT listener"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def message(self):
        """Returns all available values (4 at the moment) as a list of tuples with [(Name,Value) for task in TaskValues]"""
        return [(task["Name"], task["Value"]) for task in self.state["TaskValues"]]


device_name_class_map = {
    "DHT": DHT,
    "Environment - DHT11/12/22  SONOFF2301/7021": DHT,
    "Environment - DHT12 (I2C)": DHT,
    "Switch": Switch,
    "Switch input - Switch": Switch,
    "Display": Display,
    "Display - LCD2004": Display,
    "Display - OLED SSD1306":Display,
    "Display - OLED SSD1306/SH1106 Framed": Display,
    "GPIO": GPIO,
    "Rotary": Rotary,
    "Switch Input - Rotary Encoder": Rotary,
    "MQTT": MQTT,
    "Generic - MQTT Import": MQTT}
