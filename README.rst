Python script to monitor Sunspec compatible Solar Inverters over Modbus TCP
========================

This is a python port of https://github.com/tjko/sunspec-monitor and is only tested on:

SolarEdge	SE3000HD Wave

`Learn more <https://github.com/tjko/sunspec-monitor>`_.

---------------


#Requirements:
python module pyModbusTCP

#Configuration instructions:
copy config.ini.default to config.ini
edit config.ini to list your domoticz ip/port and the indexes of the domoticz meter devices that need to be updated.

If you want to learn more about ``setup.py`` files, check out `this repository <https://github.com/kennethreitz/setup.py>`_.
