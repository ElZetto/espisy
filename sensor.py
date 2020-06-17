"""Sensor Module

The module consists of a single Sensor class that is used to virtualize sensors that can be implemented
within the ESPEasy device.

.. note::
        There is no function to refresh a single Sensor.
        This behaviour is intended, so you do not have to refresh every single sensor and get lost in managing them.

"""

class Sensor():
    """Class that virtualizes any sensor.

    The class copies the **current state** of the sensor.
    Recommended usage is to do a single refresh of the ESP and refer to all sensors you need via :meth:`espisy.esp.ESP.sensor` method.
    """

    def __init__(self, name, state):
        self.name = name
        self.state = state
        self.data = {task["Name"]: task["Value"] for task in state}

    @property
    def temperature(self):
        """Returns the value of the TaskValue "Temperature" if available"""
        for TaskValue in self.state:
            if "temperature" in TaskValue["Name"].lower():
                return TaskValue["Value"]
        raise AttributeError(
            f"sensor {self.name} has no attribute temperature")

    @property
    def humidity(self):
        """Returns the value of the TaskValue "Humidity" if available"""
        for TaskValue in self.state:
            if "humidity" in TaskValue["Name"].lower():
                return TaskValue["Value"]
        raise AttributeError(f"sensor {self.name} has no attribute humidity")

    def feature(self, feature_name):
        """Returns the value of the TaskValue <feature_name> if available"""
        for TaskValue in self.state:
            if feature_name.lower() in TaskValue["Name"].lower():
                return TaskValue["Value"]
        raise AttributeError(
            f"sensor {self.name} has no attribute {feature_name}")
