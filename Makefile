.DEFAULT_GOAL := all

.PHONY: install-dev
install-dev:
	pip install -U setuptools pip
	pip install -r dev-requirements.txt
	pip install -U -e .[pygments]

.PHONY: install-test
install-test:
	pip install -U setuptools pip
	pip install -r tests/requirements.txt
	pip install -U .

.PHONY: isort
isort:
	isort -rc -w 120 devtools
	isort -rc -w 120 tests

.PHONY: lint
lint:
	python setup.py check -rms
	flake8 devtools/ tests/
	pytest devtools -p no:sugar -q

.PHONY: test
test:
	pytest --cov=devtools

.PHONY: testcov
testcov:
	pytest --cov=devtools
	@echo "building coverage html"
	@coverage html

.PHONY: all
all: testcov lint

.PHONY: clean
clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf htmlcov
	rm -rf *.egg-info
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	python setup.py clean
	make -C docs clean

.PHONY: docs
docs:
	make -C docs html

.PHONY: docs-lint
docs-lint:
	make -C docs lint
