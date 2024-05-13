# <img src="./fritztools.svg" width="596" height="72"/>

fritztools is a small collection of CLI-goodies for your FritzBox 

## Features
* open ports
* close ports
* list all port forwardings
* show public IP address
* reconnect

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
fritz listopen
```

For all the others commands just use the build-in `--help` argument.