VENV := .venv
PYTHON := $(if $(wildcard $(VENV)/bin/python3),$(VENV)/bin/python3,python3)
UVICORN := $(if $(wildcard $(VENV)/bin/uvicorn),$(VENV)/bin/uvicorn,uvicorn)

.PHONY: install generate run cli clean distclean

install:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r src/requirements.txt
	cd frontend && npm install

generate:
	./src/generate.sh

# Starts the IDE: backend + frontend together. Ctrl+C stops both.
run:
	@trap 'kill 0' EXIT INT TERM; \
	(PYTHONPATH=src/generated:src $(UVICORN) server:app --app-dir src --reload --port 8080) & \
	(cd frontend && npm run dev) & \
	wait

# Runs a single .cps file through the CLI, e.g. `make cli FILE=src/tests/valid.cps`
cli:
	PYTHONPATH=src/generated:src $(PYTHON) src/main.py $(FILE)

clean:
	find . -name '__pycache__' -type d -exec rm -rf {} +
	rm -rf workspace/output

distclean: clean
	rm -rf $(VENV)
