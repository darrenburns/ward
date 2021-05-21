none: clean

help:
	@echo "make test	test Ward"
	@echo
	@echo "make prep	lint and test Ward in preparation for a pull request"
	@echo
	@echo "make setup	create virtual environment and install pre-commit"
	@echo "make update	update dependencies"
	@echo "make clean	clean up build artifacts"
.PHONY: help

setup:
	poetry install
	pre-commit install
.PHONY: requirements

test:
	poetry run ward
.PHONY: test

update:
	poetry update
.PHONY: update

prep: setup update test
.PHONY: prep

clean:
	rm -rf build/
	rm -rf dist/
.PHONY: clean
