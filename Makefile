.DEFAULT_GOAL := help

init:
	uv sync
	uv run pre-commit install --install-hooks
	uv run pre-commit autoupdate

run:
	uv run src/main.py

test:
	uv run pytest -v

lint:
	uv run ruff check --config=pyproject.toml --fix ./src/

format:
	uv run ruff format --config=pyproject.toml ./src/

typecheck:
	uv run mypy --config-file=pyproject.toml ./src/

commit:
	uv run cz commit

docs-serve:
	uv run mkdocs serve

dep-update:
	uv lock
	uv pip compile pyproject.toml > requirements.txt
	uv pip compile --group dev > requirements-dev.txt

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: help run lint format

