.DEFAULT_GOAL := all

.PHONY: .uv
.uv:
	@uv --version || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'

.PHONY: install
install: .uv ## Install python dependencies and prek hooks
	uv sync
	uvx prek install --install-hooks

.PHONY: format
format: ## Format Python code
	uv run ruff format
	uv run ruff check --fix --fix-only

.PHONY: lint
lint: ## Lint Python code with ruff and basedpyright (strict)
	uv run ruff format --check
	uv run ruff check
	uv run basedpyright

.PHONY: test
test: ## Run tests
	uv run pytest

.PHONY: testcov
testcov: ## Run tests with coverage
	uv run coverage run -m pytest
	@echo "building coverage html"
	@uv run coverage html

.PHONY: all
all: lint testcov ## Run all checks and tests

.PHONY: clean
clean: ## Clean up build artifacts
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
docs: ## Build docs
	uv run ruff check --line-length=80 docs/examples/
	uv run mkdocs build

.PHONY: docs-serve
docs-serve: ## Serve docs locally
	uv run mkdocs serve

.PHONY: publish-docs
publish-docs: docs ## Publish docs to Netlify
	zip -r site.zip site
	@curl -H "Content-Type: application/zip" -H "Authorization: Bearer ${NETLIFY}" \
	      --data-binary "@site.zip" https://api.netlify.com/api/v1/sites/python-devtools.netlify.com/deploys

# (must stay last!)
.PHONY: help
help: ## Show this help (usage: make help)
	@echo "Usage: make [recipe]"
	@echo "Recipes:"
	@awk '/^[a-zA-Z0-9_-]+:.*?##/ { \
	    helpMessage = match($$0, /## (.*)/); \
	        if (helpMessage) { \
	            recipe = $$1; \
	            sub(/:/, "", recipe); \
	            printf "  \033[36mmake %-20s\033[0m %s\n", recipe, substr($$0, RSTART + 3, RLENGTH); \
	    } \
	}' $(MAKEFILE_LIST)
