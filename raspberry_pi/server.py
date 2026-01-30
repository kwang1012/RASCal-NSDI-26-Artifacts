import asyncio
import json
import pickle
import struct
from dataclasses import dataclass

from rasc.datasets import Device


@dataclass
class DeviceServerConfig:
    host: str
    port: int
    device: Device
    entity_id: str
    device_config: dict | None = None
    log_dir: str | None = None


class DeviceServer:
    BLOCK_SIZE = 4

    def __init__(self, config: DeviceServerConfig) -> None:
        self.config = config
        self.port = config.port
        self.loop = asyncio.get_event_loop()

        device = config.device
        device_cls = None
        if device == Device.DOOR or device == Device.COVER:
            from raspberry_pi.services.door_service import DoorService
            device_cls = DoorService
        elif device == Device.THERMOSTAT:
            from raspberry_pi.services.thermostat_service import ThermostatService
            device_cls = ThermostatService
        elif device == Device.SHADE:
            from raspberry_pi.services.shade_service import ShadeService
            device_cls = ShadeService
        elif device == Device.LIGHT:
            from raspberry_pi.services.light_service import LightService
            device_cls = LightService
        elif device == Device.SWITCH:
            from raspberry_pi.services.switch_service import SwitchService
            device_cls = SwitchService
        elif device == Device.LOCK:
            from raspberry_pi.services.lock_service import LockService
            device_cls = LockService
        elif device == Device.FAN:
            from raspberry_pi.services.fan_service import FanService
            device_cls = FanService
        else:
            raise ValueError("Device class not found")

        self.device = device_cls(self.loop, config)

    @classmethod
    def from_args(cls, args):
        if args.device == "climate":
            args.device = "thermostat"
        
        # convert shade.xxx to cover.xxx to match home assistant naming
        if args.entity_id.startswith("shade."):
            args.entity_id = args.entity_id.replace("shade.", "cover.")
        
        config = DeviceServerConfig(
            host=args.host,
            port=args.port,
            device=Device(args.device),
            entity_id=args.entity_id,
            log_dir=args.log_dir,
        )
        return cls(config)
    
    async def start(self):
        server = await asyncio.start_server(
            self._handle_connection,
            self.config.host,
            self.config.port,
        )
        print(f"Start listening on {self.config.host}:{self.config.port}")

        async with server:
            await server.serve_forever()

    async def _handle_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        try:
            while True:
                # Read length prefix
                raw_len = await reader.readexactly(self.BLOCK_SIZE)
                msglen = struct.unpack(">I", raw_len)[0]

                # Read payload
                buffer = await reader.readexactly(msglen)

                request = json.loads(pickle.loads(buffer))

                try:
                    resp = self.device.handle(request)

                    payload = pickle.dumps(json.dumps(resp))
                except Exception as e:
                    print('\033[31m' + f"ERROR: {e}" + '\033[0m')
                    payload = pickle.dumps(json.dumps({
                        "err_code": "internal error"
                    }))

                writer.write(struct.pack(">I", len(payload)) + payload)
                await writer.drain()

        except asyncio.IncompleteReadError:
            # Client closed connection cleanly
            pass
        except Exception as e:
            print(f"Connection error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
