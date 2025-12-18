"""Rpi device door api."""

import asyncio
from typing import Any

from raspberry_pi.services.thermostat_service import HVACMode

from .device import RaspberryPiDevice


class RaspberryPiThermostat(RaspberryPiDevice):
    """RaspberryPiThermostat component."""

    THERMOSTAT_SERVICE = "pi.virtual.thermostat"
    SET_THERMOSTAT_METHOD = "transition_thermostat_state"

    async def get_thermostat_state(self) -> None:
        """Get door state."""
        self._state = await self._query_helper(
            self.THERMOSTAT_SERVICE, "get_thermostat_state"
        )

    @property
    def thermostat_state(self) -> dict[str, str]:
        """Query the door state."""
        thermostat_state = self.sys_info["thermostat_state"]
        if thermostat_state is None:
            raise ValueError(
                "The device has no door_state or you have not called update()"
            )

        return thermostat_state

    @property
    def current_temperature(self) -> float | None:
        """Return True is the door is closed."""
        thermostat_state = self.thermostat_state
        return thermostat_state.get("current_temperature")

    @property
    def target_temperature(self):
        """Return current door position."""
        thermostat_state = self.thermostat_state
        return thermostat_state.get("target_temperature")

    @property
    def hvac_mode(self):
        """Return True is the door is opening."""
        thermostat_state = self.thermostat_state
        return thermostat_state.get("hvac_mode")

    @property
    def preset_mode(self):
        """Return True is the door is closing."""
        thermostat_state = self.thermostat_state
        return thermostat_state.get("preset_mode")

    async def set_temperature(self, temperature: float, **kwargs: Any) -> None:
        """Set new target temperature."""
        _state = {"temperature": temperature, **kwargs}

        themostat_state = await self._query_helper(
            self.THERMOSTAT_SERVICE, self.SET_THERMOSTAT_METHOD, _state
        )

        return themostat_state

    async def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _state = {"hvac_mode": hvac_mode}

        themostat_state = await self._query_helper(
            self.THERMOSTAT_SERVICE, self.SET_THERMOSTAT_METHOD, _state
        )

        return themostat_state

    async def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _state = {"preset_mode": preset_mode}

        themostat_state = await self._query_helper(
            self.THERMOSTAT_SERVICE, self.SET_THERMOSTAT_METHOD, _state
        )

        return themostat_state


async def main():
    device = RaspberryPiThermostat("127.0.0.1", 9999)
    await device.update()
    print(device.current_temperature)
    await device.set_temperature(69)
    await asyncio.sleep(10)
    await device.update()
    print(device.current_temperature)


if __name__ == "__main__":
    asyncio.run(main())
