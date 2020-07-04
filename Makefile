.PHONY: test stylecheck style

test:
	pytest

stylecheck:
	isort -c --df .
	flake8 .
	black --check .
	docformatter --check -r . --exclude venv

style:
	isort .
	docformatter -i -r . --exclude venv
	black .
	flake8 .
