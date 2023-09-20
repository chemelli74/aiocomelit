"""Test script for aiocomelit library."""
import argparse
import asyncio
import logging

from aiocomelit.api import ComeliteSerialBridgeApi
from aiocomelit.const import COVER, COVER_OPEN, LIGHT, LIGHT_ON


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
        "--alarm_pin", "-ap", type=str, default="111111", help="Set VEDO alarm pin"
    )
    arguments = parser.parse_args()

    return parser, arguments


async def main() -> None:
    """Run main."""
    parser, args = get_arguments()

    print("-" * 20)
    bridge_api = ComeliteSerialBridgeApi(args.bridge, args.alarm_pin)
    await bridge_api.login()
    print("-" * 20)
    devices = await bridge_api.get_all_devices()
    print("Devices:", devices)
    print("-" * 20)
    for device in devices[LIGHT].values():
        if device.index == 1:
            print("Test light switch on:", device.name)
            print("status before: ", await bridge_api.light_status(device.index))
            await bridge_api.light_switch(device.index, LIGHT_ON)
            print("status after: ", await bridge_api.light_status(device.index))
            break
    for device in devices[COVER].values():
        if device.index == 1:
            print("Test cover  open  on:", device.name)
            print("status before: ", await bridge_api.cover_status(device.index))
            await bridge_api.cover_move(device.index, COVER_OPEN)
            print("status after: ", await bridge_api.cover_status(device.index))
            break

    print("-" * 20)
    print("Logout & close session")
    await bridge_api.logout()
    await bridge_api.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
