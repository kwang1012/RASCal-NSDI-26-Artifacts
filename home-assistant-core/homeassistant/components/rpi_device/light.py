"""Support for TPLink HS100/HS110/HS200 smart switch."""
from __future__ import annotations

import logging

from homeassistant.components.light import ColorMode, LightEntity, LightEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.light import RaspberryPiLight
from .const import DOMAIN
from .entity import RpiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up lights."""
    devices: list[RaspberryPiLight] = hass.data[DOMAIN][config_entry.entry_id].get(
        "light", [])
    async_add_entities([RpiLight(device) for device in devices])


class RpiLight(RpiEntity, LightEntity):
    """Representation of door for Rpi."""

    device: RaspberryPiLight

    def __init__(self, device: RaspberryPiLight) -> None:
        """Initialize the Rpi door."""
        super().__init__(device)

        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_supported_features = 0
        self._attr_transition: bool | None = None

        self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        self._attr_supported_color_modes.add(ColorMode.HS)
        self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        self._attr_supported_features |= LightEntityFeature.EFFECT
        self._attr_effect_list = ["rainbow", "none"]
        self._attr_supported_features |= LightEntityFeature.TRANSITION

    @property
    def is_on(self) -> bool | None:
        return self.device.is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return self.device.brightness

    @property
    def color_mode(self) -> ColorMode | str | None:
        """Return the color mode of the light."""
        return self.device.color_mode

    @property
    def hs_color(self) -> tuple[float, float] | None:
        """Return the hue and saturation color value [float, float]."""
        return self.device.hs_color

    @property
    def xy_color(self) -> tuple[float, float] | None:
        """Return the xy color value [float, float]."""
        return self.device.xy_color

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value [int, int, int]."""
        return self.device.rgb_color

    @property
    def rgbw_color(self) -> tuple[int, int, int, int] | None:
        """Return the rgbw color value [int, int, int, int]."""
        return self.device.rgbw_color

    @property
    def rgbww_color(self) -> tuple[int, int, int, int, int] | None:
        """Return the rgbww color value [int, int, int, int, int]."""
        return self.device.rgbww_color

    @property
    def color_temp(self) -> int | None:
        """Return the CT color value in mireds."""
        return self.device.color_temp

    @property
    def color_temp_kelvin(self) -> int | None:
        """Return the CT color value in Kelvin."""
        return self.device.color_temp_kelvin

    @property
    def min_mireds(self) -> int:
        """Return the coldest color_temp that this light supports."""
        return self.device.min_mireds

    @property
    def max_mireds(self) -> int:
        """Return the warmest color_temp that this light supports."""
        return self.device.max_mireds

    @property
    def min_color_temp_kelvin(self) -> int:
        """Return the warmest color_temp_kelvin that this light supports."""
        return self.device.min_color_temp_kelvin

    @property
    def max_color_temp_kelvin(self) -> int:
        """Return the coldest color_temp_kelvin that this light supports."""
        return self.device.max_color_temp_kelvin

    @property
    def effect_list(self) -> list[str] | None:
        """Return the list of supported effects."""
        return self.device.effect_list

    @property
    def effect(self) -> str | None:
        """Return the current effect."""
        return self.device.effect

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        await self.device.turn_on(**kwargs)

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self.device.turn_off(**kwargs)
