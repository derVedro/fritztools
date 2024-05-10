import click
from fritzconnection import FritzConnection
from fritzconnection.core.exceptions import (
    FritzConnectionException,
    FritzAuthorizationError,
)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def fritz():
    """Collection of some useful commands for the FritzBox"""
    pass


def _get_connection():
    try:
        return FritzConnection(address="http://fritz.box", use_cache=True)
    except FritzAuthorizationError:
        click.echo(
            "Failed Authorization. Check your $FRITZ_PASSWORD environment variable"
        )
        exit(1)
    except FritzConnectionException:
        click.echo("Could not connect to FritzBox")
        exit(1)


def _get_hostaddress():
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.settimeout(0)
        s.connect_ex(("255.255.255.0", 1))
        return s.getsockname()[0]


def _get_hostname():
    import os

    return os.uname()[1]


def _get_portmapping():
    fc = _get_connection()
    mappings_amount = fc.call_action(
        "WANPPPConnection1", "GetPortMappingNumberOfEntries"
    ).get("NewPortMappingNumberOfEntries", 0)
    return [
        fc.call_action(
            service_name="WANPPPConnection1",
            action_name="GetGenericPortMappingEntry",
            arguments={"NewPortMappingIndex": portmapping_number},
        )
        for portmapping_number in range(mappings_amount)
    ]


def _add_port_mapping(port, protocol="TCP", enabled=True, **kwargs):
    fc = _get_connection()
    name = kwargs.get("name", "")
    description = (
        f'{_get_hostname()}-{port}{"-udp" if protocol else ""}' if not name else name
    )
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
    fc.call_action(
        service_name="WANPPPConnection1", action_name="AddPortMapping", arguments=args
    )


@fritz.command()
@click.argument("port", type=int)
@click.option("--udp", "protocol", flag_value="UDP", help="use UDP instead of TCP")
@click.option("--tcp", "protocol", flag_value="TCP", default=True)
@click.option("--name", type=str, default="", help="name for the rule")
def openport(port, protocol, name):
    """Creates a PORT forwarding."""
    _add_port_mapping(port, protocol, name=name)


@fritz.command()
@click.argument("port", type=int)
@click.option("--udp", "protocol", flag_value="UDP", help="use UDP instead of TCP")
@click.option("--tcp", "protocol", flag_value="TCP", default=True)
@click.option("--name", type=str, default="")
def closeport(port, protocol, name):
    """Disables forwarding of the PORT."""
    # may be forwarding is already known and disabled? reuse the name!
    if not name:
        client = _get_hostaddress()
        for pm in _get_portmapping():
            if pm["NewInternalClient"] != client:
                continue
            if (
                pm["NewExternalPort"] == port
                and pm["NewProtocol"] == protocol
                and pm["NewInternalPort"] == port
            ):
                name = pm["NewPortMappingDescription"]
                break
    _add_port_mapping(port, protocol, name=name, enabled=False)


@fritz.command()
def listopen():
    """Lists all port forwardings."""
    for pm in _get_portmapping():
        click.echo(
            f' [{"X" if pm["NewEnabled"] else " "}] '
            f'{pm["NewPortMappingDescription"]:<10.10} {pm["NewProtocol"]} '
            f'{pm["NewRemoteHost"]}:{pm["NewExternalPort"]} -> '
            f'{pm["NewInternalClient"]}:{pm["NewInternalPort"]}'
        )


@fritz.command()
def myip():
    """Shows the current IP address."""
    fc = _get_connection()
    res = fc.call_action(
        service_name="WANPPPConnection1", action_name="GetExternalIPAddress"
    )
    click.echo(res["NewExternalIPAddress"])


@fritz.command()
def reconnect():
    """Terminates the FritzBox connection."""
    fc = _get_connection()
    try:
        fc.call_action(service_name="WANPPPConnection1", action_name="ForceTermination")
    except FritzConnectionException:
        pass


if __name__ == "__main__":
    fritz()
