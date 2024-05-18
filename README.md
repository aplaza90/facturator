# Facturator App

## Content

The repository contains all the code of the Facturator app,an application tailored
to handle invoicing for a self-employed worker in Spain, based on current account
transaction files from the bank.  

## Code Design

TO DO

## Solution Design

TO DO

## Requirements

* docker with docker-compose

## Building the containers

```sh
make build
make up
# or
make all # builds, brings containers up, runs tests
```


## Creating a local virtualenv (optional)

```sh
python3.10 -m venv .venv && source .venv/bin/activate # or however you like to create virtualenvs

pip install -r requirements.txt
pip install -e src/
```

<!-- TODO: use a make pipinstall command -->

## Running the tests

```sh
make test
# or, to run individual test types
make unit-tests
make integration-tests
make e2e-tests
# or, if you have a local virtualenv
make up
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```


## Documentation

The code has been documented (when appropriated) using the Google style docstrings