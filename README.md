# Wagtail Nest Box

A Raspberry Pi project to show GitHub stats for [Wagtail](https://github.com/wagtail).


## Setup

Currently running on:

- [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)
- [Raspberry Pi OS Lite - Debian bookworm](https://www.raspberrypi.com/software/operating-systems/#raspberry-pi-os-64-bit)
- [Waveshare 4.2 inch e-Paper Module](https://www.waveshare.com/4.2inch-e-paper-module.htm)

Should work with any Debian bookworm versions of Raspberry Pi OS, although only the 64-bit version
has been tested.

## Installation

### Quick install

Not recommended for security reasons, but it's the fastest way.

Generate a [GitHub personal access token](https://github.com/settings/tokens?type=beta), then run
the following on the Pi over SSH:

```console
$ sudo -i
# bash <(curl -s https://raw.githubusercontent.com/tomkins/wagtail-nestbox/main/setup.sh)
```

### Manual install

Follow instructions in [setup.sh](https://github.com/tomkins/wagtail-nestbox/blob/main/setup.sh).

Not distributed on PyPI as this is a personal project.

## Licensing

Code for this project is provided under the 3-Clause BSD License.

Icons used in this project are from [Primer Octicons](https://github.com/primer/octicons),
available under the MIT License.
