none: clean

help:
	@echo "make test	test Ward"
	@echo
	@echo "make format	run formatters and linters"
	@echo "make lint	alias for format"
	@echo "make prep	format, lint, and test Ward in preparation for a pull request"
	@echo
	@echo "make setup	create virtual environment and install pre-commit"
	@echo "make update	update dependencies"
	@echo "make clean	clean up build artifacts"
.PHONY: help

setup:
	poetry install
	pre-commit install
.PHONY: requirements

format:
	pre-commit run --all
.PHONY: format

lint: format
.PHONY: lint

test:
	poetry run ward
.PHONY: test

update:
	poetry update
.PHONY: update

prep: setup update lint test
.PHONY: prep

clean:
	rm -rf build/
	rm -rf dist/
.PHONY: clean
