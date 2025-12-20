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

class DoorService:

    _attr_current_door_position: int
    _attr_is_closed: bool | None = None
    _attr_is_closing: bool | None = None
    _attr_is_opening: bool | None = None

    DOOR_SERVICE = "pi.virtual.door"
    SET_DOOR_METHOD = "transition_door_state"

    def __init__(self, loop, config: DeviceServerConfig) -> None:
        self.loop = loop
        self._state = {}
        self.tasks: set[asyncio.Task] = set()
        self.entity_id = config.entity_id

        self._attr_is_closed = True
        self._attr_current_door_position = 0 if self._attr_is_closed else 100
        self._mac = hex(uuid.getnode())

        self._update_attributes()

        self._dataset = load_dataset(Device.DOOR)
        self.logger = get_logger(self.entity_id, log_dir=config.log_dir)

        self.logger.info("Initialize door service. Entity ID: %s", self.entity_id)

    def handle(self, request):
        if "system" in request:
            cmd_obj: dict = request["system"]
            if "get_sysinfo" in cmd_obj:
                return {
                    "system": {
                        "get_sysinfo": {
                            "type": "door",
                            "mac": self._mac,
                            "alias": "RPI Device",
                            "model": "Door v1",
                            "entity_id": self.entity_id,
                            "sw_ver": "1.2.5 Build 171213 Rel.101523",
                            "hw_ver": "1.0",
                            "hwId": "45E29DA8382494D2E82688B52A0B2EB5",
                            "fwId": "00000000000000000000000000000000",
                            "dev_name": "RPI Emulated Door",
                            "door_state": self._state
                        }
                    }
                }

            return {"system": {"err_code": "cmd not found"}}
        if DoorService.DOOR_SERVICE not in request:
            return {"err_code": "service not found"}
        cmd_obj: dict = request[DoorService.DOOR_SERVICE]

        if "get_door_state" in cmd_obj:
            return {DoorService.DOOR_SERVICE: {"get_door_state": self._state}}
        if DoorService.SET_DOOR_METHOD in cmd_obj:
            args = cmd_obj[DoorService.SET_DOOR_METHOD]
            if args["on_off"] == 1:
                self.open_door(**args)
            elif args["on_off"] == 0:
                self.close_door(**args)
            return {DoorService.DOOR_SERVICE: {DoorService.SET_DOOR_METHOD: "ok"}}
        else:
            return {DoorService.DOOR_SERVICE: {"err_code": "cmd not found"}}

    def _update_attributes(self):
        self._state.update(
            {
                name: value
                for name, value in (
                    ("current_position", self._attr_current_door_position),
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

    def _close_door(self) -> None:
        self._attr_current_door_position = 0
        self._attr_is_opening = False
        self._attr_is_closing = False
        self._attr_is_closed = True
        self._update_attributes()

    def _open_door(self) -> None:
        self._attr_current_door_position = 100
        self._attr_is_opening = False
        self._attr_is_closing = False
        self._attr_is_closed = False
        self._update_attributes()

    async def _start_operation(self, interruption_level: float | None = None, action_name: str = ""):
        action_length = np.random.choice(self._dataset["close"])
        self.logger.debug("Action length: %s", action_length)
        self.logger.info("Transition %s starts: %s", action_name, datetime.now().strftime('%F %T.%f')[:-3])
        try:
            if self._attr_is_opening:
                target_position = 100.0
            elif self._attr_is_closing:
                target_position = 0.0
            else:
                raise ValueError("Door is neither opening nor closing.")
            step = (target_position -
                    self._attr_current_door_position) / action_length
            # todo: interruption: based on precentage of action length
            middle = math.floor(action_length/2)
            count = 0
            while True:
                if count == middle and interruption_level is not None:
                    await asyncio.sleep(interruption_level * action_length)
                self._attr_current_door_position += step
                if self._attr_current_door_position >= 100:
                    self._attr_current_door_position = 100
                    self._open_door()
                    self.logger.info("action finished at %s", datetime.now().strftime('%F %T.%f')[:-3])
                    break
                if self._attr_current_door_position <= 0:
                    self._attr_current_door_position = 0
                    self._close_door()
                    self.logger.info("action finished at %s", datetime.now().strftime('%F %T.%f')[:-3])
                    break
                self._update_attributes()
                await asyncio.sleep(1)
                count += 1
        except asyncio.CancelledError:
            if self._attr_current_door_position >= 100:
                self._attr_current_door_position = 100
                self._open_door()
            elif self._attr_current_door_position <= 0:
                self._attr_current_door_position = 0
                self._close_door()
            self._update_attributes()

    def open_door(self, **kwargs: Any) -> None:
        """Open the door."""
        interruption_level = kwargs.get("interruption_level")
        self._opening()
        task = self.loop.create_task(self._start_operation(
            interruption_level, action_name="open"))
        self.tasks.add(task)

    def close_door(self, **kwargs: Any) -> None:
        """Close the door."""
        interruption_level = kwargs.get("interruption_level")
        self._closing()
        task = self.loop.create_task(self._start_operation(
            interruption_level, action_name="close"))
        self.tasks.add(task)

    def stop_door(self) -> None:
        """Stop the door."""
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()
