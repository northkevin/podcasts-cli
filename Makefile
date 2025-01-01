.PHONY: install clean test lint format

install:
	python -m pip install -e .

dev-install:
	python -m pip install -e ".[dev]"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	python -m pytest podcasts/tests/ -v

test-debug:
	python -m pytest podcasts/tests/ -v --pdb

lint:
	flake8 podcasts
	black podcasts --check
	isort podcasts --check-only

format:
	black podcasts
	isort podcasts