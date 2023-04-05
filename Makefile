.DEFAULT_GOAL := all
sources = devtools tests docs/plugins.py

.PHONY: install
install:
	python -m pip install -U pip
	pip install -U -r requirements.txt
	pip install -e .

.PHONY: format
format:
	black $(sources)
	ruff $(sources) --fix --exit-zero

.PHONY: lint
lint:
	black $(sources) --check --diff
	ruff $(sources)
	mypy devtools

.PHONY: test
test:
	coverage run -m pytest

.PHONY: testcov
testcov:
	coverage run -m pytest
	@echo "building coverage html"
	@coverage html

.PHONY: all
all: lint testcov

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
	flake8 --max-line-length=80 docs/examples/
	mkdocs build

.PHONY: docs-serve
docs-serve:
	mkdocs serve

.PHONY: publish-docs
publish-docs: docs
	zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@site.zip" https://api.netlify.com/api/v1/sites/python-devtools.netlify.com/deploys
