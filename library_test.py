"""Test script for aiocomelit library."""
import argparse
import ast
import asyncio
import logging

from colorlog import ColoredFormatter

from aiocomelit import __version__
from aiocomelit.api import (
    ComeliteSerialBridgeApi,
    ComelitSerialBridgeObject,
    ComelitVedoApi,
    ComelitVedoAreaObject,
)
from aiocomelit.const import (
    ALARM_AREAS,
    ALARM_ENABLE,
    ALARM_ZONES,
    BRIDGE,
    COVER,
    IRRIGATION,
    LIGHT,
    OTHER,
    STATE_ON,
    VEDO,
)
from aiocomelit.exceptions import CannotAuthenticate, CannotConnect

INDEX = 0


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
        "--bridge_port",
        "-bport",
        type=str,
        default=80,
        help="Set Serial bridge http port",
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
    parser.add_argument(
        "--test",
        "-t",
        type=ast.literal_eval,
        default=True,
        help="Execute test actions",
    )
    arguments = parser.parse_args()

    return parser, arguments


async def execute_device_test(
    api: ComeliteSerialBridgeApi, device: ComelitSerialBridgeObject, dev_type: str
) -> None:
    """Execute a test routine on a specific device type."""

    print(f"Test {dev_type} device: {device.name}")
    print("Status before: ", await api.get_device_status(dev_type, device.index))
    await api.set_device_status(dev_type, device.index, STATE_ON)
    print("Status after: ", await api.get_device_status(dev_type, device.index))


async def execute_alarm_test(api: ComelitVedoApi, area: ComelitVedoAreaObject) -> None:
    """Execute a test routine on a specific VEDO zone."""

    print(f"Test zone: {area.name}")
    print("Status before: ", await api.get_area_status(area))
    await api.set_zone_status(area.index, ALARM_ENABLE)
    print("Status after: ", await api.get_area_status(area))


async def main() -> None:
    """Run main."""
    parser, args = get_arguments()

    print("-" * 20)
    print(f"aiocomelit version: {__version__}")
    print("-" * 20)
    bridge_api = ComeliteSerialBridgeApi(args.bridge, args.bridge_port, args.bridge_pin)
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
    if args.test:
        for device in devices[LIGHT].values():
            if device.index == INDEX:
                await execute_device_test(bridge_api, device, LIGHT)
                break
        for device in devices[COVER].values():
            if device.index == INDEX:
                await execute_device_test(bridge_api, device, COVER)
                break
        for device in devices[IRRIGATION].values():
            if device.index == INDEX:
                await execute_device_test(bridge_api, device, IRRIGATION)
                break
        for device in devices[OTHER].values():
            if device.index == INDEX:
                await execute_device_test(bridge_api, device, OTHER)
                break
        print("-" * 20)
    print("Logout & close session")
    await bridge_api.logout()
    await bridge_api.close()

    # VEDO system mandatorily requires a pin
    if not args.vedo_pin:
        print("VEDO, missing PIN. Skipping")
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
    alarm_data = await vedo_api.get_all_areas_and_zones()
    print("AREAS:")
    for area in alarm_data[ALARM_AREAS]:
        print(alarm_data[ALARM_AREAS][area])
    print("-" * 20)
    print("ZONES:")
    for zone in alarm_data[ALARM_ZONES]:
        print(alarm_data[ALARM_ZONES][zone])
    print("-" * 20)
    if args.test:
        await execute_alarm_test(vedo_api, alarm_data[ALARM_AREAS][INDEX])
        print("-" * 20)
    print("Logout & close session")
    await vedo_api.logout()
    await vedo_api.close()


def set_logging() -> None:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.INFO)
    logging.getLogger("charset_normalizer").setLevel(logging.INFO)
    fmt = (
        "%(asctime)s.%(msecs)03d %(levelname)s (%(threadName)s) [%(name)s] %(message)s"
    )
    colorfmt = f"%(log_color)s{fmt}%(reset)s"
    logging.getLogger().handlers[0].setFormatter(
        ColoredFormatter(
            colorfmt,
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
        )
    )
    return


if __name__ == "__main__":
    set_logging()
    asyncio.run(main())
