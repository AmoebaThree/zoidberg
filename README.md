# Zoidberg

The Mastermind

## Prerequisites

On nodes that will be running Zoidberg commands:

- `sudo apt-get install python3-pip`
- `sudo update-alternatives --config python` and select Python 3
- `pip install pyyaml`

On nodes that will be receiveing Zoidberg commands:

- `sudo apt-get install git python3-pip`
- `sudo update-alternatives --config python` and select Python 3
- `pip install pyyaml`

## Command spec

Assumes you have the zb symlink, and have symlinked the path to your zoidberg
config file as ./zbc.

Each command takes the following structure:

    ./zb ./zbc <instruction> [services...]

For each command, you may optionally specify a subset of services that the
command should apply to. Otherwise it will apply to all services in the specified
config file.

Available instructions:
- install
  - Install the entire system, or the specified services
  - Deletes anything that currently exists for those services and starts from scratch
- update
  - Updates the whole system or the specified services
  - Assumes everything's in place already and does a git pull on the branch specified in the source
- start
- run
  - Start the whole system, or just the specified services
  - Assumes everything's in place already, doesn't make any installation changes
  - `start` and `run` are synonyms
- stop
  - Stops the whole system, or just the specified services
  - Assumes everything's in place already, doesn't make any installation changes
- restart
  - Restarts the whole system, or just the specified services
  - Assumes everything's in place already, doesn't make any installation changes
- install_prereqs
  - Installs the prerequisites for Zoidberg on the target nodes
  - Only needs to be done once per node
- shutdown
  - Shuts down the nodes

## Config file

The YAML file specifies:

* Which hosts are available
* Which sources are available, and where they are from
* Which services need to run on which host

It is possible for a single host to hold multiple sources and multiple services.
It is possible for a single source to be used in multiple services, and those
services to be on different machines.

Example YAML:

```
hosts:
    hostid1:
        ip: 0.0.0.1
    hostid2:
        ip: 0.0.0.2
source:
    source1:
        source: https://git.uri/svc1.git
        branch: dev-branch
    source2:
        source: https://git.uri/svc2.git
services:
    svc1:
        source: source1
        host: hostid1
    svc2:
        source: source2
        host: hostid2
```