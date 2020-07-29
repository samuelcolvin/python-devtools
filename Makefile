.DEFAULT_GOAL := all
isort = isort devtools tests
black = black -S -l 120 --target-version py37 devtools

.PHONY: install
install:
	python -m pip install -U setuptools pip
	pip install -U -r requirements.txt
	pip install -e .

.PHONY: format
format:
	$(isort)
	$(black)

.PHONY: lint
lint:
	flake8 devtools/ tests/
	$(isort) --check-only --df
	$(black) --check --diff

.PHONY: check-dist
check-dist:
	python setup.py check -ms
	python setup.py sdist
	twine check dist/*

.PHONY: test
test:
	pytest --cov=devtools --cov-fail-under 0

.PHONY: testcov
testcov:
	pytest --cov=devtools --cov-fail-under 0
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
	python docs/build/main.py
	mkdocs build

.PHONY: docs-serve
docs-serve:
	python docs/build/main.py
	mkdocs serve

.PHONY: publish-docs
publish-docs: docs
	zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@site.zip" https://api.netlify.com/api/v1/sites/python-devtools.netlify.com/deploys
