"""The rpi_camera component."""
import os
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
import homeassistant.helpers.device_registry as dr

from .api.device import RaspberryPiDevice
from .api.discover import Discover
from .const import ATTR_NODES_FILE, DOMAIN, PLATFORMS

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def _async_get_or_create_rpi_device_in_registry(
    hass: HomeAssistant, entry: ConfigEntry, device: RaspberryPiDevice
) -> None:
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, device.unique_id)},
        manufacturer="RASC group",
        model=device.model,
        name=device.sys_info["dev_name"],
        sw_version=device.hw_info["sw_ver"],
        hw_version=device.hw_info["hw_ver"],
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the rpi_camera integration."""
    hass.data[DOMAIN] = {}

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Rpi device from a config entry."""
    nodes_file = entry.data.get(ATTR_NODES_FILE, None)
    if nodes_file is None:
        return True

    hosts = []
    with open(nodes_file, encoding="utf-8") as f:
        hosts = f.readlines()
    try:
        devices: list[RaspberryPiDevice] = await Discover.discover_all(hosts)
    except ValueError as ex:
        raise ConfigEntryNotReady from ex

    hass.data[DOMAIN][entry.entry_id] = {}
    for device in devices:
        await _async_get_or_create_rpi_device_in_registry(hass, entry, device)
        if device.device_type not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id][device.device_type] = []
        hass.data[DOMAIN][entry.entry_id][device.device_type].append(
            device)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
