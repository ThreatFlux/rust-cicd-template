# ThreatFlux Rust Project Makefile
# Standardized build, test, and development commands

CARGO ?= cargo
RUST_MSRV ?= 1.97.1
RUST_TOOLCHAIN ?= 1.99.0

DOCKER_IMAGE ?= $(shell basename $(CURDIR))
DOCKER_TAG ?= latest
GITHUB_OWNER ?= $(shell git config --get remote.origin.url | sed -E 's#(git@github.com:|https://github.com/)##; s#/.+##' | tr '[:upper:]' '[:lower:]')
DOCKER_REGISTRY ?= ghcr.io/$(if $(GITHUB_OWNER),$(GITHUB_OWNER),local)
BINARY_NAME ?= rust-cicd-template
BINARY_PACKAGE ?=
SBOM_MANIFEST_PATH ?= Cargo.toml
PUBLISH_PACKAGES ?=

CLIPPY_FLAGS := -D warnings \
	-D clippy::all \
	-D clippy::pedantic \
	-D clippy::nursery \
	-D clippy::cargo \
	-A clippy::multiple_crate_versions \
	-A clippy::module_name_repetitions \
	-A clippy::missing_errors_doc \
	-A clippy::missing_panics_doc \
	-A clippy::must_use_candidate

RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m

.DEFAULT_GOAL := help

.PHONY: help
help: ## Display this help message
	@echo "$(CYAN)ThreatFlux Rust Project - Available Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  $(GREEN)make dev-setup$(NC)       Install all development tools"
	@echo "  $(GREEN)make template-check$(NC)  Validate bootstrap placeholders"
	@echo "  $(GREEN)make ci$(NC)              Run all CI checks locally"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'

.PHONY: dev-setup
dev-setup: ## Install development tools
	@echo "$(CYAN)Installing development tools...$(NC)"
	@rustup component add rustfmt clippy llvm-tools-preview
	@cargo install cargo-llvm-cov --version 0.9.1 --locked
	@cargo install cargo-audit --version 0.22.2 --locked
	@cargo install cargo-deny --version 0.20.2 --locked
	@cargo install cargo-cyclonedx --version 0.5.9 --locked
	@cargo install cargo-hack --version 0.6.45 --locked
	@python3 -m pip install --user pre-commit
	@echo "$(GREEN)Development tools installed!$(NC)"

.PHONY: install-hooks hooks-install
install-hooks: ## Install hooks for this worktree without changing sibling hooks
	@echo "$(CYAN)Installing git hooks...$(NC)"
	@sh scripts/install_hooks.sh
	@echo "$(GREEN)Git hooks installed!$(NC)"

hooks-install: install-hooks ## Alias: install worktree-aware git hooks

.PHONY: build
build: ## Build the project (debug)
	@echo "$(CYAN)Building project...$(NC)"
	@$(CARGO) build --locked --all-features
	@echo "$(GREEN)Build completed!$(NC)"

.PHONY: build-release
build-release: ## Build the project (release)
	@echo "$(CYAN)Building release...$(NC)"
	@if [ -n "$(BINARY_PACKAGE)" ]; then \
		$(CARGO) build --locked --release -p $(BINARY_PACKAGE) --bin $(BINARY_NAME) --all-features; \
	else \
		$(CARGO) build --locked --release --bin $(BINARY_NAME) --all-features || $(CARGO) build --locked --release --all-features; \
	fi
	@echo "$(GREEN)Release build completed!$(NC)"

.PHONY: check
check: ## Check compilation without building
	@echo "$(CYAN)Checking compilation...$(NC)"
	@$(CARGO) check --locked --all-features --all-targets

.PHONY: fmt
fmt: ## Format code
	@echo "$(CYAN)Formatting code...$(NC)"
	@$(CARGO) fmt --all
	@echo "$(GREEN)Formatting completed!$(NC)"

.PHONY: fmt-check
fmt-check: ## Check code formatting
	@echo "$(CYAN)Checking code format...$(NC)"
	@$(CARGO) fmt --all -- --check
	@echo "$(GREEN)Format check passed!$(NC)"

.PHONY: lint
lint: ## Run clippy linter
	@echo "$(CYAN)Running clippy...$(NC)"
	@$(CARGO) clippy --locked --all-features --all-targets -- -D warnings
	@echo "$(GREEN)Linting passed!$(NC)"

.PHONY: lint-strict
lint-strict: ## Run clippy with strict flags
	@echo "$(CYAN)Running strict clippy...$(NC)"
	@$(CARGO) clippy --locked --all-features --all-targets -- $(CLIPPY_FLAGS)
	@echo "$(GREEN)Strict linting passed!$(NC)"

.PHONY: lint-fix
lint-fix: ## Run clippy and apply fixes
	@echo "$(CYAN)Applying clippy fixes...$(NC)"
	@$(CARGO) clippy --locked --all-features --all-targets --fix --allow-dirty --allow-staged -- -D warnings
	@echo "$(GREEN)Fixes applied!$(NC)"

.PHONY: test
test: ## Run all tests
	@echo "$(CYAN)Running tests...$(NC)"
	@$(CARGO) test --locked --all-features
	@echo "$(GREEN)Tests passed!$(NC)"

.PHONY: test-verbose
test-verbose: ## Run tests with output
	@echo "$(CYAN)Running tests (verbose)...$(NC)"
	@$(CARGO) test --locked --all-features -- --nocapture

.PHONY: test-doc
test-doc: ## Run documentation tests
	@echo "$(CYAN)Running doc tests...$(NC)"
	@$(CARGO) test --locked --doc --all-features
	@echo "$(GREEN)Doc tests passed!$(NC)"

.PHONY: test-features
test-features: ## Test feature combinations
	@echo "$(CYAN)Testing feature combinations...$(NC)"
	@echo "$(BLUE)  No default features...$(NC)"
	@$(CARGO) check --locked --workspace --no-default-features
	@echo "$(BLUE)  All features...$(NC)"
	@$(CARGO) check --locked --workspace --all-features
	@echo "$(BLUE)  Default features only...$(NC)"
	@$(CARGO) check --locked --workspace
	@echo "$(GREEN)Feature checks passed!$(NC)"

.PHONY: test-features-full
test-features-full: ## Test full feature powerset
	@echo "$(CYAN)Testing full feature powerset...$(NC)"
	@cargo hack check --locked --workspace --feature-powerset --no-dev-deps
	@echo "$(GREEN)Feature powerset passed!$(NC)"

.PHONY: coverage
coverage: ## Generate code coverage report
	@echo "$(CYAN)Generating coverage...$(NC)"
	@cargo llvm-cov --locked --all-features --workspace --lcov --output-path lcov.info
	@echo "$(GREEN)Coverage report: lcov.info$(NC)"

.PHONY: coverage-html
coverage-html: ## Generate HTML coverage report
	@echo "$(CYAN)Generating HTML coverage...$(NC)"
	@cargo llvm-cov --locked --all-features --workspace --html
	@echo "$(GREEN)Report: target/llvm-cov/html/index.html$(NC)"

.PHONY: coverage-summary
coverage-summary: ## Show coverage summary
	@echo "$(CYAN)Coverage summary:$(NC)"
	@cargo llvm-cov --locked --all-features --workspace --summary-only

.PHONY: audit
audit: ## Run security audit
	@echo "$(CYAN)Running security audit...$(NC)"
	@cargo audit
	@echo "$(GREEN)Security audit passed!$(NC)"

.PHONY: deny
deny: ## Check licenses and advisories
	@echo "$(CYAN)Running cargo-deny...$(NC)"
	@cargo deny check
	@echo "$(GREEN)Deny checks passed!$(NC)"

.PHONY: sbom
sbom: ## Generate a CycloneDX SBOM
	@echo "$(CYAN)Generating SBOM...$(NC)"
	@mkdir -p sbom
	@rm -f sbom/*.json
	@cargo cyclonedx --manifest-path $(SBOM_MANIFEST_PATH) --all-features --format json --spec-version 1.5 --override-filename $(BINARY_NAME)-sbom
	@find . -maxdepth 4 -path './sbom' -prune -o -name '$(BINARY_NAME)-sbom.json' -exec mv {} sbom/ \;
	@test -s 'sbom/$(BINARY_NAME)-sbom.json'
	@echo "$(GREEN)SBOM written to sbom/$(BINARY_NAME)-sbom.json$(NC)"

.PHONY: security
security: audit deny ## Run all security checks
	@echo "$(GREEN)All security checks passed!$(NC)"

.PHONY: docs
docs: ## Build documentation
	@echo "$(CYAN)Building documentation...$(NC)"
	@RUSTDOCFLAGS="-D warnings" $(CARGO) doc --locked --all-features --no-deps
	@echo "$(GREEN)Documentation built!$(NC)"

.PHONY: docs-open
docs-open: ## Build and open documentation
	@$(CARGO) doc --locked --all-features --no-deps --open

.PHONY: bench
bench: ## Run benchmarks
	@echo "$(CYAN)Running benchmarks...$(NC)"
	@$(CARGO) bench --locked --all-features

.PHONY: bench-check
bench-check: ## Check benchmarks compile
	@echo "$(CYAN)Checking benchmarks...$(NC)"
	@$(CARGO) bench --locked --all-features --no-run
	@echo "$(GREEN)Benchmarks compile!$(NC)"

.PHONY: msrv
msrv: ## Check minimum supported Rust version
	@echo "$(CYAN)Checking MSRV ($(RUST_MSRV))...$(NC)"
	@rustup toolchain install $(RUST_MSRV) --profile minimal
	@RUSTUP_TOOLCHAIN=$(RUST_MSRV) rustc --version --verbose
	@RUSTUP_TOOLCHAIN=$(RUST_MSRV) cargo --version
	@RUSTUP_TOOLCHAIN=$(RUST_MSRV) cargo check --locked --workspace --all-features --all-targets
	@echo "$(GREEN)MSRV check passed!$(NC)"

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(NC)"
	@docker build \
		--build-arg BINARY_NAME=$(BINARY_NAME) \
		--build-arg BINARY_PACKAGE=$(BINARY_PACKAGE) \
		--build-arg SBOM_MANIFEST_PATH=$(SBOM_MANIFEST_PATH) \
		-t $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)Docker image built: $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

.PHONY: docker-push
docker-push: ## Push Docker image to registry
	@echo "$(CYAN)Pushing Docker image...$(NC)"
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)Docker image pushed!$(NC)"

.PHONY: pre-commit
pre-commit: fmt-check lint test-doc ## Pre-commit checks

.PHONY: template-check
template-check: ## Fail if template placeholders are still present
	@echo "$(CYAN)Checking for template placeholders...$(NC)"
	@python3 scripts/check_template_placeholders.py
	@echo "$(GREEN)No unresolved template placeholders found!$(NC)"

.PHONY: ci
ci: template-check fmt-check lint test test-features docs security ## Full CI checks

.PHONY: ci-local
ci-local: all lint-strict test-features-full msrv sbom ## Full local validation and pre-push gate

.PHONY: ci-quick
ci-quick: template-check fmt-check lint check ## Quick CI checks

.PHONY: all
all: ci coverage bench-check ## Full validation suite

.PHONY: release-check
release-check: ## Check release readiness
	@echo "$(CYAN)Checking release readiness...$(NC)"
	@$(CARGO) check --locked --all-features
	@$(CARGO) test --locked --all-features
	@$(CARGO) clippy --locked --all-features --all-targets -- -D warnings
	@python3 scripts/check_template_placeholders.py
	@echo "$(GREEN)Release readiness checks passed!$(NC)"

.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(CYAN)Cleaning artifacts...$(NC)"
	@$(CARGO) clean
	@rm -rf lcov.info sbom dist
	@echo "$(GREEN)Cleaned!$(NC)"

.PHONY: f l t b c
f: fmt   ## Alias: format
l: lint  ## Alias: lint
t: test  ## Alias: test
b: build ## Alias: build
c: check ## Alias: check
