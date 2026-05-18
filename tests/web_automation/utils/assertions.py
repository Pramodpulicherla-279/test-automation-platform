def assert_equal(actual, expected, field_name):
    assert actual == expected, (
        f"\nMismatch in '{field_name}'"
        f"\nExpected: {expected}"
        f"\nActual: {actual}"
    )