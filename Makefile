.PHONY: init install run test lint
PYTHON := /opt/homebrew/opt/python@3.11/bin/python3.11

init:
	$(PYTHON) -m venv .venv
	. .venv/bin/activate && pip install -U pip

install:
	. .venv/bin/activate && pip install -e .

run:
	. .venv/bin/activate && azimg inventory --out out/vm_inventory.csv

test:
	. .venv/bin/activate && pytest -q