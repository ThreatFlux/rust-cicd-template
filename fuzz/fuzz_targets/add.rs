#![no_main]

use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let &[a0, a1, a2, a3, b0, b1, b2, b3] = data else {
        return;
    };
    let a = i32::from_le_bytes([a0, a1, a2, a3]);
    let b = i32::from_le_bytes([b0, b1, b2, b3]);

    // Only representable sums have an oracle here. The library's overflow
    // behavior is intentionally unchanged and is outside this target's contract.
    if let Some(expected) = a.checked_add(b) {
        assert_eq!(rust_cicd_template::add(a, b), expected);
    }
});
