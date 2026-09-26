# ---------------------------------------------------------------------------
# StormRoute — single entry point for every routine task.
#
# Targets appear here in the same order as the README quick start. A judge or
# a new teammate should never need to learn a second setup procedure.
#
# Targets that depend on work from a later milestone fail loudly rather than
# succeeding silently, so an unfinished stage can never be mistaken for a
# working one.
# ---------------------------------------------------------------------------

.DEFAULT_GOAL := help
SHELL := /bin/bash

PYTHON ?= python3
UV     ?= uv
FRONTEND_DIR := frontend
EDA_NOTEBOOK := notebooks/01_storm_events_eda.ipynb

# Marks a target whose implementation lands in a later milestone.
define not_yet
	@echo ""
	@echo "  $(1) is not yet implemented — see $(2) in docs/build_guide.md."
	@echo "  The scaffold intentionally has no behavior here."
	@echo ""
	@exit 1
endef

.PHONY: help setup download eda data train evaluate api web test lint verify demo-cache clean

help: ## Show every available target
	@echo "StormRoute — available commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[1m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""

setup: ## Install Python, notebook, and frontend dependencies
	$(UV) sync --extra dev --extra notebook
	@if [ -f $(FRONTEND_DIR)/package-lock.json ]; then \
		npm --prefix $(FRONTEND_DIR) ci; \
	else \
		echo "No frontend/package-lock.json yet — resolving and creating it."; \
		npm --prefix $(FRONTEND_DIR) install; \
		echo "Commit frontend/package-lock.json so CI and teammates match."; \
	fi
	$(UV) run pre-commit install
	@echo "Setup complete. Copy .env.example to .env if you have not already."

download: ## Download/version required source data (Milestone 1)
	$(UV) run $(PYTHON) scripts/download_noaa.py
	@echo ""
	@echo "  NOTE: county boundaries are not downloaded yet: scripts/download_boundaries.py"
	@echo "  is pending (issue #3, CS major). The EDA choropleth needs it."

eda: ## Execute the EDA notebook top to bottom in a clean kernel (Milestone 2)
	$(UV) run jupyter nbconvert --to notebook --execute \
		--ExecutePreprocessor.timeout=1800 --output-dir outputs/executed $(EDA_NOTEBOOK)
	@echo "Executed copy: outputs/executed/ (ignored). The tracked notebook stays output-free."

data: ## Build the production county-window table (Milestone 3)
	$(call not_yet,make data,Milestone 3)

train: ## Train baselines and the candidate final model (Milestone 4)
	$(call not_yet,make train,Milestone 4)

evaluate: ## Evaluate and export final metrics and figures (Milestone 4)
	$(call not_yet,make evaluate,Milestone 4)

api: ## Start FastAPI on port 8000 (Milestone 6)
	$(call not_yet,make api,Milestone 6)

web: ## Start Vite on port 5173 (Milestone 7)
	npm --prefix $(FRONTEND_DIR) run dev

test: ## Run Python and frontend tests
	$(UV) run pytest --cov --cov-report=term-missing
	@if [ -f $(FRONTEND_DIR)/package-lock.json ]; then \
		npm --prefix $(FRONTEND_DIR) run test -- --run; \
	else \
		echo "Skipping frontend tests: frontend dependencies are not installed."; \
	fi

lint: ## Run formatters, linters, and type checks
	$(UV) run ruff format --check .
	$(UV) run ruff check .
	$(UV) run mypy
	@if [ -f $(FRONTEND_DIR)/package-lock.json ]; then \
		npm --prefix $(FRONTEND_DIR) run lint; \
		npm --prefix $(FRONTEND_DIR) run typecheck; \
	else \
		echo "Skipping frontend lint: frontend dependencies are not installed."; \
	fi

verify: ## Run the complete repository verification suite
	$(MAKE) lint
	$(MAKE) test
	$(UV) run $(PYTHON) scripts/verify_repository.py

demo-cache: ## Rebuild the offline presentation scenario (Milestone 5)
	$(call not_yet,make demo-cache,Milestone 5)

clean: ## Remove caches and build output; never touches data/ or artifacts/
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/.vite
