.PHONY: clean clean-test clean-pyc clean-build docs help
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint/flake8: ## check style with flake8
	flake8 jupyterbook_to_zendesk tests

lint/black: ## check style with black
	black --check jupyterbook_to_zendesk tests

lint: lint/flake8 lint/black ## check style

test-all: ## run tests on every Python version with tox
	tox

coverage: ## check code coverage quickly with the default Python
	coverage run --source jupyterbook_to_zendesk -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/jupyterbook_to_zendesk.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ jupyterbook_to_zendesk
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: dist ## package and upload a release
	twine upload dist/*

dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	python setup.py build; python setup.py install

install/dev: clean
	pip install -r requirements.txt -r requirements_dev.txt
	python setup.py build; python setup.py install

test: ## run tests quickly with the default Python
	$(MAKE) install/dev
	pytest -s

test/watch: ## run tests quickly with the default Python
	$(MAKE) install/dev
	pwt .

docker/build:
	$(MAKE) clean
	docker build -t dabbleofdevops/jb-to-zendesk .

docker/build/clean:
	$(MAKE) clean
	docker build --no-cache -t dabbleofdevops/jb-to-zendesk .

pre-commit/init:
	pre-commit install-hooks
	pre-commit clean
	pre-commit install
	pre-commit install-hooks
	precommit hooks installation


format:
	pre-commit run --all-files
	black .

docker/format:
	docker run --rm -it \
		-v $(shell pwd):/usr/src/app \
		-w /usr/src/app \
		dabbleofdevops/jb-to-zendesk bash -c "make format"

docker/test/run-cli:
	$(MAKE) docker/build/clean
	docker run --rm -it dabbleofdevops/jb-to-zendesk bash -c "jupyterbook-to-zendesk"

docker/test/pytest/watch:
	docker run --rm -it \
		-v $(shell pwd):/usr/src/app \
		-w /usr/src/app \
		dabbleofdevops/jb-to-zendesk bash -c "make test/watch"

docker/test/pytest:
	docker run --rm -it \
		-v $(shell pwd):/usr/src/app \
		-w /usr/src/app \
		dabbleofdevops/jb-to-zendesk bash -c "make test"

docker/shell:
	$(MAKE) build-docker
	docker run --rm -it \
		-v $(shell pwd):/usr/src/app \
		dabbleofdevops/jb-to-zendesk bash

ci/docker/install/dev:
	docker run --rm -it \
		-v $(shell pwd):/usr/src/app/ \
		-w /usr/src/app \
		python:3.8 bash -c "make clean; make install/dev"

# Processes to help with CI/CD
# Install to a clean environment
ci/docker/install:
	docker run --rm -it \
		-v $(shell pwd):/usr/src/app/ \
		-w /usr/src/app \
		python:3.8 bash -c "make clean; make install"

example:
	cd example/mynewbook
	jupyterbook-to-zendesk -s . -d . build-jb
	jupyterbook-to-zendesk -s . -d . sync-jb-to-zendesk
	livereload _build/html/ -p 8000

ci/docker/example:
	$(MAKE) ci/docker/install/dev
	docker run --rm -it \
		-v $(shell pwd):/usr/src/app/ \
		-w /usr/src/app \
		-p 8000:8000 \
		python:3.8 bash -c "make dev/install; make example"
