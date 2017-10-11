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
	pip install -r docs/requirements.txt
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

.PHONY: publish
publish: docs
	cd docs/_build/ && cp -r html site && zip -r site.zip site
	@curl -i -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@docs/_build/site.zip" https://api.netlify.com/api/v1/sites/python-devtools.netlify.com/deploys
	@echo " "
