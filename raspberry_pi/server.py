import asyncio
import json
import pickle
import socket
import struct
import sys
import argparse
from dataclasses import dataclass

from raspberry_pi.utils import Device

@dataclass
class DeviceServerConfig:
    host: str
    port: int
    device: Device
    entity_id: str
    device_config: dict | None = None

def create_socket(host, start_port):
    """
    Finds the next available port starting from a given port number.

    Args:
        start_port (int): The port number to start searching from.

    Returns:
        int: The next available port number, or None if no port is available.
    """
    port = start_port
    while port < 65535:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return sock, port
        except OSError:
            port += 1
    return None, None

class DeviceServer:
    BLOCK_SIZE = 4

    def __init__(self, config: DeviceServerConfig) -> None:
        sock, port = create_socket(
            config.host, config.port)
        if sock is None:
            raise ValueError("Failed to create server")
        # become a server socket
        sock.listen(8)
        sock.setblocking(False)
        self.server = sock
        self.config = config
        self.port = port

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
            raise ValueError("Devicecd class not found")
        assert device_cls is not None
        self.device = device_cls(self.loop, config.entity_id)

    @classmethod
    def from_args(cls, args):
        
        config = DeviceServerConfig(
            host=args.host,
            port=args.port,
            device=Device(args.device),
            entity_id=args.entity_id
        )
        return cls(config)

    async def start(self):
        print(f"Start listening on port {self.port}...")
        while True:
            client, _ = await self.loop.sock_accept(self.server)
            self.loop.create_task(self._handle_connection(client))

    async def _handle_connection(self, sock: socket.socket):
        while True:
            try:
                buffer = await self._recv_msg(sock)
                if buffer is None:
                    break
                request = json.loads(pickle.loads(buffer))
                try:
                    resp = self.device.handle(request)
                    await self._send_msg(
                        sock, pickle.dumps(json.dumps(resp))
                    )
                except Exception as e:
                    print('\033[31m' + f"ERROR: {e}" + '\033[0m')
                    await self._send_msg(
                        sock, pickle.dumps(json.dumps({
                            "err_code": "internal error"
                        }))
                    )
            except Exception as e:
                print(e)
                break
        sock.close()

    async def _send_msg(self, sock, msg):
        """send message"""
        msg = struct.pack(">I", len(msg)) + msg
        await self.loop.sock_sendall(sock, msg)

    async def _recv_msg(self, sock):
        """receive message"""
        raw_msglen = await self._recvall(sock, 4)
        if not raw_msglen:
            return None
        msglen = struct.unpack(">I", raw_msglen)[0]
        # Read the message data
        return await self._recvall(sock, msglen)

    async def _recvall(self, sock, n):
        data = bytearray()
        while len(data) < n:
            packet = await self.loop.sock_recv(sock, n - len(data))
            if not packet:
                return data
            data.extend(packet)
        return data
