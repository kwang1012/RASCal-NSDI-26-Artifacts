"""Rpi device fan api."""
import asyncio
from typing import Any

from .device import RaspberryPiDevice


class RaspberryPiFan(RaspberryPiDevice):
    """RaspberryPiDoor component."""

    FAN_SERVICE = "pi.virtual.fan"
    SET_FAN_METHOD = "transition_fan_state"

    async def get_fan_state(self) -> None:
        """Get shade state."""
        self._state = await self._query_helper(self.FAN_SERVICE, "get_fan_state")

    @property
    def fan_state(self) -> dict[str, str]:
        """Query the fan state."""
        fan_state = self.sys_info["fan_state"]
        if fan_state is None:
            raise ValueError(
                "The device has no shade_state or you have not called update()"
            )

        return fan_state

    @property
    def is_on(self) -> bool | None:
        """Return true if the entity is on."""
        return (
            self.percentage is not None and self.percentage > 0
        ) or self.preset_mode is not None

    @property
    def percentage(self) -> int | None:
        fan_state = self.fan_state
        return fan_state.get("percentage")

    @property
    def speed_count(self) -> int:
        fan_state = self.fan_state
        return fan_state.get("speed_count")

    @property
    def percentage_step(self) -> float:
        fan_state = self.fan_state
        return fan_state.get("percentage_step")

    @property
    def current_direction(self) -> str | None:
        fan_state = self.fan_state
        return fan_state.get("direction")

    @property
    def oscillating(self) -> bool | None:
        fan_state = self.fan_state
        return fan_state.get("oscillating")

    @property
    def preset_mode(self) -> str | None:
        fan_state = self.fan_state
        return fan_state.get("preset_mode")

    @property
    def preset_modes(self) -> list[str] | None:
        """Return a list of available preset modes.

        Requires FanEntityFeature.SET_SPEED.
        """
        if hasattr(self, "_attr_preset_modes"):
            return self._attr_preset_modes
        return None

    async def set_percentage(self, percentage: int) -> None:
        """Set the speed of the fan, as a percentage."""

        _state = {"percentage": percentage}

        shade_state = await self._query_helper(
            self.FAN_SERVICE, self.SET_FAN_METHOD, _state
        )

    async def set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        _state = {"preset_mode": preset_mode}

        fan_state = await self._query_helper(
            self.FAN_SERVICE, self.SET_FAN_METHOD, _state
        )
        return fan_state

    async def turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the entity."""
        _state = {"on_off": 1}

        fan_state = await self._query_helper(
            self.FAN_SERVICE, self.SET_FAN_METHOD, _state
        )
        return fan_state

    async def turn_off(self, **kwargs: Any) -> None:
        """Turn off the entity."""
        _state = {"on_off": 0}

        fan_state = await self._query_helper(
            self.FAN_SERVICE, self.SET_FAN_METHOD, _state
        )
        return fan_state

    async def set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        _state = {"direction": direction}

        fan_state = await self._query_helper(
            self.FAN_SERVICE, self.SET_FAN_METHOD, _state
        )
        return fan_state

    async def oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        _state = {"oscillating": oscillating}

        fan_state = await self._query_helper(
            self.FAN_SERVICE, self.SET_FAN_METHOD, _state
        )
        return fan_state


async def main():
    device = RaspberryPiFan("127.0.0.1", 9999)
    await device.update()
    print(device.fan_state)
    await device.turn_on()
    await asyncio.sleep(2)
    await device.update()
    print(device.fan_state)
    await device.set_percentage(100)
    await asyncio.sleep(2)
    await device.update()
    print(device.fan_state)

if __name__ == "__main__":
    asyncio.run(main())
