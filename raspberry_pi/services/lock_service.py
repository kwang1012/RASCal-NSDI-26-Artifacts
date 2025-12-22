from __future__ import annotations
from typing import Any
import uuid
import asyncio
from enum import IntFlag
import random

from raspberry_pi.server import DeviceServerConfig
from raspberry_pi.utils import get_logger

INITIAL_STATE = {}

class LockEntityFeature(IntFlag):
    """Supported features of the lock entity."""

    OPEN = 1


class LockService:

    _attr_changed_by: str | None = None
    _attr_code_format: str | None = None
    _attr_is_locked: bool | None = None
    _attr_is_locking: bool | None = None
    _attr_is_unlocking: bool | None = None
    _attr_is_jammed: bool | None = None
    _attr_state: None = None
    _attr_supported_features: LockEntityFeature = LockEntityFeature(0)
    _lock_option_default_code: str = ""

    LOCK_SERVICE = "pi.virtual.lock"
    SET_LOCK_METHOD = "transition_lock_state"

    def __init__(self, loop: asyncio.AbstractEventLoop, config: DeviceServerConfig, **kwargs) -> None:
        self.loop = loop
        self._state = {}

        self._task: asyncio.Task | None = None
        self.entity_id = config.entity_id
        
        self._change_time = kwargs.get("locking_time", 3)
        self._test_jamming = 0

        self._attr_is_locked = False

        self._mac = hex(uuid.getnode())

        self._update_attributes()
        
        self.logger = get_logger(config.entity_id, config.log_dir)

        self.logger.info("Initialize lock service. Entity ID: %s", self.entity_id)

    def handle(self, request):
        if "system" in request:
            cmd_obj: dict = request["system"]
            if "get_sysinfo" in cmd_obj:
                return {
                    "system": {
                        "get_sysinfo": {
                            "type": "lock",
                            "mac": self._mac,
                            "alias": "RPI Device",
                            "model": "Lock v1",
                            "entity_id": self.entity_id,
                            "sw_ver": "1.2.5 Build 171213 Rel.101523",
                            "hw_ver": "1.0",
                            "hwId": "45E29DA8382494D2E82688B52A0B2EB5",
                            "fwId": "00000000000000000000000000000000",
                            "dev_name": "RPI Emulated Lock",
                            "lock_state": self._state
                        }
                    }
                }

            return {"system": {"err_code": "cmd not found"}}
        if LockService.LOCK_SERVICE not in request:
            return {"err_code": "service not found"}
        cmd_obj: dict = request[LockService.LOCK_SERVICE]

        if "get_lock_state" in cmd_obj:
            return {LockService.LOCK_SERVICE: {"get_lock_state": self._state}}
        if LockService.SET_LOCK_METHOD in cmd_obj:
            args = cmd_obj[LockService.SET_LOCK_METHOD]
            if args["on_off"] == 1:
                self.lock(**args)
            elif args["on_off"] == 0:
                self.unlock(**args)
            elif "open" in args:
                self.open(**args)
            return {LockService.LOCK_SERVICE: {LockService.SET_LOCK_METHOD: "ok"}}
        else:
            return {LockService.LOCK_SERVICE: {"err_code": "cmd not found"}}

    def _update_attributes(self):
        self._state.update(
            {
                name: value
                for name, value in (
                    ("is_locked", self._attr_is_locked),
                    (
                        "is_locking",
                        self._attr_is_locking,
                    ),
                    ("is_unlocking", self._attr_is_unlocking),
                    ("is_jammed", self._attr_is_jammed),
                )
                if value is not None
            }
        )

    def _lock(self) -> None:
        if self._test_jamming == 0 or random.randint(0, self._test_jamming) > 0:
            self._attr_is_locked = True
            self._attr_is_locking = False
            self._attr_is_unlocking = False
            self._attr_is_jammed = False
            self._update_attributes()
        else:
            self._jam()

    def _locking(self) -> None:
        self._attr_is_locked = False
        self._attr_is_locking = True
        self._attr_is_unlocking = False
        self._attr_is_jammed = False
        self._update_attributes()

    def _unlock(self) -> None:
        self._attr_is_locked = False
        self._attr_is_locking = False
        self._attr_is_unlocking = False
        self._attr_is_jammed = False
        self._update_attributes()

    def _unlocking(self) -> None:
        self._attr_is_locked = False
        self._attr_is_locking = False
        self._attr_is_unlocking = True
        self._attr_is_jammed = False
        self._update_attributes()

    def _jam(self) -> None:
        self._attr_is_locked = False
        self._attr_is_jammed = True
        self._update_attributes()

    def _finish_operation(self) -> None:
        if self._attr_is_locking:
            self._lock()
        if self._attr_is_unlocking:
            self._unlock()

    async def _start_operation(self):
        await asyncio.sleep(self._change_time)
        self._finish_operation()

    def lock(self, **kwargs: Any) -> None:
        """Lock."""
        if self._change_time is None:
            self._lock()
        else:
            self._locking()
            if self._task is not None:
                self._task.cancel()
            self._task = self.loop.create_task(
                self._start_operation()
            )

    def unlock(self, **kwargs: Any) -> None:
        """Unlock."""
        if self._change_time is None:
            self._unlock()
        else:
            self._unlocking()
            if self._task is not None:
                self._task.cancel()
            self._task = self.loop.create_task(
                self._start_operation()
            )

    def open(self, **kwargs: Any) -> None:
        """Open."""
        self.unlock()
