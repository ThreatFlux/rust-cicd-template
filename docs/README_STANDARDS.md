# ThreatFlux README Standards

Best practices for README files in ThreatFlux repositories.

## Required Sections

Every README must include:

1. **Title and Badges**
2. **Description** (1-2 sentences)
3. **Features** (bullet list)
4. **Installation**
5. **Quick Start** (working code example)
6. **License**

## Recommended Sections

Based on project complexity:

- Feature Flags (if applicable)
- Configuration
- API Reference
- Development setup
- Contributing
- Security

## Badge Order

```markdown
[![Crates.io](https://img.shields.io/crates/v/PROJECT.svg)](https://crates.io/crates/PROJECT)
[![Documentation](https://docs.rs/PROJECT/badge.svg)](https://docs.rs/PROJECT)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Rust](https://img.shields.io/badge/rust-1.92%2B-orange.svg)](https://www.rust-lang.org)
[![CI](https://github.com/threatflux/PROJECT/actions/workflows/ci.yml/badge.svg)](https://github.com/threatflux/PROJECT/actions/workflows/ci.yml)
[![Security](https://github.com/threatflux/PROJECT/actions/workflows/security.yml/badge.svg)](https://github.com/threatflux/PROJECT/actions/workflows/security.yml)
[![codecov](https://codecov.io/gh/threatflux/PROJECT/branch/main/graph/badge.svg)](https://codecov.io/gh/threatflux/PROJECT)
```

## Best Practices Observed

### From threatflux-binary-analysis (Best Example)
- Comprehensive badges row
- Emoji-enhanced feature sections
- Feature flags table
- Multiple code examples

### From threatflux-hashing
- Clean, focused documentation
- Good async/await examples
- Configuration options table

### From FluxAgent
- Clear project status warning
- Architecture explanation
- Docker quick start

### From file-scanner
- Detailed CLI usage
- Multiple format examples
- Integration examples

## Database Migration Best Practices

ThreatFlux projects use **embedded migrations** instead of separate SQL files:

### Pattern
```rust
// src/migrations.rs
pub const MIGRATIONS: &[&str] = &[
    // V1: Initial schema
    r#"
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    "#,
    // V2: Add new column
    r#"
    ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT;
    "#,
];

pub async fn run(pool: &PgPool) -> Result<(), sqlx::Error> {
    for migration in MIGRATIONS {
        sqlx::query(migration).execute(pool).await?;
    }
    Ok(())
}
```

### Key Principles

1. **No separate SQL files** - All migrations embedded in Rust code
2. **Idempotent statements** - Use `IF NOT EXISTS` / `IF EXISTS` patterns
3. **Auto-run on startup** - Call `migrations::run(pool)` in main
4. **Safe to re-run** - Migrations should be safe to execute multiple times
5. **Version comments** - Document migration versions inline

### Benefits

- Type-checked at compile time
- No file system dependencies at runtime
- Single binary deployment
- Easy to review in PRs
- Works with all deployment methods (Docker, binary, etc.)

### Anti-Pattern: Avoid These

```
# DON'T create these:
migrations/
├── 001_initial.sql
├── 002_add_users.sql
└── 003_add_index.sql
```

## Anti-Patterns to Avoid

1. **No code examples** - Always include runnable code
2. **Missing license** - Always specify MIT
3. **No badges** - Add at minimum: CI, License, Rust version
4. **Outdated Rust version** - Keep MSRV current (1.92.0)
5. **No installation section** - Show Cargo.toml entry
6. **Walls of text** - Use lists, tables, code blocks
7. **Separate SQL migration files** - Use embedded migrations pattern

## License Standard

All ThreatFlux repositories MUST use MIT license:

```
MIT License

Copyright (c) 2025 ThreatFlux

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Repos Needing License Updates

The following repos are missing MIT license files:

| Repository | Current Status | Action Needed |
|------------|---------------|---------------|
| openai_rust_sdk | Missing | Add LICENSE |
| lifeflux | Missing | Add LICENSE |
| threatflux | Missing | Add LICENSE |
| virustotal-rs | Missing | Add LICENSE |
| threatflux-string-analysis | Missing | Add LICENSE |
| fluxdefense | Missing | Add LICENSE |
| mcp_rust | Missing | Add LICENSE |
| FluxEncrypt | NOASSERTION | Fix LICENSE |

## Cargo.toml License Field

```toml
[package]
license = "MIT"
```

## Template Files

Use the templates in this repository:

- `README_TEMPLATE.md` - README structure
- `CONTRIBUTING.md` - Contribution guidelines
- `SECURITY.md` - Security policy
- `LICENSE` - MIT license text
