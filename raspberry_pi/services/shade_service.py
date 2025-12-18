from __future__ import annotations
from datetime import datetime
import math
from typing import Any
import uuid
import numpy as np
import asyncio

from rasc.datasets import Device, load_dataset
from raspberry_pi.server import DeviceServerConfig
from raspberry_pi.utils import get_logger

INITIAL_STATE = {}

class ShadeService:

    _attr_current_cover_position: int | None = None
    _attr_current_cover_tilt_position: int | None = None
    _attr_is_closed: bool | None = None
    _attr_is_closing: bool | None = None
    _attr_is_opening: bool | None = None

    SHADE_SERVICE = "pi.virtual.shade"
    SET_SHADE_METHOD = "transition_shade_state"

    def __init__(self, loop, config: DeviceServerConfig) -> None:
        self.loop = loop
        self._state = {}
        self.cover_tasks: set[asyncio.Task] = set()
        self.tilt_tasks = set()
        self.entity_id = config.entity_id
        self.logger = get_logger(config.entity_id, config.log_dir)

        self._attr_is_closed = True
        self._attr_current_cover_position = 0 if self._attr_is_closed else 100
        self._mac = hex(uuid.getnode())

        self._update_attributes()

        self._dataset = load_dataset(Device.SHADE)

        self.logger.info("Initialize shade service. Entity ID: %s", self.entity_id)

    def handle(self, request):
        if "system" in request:
            cmd_obj: dict = request["system"]
            if "get_sysinfo" in cmd_obj:
                return {
                    "system": {
                        "get_sysinfo": {
                            "type": "shade",
                            "mac": self._mac,
                            "alias": "RPI Device",
                            "model": "Shade v1",
                            "entity_id": self.entity_id,
                            "sw_ver": "1.2.5 Build 171213 Rel.101523",
                            "hw_ver": "1.0",
                            "hwId": "45E29DA8382494D2E82688B52A0B2EB5",
                            "fwId": "00000000000000000000000000000000",
                            "dev_name": "RPI Emulated Shade",
                            "shade_state": self._state
                        }
                    }
                }

            return {"system": {"err_code": "cmd not found"}}
        if ShadeService.SHADE_SERVICE not in request:
            return {"err_code": "service not found"}
        cmd_obj: dict = request[ShadeService.SHADE_SERVICE]

        if "get_shade_state" in cmd_obj:
            return {ShadeService.SHADE_SERVICE: {"get_shade_state": self._state}}
        if ShadeService.SET_SHADE_METHOD in cmd_obj:
            args = cmd_obj[ShadeService.SET_SHADE_METHOD]
            if args["on_off"] == 1:
                self.open_cover(**args)
            elif args["on_off"] == 0:
                self.close_cover(**args)
            return {ShadeService.SHADE_SERVICE: {ShadeService.SET_SHADE_METHOD: "ok"}}
        else:
            return {ShadeService.SHADE_SERVICE: {"err_code": "cmd not found"}}

    def _update_attributes(self):
        self._state.update(
            {
                name: value
                for name, value in (
                    ("current_position", self._attr_current_cover_position),
                    (
                        "current_tilt_position",
                        self._attr_current_cover_tilt_position,
                    ),
                    ("closed", self._attr_is_closed),
                    ("opening", self._attr_is_opening),
                    ("closing", self._attr_is_closing),
                )
                if value is not None
            }
        )

    def _opening(self) -> None:
        self._attr_is_opening = True
        self._attr_is_closing = False
        self._attr_is_closed = False
        self._update_attributes()

    def _closing(self) -> None:
        self._attr_is_opening = False
        self._attr_is_closing = True
        self._attr_is_closed = False
        self._update_attributes()

    def _close_cover(self) -> None:
        self._attr_current_cover_position = 0
        self._attr_is_opening = False
        self._attr_is_closing = False
        self._attr_is_closed = True
        self._update_attributes()

    def _open_cover(self) -> None:
        self._attr_current_cover_position = 100
        self._attr_is_opening = False
        self._attr_is_closing = False
        self._attr_is_closed = False
        self._update_attributes()

    async def _start_operation(self, interruption_level: float | None = None, action_name: str = ""):
        try:
            if self._attr_is_opening:
                target_position = 100.0
                action_length = np.random.choice(self._dataset["up"])
            elif self._attr_is_closing:
                target_position = 0.0
                action_length = np.random.choice(self._dataset["down"])
            step = (target_position - self._attr_current_cover_position) / action_length
            # todo: interruption: based on precentage of action length
            self.logger.debug("Action length: %s", action_length)
            self.logger.info("Transition %s starts: %s", action_name, datetime.now().strftime('%F %T.%f')[:-3])
            middle = math.floor(action_length/2)
            count = 0
            while True:
                if count == middle and interruption_level is not None:
                    await asyncio.sleep(interruption_level * action_length)
                self._attr_current_cover_position += step
                if self._attr_current_cover_position >= 100:
                    self._attr_current_cover_position = 100
                    self._open_cover()
                    self.logger.info("action finished at %s", datetime.now().strftime('%F %T.%f')[:-3])
                    break
                if self._attr_current_cover_position <= 0:
                    self._attr_current_cover_position = 0
                    self._close_cover()
                    self.logger.info("action finished at %s", datetime.now().strftime('%F %T.%f')[:-3])
                    break
                self._update_attributes()
                await asyncio.sleep(1)
                count += 1
        except asyncio.CancelledError:
            if self._attr_current_cover_position >= 100:
                self._attr_current_cover_position = 100
                self._open_cover()
            elif self._attr_current_cover_position <= 0:
                self._attr_current_cover_position = 0
                self._close_cover()
            self._update_attributes()

    def open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        interruption_level = kwargs.get("interruption_level")
        self._opening()
        task = self.loop.create_task(self._start_operation(interruption_level, action_name="open"))
        self.cover_tasks.add(task)

    def close_cover(self, **kwargs: Any) -> None:
        """Close the cover."""
        interruption_level = kwargs.get("interruption_level")
        self._closing()
        task = self.loop.create_task(self._start_operation(interruption_level, action_name="close"))
        self.cover_tasks.add(task)

    def stop_cover(self) -> None:
        """Stop the cover."""
        for task in self.cover_tasks:
            task.cancel()
        self.cover_tasks.clear()
