# taskbot

Proof of concept of a Matrix interface for taskwarrior.

Initial codebase derived from https://github.com/anoadragon453/nio-template (Apache 2.0 License)

## Setup

### Dependencies

`matrix-nio` requires [libolm](https://gitlab.matrix.org/matrix-org/olm) for end-to-end encryption.

On debian:

```
apt install python-dev libolm-dev
```

### Installing

Preferably in a venv:

```
pip install .
```

### Configuration

`cp sample.config.yaml config.yaml`

Edit the `matrix` section.

## Running

`taskbot [config file path]`

## Usage

Once the bot is running, you can send it direct messages.

Commands implemented:

 - list: returns pending tasks
 - add <text>
 - done <id>
