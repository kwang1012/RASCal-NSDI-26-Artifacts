from __future__ import annotations
from datetime import datetime
from enum import StrEnum
import math
from typing import Any
import uuid
import numpy as np
import asyncio

from rasc.datasets import Device, load_dataset
from raspberry_pi.server import DeviceServerConfig
from raspberry_pi.utils import get_logger

INITIAL_STATE = {}

class HVACMode(StrEnum):
    """HVAC mode for climate devices."""

    # All activity disabled / Device is off/standby
    OFF = "off"

    # Heating
    HEAT = "heat"

    # Cooling
    COOL = "cool"

    # The device supports heating/cooling to a range
    HEAT_COOL = "heat_cool"

    # The temperature is set based on a schedule, learned behavior, AI or some
    # other related mechanism. User is not able to adjust the temperature
    AUTO = "auto"

    # Device is in Dry/Humidity mode
    DRY = "dry"

    # Only the fan is on, not fan and another mode like cool
    FAN_ONLY = "fan_only"


PRESET_NONE = "none"


class ThermostatService:

    THERMOSTAT_SERVICE = "pi.virtual.thermostat"
    SET_THERMOSTAT_METHOD = "transition_thermostat_state"

    _attr_min_temp = 62.0
    _attr_max_temp = 85.0

    def __init__(self, loop, config: DeviceServerConfig) -> None:
        self.loop = loop
        self._state = {}
        self.entity_id = config.entity_id
        self.logger = get_logger(config.entity_id, config.log_dir)
        self._mac = hex(uuid.getnode())

        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
        self._attr_preset_modes = [PRESET_NONE]

        self._task: asyncio.Task | None = None

        self._attr_hvac_mode = HVACMode.HEAT
        self._attr_preset_mode = PRESET_NONE
        self._attr_current_temperature = 68.0
        self._attr_target_temperature = 68.0

        self._update_attributes()
        self._dataset = load_dataset(Device.THERMOSTAT)

        self.logger.info("Initialize thermostat service. Entity ID: %s", self.entity_id)

    @property
    def min_temp(self):
        return self._attr_min_temp

    @property
    def max_temp(self):
        return self._attr_max_temp

    def handle(self, request):
        if "system" in request:
            cmd_obj: dict = request["system"]
            if "get_sysinfo" in cmd_obj:
                return {
                    "system": {
                        "get_sysinfo": {
                            "type": "thermostat",
                            "mac": self._mac,
                            "alias": "RPI Device",
                            "model": "Thermostat v1",
                            "entity_id": self.entity_id,
                            "sw_ver": "1.2.5 Build 171213 Rel.101523",
                            "hw_ver": "1.0",
                            "hwId": "45E29DA8382494D2E82688B52A0B2EB5",
                            "fwId": "00000000000000000000000000000000",
                            "dev_name": "RPI Emulated Thermostat",
                            "thermostat_state": self._state,
                        }
                    }
                }

            return {"system": {"err_code": "cmd not found"}}
        if ThermostatService.THERMOSTAT_SERVICE not in request:
            return {"err_code": "service not found"}
        cmd_obj: dict = request[ThermostatService.THERMOSTAT_SERVICE]

        if "get_thermostat_state" in cmd_obj:
            return {
                ThermostatService.THERMOSTAT_SERVICE: {
                    "get_thermostat_state": self._state
                }
            }
        if ThermostatService.SET_THERMOSTAT_METHOD in cmd_obj:
            args = cmd_obj[ThermostatService.SET_THERMOSTAT_METHOD]
            if "preset_mode" in args:
                self.set_preset_mode(args["preset_mode"])
            elif "hvac_mode" in args:
                self.set_hvac_mode(HVACMode(args["hvac_mode"]))
            elif "reset" in args:
                self.reset(args["reset"])
            elif "temperature" in args:
                temperature = args["temperature"]
                del args["temperature"]
                self.set_temperature(
                    temperature,
                    **args,
                )
            return {
                ThermostatService.THERMOSTAT_SERVICE: {
                    ThermostatService.SET_THERMOSTAT_METHOD: self._state
                }
            }
        else:
            return {ThermostatService.THERMOSTAT_SERVICE: {"err_code": "cmd not found"}}

    def _update_attributes(self):
        self._state.update(
            {
                name: value
                for name, value in (
                    ("current_temperature", self._attr_current_temperature),
                    ("target_temperature", self._attr_target_temperature),
                    ("hvac_mode", self._attr_hvac_mode),
                )
                if value is not None
            }
        )

    async def _async_update_temperature(
        self,
        target_temperature,
        interruption_level: float | None = None,
        interruption_time: float | None = None,
        interruption_moment: float | None = None,
    ):
        start = math.floor(self._attr_current_temperature)
        target = math.floor(target_temperature)
        if self._dataset is None or target < start:
            action_length = 1
        else:
            action = f"{start},{target}"
            if action in self._dataset:
                action_length = np.random.choice(self._dataset[action])
            else:
                start_keys = list(
                    filter(lambda key: key.startswith(str(start)), self._dataset.keys())
                )
                max_key = max(start_keys)
                max_action_length = np.random.choice(self._dataset[max_key])
                max_target = int(max_key.split(",")[-1])
                action_length = (
                    max_action_length / (max_target - start) * (target - start)
                )
        interruption_moment = interruption_moment or 0.5
        self.logger.debug("Action length: %s", action_length)
        # self.logger.debug("Interruption level: %s", interruption_level)
        self.logger.debug("Interruption time: %s", interruption_time)
        self.logger.debug("Interruption moment: %s", interruption_moment)
        self.logger.info("Transition from %s to %s at %s", start, target, datetime.now().strftime('%F %T.%f')[:-3])
        step = (target_temperature - self._attr_current_temperature) / action_length
        step = -math.ceil(abs(step)) if step < 0 else math.ceil(step)
        middle = math.floor(action_length * interruption_moment)
        count = 0
        increasing = step > 0
        print(step, increasing)
        try:
            while True:
                if count == middle and interruption_level is not None:
                    self.logger.info("Action interrupted for %s seconds!", interruption_level * action_length)
                    await asyncio.sleep(interruption_level * action_length)
                elif count == middle and interruption_time is not None:
                    self.logger.info("Action interrupted for %s seconds!", interruption_time)
                    await asyncio.sleep(interruption_time)
                self._attr_current_temperature += step
                if increasing and self._attr_current_temperature >= target_temperature:
                    self._attr_current_temperature = target_temperature
                    self.logger.info("action finished at %s", datetime.now().strftime('%F %T.%f')[:-3])
                    self._update_attributes()
                    break
                if (
                    not increasing
                    and self._attr_current_temperature <= target_temperature
                ):
                    self._attr_current_temperature = target_temperature
                    self._update_attributes()
                    self.logger.info("action finished at %s", datetime.now().strftime('%F %T.%f')[:-3])
                    break
                self._update_attributes()
                await asyncio.sleep(1)
                count += 1
        except asyncio.CancelledError:
            if increasing and self._attr_current_temperature >= target_temperature:
                self._attr_current_temperature = target_temperature
            elif not increasing and self._attr_current_temperature <= target_temperature:
                self._attr_current_temperature = target_temperature
            self._update_attributes()

    def reset(self, temperature: float | None = None) -> None:
        self._attr_hvac_mode = HVACMode.HEAT
        self._attr_preset_mode = PRESET_NONE
        if temperature is not None:
            self._attr_current_temperature = temperature
            self._attr_target_temperature = temperature
        self._update_attributes()

    def set_temperature(self, temperature, **kwargs: Any) -> None:
        """Set new target temperature."""
        interruption_level = kwargs.get("interruption_level")
        interruption_time = kwargs.get("interruption_time")
        interruption_moment = kwargs.get("interruption_moment")
        self._attr_target_temperature = temperature
        self._update_attributes()
        if self._task is not None:
            self._task.cancel()
        self._task = self.loop.create_task(
            self._async_update_temperature(
                temperature, interruption_level, interruption_time, interruption_moment
            )
        )

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        self._attr_hvac_mode = hvac_mode
        if self._task is not None:
            self._task.cancel()
            self._task = None
        self._update_attributes()

    def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        self._attr_preset_mode = preset_mode
        self._update_attributes()
