"""Test script for aiocomelit VEDO system."""
import argparse
import asyncio
import datetime
import logging

from aiocomelit import __version__
from aiocomelit.api import ComelitVedoApi, ComelitVedoObject
from aiocomelit.const import ALARM_ENABLE, VEDO
from aiocomelit.exceptions import CannotAuthenticate, CannotConnect

INDEX = 0
NUM_LOOPS = 500


def get_arguments() -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Get parsed passed in arguments."""
    parser = argparse.ArgumentParser(description="aiovodafone library test")
    parser.add_argument(
        "--vedo",
        "-v",
        type=str,
        default="192.168.1.230",
        help="Set VEDO system IP address",
    )
    parser.add_argument(
        "--vedo_port",
        "-vport",
        type=str,
        default=80,
        help="Set VEDO system http port",
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


async def execute_alarm_test(api: ComelitVedoApi, zone: ComelitVedoObject) -> None:
    """Execute a test routine on a specific VEDO zone."""

    print(f"Test zone: {zone.name}")
    print("Status before: ", await api.get_zone_status(zone.index))
    await api.set_zone_status(zone.index, ALARM_ENABLE)

    for i in range(NUM_LOOPS):
        print(
            datetime.datetime.now(),
            "- Status : ",
            await api.get_zone_status(zone.index),
        )
        await asyncio.sleep(2)


async def main() -> None:
    """Run main."""
    parser, args = get_arguments()

    print("-" * 20)
    print(f"aiocomelit version: {__version__}")
    print("-" * 20)

    # VEDO system mandatorily requires a pin
    if not args.vedo_pin:
        print("No pin specified, exiting...")
        return

    vedo_api = ComelitVedoApi(args.vedo, args.vedo_port, args.vedo_pin)
    logged = False
    try:
        logged = await vedo_api.login()
    except (CannotConnect, CannotAuthenticate):
        pass
    finally:
        if not logged:
            print(f"Unable to login to {VEDO} [{vedo_api.host}]")
            await vedo_api.close()
            exit(1)
    print("Logged:", logged)
    print("-" * 20)
    alarm_data = await vedo_api.get_config_and_status()
    print("Config:", alarm_data)
    print("-" * 20)
    await execute_alarm_test(vedo_api, alarm_data["alarm"][INDEX])
    print("-" * 20)
    print("Logout & close session")
    await vedo_api.logout()
    await vedo_api.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())
