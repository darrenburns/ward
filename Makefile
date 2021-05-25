none: clean

help:
	@echo "make lint	lint (flake8)"
	@echo "make format	run autoformatter"
	@echo "make test	test Ward"
	@echo
	@echo "make prep	lint and test Ward in preparation for a pull request"
	@echo
	@echo "make venv	create virtual environment"
	@echo "make clean	clean up build artifacts and automatically created venv"
.PHONY: help

requirements:
	poetry update
	poetry install
.PHONY: requirements

lint:
	poetry run flake8 ward --count --select=E9,F63,F7,F82 --show-source --statistics
	poetry run flake8 ward --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics
.PHONY: lint

format:
	poetry run black ward
.PHONY: format

test:
	poetry run ward
.PHONY: test

coverage:
	poetry run coverage run -m ward
	poetry run coverage html -i
.PHONY: coverage

update:
	poetry update
.PHONY: update

prep: requirements format test
.PHONY: prep

clean:
	rm -rf build/
	rm -rf dist/
.PHONY: clean
