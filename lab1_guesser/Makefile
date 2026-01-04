# Vite-driven SPA under src/crypto_app → build/crypto_app
APP_DIR := src/crypto_app
BUILD_DIR := build/crypto_app
VITE := npx vite
VITECFG := vite.config.ts

.PHONY: install dev serve build preview clean check test test-watch test-coverage lint lint-js lint-html lint-py

install:
	@npm install
	@npm install openpgp

dev:
	@if [ ! -d "node_modules/vite" ]; then \
		echo "Dependencies not installed. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@npm run dev

serve: dev

build: clean
	@$(VITE) build --config $(VITECFG)
	@echo "Built → $(BUILD_DIR)"

preview:
	@$(VITE) preview --config $(VITECFG)

test:
	@if [ ! -d "node_modules/vitest" ]; then \
		echo "Dependencies not installed. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@npm run test

test-watch:
	@if [ ! -d "node_modules/vitest" ]; then \
		echo "Dependencies not installed. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@npm run test:watch

test-coverage:
	@if [ ! -d "node_modules/vitest" ]; then \
		echo "Dependencies not installed. Running 'make install' first..."; \
		$(MAKE) install; \
	fi
	@npm run test:coverage

check: test lint
	@echo "✓ All checks passed"

lint: lint-js lint-html lint-py
	@echo "✓ All linting passed"

lint-js:
	@echo "Running ESLint on .js and .ts files..."
	@npx eslint src/

lint-html:
	@echo "Running djlint on .html files..."
	@if command -v djlint >/dev/null 2>&1; then \
		find src -name "*.html" -exec djlint {} \; || true; \
	else \
		echo "djlint not found, skipping HTML linting (install with: pip install djlint)"; \
	fi

lint-py:
	@echo "Running pylint and pyright on .py files..."
	@if [ -n "$$(find . -name '*.py' -not -path './node_modules/*' -not -path './.git/*' 2>/dev/null)" ]; then \
		if command -v pylint >/dev/null 2>&1; then \
			find . -name "*.py" -not -path "./node_modules/*" -not -path "./.git/*" -exec pylint {} \; || true; \
		else \
			echo "pylint not found, skipping (install with: pip install pylint)"; \
		fi; \
		if command -v pyright >/dev/null 2>&1; then \
			pyright . || true; \
		else \
			echo "pyright not found, skipping (install with: npm install -g pyright or pip install pyright)"; \
		fi; \
	else \
		echo "No .py files found, skipping Python linting"; \
	fi

clean:
	@rm -rf $(BUILD_DIR)
	@rm -rf coverage
