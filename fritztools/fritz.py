"""
Collection of some useful commands for the FritzBox
"""

import click
from fritzconnection import FritzConnection
from fritzconnection.core.exceptions import (
    FritzConnectionException,
    FritzAuthorizationError,
    FritzServiceError,
)
from fritztools.clickhelpers import OrderedGroup, split_params_commas_callback
from fritztools.outputhelpers import tabello, upline, heighlight, active_mark, charbar
from fritztools.consts import WIFI
from fritztools import __version__


@click.group(cls=OrderedGroup, context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__)
def fritz():
    """Collection of some useful commands for the FritzBox"""
    pass


@fritz.group(cls=OrderedGroup)
def port():
    """Do port forwarding"""
    pass


@fritz.group(cls=OrderedGroup)
def wlan():
    """Do wi-fi stuff"""
    pass


def _get_connection():
    global _fritz_connection
    if "_fritz_connection" not in globals():
        try:
            _fritz_connection = FritzConnection(
                address="http://fritz.box", use_cache=True
            )
            # have to do it here, otherwise auth errors must be catched later in different places
            _fritz_connection.call_action(
                service_name="WANPPPConnection1", action_name="GetExternalIPAddress"
            )
        except FritzAuthorizationError:
            click.echo(
                "Failed Authorization. Check your $FRITZ_PASSWORD environment variable."
            )
            exit(1)
        except FritzConnectionException:
            click.echo("Could not connect to FritzBox.")
            exit(1)

    return _fritz_connection


def _call(service_name, action_name, arguments=None):
    if arguments is None:
        arguments = dict()
    fc = _get_connection()
    return fc.call_action(
        service_name=service_name, action_name=action_name, arguments=arguments
    )


def _get_hostaddress():
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(0)
        s.connect_ex(("255.255.255.0", 1))
        return s.getsockname()[0]


def _get_hostname(mac_address=None):
    if mac_address is None:
        import os

        return os.uname()[1]
    return _call(
        service_name="Hosts1",
        action_name="GetSpecificHostEntry",
        arguments={"NewMACAddress": mac_address},
    )["NewHostName"]


def _get_portmapping():
    mappings_amount = _call(
        service_name="WANPPPConnection1", action_name="GetPortMappingNumberOfEntries"
    ).get("NewPortMappingNumberOfEntries", 0)
    return [
        _call(
            service_name="WANPPPConnection1",
            action_name="GetGenericPortMappingEntry",
            arguments={"NewPortMappingIndex": portmapping_number},
        )
        for portmapping_number in range(mappings_amount)
    ]


def _get_suitable_name(port, protocol):
    client = _get_hostaddress()
    # maybe forwarding is already known? reuse the name!
    for pm in _get_portmapping():
        if (
            pm["NewInternalClient"] == client
            and pm["NewProtocol"] == protocol
            and pm["NewExternalPort"] == port
            and pm["NewInternalPort"] == port
        ):
            name = pm["NewPortMappingDescription"]
            break
    else:
        name = f"{_get_hostname()}-{port}-{protocol.lower()}"
    return name


def _add_port_mapping(port, protocol="TCP", enabled=True, name=""):
    description = name if name != "" else _get_suitable_name(port, protocol)
    client = _get_hostaddress()
    args = {
        "NewRemoteHost": "0.0.0.0",
        "NewExternalPort": port,
        "NewProtocol": protocol,
        "NewInternalPort": port,
        "NewInternalClient": client,
        "NewEnabled": enabled,
        "NewPortMappingDescription": description,
        "NewLeaseDuration": 0,
    }
    _call(
        service_name="WANPPPConnection1", action_name="AddPortMapping", arguments=args
    )


def _get_myip():
    res = _call(service_name="WANPPPConnection1", action_name="GetExternalIPAddress")
    return res["NewExternalIPAddress"]


def _terminate():
    try:
        _call(service_name="WANPPPConnection1", action_name="ForceTermination")
    except FritzConnectionException:
        pass


@port.command(name="open")
@click.argument("port", type=int)
@click.option("--udp", "protocol", flag_value="UDP", help="use UDP instead of TCP")
@click.option("--tcp", "protocol", flag_value="TCP", default=True)
@click.option("--name", type=str, default="", help="name for the rule")
def port_open(port, protocol, name):
    """Creates a PORT forwarding."""
    _add_port_mapping(port, protocol, name=name)


@port.command(name="close")
@click.argument("port", type=int)
@click.option("--udp", "protocol", flag_value="UDP", help="use UDP instead of TCP")
@click.option("--tcp", "protocol", flag_value="TCP", default=True)
@click.option("--name", type=str, default="")
def port_close(port, protocol, name):
    """Disables forwarding of the PORT."""
    _add_port_mapping(port, protocol, name=name, enabled=False)


@port.command(name="list")
def port_list():
    """Lists all port forwardings."""

    t_header = ["ACTIVE ", "DECRIPTION", "PROTOCOL", "FROM", "TO"]
    t_data = [
        [
            f'{active_mark(pm["NewEnabled"])}',
            f'{pm["NewPortMappingDescription"]}',
            f'{pm["NewProtocol"]}',
            f'{pm["NewRemoteHost"]}:{pm["NewExternalPort"]}',
            f'{pm["NewInternalClient"]}:{pm["NewInternalPort"]}',
        ]
        for pm in _get_portmapping()
    ]
    if t_data:
        click.echo(tabello(headers=t_header, data=t_data, aligns="^<<<<"))
    else:
        click.echo("no port mappings found")


@fritz.command()
@click.option("--newip", "insistent", is_flag=True, default=False)
def reconnect(insistent=False, attempts=5, attempt_delay=5):
    """Terminates the FritzBox connection."""

    if not insistent:
        _terminate()
    else:
        import time, os

        old_ip = _get_myip()
        for attempt in range(attempts):
            click.echo(f"\r{attempt+1} attempt to get a new IP", nl=False)
            _terminate()
            time.sleep(attempt_delay)
            new_ip = _get_myip()
            if new_ip != old_ip:
                click.echo(f"{os.linesep}new IP: {new_ip}")
                break
        else:
            click.echo(f"{os.linesep}could not get a new IP")
            exit(-1)


@fritz.command()
def myip():
    """Shows the current IP address."""
    click.echo(_get_myip())


@wlan.command(name="on")
@click.argument("wlans", nargs=-1, callback=split_params_commas_callback)
def wlan_on(wlans):
    """Turn on wi-fi network."""
    _wlan_on_off(names=wlans, activate=True)


@wlan.command(name="off")
@click.argument("wlans", nargs=-1, callback=split_params_commas_callback)
def wlan_off(wlans):
    """Turn off wi-fi network."""
    _wlan_on_off(names=wlans, activate=False)


def _wlan_on_off(names, activate):
    # the default fall if names was empty
    if not names:
        names = ["1", "2"] if activate else ["all"]  # TODO: hard coded values :(
    wlan_nums, unknown_names = [], []
    for wlan_name in names:
        try:
            wlan_nums.extend(WIFI.NAMES_TO_CONNECTION_NUMBERS[wlan_name])
        except KeyError:
            if wlan_name:
                unknown_names.append(wlan_name)
    if unknown_names:
        click.echo(
            f"unknown wlan name{'s' if len(unknown_names) > 1 else ''}: "
            f"{', '.join(unknown_names)}"
        )
    for wlan_num in set(wlan_nums):
        _call(
            service_name=f"WLANConfiguration{wlan_num}",
            action_name="SetEnable",
            arguments={"NewEnable": activate},
        )


@wlan.command(name="list")
def wlan_list():
    """List all wi-fis and their stats"""
    t_headers = ["NETWORK", "ACTIVE", "SSID", "CHANNEL", "FREQ"]
    t_data = []
    for wlan_number, wlan_name in WIFI.NAMES.items():
        try:
            res = _call(
                service_name=f"WLANConfiguration{wlan_number}", action_name="GetInfo"
            )
            t_data.append(
                [
                    f"{wlan_name}",
                    f'{active_mark(res["NewStatus"] == "Up")}',
                    f'{res["NewSSID"]}',
                    f'{res["NewChannel"]:4}',
                    f'{WIFI.FREQ_STR[res.get("NewX_AVM-DE_FrequencyBand", "unknown")]}',
                ]
            )
        except FritzServiceError:
            break
    click.echo(tabello(data=t_data, headers=t_headers))


@wlan.command(name="qr")
@click.argument("wlan")
def wlan_qr(wlan):
    """Print the credentials of given wi-fi network as QR code."""
    wlan_number = WIFI.NAMES_TO_CONNECTION_NUMBERS.get(wlan, None)
    if not wlan_number:
        click.echo("unknown wlan name")
        exit(-1)

    service = f"WLANConfiguration{wlan_number[0]}"  # wlan_number comes as list
    ssid = _call(service_name=service, action_name="GetInfo")["NewSSID"]
    passw = _call(service_name=service, action_name="GetSecurityKeys")[
        "NewKeyPassphrase"
    ]
    hidden = not _call(service_name=service, action_name="GetBeaconAdvertisement")[
        "NewBeaconAdvertisementEnabled"
    ]
    beacontype = _call(service_name=service, action_name="GetInfo")["NewBeaconType"]
    if beacontype in ["None", "OWE", "OWETrans"]:
        security = "nopass"
        passw = None
    else:                   # almost nobody cares about this special value,
        security = "WPA"    # your device handles the proper encryption for self

    from segno.helpers import make_wifi
    from io import StringIO

    qr = make_wifi(ssid=ssid, password=passw, hidden=hidden, security=security)
    str_stream = StringIO()
    qr.terminal(out=str_stream, border=1, compact=True)
    click.echo(str_stream.getvalue())


@wlan.command(name="devices")
def wlan_listdevice():
    """List all wi-fi connected devices."""
    t_headers = ["HOSTNAME", "MAC ADRESS", "IP ADRESS", "SPEED", "SIGNAL"]
    t_data = []
    for wlan_number, wlan_name in WIFI.NAMES.items():
        try:
            res = _call(
                service_name=f"WLANConfiguration{wlan_number}",
                action_name="GetTotalAssociations",
            )
            for i in range(res["NewTotalAssociations"]):
                res = _call(
                    service_name=f"WLANConfiguration{wlan_number}",
                    action_name="GetGenericAssociatedDeviceInfo",
                    arguments={"NewAssociatedDeviceIndex": i},
                )
                t_data.append(
                    [
                        f'{_get_hostname(res["NewAssociatedDeviceMACAddress"])}',
                        f'{res["NewAssociatedDeviceMACAddress"]}',
                        f'{res["NewAssociatedDeviceIPAddress"]}',
                        f'{res["NewX_AVM-DE_Speed"]}',
                        f'{res["NewX_AVM-DE_SignalStrength"]}',
                    ]
                )

        except FritzServiceError:
            break
    click.echo(tabello(data=t_data, headers=t_headers))


def _get_online_monitor():
    res = _call(
        service_name="WANCommonInterfaceConfig",
        action_name="X_AVM-DE_GetOnlineMonitor",
        arguments={"NewSyncGroupIndex": 0},
    )

    return {
        "max_upload": res["Newmax_us"],
        "max_download": res["Newmax_ds"],
        "last_uploads": list(map(int, res["Newus_current_bps"].split(","))),
        "last_downloads": list(map(int, res["Newds_current_bps"].split(","))),
    }


@fritz.command(name="speedmeter")
@click.option("--once", is_flag=True)
def speedmeter(once=False):
    """Monitor up and downlink speed and utilisation."""
    import time

    t_headers = ["LINK", "CURRENT", "MAX", "UTILIZATION", "HISTORY"]
    abort = False
    while not abort:
        out = _get_online_monitor()
        t_data = [
            [
                "UP",
                f'{out["last_uploads"][0]}',
                f'{out["max_upload"]}',
                f'{(out["last_uploads"][0] / out["max_upload"]) if out["max_upload"] != 0 else 0:.3f}',
                "".join(
                    [charbar(val, out["max_upload"]) for val in out["last_uploads"]]
                ),
            ],
            [
                "DOWN",
                f'{out["last_downloads"][0]}',
                f'{out["max_download"]}',
                f'{(out["last_downloads"][0] / out["max_download"]) if out["max_download"] != 0 else 0:.3f}',
                "".join(
                    [charbar(val, out["max_download"]) for val in out["last_downloads"]]
                ),
            ],
        ]

        table = tabello(data=t_data, headers=t_headers, aligns=">")
        table_lines = len(table.splitlines())
        click.echo(table + upline(table_lines))

        if not once:
            time.sleep(1)
        else:
            abort = True


@fritz.command()
@click.option("-l", "--lastlines", default=10)
def log(lastlines):
    """Get the log from the FritzBox"""
    import os

    res = _call(service_name="DeviceInfo", action_name="GetDeviceLog")
    log_lines = res["NewDeviceLog"].split("\n")
    if lastlines < len(log_lines):
        log_lines = log_lines[:lastlines]
    click.echo(os.linesep.join(heighlight(line[:17]) + line[17:] for line in log_lines))


if __name__ == "__main__":
    fritz()
