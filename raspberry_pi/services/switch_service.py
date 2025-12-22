from __future__ import annotations
from typing import Any
import uuid

from raspberry_pi.server import DeviceServerConfig
from raspberry_pi.utils import get_logger

INITIAL_STATE = {}

class SwitchService:

    _attr_is_on: bool | None = None

    SWITCH_SERVICE = "pi.virtual.switch"
    SET_SWITCH_METHOD = "transition_switch_state"

    def __init__(self, loop, config: DeviceServerConfig) -> None:
        self.loop = loop
        self._state = {}
        self.entity_id = config.entity_id
        self.logger = get_logger(config.entity_id, config.log_dir)

        self._attr_is_on = False
        self._mac = hex(uuid.getnode())

        self._update_attributes()

        self.logger.info("Initialize switch service. Entity ID: %s", self.entity_id)

    def handle(self, request):
        if "system" in request:
            cmd_obj: dict = request["system"]
            if "get_sysinfo" in cmd_obj:
                return {
                    "system": {
                        "get_sysinfo": {
                            "type": "switch",
                            "mac": self._mac,
                            "alias": "RPI Device",
                            "model": "Switch v1",
                            "entity_id": self.entity_id,
                            "sw_ver": "1.2.5 Build 171213 Rel.101523",
                            "hw_ver": "1.0",
                            "hwId": "45E29DA8382494D2E82688B52A0B2EB5",
                            "fwId": "00000000000000000000000000000000",
                            "dev_name": "RPI Emulated Switch",
                            "switch_state": self._state
                        }
                    }
                }

            return {"system": {"err_code": "cmd not found"}}
        if SwitchService.SWITCH_SERVICE not in request:
            return {"err_code": "service not found"}
        cmd_obj: dict = request[SwitchService.SWITCH_SERVICE]

        if "get_switch_state" in cmd_obj:
            return {SwitchService.SWITCH_SERVICE: {"get_switch_state": self._state}}
        if SwitchService.SET_SWITCH_METHOD in cmd_obj:
            args = cmd_obj[SwitchService.SET_SWITCH_METHOD]
            if args["on_off"] == 1:
                self.turn_on(**args)
            elif args["on_off"] == 0:
                self.turn_off(**args)
            return {SwitchService.SWITCH_SERVICE: {SwitchService.SET_SWITCH_METHOD: "ok"}}
        else:
            return {SwitchService.SWITCH_SERVICE: {"err_code": "cmd not found"}}

    def _update_attributes(self):
        self._state.update(
            {
                name: value
                for name, value in (
                    ("is_on", self._attr_is_on),
                )
                if value is not None
            }
        )

    def turn_on(self, **kwargs: Any) -> None:
        """Turn on."""
        self._attr_is_on = True
        self._update_attributes()

    def turn_off(self, **kwargs: Any) -> None:
        """Turn off."""
        self._attr_is_on = False
        self._update_attributes()
