test:
	python -m pytest tests/ -q

test-verbose:
	python -m pytest tests/ -v

test-cov:
	python -m pytest tests/ --cov=app --cov-report=term-missing -q

test-fast:
	python -m pytest tests/ -x -q

clean:
	rm -rf .pytest_cache htmlcov .coverage
