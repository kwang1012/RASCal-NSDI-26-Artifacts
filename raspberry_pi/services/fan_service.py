from __future__ import annotations
from typing import Any
import uuid
import asyncio

from raspberry_pi.services.elevator_service import DeviceServerConfig
from raspberry_pi.utils import get_logger

INITIAL_STATE = {}

class FanService:

    _attr_current_direction: str | None = None
    _attr_oscillating: bool | None = None
    _attr_percentage: int | None
    _attr_preset_mode: str | None
    _attr_preset_modes: list[str] | None
    _attr_speed_count: int

    FAN_SERVICE = "pi.virtual.fan"
    SET_FAN_METHOD = "transition_fan_state"

    def __init__(self, loop, config: DeviceServerConfig) -> None:
        self.loop = loop
        self._state = {}
        self.tasks: set[asyncio.Task] = set()
        self.entity_id = config.entity_id
        
        self._attr_preset_mode = None
        self._attr_preset_modes = ["Breeze", "Normal", "Sleep"]
        self._attr_percentage = 0
        self._attr_oscillating = False
        self._attr_speed_count = 3
        self._mac = hex(uuid.getnode())

        self._update_attributes()
        self.logger = get_logger(config.entity_id, config.log_dir)

        self.logger.info("Initialize fan service. Entity ID: %s", self.entity_id)

    def handle(self, request):
        if "system" in request:
            cmd_obj: dict = request["system"]
            if "get_sysinfo" in cmd_obj:
                print(f"{self._state=}")
                return {
                    "system": {
                        "get_sysinfo": {
                            "type": "fan",
                            "mac": self._mac,
                            "alias": "RPI Device",
                            "model": "Fan v1",
                            "entity_id": self.entity_id,
                            "sw_ver": "1.2.5 Build 171213 Rel.101523",
                            "hw_ver": "1.0",
                            "hwId": "45E29DA8382494D2E82688B52A0B2EB5",
                            "fwId": "00000000000000000000000000000000",
                            "dev_name": "RPI Emulated Fan",
                            "fan_state": self._state
                        }
                    }
                }

            return {"system": {"err_code": "cmd not found"}}
        if FanService.FAN_SERVICE not in request:
            return {"err_code": "service not found"}
        cmd_obj: dict = request[FanService.FAN_SERVICE]

        if "get_fan_state" in cmd_obj:
            return {FanService.FAN_SERVICE: {"get_fan_state": self._state}}
        
        if FanService.SET_FAN_METHOD in cmd_obj:
            args = cmd_obj[FanService.SET_FAN_METHOD]
            print(f"{self.entity_id}: {args}")
            if "preset_mode" in args:
                self.set_preset_mode(args["preset_mode"])
            elif "percentage" in args:
                percentage = args["percentage"]
                del args["percentage"]
                self.set_percentage(
                    percentage,
                )
            elif args.get("on_off", None) == 1:
                self.turn_on()
            elif args.get("on_off", None) == 0:
                self.turn_off()
            elif "oscillating" in args:
                self.oscillate(args["oscillating"])
                
            print(f"{self._state=}")
            return {FanService.FAN_SERVICE: {FanService.SET_FAN_METHOD: "ok"}}
        else:
            return {FanService.FAN_SERVICE: {"err_code": "cmd not found"}}

    def _update_attributes(self):
        self._state.update(
            {
                name: value
                for name, value in (
                    ("direction", self._attr_current_direction),
                    ("oscillating", self._attr_oscillating),
                    ("percentage", self._attr_percentage),
                    ("preset_mode", self._attr_preset_mode),
                )
                if value is not None
            }
        )

    def set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""
        self._attr_percentage = percentage
        self._attr_preset_mode = None
        self._update_attributes()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if self.preset_modes is None:
            raise ValueError("The device does no support preset mode")
        if preset_mode in self.preset_modes:
            self._attr_preset_mode = preset_mode
            self._attr_percentage = None
            self._update_attributes()
        else:
            raise ValueError(f"Invalid preset mode: {preset_mode}")

    def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the entity."""
        if preset_mode:
            self.set_preset_mode(preset_mode)
            return

        if percentage is None:
            percentage = 67
        self.set_percentage(percentage)
        print(self._state)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off the entity."""
        self.set_percentage(0)

    def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        self._attr_current_direction = direction
        self._update_attributes()

    def oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        self._attr_oscillating = oscillating
        self._update_attributes()
