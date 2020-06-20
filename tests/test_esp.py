from unittest import TestCase
import unittest.main
import sys
import os
import logging
from time import sleep

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from espisy.core import ESP
from espisy.errors import ESPNotFoundError, NoGPIOError
from tests.constants import test_ip, test_name, test_gpio, test_state

logger = logging.getLogger(__name__)
fh = logging.FileHandler("test_details.log", "w")
formatter = logging.Formatter(
    "%(asctime)s %(name)s.%(funcName)s, line %(lineno)s \t %(levelname)s: %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)


class TestBasicESPFunctions(TestCase):
    def test_create_esp(self):
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        self.assertIn(esp.ip, ESP._device_register)
        self.assertIsInstance(esp, ESP)
        self.assertEqual(esp.ip, test_ip)

    def test_get_state(self):
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        if dummy == True:
            self.assertEqual(esp.state, test_state)
        else:
            logger.info(f"....ok:\n{esp.state}")

    def test_gpio_on(self):
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        answer = esp.gpio_on(test_gpio)
        if dummy == True:
            self.assertEqual(
                f"http://{test_ip}/control?cmd=GPIO,{test_gpio},1", answer)
        else:
            logger.info(f"....ok:\n{answer}")

    def test_gpio_off(self):
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        answer = esp.gpio_off(test_gpio)
        if dummy == True:
            self.assertEqual(
                f"http://{test_ip}/control?cmd=GPIO,{test_gpio},0", answer)
        else:
            logger.info(f"....ok:\n{answer}")

    def test_network_scan(self):
        pass


class TestESPSwitches(TestCase):

    def test_init_and_delete_switches(self):
        """Initializes and deletes a specific switchs"""
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        self.assertIn("door", esp._switches)
        self.assertIn("DHT", esp.sensors)
        self.assertEqual({"GPIO": None}, esp.delete_switch("door"))
        self.assertNotIn("door", esp._switches)

    def test_switch_on_off(self):
        """Try to turn the switch on and off."""
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        # raises NoGPIOError, because the gpio was not set
        self.assertRaises(NoGPIOError, esp.on, "door")
        # raises NoGPIOError, because the gpio was not set
        self.assertRaises(NoGPIOError, esp.off, "door")
        # map GPIO to the switch and test again.
        # The output should be the same as in gpio_on / gpio_off, as the functions
        # are called internally
        esp.map_gpio_to_switch("door", test_gpio)
        answer_on = esp.on("door")
        sleep(2)
        answer_off = esp.off("door")
        sleep(2)
        if dummy == True:
            self.assertEqual(
                f"http://{test_ip}/control?cmd=GPIO,{test_gpio},1", answer_on)
            self.assertEqual(
                f"http://{test_ip}/control?cmd=GPIO,{test_gpio},0", answer_off)
        else:
            answer_toggle = esp.toggle("door")
            logger.info(f"....ok:\n{answer_on}\n{answer_off}\n{answer_toggle}")

    def test_get_switch_state(self):
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        esp.map_gpio_to_switch("door", test_gpio)
        answer = esp.switch_state("door")
        if dummy == True:
            self.assertEqual(
                f"http://{test_ip}/control?cmd=status,gpio,{test_gpio}", answer)
        else:
            logger.info(f"....ok:\n{answer}")


class TestClassMethods(TestCase):
    def test_get_esp_by_ip(self):
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        self.assertRaises(ESPNotFoundError, ESP.get, "name not available")
        self.assertEqual(ESP.get(test_ip).name, test_name)

    def test_delete_esp(self):
        ESP.add(test_ip, dummy=dummy)
        esp = ESP.get(test_ip)
        deleted_esp = ESP.remove(test_ip)
        self.assertEqual(deleted_esp.name, test_name)
        self.assertNotIn(esp.ip, ESP._device_register)
        self.assertRaises(KeyError, ESP.remove, test_ip)


if __name__ == "__main__":
    if "--dummy" in sys.argv:
        dummy = True
        sys.argv.remove("--dummy")
    else:
        dummy = False
    if "--ip" in sys.argv:
        test_ip = sys.argv[sys.argv.index("--ip")+1]
        sys.argv.pop(sys.argv.index("--ip")+1)
        sys.argv.remove("--ip")
    unittest.main()
