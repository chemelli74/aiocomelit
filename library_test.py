"""Test script for aiocomelit library."""
import argparse
import asyncio
import logging

from aiocomelit.api import (
    ComeliteSerialBridgeApi,
    ComelitSerialBridgeObject,
    ComelitVedoApi,
)
from aiocomelit.const import BRIDGE, COVER, IRRIGATION, LIGHT, OTHER, VEDO
from aiocomelit.exceptions import CannotAuthenticate, CannotConnect

GENERIC_ON = 1
INDEX = 1


def get_arguments() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Get parsed passed in arguments."""
    parser = argparse.ArgumentParser(description="aiovodafone library test")
    parser.add_argument(
        "--bridge",
        "-b",
        type=str,
        default="192.168.1.252",
        help="Set Serial bridge IP address",
    )
    parser.add_argument(
        "--bridge_pin",
        "-bp",
        type=str,
        default="",
        help="Set Serial bridge pin",
    )
    parser.add_argument(
        "--vedo",
        "-v",
        type=str,
        default="192.168.1.230",
        help="Set VEDO system IP address",
    )
    parser.add_argument(
        "--vedo_pin",
        "-vp",
        type=str,
        default="",
        help="Set VEDO system pin",
    )
    arguments = parser.parse_args()

    return parser, arguments


async def execute_test(
    api: ComeliteSerialBridgeApi, device: ComelitSerialBridgeObject, dev_type: str
) -> None:
    """Execute a test routine on a specific device type."""

    print(f"Test {dev_type} device: {device.name}")
    print("Status before: ", await api.get_device_status(dev_type, device.index))
    await api.set_device_status(dev_type, device.index, GENERIC_ON)
    print("Status after: ", await api.get_device_status(dev_type, device.index))


async def main() -> None:
    """Run main."""
    parser, args = get_arguments()

    print("-" * 20)
    bridge_api = ComeliteSerialBridgeApi(args.bridge, args.bridge_pin)
    logged = False
    try:
        logged = await bridge_api.login()
    except (CannotConnect, CannotAuthenticate):
        pass
    finally:
        if not logged:
            print("Unable to login to %s [%s]", BRIDGE, bridge_api.host)
            await bridge_api.close()
            exit(1)
    print("Logged:", logged)
    print("-" * 20)
    devices = await bridge_api.get_all_devices()
    print("Devices:", devices)
    print("-" * 20)
    for device in devices[LIGHT].values():
        if device.index == INDEX:
            await execute_test(bridge_api, device, LIGHT)
            break
    for device in devices[COVER].values():
        if device.index == INDEX:
            await execute_test(bridge_api, device, COVER)
            break
    for device in devices[IRRIGATION].values():
        if device.index == INDEX:
            await execute_test(bridge_api, device, IRRIGATION)
            break
    for device in devices[OTHER].values():
        if device.index == INDEX:
            await execute_test(bridge_api, device, OTHER)
            break

    print("-" * 20)
    print("Logout & close session")
    await bridge_api.logout()
    await bridge_api.close()

    # VEDO system mandatorily requires a pin
    if not args.vedo_pin:
        return

    vedo_api = ComelitVedoApi(args.vedo, args.vedo_pin)
    logged = False
    try:
        logged = await vedo_api.login()
    except (CannotConnect, CannotAuthenticate):
        pass
    finally:
        if not logged:
            print("Unable to login to %s[%s]", VEDO, vedo_api.host)
            await vedo_api.close()
            exit(1)
    print("Logged:", logged)
    print("-" * 20)
    config = await vedo_api.get_config()
    print("Config:", config)
    print("-" * 20)
    print("Logout & close session")
    await vedo_api.logout()
    await vedo_api.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
