.DEFAULT_GOAL := all
sources = devtools tests docs/plugins.py

.PHONY: install
install:
	python -m pip install -U pip pre-commit
	pip install -U -r requirements/all.txt
	pip install -e .
	pre-commit install

.PHONY: refresh-lockfiles
refresh-lockfiles:
	find requirements/ -name '*.txt' ! -name 'all.txt' -type f -delete
	make update-lockfiles

.PHONY: update-lockfiles
update-lockfiles:
	@echo "Updating requirements/*.txt files using pip-compile"
	pip-compile -q --resolver backtracking -o requirements/linting.txt requirements/linting.in
	pip-compile -q --resolver backtracking -o requirements/testing.txt requirements/testing.in
	pip-compile -q --resolver backtracking -o requirements/docs.txt requirements/docs.in
	pip-compile -q --resolver backtracking -o requirements/pyproject.txt pyproject.toml
	pip install --dry-run -r requirements/all.txt

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
	ruff --line-length=80 docs/examples/
	mkdocs build

.PHONY: docs-serve
docs-serve:
	mkdocs serve

.PHONY: publish-docs
publish-docs: docs
	zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@site.zip" https://api.netlify.com/api/v1/sites/python-devtools.netlify.com/deploys
