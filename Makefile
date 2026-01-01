.DEFAULT_GOAL := help

init:
	uv sync

run:
	uv run src/main.py

typecheck:
	uv run mypy --config-file=pyproject.toml ./src/

commit:
	uv run cz commit

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: help run

