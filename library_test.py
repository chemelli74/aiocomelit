"""Test script for aiocomelit library."""

import asyncio
import json
import logging
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from aiohttp import ClientSession, CookieJar, TCPConnector
from colorlog import ColoredFormatter

from aiocomelit import __version__
from aiocomelit.api import (
    ComelitCommonApi,
    ComeliteSerialBridgeApi,
    ComelitSerialBridgeObject,
    ComelitVedoApi,
    ComelitVedoAreaObject,
)
from aiocomelit.const import (
    ALARM_ENABLE,
    BRIDGE,
    COVER,
    IRRIGATION,
    LIGHT,
    OTHER,
    STATE_ON,
    VEDO,
)
from aiocomelit.exceptions import CannotAuthenticate, CannotConnect, CannotRetrieveData

INDEX = 0


def get_arguments() -> tuple[ArgumentParser, Namespace]:
    """Get parsed passed in arguments."""
    parser = ArgumentParser(description="aiocomelit library test")
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
        "--bridge_vedo",
        "-bv",
        action="store_true",
        default=False,
        help="Use Serial bridge to access VEDO",
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
        action="store_true",
        default=False,
        help="Execute test actions",
    )
    parser.add_argument(
        "--configfile",
        "-cf",
        type=str,
        help="Load options from JSON config file. \
        Command line options override those in the file.",
    )
    arguments = parser.parse_args()
    # Re-parse the command line
    # taking the options in the optional JSON file as a basis
    if arguments.configfile and Path(arguments.configfile).exists():
        with Path.open(arguments.configfile) as f:
            arguments = parser.parse_args(namespace=Namespace(**json.load(f)))

    return parser, arguments


def logger(host_type: str, host: str, port: str) -> str:
    """Create logging string."""
    return f"{host_type} ({host}:{port})"


async def execute_device_test(
    api: ComeliteSerialBridgeApi,
    device: ComelitSerialBridgeObject,
    dev_type: str,
    api_logging: str,
) -> None:
    """Execute a test routine on a specific device type."""
    print(f"[{api_logging}] Test {dev_type} device: {device.name}")
    status = await api.get_device_status(dev_type, device.index)
    print(f"[{api_logging}] Status before: {status}")
    await api.set_device_status(dev_type, device.index, STATE_ON)
    status = await api.get_device_status(dev_type, device.index)
    print(f"[{api_logging}] Status after: {status}")


async def execute_alarm_test(
    api: ComelitCommonApi, area: ComelitVedoAreaObject, api_logging: str
) -> None:
    """Execute a test routine on a specific VEDO zone."""
    print(f"[{api_logging}] Test zone: {area.name}")
    print(f"[{api_logging}] Status before: {await api.get_area_status(area)}")
    await api.set_zone_status(area.index, ALARM_ENABLE)
    print(f"[{api_logging}] Status after: {await api.get_area_status(area)}")


async def bridge_test(session: ClientSession, args: Namespace) -> bool:
    """Test code for Comelit Serial Bridge."""
    bridge_api = ComeliteSerialBridgeApi(
        args.bridge, args.bridge_port, args.bridge_pin, session
    )
    api_logging = logger(BRIDGE, args.bridge, args.bridge_port)

    logged = False
    try:
        logged = await bridge_api.login()
    except (CannotConnect, CannotAuthenticate):
        pass
    finally:
        if not logged:
            print(f"[{api_logging}] Unable to login")
            await session.close()
            sys.exit(1)
    print(f"[{api_logging}] Logged = {logged}")
    print("-" * 20)
    devices = await bridge_api.get_all_devices()
    print(f"[{api_logging}] Devices: {devices}")
    print("-" * 20)
    if args.test:
        for device in devices[LIGHT].values():
            if device.index == INDEX:
                await execute_device_test(bridge_api, device, LIGHT, api_logging)
                break
        for device in devices[COVER].values():
            if device.index == INDEX:
                await execute_device_test(bridge_api, device, COVER, api_logging)
                break
        for device in devices[IRRIGATION].values():
            if device.index == INDEX:
                await execute_device_test(bridge_api, device, IRRIGATION, api_logging)
                break
        for device in devices[OTHER].values():
            if device.index == INDEX:
                await execute_device_test(bridge_api, device, OTHER, api_logging)
                break
        print("-" * 20)

    vedo_enabled: bool = (
        await bridge_api.vedo_enabled(args.vedo_pin or args.bridge_pin)
        and args.bridge_vedo
    )

    if vedo_enabled:
        print(f"[{api_logging}] VEDO Enabled !")
        await vedo_test(session, args, bridge_api)

    print(f"[{api_logging}] Logout")
    await bridge_api.logout()

    return vedo_enabled


async def vedo_test(
    session: ClientSession,
    args: Namespace,
    bridge_api: ComeliteSerialBridgeApi | None = None,
) -> None:
    """Test code for Comelit VEDO system."""
    api: ComelitCommonApi

    if not bridge_api:
        api = ComelitVedoApi(args.vedo, args.vedo_port, args.vedo_pin, session)
        api_logging = logger(VEDO, args.vedo, args.vedo_port)
        logged = False
        try:
            logged = await api.login()
        except (CannotConnect, CannotAuthenticate):
            pass
        finally:
            if not logged:
                print(f"[{api_logging}] Unable to login to {VEDO}")
                await session.close()
                sys.exit(1)
        print(f"[{api_logging}] Logged = {logged}")
    else:
        api = bridge_api
        api_logging = logger(BRIDGE, args.bridge, args.bridge_port)
        print(f"[{api_logging}] {VEDO} logged")
    print("-" * 20)
    try:
        alarm_data = await api.get_all_areas_and_zones()
    except (CannotAuthenticate, CannotRetrieveData):
        print(f"[{api_logging}] Unable to retrieve data for {VEDO}")
        await api.logout()
        await session.close()
        sys.exit(2)
    print(f"[{api_logging}] AREAS:")
    for area in alarm_data["alarm_areas"]:
        print(alarm_data["alarm_areas"][area])
    print("-" * 20)
    print(f"[{api_logging}] ZONES:")
    for zone in alarm_data["alarm_zones"]:
        print(alarm_data["alarm_zones"][zone])
    print("-" * 20)
    if args.test:
        await execute_alarm_test(api, alarm_data["alarm_areas"][INDEX], api_logging)
        print("-" * 20)
    print(f"{api_logging} Logout")
    await api.logout()


async def main() -> None:
    """Run main."""
    parser, args = get_arguments()

    print("-" * 20)
    print(f"aiocomelit version: {__version__}")
    print("-" * 20)

    # Create aiohttp.ClientSsession
    print("Creating HTTP ClientSession")
    jar = CookieJar(unsafe=True)
    connector = TCPConnector(force_close=True)
    session = ClientSession(cookie_jar=jar, connector=connector)

    bridge_vedo_enabled = await bridge_test(session, args)

    # VEDO is not accessible via Serial bridge, need direct access
    if not bridge_vedo_enabled:
        # VEDO system mandatorily requires a pin for direct access
        if not args.vedo_pin:
            print(f"{VEDO}: Missing PIN. Skipping tests")
            parser.print_help()
            return
        await vedo_test(session, args, None)

    print("Closing HTTP ClientSession")
    await session.close()


def set_logging() -> None:
    """Set logging levels."""
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
        ),
    )


if __name__ == "__main__":
    set_logging()
    asyncio.run(main())
