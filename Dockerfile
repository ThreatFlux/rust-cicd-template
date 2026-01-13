# ThreatFlux Rust Dockerfile
# Multi-stage build for minimal production images
# Version: 1.1.0

# =============================================================================
# Build Stage
# =============================================================================
FROM rust:1.92-bookworm AS builder

# Build arguments
ARG VERSION=0.0.0
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown
ARG BINARY_NAME=rust-cicd-template

# Install build dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create build user
RUN useradd -m -u 1000 builder
USER builder

WORKDIR /build

# Copy manifests first for better caching
COPY --chown=builder:builder Cargo.toml Cargo.lock* ./

# Create dummy src for dependency caching
RUN mkdir src && echo "fn main() {}" > src/main.rs

# Build dependencies only (ignore errors if no deps)
RUN cargo build --release 2>/dev/null || true
RUN rm -rf src target/release/deps/${BINARY_NAME}* 2>/dev/null || true

# Copy actual source
COPY --chown=builder:builder src ./src

# Build release binary
RUN cargo build --release --all-features

# =============================================================================
# Runtime Stage
# =============================================================================
FROM debian:bookworm-slim AS runtime

# Build arguments
ARG VERSION=0.0.0
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown
ARG BINARY_NAME=rust-cicd-template

# Labels
LABEL org.opencontainers.image.title="ThreatFlux Application" \
      org.opencontainers.image.description="ThreatFlux Rust Application" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="ThreatFlux" \
      org.opencontainers.image.source="https://github.com/threatflux"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 app

# Copy binary from builder
COPY --from=builder /build/target/release/${BINARY_NAME} /usr/local/bin/app

# Set ownership
RUN chown app:app /usr/local/bin/app

# Switch to non-root user
USER app
WORKDIR /home/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/app", "--version"]

# Use tini as init
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default command
CMD ["/usr/local/bin/app"]
