# iproute4mac

[![GH Actions CI](https://github.com/signal-09/iproute4mac/actions/workflows/python-package.yml/badge.svg?branch=master)](https://github.com/signal-09/iproute4mac/actions/workflows/python-package.yml)

This is a macOS network wrapper to imitate GNU/Linux [iproute2](https://wiki.linuxfoundation.org/networking/iproute2) suite, inspired by the [iproute2mac](https://github.com/brona/iproute2mac) project.

#### WARNING: early Aplha stage

Read only `ip link [show]` and `ip address [show]` objects implemented.

## Installation and usage

In order to use this tap, you need to install Homebrew.

Then, to run a default installation, run:

```bash
brew install signal-09/repo/iproute4mac
```

### Installing latest Git version (`HEAD`)

You can install the latest Git version by adding the `--HEAD` option:

```bash
brew install signal-09/repo/iproute4mac --HEAD
```
