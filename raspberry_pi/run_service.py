from raspberry_pi.server import DeviceServer
import argparse
import asyncio


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("device", type=str)
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", "-p", type=int, default=9999)
    parser.add_argument("--entity_id", "-e", type=str, default="default_id")
    parser.add_argument("--log_dir", "-l", type=str, default=None)
    args = parser.parse_args()
    
    server = DeviceServer.from_args(args)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())