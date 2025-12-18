from .light import RaspberryPiLight
from .door import RaspberryPiDoor
from .fan import RaspberryPiFan
from .lock import RaspberryPiLock
from .shade import RaspberryPiShade
from .switch import RaspberryPiSwitch
from .thermostat import RaspberryPiThermostat

_ALL_DEVICES = [
    RaspberryPiLight,
    RaspberryPiDoor,
    RaspberryPiFan,
    RaspberryPiLock,
    RaspberryPiShade,
    RaspberryPiSwitch,
    RaspberryPiThermostat
]