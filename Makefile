.PHONY: install models build run clean

install:
	python3.11 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

models:
	.venv/bin/python -c "from src.utils.models import download_all; download_all()"

build: install models
	.venv/bin/pyinstaller karaoke_forge.spec

run:
	.venv/bin/python -m src.main

clean:
	rm -rf build/ dist/ *.spec.bak
