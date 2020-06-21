########
README
########

Simple client to access and controll ESPs that run ESPEasy in your local network.

    
********
ESPEasy
********

    **This project is not related to the ESPEasy project.
    It only provides a python class to control an device running ESPEasy**

You can run the `ESPEasy Firmware <https://github.com/letscontrolit/ESPEasy>`_ firmware on ESP8266 devices, for example the NodeMCU.

********************
Configuration files
********************
espisy uses config files (.ini files) within the package. Other configurations, like esp specific settings, a subnet for 
scanning etc. are stored in .yaml files for easier access. You can find all .yaml finds in one directory. Standard, is ``/.espisy`` in your 
home directory, but you can change it in the .ini file. Espisy comes with a script ``espisy_setup.py`` that will lead you through the first steps and (hopefully)
leave you with working settings.

******
Usage
******

.. _create:

Create an ESP device
=====================

.. note::
    **You should always use the classmethod** :meth:`~~espisy.core.ESP.add` **to add a new ESP device**

The ESP has a static register which keeps track of the ESP instances. It is possible to refer to every created ESP with
the :meth:`~espisy.core.ESP.get` method. This was implemented, because it simplifies the dynamic instantiation of ESP devices. A thing I needed pretty soon during development.

If you want to access a specific ESP device faster, you can of course use it with your own variable as usual.

.. code-block:: python

    ESP.add("192.0.0.255")
    my_esp = ESP.get("192.0.0.255")
    # do stuff with my_esp

    # you can also access the ESP with the name you gave it in the ESPEasy frontend
    my_esp = ESP.get("garden")


Scan the network
=================

You can scan your network for ESPEasy devices.
configure the network (ipv4 with suffix) in the esp.yaml file or pass it as argument to :meth:`~espisy.core.ESP.scan_network`

.. code-block:: python

    ESP.scan_network("192.168.0.0/24")

    # or with config file:
    # esp.yaml:
    #   ipv4network: 192.168.0.0/24
    ESP.scan_network()

    ESP.get("living room")

.. _gpio:

GPIO
=======
.. note::
    It is recommended to use :ref:`switches`.
    The usage will be easier and more comfortable

You can manipulate the ESP GPIOS directly via HTTP request.

.. code-block:: html

    http://<ip>/control?cmd=GPIO,<gpio>,<state>

espisy wraps this with the functions :meth:`~espisy.core.ESP.gpio_on` and :meth:`~espisy.core.ESP.gpio_off`.

.. code-block:: python

    # Example to switch GPIO 2 of your ESP with IP 192.0.0.255 on:
    ESP.get("192.0.0.255").gpio_off(2)

.. _switches:

Switches
=========
If you have defined a switch in ESPEasy, it is easier to manipulate the :ref:`GPIO`, once it is mapped.
Since it is not possible to receive the GPIO of a switch via HTTP requests (at least not without 
manually parsing the HTML response), you need to map the GPIO initially to the switch.

Let's say you have set up a switch named "LED" on GPIO 2 at 127.0.0.1 in ESPEasy. During initialization, 
all ESPEasy tasks will be searched. Tasks with the keyword "switch" will be handled extra and allow a few extra methods.

In order to use the switches, you have to map the right GPIO once

.. code-block:: python

    ESP.get("192.0.0.255").map_gpio_to_switch("LED",2)

Now you can use the commands :meth:`~espisy.core.ESP.switch_state`, :meth:`~espisy.core.ESP.on()`, 
:meth:`~espisy.core.ESP.off()` and :meth:`~espisy.core.ESP.toggle()`

.. code-block:: python

    esp = ESP.get("192.0.0.255")
    esp.on("LED")   # Will set the GPIO HIGH
    esp.off("LED")  # Will set the GPIO LOW
    esp.toggle("LED")   # Will toggle the GPIO
    esp.switch_state("LED") # Will return the following dictionary and always be up to date
    {
        "log": "",
        "plugin": 1,
        "pin": 2,
        "mode": "output",
        "state": 1
    }

.. _sensors:

Sensors
========
You can access every Sensor from your ESPEasy Device by calling sensor_state(\<name_of_sensor>).
Say you have a Sensor *"Environment - DHT11/12/22 SONOFF2301/7021"* named *"Living Room"* set up.

.. code-block:: python

    ESP.get(<ip_of_ESP>).sensor_state("Living Room")
    # will return something like
    [
        {
            'ValueNumber': 1,
            'Name': 'Temperature',
            'NrDecimals': 2,
            'Value': 21.3
        },
        {
            'ValueNumber': 2,
            'Name': 'Humidity',
            'NrDecimals': 2,
            'Value': 77.4
        }
    ]

Alternatively, you can also access the sensor as a :doc:`subclass <sensor>`, which provides the properties
:attr:`~espisy.sensor.Sensor.temperature`, :attr:`~espisy.sensor.Sensor.humidity` and the method :meth:`~~espisy.sensor.Sensor.feature`.

.. code-block:: python

    esp = ESP.get(<ip_of_ESP>)
    dht = esp.sensor("DHT")
    print(dht.temperature)
    # will output 21.3 or whatever the current data is

.. _testing:

Testing
========
.. warning::
    The test toggles GPIO 2 high and low a few times. Only wire the GPIO up to LED or something if you know what you are doing.

The testing module that comes with espisy can be executed with a dummy (which is only useful for development) or with a real ESP. If you want to test automatically with a real ESP, please set up an ESPEasy device like this:

+----------------------------+--------+------+
| Device                     | Name   | GPIO |
+============================+========+======+
| Switch -                   | "door" | 2    |
|                            |        |      |
| input Switch               |        |      |
+----------------------------+--------+------+
| Environment -              | "DHT"  | 14   |
| DHT11/12/22SONOFF2301/7021 |        |      |
+----------------------------+--------+------+

Start the test either with `--dummmy` or with `--ip xxx.xxx.xxx`

.. code-block:: python

    python test_esp --dummy
    # or with an example ip:
    python test_esp --ip 192.0.0.255


It will try to create and delete the ESP, switches and toggle