# Zoidberg

The Mastermind

## Prerequisites

- `pip install pyyaml`

## Command spec

* zoidberg install
* zoidberg update
  * Install updates to the specified config
  * `update` and `install` are synonymous
* zoidberg run file.yaml
* zoidberg start file.yaml
  * Run the app specified in the config
  * Only ever runs what's currently installed
  * Will probably silently fail if install hasn't been run yet
  * `start` and `run` are synonymous
* zoidberg stop file.yaml
  * Stop the app specified in the config

## Config file

The YAML file specifies:

* Which hosts are available
* Which services are available, and where they are from
* Which services need to run on which host

Example YAML:

```
hosts:
    hostid1:
        ip: 0.0.0.1
    hostid2:
        ip: 0.0.0.2
services:
    svc1:
        source: https://git.uri/svc1.git
        host: hostid1
    svc2:
        source: https://git.uri/svc2.git
        host: hostid2