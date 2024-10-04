.PHONY: help
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  clean     Remove build artifacts"
	@echo "  format    Format code with ruff"
	@echo "  lint      Check code with ruff"
	@echo "  install   Install package in editable mode"

.PHONY: clean
clean:
	@rm -rf build dist *.egg-info .ruff_cache
	@find . -name "*.pyc" -print0 | xargs -0 rm -f
	@find . -name "*.pyo" -print0 | xargs -0 rm -f
	@find . -name "__pycache__" -print0 | xargs -0 rm -rf

.PHONY: format
format:
	echo -n "Formatting code with ruff: "
	python3 -m ruff format .

.PHONY: lint
lint:
	python3 -m ruff check .

.PHONY: install
install: lint format
	@python3 -m pip install --editable .

.PHONY: uninstall
uninstall:
	@python3 -m pip uninstall -y torrent_tools
