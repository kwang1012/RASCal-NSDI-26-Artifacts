import asyncio
from raspberry_pi.devices import (
    RaspberryPiDoor,
    RaspberryPiFan,
    RaspberryPiLight,
    RaspberryPiLock,
    RaspberryPiShade,
    RaspberryPiSwitch,
    RaspberryPiThermostat
)
from raspberry_pi.devices.device import RaspberryPiDevice
import time

def _get_device_class(info: dict) -> type[RaspberryPiDevice]:
    """Find SmartDevice subclass for device described by passed data."""
    if "system" not in info or "get_sysinfo" not in info["system"]:
        raise ValueError("No 'system' or 'get_sysinfo' in response")

    sysinfo = info["system"]["get_sysinfo"]
    type_ = sysinfo.get("type", sysinfo.get("mic_type"))
    if type_ is None:
        raise ValueError("Unable to find the device type field!")

    if "door" in type_.lower():
        return RaspberryPiDoor

    if "thermostat" in type_.lower():
        return RaspberryPiThermostat

    if "shade" in type_.lower():
        return RaspberryPiShade

    if "fan" in type_.lower():
        return RaspberryPiFan

    if "light" in type_.lower():
        return RaspberryPiLight

    if "switch" in type_.lower():
        return RaspberryPiSwitch

    if "lock" in type_.lower():
        return RaspberryPiLock

    raise ValueError("Unknown device type: %s" % type_)

async def discover_device(host, port):
    device = RaspberryPiDevice(host, port=port)

    info = await device.query(
        {
            "system": {"get_sysinfo": None},
        }
    )

    device_class = _get_device_class(info)
    dev = device_class(host, port=port)
    await dev.update()
    
    return dev

async def async_device_update(device: RaspberryPiDevice) -> None:
    """
    Helper function to update a device asynchronously.
    :param device: The RaspberryPiDevice instance to update.
    """
    start = time.time()
    try:
        await device.update()
    except Exception as ex:
        print(f"Failed to update device {device.host}:{device.port}: {ex}")
    end = time.time()
    return end - start

async def main():
    """
    Main function to run network experiments on Raspberry Pi.
    This is a placeholder for actual network experiment code.
    """
    print("Running network experiments on Raspberry Pi...")
    # Add your network experiment code here
    with open("nodes.txt", "r") as f:
        hosts = [l.strip() for l in f.readlines()]
        
    devices = []

    try_ports = [9999+i for i in range(30)]
    for host in hosts:
        for port in try_ports:
            try:
                device = await discover_device(host, port=port)
                devices.append(device)
            except ValueError:
                pass
    latencies = [[] for _ in range(len(devices))]
    for _ in range(10):
        tasks = []
        for i, device in enumerate(devices):
            tasks.append(asyncio.create_task(async_device_update(device)))
        latency_list = await asyncio.gather(*tasks)
        for i, latency in enumerate(latency_list):
            if latency is not None:
                latencies[i].append(latency)
            else:
                print(f"Failed to get latency for device {i}")
        await asyncio.sleep(0.5)
    print("Average latencies for devices:")
    for i, device in enumerate(devices):
        if latencies[i]:
            avg_latency = sum(latencies[i]) / len(latencies[i])
            print(f"Device {i} (host: {device.host}, port: {device.port}): Average latency: {avg_latency:.4f} seconds")
        else:
            print(f"Device {i} (host: {device.host}, port: {device.port}): No successful updates")

if __name__ == "__main__":
    asyncio.run(main())