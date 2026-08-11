# ThreatFlux Rust Dockerfile
# Canonical multi-stage build for single-crate or workspace-based applications.
#
# This file is the single source of truth for every ThreatFlux Rust repo that
# ships a binary. It is intended to be byte-identical across repos: everything
# repo-specific is a build ARG, supplied by .github/workflows/docker.yml from
# repository variables. A CI conformance job diffs each repo's copy against this
# one, so DO NOT fork it — if you need something it cannot express, add an ARG
# here instead.
#
# The runtime stage is distroless: no shell, no package manager, no coreutils.
# If you genuinely need a shell at runtime, use the sanctioned Dockerfile.debian
# variant rather than editing this file.
#
# Base images are pinned by digest for reproducibility (Scorecard Pinned-Dependencies).
# Refresh with: docker buildx imagetools inspect <image> | awk '/^Digest:/{print $2}'
# Dependabot refreshes the first FROM (the Rust builder); maintainers refresh
# the later runtime digest with the command above during template updates.

FROM rust:1.97.1-bookworm@sha256:14bc9c5966e7b3a385794b3d5389a8765668342025fbcc7b2e3d2866ac4bd8c3 AS rust-base

ARG VERSION=0.0.0
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown
ARG BINARY_NAME=rust-cicd-template
ARG BINARY_PACKAGE=
ARG CLI_NAME=rust-cicd-template
ARG SBOM_MANIFEST_PATH=Cargo.toml
# Space-separated extra apt packages required to COMPILE, e.g. "clang lld build-essential".
# Build-time only — the distroless runtime has no package manager, so extra
# RUNTIME packages are supported exclusively by Dockerfile.debian.
ARG EXTRA_BUILD_PACKAGES=
ARG OCI_IMAGE_TITLE=Rust Application
ARG OCI_IMAGE_DESCRIPTION=Rust Application
ARG OCI_IMAGE_VENDOR=ThreatFlux
ARG OCI_IMAGE_SOURCE=https://github.com

# tini is installed here so the runtime stage can copy it out: distroless ships
# no init, and PID 1 must reap zombies and forward signals. Exact Debian package
# revisions are intentionally not pinned because this cross-repo template accepts
# arbitrary EXTRA_BUILD_PACKAGES and follows the repositories in its pinned base.
# hadolint ignore=DL3008
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    pkg-config \
    libssl-dev \
    tini \
    ${EXTRA_BUILD_PACKAGES} \
    && rm -rf /var/lib/apt/lists/*

FROM rust-base AS builder

RUN useradd -m -u 1000 builder
USER builder
WORKDIR /build

ENV CARGO_HOME=/home/builder/.cargo
ENV PATH="/home/builder/.cargo/bin:${PATH}"

COPY --chown=builder:builder . .

RUN if [ -n "${BINARY_PACKAGE}" ]; then \
      cargo build --release -p "${BINARY_PACKAGE}" --bin "${BINARY_NAME}" --all-features; \
    else \
      cargo build --release --bin "${BINARY_NAME}" --all-features || cargo build --release --all-features; \
    fi

# cargo-cyclonedx writes the SBOM beside the manifest it was handed, which in a
# workspace is not necessarily /build. The find normalizes the output location.
RUN cargo install cargo-cyclonedx --locked --version 0.5.8 && \
    cargo cyclonedx \
      --manifest-path "${SBOM_MANIFEST_PATH}" \
      --all-features \
      --format json \
      --spec-version 1.5 \
      --override-filename "${BINARY_NAME}-sbom" && \
    find /build -name "${BINARY_NAME}-sbom.json" -exec cp {} /build/sbom.cdx.json \; -quit

# Stage the runtime filesystem under a fixed layout.
#
# The binary is staged as `app` at a FIXED path deliberately: exec-form
# ENTRYPOINT and HEALTHCHECK do NOT expand build ARGs, so they cannot reference
# ${CLI_NAME}. A symlink preserves the friendly name for `docker run <img>` and
# for anyone exec'ing into the Dockerfile.debian variant.
#
# Writable directories are created here because the distroless runtime has no
# shell to mkdir with; ownership is applied on the way in via COPY --chown.
RUN mkdir -p /home/builder/out/bin /home/builder/out/doc \
             /home/builder/runtime-skel/data \
             /home/builder/runtime-skel/config \
             /home/builder/runtime-skel/output && \
    cp "target/release/${BINARY_NAME}" /home/builder/out/bin/app && \
    if [ "${CLI_NAME}" != "app" ]; then \
      ln -s app "/home/builder/out/bin/${CLI_NAME}"; \
    fi && \
    cp /build/sbom.cdx.json /home/builder/out/doc/sbom.cdx.json

FROM gcr.io/distroless/cc-debian12:nonroot@sha256:fccdbb0a547c14e23fcf4ce8ad62ca5d43b4faae8d22cd292f490fef9946c96e AS runtime

ARG VERSION=0.0.0
ARG BUILD_DATE=unknown
ARG VCS_REF=unknown
# Advertised listening port. Metadata only — this does not publish the port.
ARG APP_PORT=8080
ARG OCI_IMAGE_TITLE=Rust Application
ARG OCI_IMAGE_DESCRIPTION=Rust Application
ARG OCI_IMAGE_VENDOR=ThreatFlux
ARG OCI_IMAGE_SOURCE=https://github.com
ARG OCI_IMAGE_LICENSES=MIT
ARG OCI_IMAGE_DOCUMENTATION=https://github.com

LABEL org.opencontainers.image.title="${OCI_IMAGE_TITLE}" \
      org.opencontainers.image.description="${OCI_IMAGE_DESCRIPTION}" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="${OCI_IMAGE_VENDOR}" \
      org.opencontainers.image.source="${OCI_IMAGE_SOURCE}" \
      org.opencontainers.image.licenses="${OCI_IMAGE_LICENSES}" \
      org.opencontainers.image.documentation="${OCI_IMAGE_DOCUMENTATION}"

COPY --from=builder /usr/bin/tini /usr/bin/tini

COPY --from=builder --chown=65532:65532 /home/builder/out/bin/ /usr/local/bin/
COPY --from=builder --chown=65532:65532 /home/builder/out/doc/ /usr/share/doc/app/
COPY --from=builder --chown=65532:65532 /home/builder/runtime-skel/data /data
COPY --from=builder --chown=65532:65532 /home/builder/runtime-skel/config /config
COPY --from=builder --chown=65532:65532 /home/builder/runtime-skel/output /output

USER 65532:65532
WORKDIR /data

ENV RUST_LOG=info

# Exec form (there is no shell in distroless); a nonzero exit means unhealthy.
# Every ThreatFlux CLI must therefore implement `--version`.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/app", "--version"]

EXPOSE ${APP_PORT}

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/app"]
