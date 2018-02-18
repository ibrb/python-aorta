# Aorta Message Publishing Library

![IBR Logo](https://media.ibrb.org/ibr/images/logos/landscape1200.png)

The `aorta` library provides various implementations around the
`proton` AMQP messaging framework.

The `aorta` codebase is subject to a feature freeze until test coverage
is at 100%.

## Table of Contents

- [Security](#security)
- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [TODO](#todo)
- [License](#license)


## Security

- Authentication is not implemented. All producers/consumers that can connect
  to the Aorta system are assumed to be allowed to do so, and that access control
  is managed at the network (firewall) level.
- We suggest mounting `/var/spool/aorta` on a separate (encrypted)
  filesystem.

## Background

## Install

## Usage

## TODO

- Authentication.


## License

© 2018 International Blockchain Reserve B.V.
