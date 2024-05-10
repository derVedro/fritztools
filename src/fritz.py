import click
from fritzconnection import FritzConnection
from fritzconnection.core.exceptions import (
    FritzConnectionException,
    FritzAuthorizationError,
)


def _get_connection():
    try:
        return FritzConnection(address="http://fritz.box", use_cache=True)
    except FritzConnectionException:
        click.echo("Could not connect to FritzBox")
        exit(1)
    except FritzAuthorizationError:
        click.echo(
            "Failed Authorization. Check your $FRITZ_PASSWORD environment variable"
        )
        exit(1)


def _get_hostadress():
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
            "WANPPPConnection1",
            "GetGenericPortMappingEntry",
            arguments={"NewPortMappingIndex": portmapping_number},
        )
        for portmapping_number in range(mappings_amount)
    ]


def _add_port_mapping(port, udp=False, enabled=True, **kwargs):
    fc = _get_connection()
    protocol = "UDP" if udp else "TCP"
    name = kwargs.get("name", "")
    description = (
        f'{_get_hostname()}-{port}{"-udp" if udp else ""}' if not name else name
    )
    client = _get_hostadress()

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
    fc.call_action("WANPPPConnection1", "AddPortMapping", arguments=args)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("port", type=int)
@click.option("--udp", is_flag=True, default=False)
@click.option("--name", type=str, default="")
def openport(port, udp, name):
    _add_port_mapping(port, udp, name=name)


@cli.command()
@click.argument("port", type=int)
@click.option("--udp", is_flag=True, default=False)
@click.option("--name", type=str, default="")
def closeport(port, udp, name):
    # may be forwarding is already known and disabled? reuse the name!
    if not name:
        client = _get_hostadress()
        for pm in _get_portmapping():
            if pm["NewInternalClient"] != client:
                continue
            if (
                pm["NewExternalPort"] == port
                and pm["NewProtocol"]
                and pm["NewInternalPort"] == port
            ):
                name = pm["NewPortMappingDescription"]
                break
    _add_port_mapping(port, udp, name=name, enabled=False)


@cli.command()
def listopen():
    for pm in _get_portmapping():
        click.echo(
            f' [{"X" if pm["NewEnabled"] else " "}] '
            f'{pm["NewPortMappingDescription"]:<10.10} {pm["NewProtocol"]} '
            f'{pm["NewRemoteHost"]}:{pm["NewExternalPort"]} -> '
            f'{pm["NewInternalClient"]}:{pm["NewInternalPort"]}'
        )


@cli.command()
def myip():
    fc = _get_connection()
    out = fc.call_action("WANPPPConnection1", "GetExternalIPAddress")
    print(out["NewExternalIPAddress"])


@cli.command()
def reconnect():
    fc = _get_connection()
    try:
        fc.call_action("WANPPPConnection1", "ForceTermination")
    except FritzConnectionException:
        pass


if __name__ == "__main__":
    cli()
