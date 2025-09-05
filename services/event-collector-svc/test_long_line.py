# Test file for long line fixing

def very_long_function_call_that_exceeds_the_maximum_line_length_and_should_be_wrapped():
    return "This function name is intentionally very long to test line wrapping"

# A long assignment that should be wrapped
very_long_variable_name_that_exceeds_line_limit = (
    some_function_call_with_many_arguments(
)
    arg1,
    arg2,
    arg3,
    arg4,
    arg5
)

# A long conditional statement
if some_very_long_condition_that_exceeds_line_limit
    and another_condition_that_is_also_long:
    pass
