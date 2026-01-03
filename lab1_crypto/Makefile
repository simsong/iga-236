# Vite-driven SPA under src/crypto_app → build/crypto_app
APP_DIR := src/crypto_app
BUILD_DIR := build/crypto_app
VITE := npx vite
VITECFG := vite.config.ts

.PHONY: install dev build preview clean

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

clean:
	@rm -rf $(BUILD_DIR)
