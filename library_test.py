import argparse
import asyncio
import logging

from aiocomelit.api import ComeliteSerialBridgeAPi
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
    api = ComeliteSerialBridgeAPi(args.bridge, args.alarm_pin)
    devices = await api.get_all_devices()
    print("Devices:", devices)
    print("-" * 20)
    alarm = await api.get_alarm_config()
    print("Alarm config:", alarm)
    print("-" * 20)
    for device in devices:
        if device.index == 1:
            if device.type == LIGHT:
                print("Test light switch on:", device.name)
                await api.light_switch(device.index, LIGHT_ON)
            if device.type == COVER:
                print("Test cover  open  on:", device.name)
                await api.cover_move(device.index, COVER_OPEN)
    print("-" * 20)
    print("Logout & close session")
    await api.logout()
    await api.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
