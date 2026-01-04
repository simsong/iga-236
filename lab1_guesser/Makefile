# Vite-driven SPA under src/crypto_app → build/crypto_app
APP_DIR := src/crypto_app
BUILD_DIR := build/crypto_app
VITE := npx vite
VITECFG := vite.config.ts

.PHONY: install dev build preview clean check test test-watch test-coverage

install:
	@npm install
	@npm install openpgp

dev:
	@$(VITE) --config $(VITECFG)

build: clean
	@$(VITE) build --config $(VITECFG)
	@echo "Built → $(BUILD_DIR)"

preview:
	@$(VITE) preview --config $(VITECFG)

test:
	@npm run test

test-watch:
	@npm run test:watch

test-coverage:
	@npm run test:coverage

check: test
	@echo "✓ All checks passed"

clean:
	@rm -rf $(BUILD_DIR)
	@rm -rf coverage
