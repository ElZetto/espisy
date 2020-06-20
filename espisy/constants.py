import configparser
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
formatter = logging.Formatter(
    "%(asctime)s %(name)s.%(funcName)s, line %(lineno)s \t %(levelname)s: %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)
logger.setLevel(logging.WARNING)

filepath = os.path.dirname(__file__)

# read configuration
config = configparser.ConfigParser()
config_file_name = os.path.join(filepath, 'esp.ini')
logger.debug(f"Trying to read ini file from {config_file_name}")
_config_correct = config.read(config_file_name)
if _config_correct:
    logger.debug(f"read sections:\n {config.sections()}")
else:
    sys.exit(f"""\033[91mFATAL: Could not read config file. Please check if {config_file_name} exists and is readable.
Search for inifile at https://espisy.readthedocs.io for more information\033[0m""")

# Dummy values:
test_ip = "127.0.0.1"
test_name = "test_name"
test_gpio = 2
test_state = {"System": {
    "Build": 20103,
    "Git Build": "mega-20190830",
    "System Libraries": "ESP82xx Core 2_5_2, NONOS SDK 2.2.1(cfd48f3), LWIP: 2.1.2 PUYA support",
    "Plugins": 48,
    "Plugin description": " [Normal]",
    "Local Time": "1970-00-00 00:00:00",
    "Unit Number": 2,
    "Unit Name": "Room_1",
    "Uptime": 13023,
    "Last Boot Cause": "Cold boot",
    "Reset Reason": "External System",
    "Load": 12.10,
    "Load LC": 4881,
    "CPU Eco Mode": "false",
    "Heap Max Free Block": 19032,
    "Heap Fragmentation": 4,
    "Free RAM": 19736
},
    "WiFi": {
    "Hostname": "Room_1",
    "IP Config": "DHCP",
    "IP Address": "192.168.0.255",
    "IP Subnet": "255.255.255.0",
    "Gateway": "192.168.0.1",
    "STA MAC": "84:F3:EB:05:16:0D",
    "DNS 1": "192.168.0.1",
    "DNS 1": "192.168.0.1",
    "SSID": "YOUR_SSID",
    "BSSID": "YOUR_BSSID",
    "Channel": 1,
    "Connected msec": 1,
    "Last Disconnect Reason": 1,
    "Last Disconnect Reason str": "(1) Unspecified",
    "Number Reconnects": 0,
    "Force WiFi B/G": "false",
    "Restart WiFi Lost Conn": "false",
    "Force WiFi No Sleep": "false",
    "Periodical send Gratuitous ARP": "false",
    "Connection Failure Threshold": 0,
    "RSSI": -40
},
    "Sensors": [
    {
        "TaskValues": [
            {"ValueNumber": 1,
             "Name": "State",
             "NrDecimals": 0,
             "Value": 0
             }],
        "DataAcquisition": [
            {"Controller": 1,
             "IDX": 0,
             "Enabled": "true"
             },
            {"Controller": 2,
             "IDX": 0,
             "Enabled": "false"
             },
            {"Controller": 3,
             "IDX": 0,
             "Enabled": "false"
             }],
        "TaskInterval": 0,
        "Type": "switch",
        "TaskName": "door",
        "TaskDeviceNumber": 1,
        "TaskEnabled": "true",
        "TaskNumber": 1
    },
    {
        "TaskValues": [
            {"ValueNumber": 1,
             "Name": "Temperature",
             "NrDecimals": 2,
             "Value": 20.60
             },
            {"ValueNumber": 2,
             "Name": "Humidity",
             "NrDecimals": 2,
             "Value": 62.10
             }],
        "DataAcquisition": [
            {"Controller": 1,
             "IDX": 0,
             "Enabled": "true"
             },
            {"Controller": 2,
             "IDX": 0,
             "Enabled": "false"
             },
            {"Controller": 3,
             "IDX": 0,
             "Enabled": "false"
             }],
        "TaskInterval": 600,
        "Type": "environment",
        "TaskName": "DHT",
        "TaskDeviceNumber": 5,
        "TaskEnabled": "true",
        "TaskNumber": 2
    }
],
    "TTL": 60000
}
