.PHONY: clean clean-build clean-pyc clean-test coverage lint test format install typecheck run

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
	rm -fr .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

lint: ## check style with ruff
	uv run ruff check computerquest tests

test: ## run tests with pytest
	uv run pytest

coverage: ## check code coverage with pytest-cov
	uv run pytest --cov=computerquest --cov-report=html
	@echo "Open htmlcov/index.html to view the coverage report"

format: ## format code with ruff
	uv run ruff format computerquest tests

typecheck: ## run static type checker
	uv run mypy computerquest tests

install: ## install the package and dev dependencies via uv
	uv sync --dev

run: ## run the game
	uv run python main.py