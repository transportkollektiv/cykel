.PHONY: test stylecheck style

test:
	pytest

stylecheck:
	isort -c -rc -df .
	flake8 .
	black --check .
	docformatter --check -r .

style:
	isort -rc .
	docformatter -i -r . --exclude venv
	black .
	flake8 .
