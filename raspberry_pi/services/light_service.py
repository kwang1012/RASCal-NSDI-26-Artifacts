from __future__ import annotations
import math
import uuid
import asyncio
from enum import IntFlag, StrEnum
from raspberry_pi.server import DeviceServerConfig
from raspberry_pi.utils import get_logger

INITIAL_STATE = {}

class LightEntityFeature(IntFlag):
    """Supported features of the light entity."""

    EFFECT = 4
    FLASH = 8
    TRANSITION = 32
    
class ColorMode(StrEnum):
    """Possible light color modes."""

    UNKNOWN = "unknown"
    """Ambiguous color mode"""
    ONOFF = "onoff"
    """Must be the only supported mode"""
    BRIGHTNESS = "brightness"
    """Must be the only supported mode"""
    COLOR_TEMP = "color_temp"
    HS = "hs"
    XY = "xy"
    RGB = "rgb"
    RGBW = "rgbw"
    RGBWW = "rgbww"
    WHITE = "white"
    """Must *NOT* be the only supported mode"""

class LightService:

    _attr_brightness: int | None = None
    _attr_color_mode: ColorMode | str | None = None
    _attr_color_temp: int | None = None
    _attr_color_temp_kelvin: int | None = None
    _attr_effect_list: list[str] | None = None
    _attr_effect: str | None = None
    _attr_hs_color: tuple[float, float] | None = None
    # Default to the Philips Hue value that HA has always assumed
    # https://developers.meethue.com/documentation/core-concepts
    _attr_max_color_temp_kelvin: int | None = None
    _attr_min_color_temp_kelvin: int | None = None
    _attr_max_mireds: int = 500  # 2000 K
    _attr_min_mireds: int = 153  # 6500 K
    _attr_rgb_color: tuple[int, int, int] | None = None
    _attr_rgbw_color: tuple[int, int, int, int] | None = None
    _attr_rgbww_color: tuple[int, int, int, int, int] | None = None
    _attr_supported_color_modes: set[ColorMode] | set[str] | None = None
    _attr_supported_features: LightEntityFeature = LightEntityFeature(0)
    _attr_xy_color: tuple[float, float] | None = None
    
    LIGHT_SERVICE = "pi.virtual.light"
    SET_LIGHT_METHOD = "transition_light_state"

    def __init__(self, loop, config: DeviceServerConfig) -> None:
        self.loop = loop
        self._state = {}
        self._task: set[asyncio.Task] | None = None
        self.entity_id = config.entity_id
        
        self._attr_supported_color_modes = {ColorMode.ONOFF}
        self._attr_supported_features = 0
        self._attr_transition: bool | None = None

        self._attr_supported_color_modes.add(ColorMode.BRIGHTNESS)
        self._attr_supported_color_modes.add(ColorMode.HS)
        self._attr_supported_color_modes.add(ColorMode.COLOR_TEMP)
        self._attr_supported_features |= LightEntityFeature.EFFECT
        self._attr_effect_list = ["rainbow", "none"]
        self._attr_supported_features |= LightEntityFeature.TRANSITION

        self._attr_is_on = False
        self._attr_brightness = 0
        self._attr_color_mode = ColorMode.HS
        
        self._mac = hex(uuid.getnode())

        self._update_attributes()
        self.logger = get_logger(config.entity_id, config.log_dir)

        self.logger.info("Initialize light service. Entity ID: %s", self.entity_id)

    def handle(self, request):
        if "system" in request:
            cmd_obj: dict = request["system"]
            if "get_sysinfo" in cmd_obj:
                return {
                    "system": {
                        "get_sysinfo": {
                            "type": "light",
                            "mac": self._mac,
                            "alias": "RPI Device",
                            "model": "Light v1",
                            "entity_id": self.entity_id,
                            "sw_ver": "1.2.5 Build 171213 Rel.101523",
                            "hw_ver": "1.0",
                            "hwId": "45E29DA8382494D2E82688B52A0B2EB5",
                            "fwId": "00000000000000000000000000000000",
                            "dev_name": "RPI Emulated Light",
                            "light_state": self._state
                        }
                    }
                }

            return {"system": {"err_code": "cmd not found"}}
        if LightService.LIGHT_SERVICE not in request:
            return {"err_code": "service not found"}
        cmd_obj: dict = request[LightService.LIGHT_SERVICE]

        if "get_light_state" in cmd_obj:
            return {LightService.LIGHT_SERVICE: {"get_light_state": self._state}}
        if LightService.SET_LIGHT_METHOD in cmd_obj:
            args = cmd_obj[LightService.SET_LIGHT_METHOD]
            # self.logger.debug(f"{self.entity_id}: cmd {args}")
            if args["on_off"] == 1:
                self.turn_on(**args)
            elif args["on_off"] == 0:
                self.turn_off(**args)
            return {LightService.LIGHT_SERVICE: {LightService.SET_LIGHT_METHOD: "ok"}}
        else:
            return {LightService.LIGHT_SERVICE: {"err_code": "cmd not found"}}

    def _update_attributes(self):
        """Return the state attributes."""
        self._state.update(
            {
                name: value
                for name, value in (
                    ("is_on", self._attr_is_on),
                    ("brightness", self._attr_brightness),
                    ("color_mode", self._attr_color_mode),
                    ("color_temp", self._attr_color_temp),
                    ("effect", self._attr_effect),
                    ("effect_list", self._attr_effect_list),
                    ("hs_color", self._attr_hs_color),
                )
                if value is not None
            }
        )

    def turn_on(self, **kwargs):
        """Turn the light on."""
        transition = kwargs.get("transition")
        hs_color = kwargs.get("hs_color", None)
        self.logger.info("%s: Turn on light with kwargs: %s", self.entity_id, kwargs)
        if (
            hs_color is not None
            and ColorMode.COLOR_TEMP in self._attr_supported_color_modes
        ):
            self._attr_color_mode = ColorMode.HS
            self._attr_hs_color = hs_color
            self._attr_color_temp = None

        ct = kwargs.get("color_temp", None)
        if ct is not None and ColorMode.COLOR_TEMP in self._attr_supported_color_modes:
            self._attr_color_mode = ColorMode.COLOR_TEMP
            self._attr_color_temp = ct
            self._attr_hs_color = None

        brightness = kwargs.get("brightness", None)
        if brightness is not None:
            if (
                transition is not None
                and transition > 0
                and self._attr_supported_features & LightEntityFeature.TRANSITION
            ):
                if self._task is not None:
                    if not self._task.done():
                        self.logger.error(
                            f'Previous brightness transition task is still running on {self.entity_id}. Cancelling it.')
                    self._task.cancel()
                self._task = asyncio.create_task(
                    self._async_update_brightness(brightness, transition)
                )
            else:
                self._attr_brightness = brightness

        effect = kwargs.get("effect", None)
        if (
            effect is not None
            and self._attr_supported_features & LightEntityFeature.EFFECT
        ):
            self._attr_effect = effect

        self._attr_is_on = True
        self._update_attributes()

    def turn_off(self, **kwargs):
        """Turn the light off."""
        self._attr_is_on = False
        self._update_attributes()

    async def _async_update_brightness(
        self, brightness: int, transition: float
    ) -> None:
        """Update brightness with transition."""
        if self._attr_brightness is None:
            self._attr_brightness = 0
        step = (brightness - self._attr_brightness) / transition
        step = -math.ceil(abs(step)) if step < 0 else math.ceil(step)
        increasing = step > 0
        self.logger.debug("%s starts async brightness transition from %s to %s with step %s", self.entity_id, self._attr_brightness, brightness, step)
        try:
            while True:
                self._attr_brightness += step
                self.logger.debug("%s: Current brightness %s", self.entity_id, self._attr_brightness)
                if not increasing and self._attr_brightness <= brightness:
                    self._attr_brightness = brightness
                    self._update_attributes()
                    break
                if increasing and self._attr_brightness >= brightness:
                    self._attr_brightness = brightness
                    self._update_attributes()
                    break
                self._update_attributes()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            if self._attr_brightness <= 0:
                self._attr_brightness = 0
            elif self._attr_brightness >= brightness:
                self._attr_brightness = brightness
            self._update_attributes()
