"""Test script for aiocomelit library."""
import argparse
import asyncio
import logging

from aiocomelit.api import ComeliteSerialBridgeApi, ComelitVedoApi
from aiocomelit.const import BRIDGE, COVER, COVER_OPEN, LIGHT, LIGHT_ON, VEDO
from aiocomelit.exceptions import CannotAuthenticate, CannotConnect


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
            print(f"Unable to login to {BRIDGE} [{bridge_api.host}]")
            await bridge_api.close()
            exit(1)
    print("Logged:", logged)
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
