.PHONY: build install test lint format clean

build:
	pipx run build

install:
	pip install -e ".[test]"

test:
	pytest

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

clean:
	rm -rf build dist wheelhouse *.egg-info kcp/extension.c kcp/*.so kcp/*.pyd
