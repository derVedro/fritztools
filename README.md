# <img src="./fritztools.svg" width="596" height="72"/>

fritztools is a small collection of CLI-goodies for your FritzBox 

## Features
* open, close and list ports forwardings
* turn on/off FritzBox wi-fi, list connected devices, get credentials as QR code
* show public IP address
* reconnect
* monitor up and downlink
* get FritzBox log

## Install
Clone the repo, then:

```
pip install .
```

## Usage
First at all, you should set FRITZ_PASSWORD environment variable with your FritzBox user password.

```
export FRITZ_PASSWORD=your_password
```

Then you can use fritztools on your shell with `fritz` command. A simple example of how to figure out all port forwardings on your FritzBox would look like this:  

```
fritz port list
```

For all the others commands just use the build-in `--help` argument.