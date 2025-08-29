.PHONY: dev test lint build docker-run

# Ensure local package imports (e.g., 'app') resolve during all commands
export PYTHONPATH:=$(CURDIR)

VENV?=.venv
PY?=$(VENV)/bin/python
PIP?=$(VENV)/bin/pip

$(VENV)/bin/activate: requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

dev: $(VENV)/bin/activate
	$(VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test: $(VENV)/bin/activate
	$(VENV)/bin/pytest -q tests

build:
	docker build -t gumstamp-pro:latest .

docker-run:
	docker run --rm -it -p 8000:8000 --env-file .env -v $(PWD)/storage:/app/storage gumstamp-pro:latest
