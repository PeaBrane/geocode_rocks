.PHONY: build run

build:
	pip install -r requirements.txt
	maturin build --release

run:
	python script.py $(filename)
