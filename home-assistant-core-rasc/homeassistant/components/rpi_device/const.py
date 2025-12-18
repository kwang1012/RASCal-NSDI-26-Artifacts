"""Consts used by rpi_device."""

from typing import Final

from homeassistant.const import Platform

DOMAIN = "rpi_device"
ATTR_NODES_FILE = "nodes_file"

PLATFORMS: Final = [
    Platform.COVER,
    Platform.CLIMATE,
    Platform.FAN,
    Platform.SWITCH,
    Platform.LIGHT,
    Platform.LOCK,
]
