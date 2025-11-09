.PHONY: lock lock-dev live_preview build prepare clean build

# Dependency management commands
lock: requirements.in
	uv pip compile requirements.in --universal --output-file requirements.txt

lock-dev: requirements-dev.in requirements.in
	uv pip compile requirements-dev.in --universal --output-file requirements-dev.txt

lock-all: lock lock-dev

preview:
	bash src/dashboard/run.sh
