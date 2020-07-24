from tests.constants import test_name, test_gpio
from espisy.errors import ESPNotFoundError, NoGPIOError
from espisy.core import ESP
from unittest import TestCase
import unittest.main
import sys
import os
import logging
from time import sleep

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))


logger = logging.getLogger(__name__)
fh = logging.FileHandler("test_details.log", "w")
formatter = logging.Formatter(
    "%(asctime)s %(name)s.%(funcName)s, line %(lineno)s \t %(levelname)s: %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.setLevel(logging.DEBUG)


class TestBasicESPFunctions(TestCase):
    def test_create_esp(self):
        ESP.add(test_ip)
        esp = ESP.get(test_ip)
        self.assertIn(esp.ip, ESP._device_register)
        self.assertIsInstance(esp, ESP)
        self.assertEqual(esp.ip, test_ip)

    def test_get_state(self):
        ESP.add(test_ip)
        esp = ESP.get(test_ip)
        logger.info(f"....ok:\n{esp.state}")

    def test_gpio_on(self):
        ESP.add(test_ip)
        esp = ESP.get(test_ip)
        answer = esp.gpio_on(test_gpio)
        logger.info(f"....ok:\n{answer}")

    def test_gpio_off(self):
        ESP.add(test_ip)
        esp = ESP.get(test_ip)
        answer = esp.gpio_off(test_gpio)
        logger.info(f"....ok:\n{answer}")

    def test_network_scan(self):
        pass


class TestClassMethods(TestCase):
    def test_get_esp_by_ip(self):
        ESP.add(test_ip)
        esp = ESP.get(test_ip)
        self.assertRaises(ESPNotFoundError, ESP.get, "name not available")
        self.assertEqual(ESP.get(test_ip).name, test_name)

    def test_delete_esp(self):
        ESP.add(test_ip)
        esp = ESP.get(test_ip)
        deleted_esp = ESP.remove(test_ip)
        self.assertEqual(deleted_esp.name, test_name)
        self.assertNotIn(esp.ip, ESP._device_register)
        self.assertRaises(KeyError, ESP.remove, test_ip)


if __name__ == "__main__":
    if "--ip" in sys.argv:
        test_ip = sys.argv[sys.argv.index("--ip")+1]
        sys.argv.pop(sys.argv.index("--ip")+1)
        sys.argv.remove("--ip")
    else:
        logger.error(
            "Please setup a ESP_Easy device and pass its IP address to the test")
        print("Usage\n-----\n"
              "python test_esp.py -options[all from unittest] --ip 0.0.0.0")
        sys.exit()
    unittest.main()
