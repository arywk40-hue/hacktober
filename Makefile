.PHONY: setup dev test lint eval
setup:
	uv sync --frozen --extra dev

dev:
	./run.sh

test:
	uv run --offline python -m pytest -q

lint:
	uv run --offline ruff check study tests scripts

eval:
	uv run --offline python -m scripts.evaluate
