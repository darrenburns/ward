VENV=make-venv
VENVBIN=$(VENV)/bin

none: clean dist tidy

help:
	@echo "make lint	lint (flake8)"
	@echo "make format	run autoformatter"
	@echo "make test	test Ward"
	@echo
	@echo "make prep	lint and test Ward in preparation for a pull request"
	@echo "make dist	build Ward in preparation for PyPI upload"
	@echo
	@echo "make venv	create virtual environment"
	@echo "make tidy	remove cache, pyc files, and eggs"
	@echo "make clean	clean up build artifacts and automatically created venv"
.PHONY: help

venv: make-venv
.PHONY: venv

make-venv:
	python3 -m venv make-venv
	$(VENVBIN)/pip install .[dev]

lint: make-venv
	$(VENVBIN)/flake8 ward --count --select=E9,F63,F7,F82 --show-source --statistics
	$(VENVBIN)/flake8 ward --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics
.PHONY: lint

format: make-venv
	$(VENVBIN)/black ward
.PHONY: format

test: make-venv
	$(VENVBIN)/ward --path tests
.PHONY: test

prep: lint format test tidy
.PHONY: prep

dist: lint format test
	$(VENVBIN)/flit build

build: dist
.PHONE: dist

tidy: make-venv
	$(VENVBIN)/pycleanup --cache --pyc --egg

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf $(VENV)
.PHONY: clean
