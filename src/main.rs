//! ThreatFlux Rust CI/CD Template
//!
//! This is a minimal example project demonstrating CI/CD best practices.

fn main() {
    println!("ThreatFlux Rust CI/CD Template");
    println!("Version: {}", env!("CARGO_PKG_VERSION"));
}

#[cfg(test)]
mod tests {
    #[test]
    fn test_example() {
        assert_eq!(2 + 2, 4);
    }
}
