# Zoidberg

The Mastermind

## Prerequisites

- `pip install pyyaml`

## Command spec

* zoidberg install
* zoidberg update
  * Install updates to the specified config
  * Note update and install are synonymous
* zoidberg run file.yaml
  * Run the app specified in the config
  * Only ever runs what's currently installed
  * Will fail if install hasn't been run yet

## Config file

The YAML file specifies:

* Which nodes are available
* Which services are available, and where they are from
* Which services need to run on which node