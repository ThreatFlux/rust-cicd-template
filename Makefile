# ThreatFlux Rust Project Makefile
# Standardized build, test, and development commands
# Version: 1.0.0

# =============================================================================
# Configuration
# =============================================================================

CARGO ?= cargo
RUST_MSRV ?= 1.92.0
RUST_TOOLCHAIN ?= stable

# Docker configuration
DOCKER_IMAGE ?= $(shell basename $(CURDIR))
DOCKER_TAG ?= latest
DOCKER_REGISTRY ?= ghcr.io/threatflux

# Coverage configuration
COVERAGE_IGNORE ?=

# Clippy configuration - strict by default
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

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
CYAN := \033[0;36m
NC := \033[0m

# =============================================================================
# Default Target
# =============================================================================

.DEFAULT_GOAL := help

.PHONY: help
help: ## Display this help message
	@echo "$(CYAN)ThreatFlux Rust Project - Available Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Quick Start:$(NC)"
	@echo "  $(GREEN)make dev-setup$(NC)    Install all development tools"
	@echo "  $(GREEN)make ci$(NC)           Run all CI checks locally"
	@echo "  $(GREEN)make all$(NC)          Run full validation suite"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2}'

# =============================================================================
# Setup
# =============================================================================

.PHONY: dev-setup
dev-setup: ## Install development tools
	@echo "$(CYAN)Installing development tools...$(NC)"
	@rustup component add rustfmt clippy llvm-tools-preview 2>/dev/null || true
	@cargo install cargo-llvm-cov --locked 2>/dev/null || echo "cargo-llvm-cov already installed"
	@cargo install cargo-audit --locked 2>/dev/null || echo "cargo-audit already installed"
	@cargo install cargo-deny --locked 2>/dev/null || echo "cargo-deny already installed"
	@cargo install cargo-hack --locked 2>/dev/null || echo "cargo-hack already installed"
	@echo "$(GREEN)Development tools installed!$(NC)"

.PHONY: install-hooks
install-hooks: ## Install git pre-commit hooks
	@echo "$(CYAN)Installing git hooks...$(NC)"
	@mkdir -p .git/hooks
	@echo '#!/bin/sh\nmake pre-commit' > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "$(GREEN)Git hooks installed!$(NC)"

# =============================================================================
# Building
# =============================================================================

.PHONY: build
build: ## Build the project (debug)
	@echo "$(CYAN)Building project...$(NC)"
	@$(CARGO) build --all-features
	@echo "$(GREEN)Build completed!$(NC)"

.PHONY: build-release
build-release: ## Build the project (release)
	@echo "$(CYAN)Building release...$(NC)"
	@$(CARGO) build --release --all-features
	@echo "$(GREEN)Release build completed!$(NC)"

.PHONY: check
check: ## Check compilation without building
	@echo "$(CYAN)Checking compilation...$(NC)"
	@$(CARGO) check --all-features --all-targets

# =============================================================================
# Code Quality
# =============================================================================

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
lint: ## Run clippy linter (standard)
	@echo "$(CYAN)Running clippy...$(NC)"
	@$(CARGO) clippy --all-features --all-targets -- -D warnings
	@echo "$(GREEN)Linting passed!$(NC)"

.PHONY: lint-strict
lint-strict: ## Run clippy with strict flags
	@echo "$(CYAN)Running strict clippy...$(NC)"
	@$(CARGO) clippy --all-features --all-targets -- $(CLIPPY_FLAGS)
	@echo "$(GREEN)Strict linting passed!$(NC)"

.PHONY: lint-fix
lint-fix: ## Run clippy and apply fixes
	@echo "$(CYAN)Applying clippy fixes...$(NC)"
	@$(CARGO) clippy --all-features --all-targets --fix --allow-dirty --allow-staged -- -D warnings
	@echo "$(GREEN)Fixes applied!$(NC)"

# =============================================================================
# Testing
# =============================================================================

.PHONY: test
test: ## Run all tests
	@echo "$(CYAN)Running tests...$(NC)"
	@$(CARGO) test --all-features
	@echo "$(GREEN)Tests passed!$(NC)"

.PHONY: test-verbose
test-verbose: ## Run tests with output
	@echo "$(CYAN)Running tests (verbose)...$(NC)"
	@$(CARGO) test --all-features -- --nocapture

.PHONY: test-doc
test-doc: ## Run documentation tests
	@echo "$(CYAN)Running doc tests...$(NC)"
	@$(CARGO) test --doc --all-features
	@echo "$(GREEN)Doc tests passed!$(NC)"

.PHONY: test-features
test-features: ## Test feature combinations
	@echo "$(CYAN)Testing feature combinations...$(NC)"
	@echo "$(BLUE)  No default features...$(NC)"
	@$(CARGO) check --no-default-features
	@echo "$(BLUE)  All features...$(NC)"
	@$(CARGO) check --all-features
	@echo "$(BLUE)  Default features only...$(NC)"
	@$(CARGO) check
	@echo "$(GREEN)Feature checks passed!$(NC)"

.PHONY: test-features-full
test-features-full: ## Test all feature powerset (requires cargo-hack)
	@echo "$(CYAN)Testing full feature powerset...$(NC)"
	@cargo hack check --feature-powerset --no-dev-deps
	@echo "$(GREEN)Feature powerset passed!$(NC)"

# =============================================================================
# Coverage
# =============================================================================

.PHONY: coverage
coverage: ## Generate code coverage report
	@echo "$(CYAN)Generating coverage...$(NC)"
	@cargo llvm-cov --all-features --workspace --lcov --output-path lcov.info
	@echo "$(GREEN)Coverage report: lcov.info$(NC)"

.PHONY: coverage-html
coverage-html: ## Generate HTML coverage report
	@echo "$(CYAN)Generating HTML coverage...$(NC)"
	@cargo llvm-cov --all-features --workspace --html
	@echo "$(GREEN)Report: target/llvm-cov/html/index.html$(NC)"

.PHONY: coverage-summary
coverage-summary: ## Show coverage summary
	@echo "$(CYAN)Coverage summary:$(NC)"
	@cargo llvm-cov --all-features --workspace --summary-only

# =============================================================================
# Security
# =============================================================================

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

.PHONY: security
security: audit deny ## Run all security checks
	@echo "$(GREEN)All security checks passed!$(NC)"

# =============================================================================
# Documentation
# =============================================================================

.PHONY: docs
docs: ## Build documentation
	@echo "$(CYAN)Building documentation...$(NC)"
	@RUSTDOCFLAGS="-D warnings" $(CARGO) doc --all-features --no-deps
	@echo "$(GREEN)Documentation built!$(NC)"

.PHONY: docs-open
docs-open: ## Build and open documentation
	@$(CARGO) doc --all-features --no-deps --open

# =============================================================================
# Benchmarks
# =============================================================================

.PHONY: bench
bench: ## Run benchmarks
	@echo "$(CYAN)Running benchmarks...$(NC)"
	@$(CARGO) bench --all-features

.PHONY: bench-check
bench-check: ## Check benchmarks compile
	@echo "$(CYAN)Checking benchmarks...$(NC)"
	@$(CARGO) bench --all-features --no-run
	@echo "$(GREEN)Benchmarks compile!$(NC)"

# =============================================================================
# MSRV
# =============================================================================

.PHONY: msrv
msrv: ## Check minimum supported Rust version
	@echo "$(CYAN)Checking MSRV ($(RUST_MSRV))...$(NC)"
	@rustup run $(RUST_MSRV) cargo check --all-features
	@echo "$(GREEN)MSRV check passed!$(NC)"

# =============================================================================
# Docker
# =============================================================================

.PHONY: docker-build
docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(NC)"
	@docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .
	@echo "$(GREEN)Docker image built: $(DOCKER_IMAGE):$(DOCKER_TAG)$(NC)"

.PHONY: docker-push
docker-push: ## Push Docker image to registry
	@echo "$(CYAN)Pushing Docker image...$(NC)"
	@docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	@docker push $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo "$(GREEN)Image pushed!$(NC)"

# =============================================================================
# CI Targets
# =============================================================================

.PHONY: pre-commit
pre-commit: fmt-check lint test-doc ## Pre-commit checks
	@echo "$(GREEN)Pre-commit checks passed!$(NC)"

.PHONY: ci
ci: fmt-check lint test test-features docs security ## Full CI checks
	@echo "$(GREEN)All CI checks passed!$(NC)"

.PHONY: ci-quick
ci-quick: fmt-check lint check ## Quick CI checks
	@echo "$(GREEN)Quick CI checks passed!$(NC)"

.PHONY: all
all: ci coverage bench-check ## Full validation suite
	@echo "$(GREEN)Full validation passed!$(NC)"

# =============================================================================
# Release
# =============================================================================

.PHONY: release-check
release-check: ## Check release readiness
	@echo "$(CYAN)Checking release readiness...$(NC)"
	@$(MAKE) ci
	@$(MAKE) msrv
	@cargo publish --dry-run
	@echo "$(GREEN)Ready for release!$(NC)"

# =============================================================================
# Cleanup
# =============================================================================

.PHONY: clean
clean: ## Clean build artifacts
	@echo "$(CYAN)Cleaning...$(NC)"
	@$(CARGO) clean
	@rm -f lcov.info
	@echo "$(GREEN)Clean completed!$(NC)"

# =============================================================================
# Aliases
# =============================================================================

.PHONY: f l t b c
f: fmt        ## Alias: format
l: lint       ## Alias: lint
t: test       ## Alias: test
b: build      ## Alias: build
c: check      ## Alias: check
