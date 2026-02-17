.DEFAULT_GOAL := help

.PHONY: test coverage help

test: ## Run all plugin tests
	pytest

coverage: ## Run tests with coverage report
	pytest --cov=plugins --cov-report=term-missing

test-%: ## Run tests for a plugin (e.g., make test-finite-skill-machine)
	@test -d tests/plugins/$* || { echo "Error: no test directory 'tests/plugins/$*/'"; exit 1; }
	pytest tests/plugins/$*/

help: ## Show available targets
	@grep -E '^[a-zA-Z_%-]+:.*##' $(MAKEFILE_LIST) | \
		awk -F ':.*## ' '{printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Plugin test targets:"
	@for d in tests/plugins/*/; do \
		plugin=$$(basename "$$d"); \
		case "$$plugin" in example-*) continue ;; esac; \
		printf "    \033[36mmake test-%s\033[0m\n" "$$plugin"; \
	done
