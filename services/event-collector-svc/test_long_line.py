"""Test file for checking line length formatting."""


def very_long_function_call_that_exceeds_the_maximum_line_length():
    """This function name is intentionally very long to test line wrapping."""
    return (
        "This function name is intentionally very long to test line wrapping"
    )


# A long assignment that should be wrapped
very_long_variable_name_that_exceeds_line_limit = "some_function_call_result"

# Mock variables for testing
arg1 = "arg1"
arg2 = "arg2"
arg3 = "arg3"
arg4 = "arg4"
arg5 = "arg5"

# Mock conditions
some_very_long_condition_that_exceeds_line_limit = True
another_condition_that_is_also_long = True

# A long conditional statement
if (
    some_very_long_condition_that_exceeds_line_limit
    and another_condition_that_is_also_long
):
    pass
