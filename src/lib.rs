//! ThreatFlux Rust CI/CD Template Library
//!
//! This is a minimal example library demonstrating CI/CD best practices.

/// Example function that adds two numbers.
///
/// # Examples
///
/// ```
/// use rust_cicd_template::add;
/// assert_eq!(add(2, 3), 5);
/// ```
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
        assert_eq!(add(-1, 1), 0);
        assert_eq!(add(0, 0), 0);
    }
}
