

.PHONY: install
install: ## Install the poetry environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using pyenv and poetry"
	@cd arcade && poetry install --all-extras
	@cd arcade && poetry run pre-commit install
	@cd arcade && poetry shell

.PHONY: check
check: ## Run code quality tools.
	@echo "🚀 Checking Poetry lock file consistency with 'pyproject.toml': Running poetry check --lock"
	@cd arcade && poetry check --lock
	@echo "🚀 Linting code: Running pre-commit"
	@cd arcade && poetry run pre-commit run -a
	@echo "🚀 Static type checking: Running mypy"
	@cd arcade && poetry run mypy $(git ls-files '*.py')

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@cd arcade && poetry run pytest -v --cov --cov-config=pyproject.toml --cov-report=xml

.PHONY: build
build: clean-build ## Build wheel file using poetry
	@echo "🚀 Creating wheel file"
	@cd arcade && poetry build

.PHONY: clean-build
clean-build: ## clean build artifacts
	@cd arcade && rm -rf dist

.PHONY: publish
publish: ## publish a release to pypi.
	@echo "🚀 Publishing: Dry run."
	@cd arcade && poetry config pypi-token.pypi $(PYPI_TOKEN)
	@cd arcade && poetry publish --dry-run
	@echo "🚀 Publishing."
	@cd arcade && poetry publish

.PHONY: build-and-publish
build-and-publish: build publish ## Build and publish.

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@cd arcade && poetry run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@cd arcade && poetry run mkdocs serve -a localhost:8777

.PHONY: docker
docker: ## Build and run the Docker container
	@cd docker && make docker-build
	@cd docker && make docker-run

.PHONY: full-dist
full-dist: clean-dist ## Build all projects and copy wheels to arcade/dist
	@echo "🚀 Building all projects and copying wheels to arcade/dist"

	# Build the main arcade project
	@echo "Building arcade project..."
	@cd arcade && poetry build

	# Create the arcade/dist directory if it doesn't exist
	@mkdir -p arcade/dist

	# Build and copy wheels for each toolkit
	@for toolkit_dir in toolkits/*; do \
		if [ -d "$$toolkit_dir" ]; then \
			toolkit_name=$$(basename "$$toolkit_dir"); \
			echo "Building $$toolkit_name project..."; \
			cd "$$toolkit_dir" && poetry build; \
			cp dist/*.whl ../../arcade/dist; \
			cd -; \
		fi; \
	done

	@echo "✅ All projects built and wheels copied to arcade/dist"

.PHONY: clean-dist
clean-dist: ## Clean the arcade/dist directory
	@echo "🗑️ Cleaning arcade/dist directory"
	@rm -rf arcade/dist

.PHONY: help
help:
	@echo "🛠️ Arcade AI Dev Commands:\n"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
