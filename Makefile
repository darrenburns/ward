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
	poetry run pre-commit install
.PHONY: requirements

format:
	poetry run pre-commit run --all
.PHONY: format

lint: format
.PHONY: lint

test:
	poetry run ward
.PHONY: test

coverage:
	poetry run coverage run -m ward
	poetry run coverage report --skip-empty --show-missing --sort=-cover
	poetry run coverage html
.PHONY: coverage

update:
	poetry update
.PHONY: update

prep: setup lint test
.PHONY: prep

clean:
	rm -rf build/
	rm -rf dist/
.PHONY: clean
