Module ward.terminal
====================

Functions
---------

    
`get_terminal_size()`
:   

    
`lightblack(s)`
:   

    
`truncate(s, num_chars)`
:   

Classes
-------

`SimpleTestResultWrite(suite)`
:   

    ### Ancestors (in MRO)

    * ward.terminal.TestResultWriterBase

    ### Methods

    `generate_chart(self, num_passed, num_failed, num_skipped, num_xfail, num_unexp)`
    :

    `output_captured_stderr(self, test_result)`
    :

    `output_captured_stdout(self, test_result)`
    :

    `output_test_result_summary(self, test_results, time_taken)`
    :

    `output_test_run_post_failure_summary(self, test_results)`
    :

    `print_expect_chain_item(self, expect)`
    :

    `print_failure_equals(self, err)`
    :

    `print_traceback(self, err)`
    :

    `result_checkbox(self, expect)`
    :

`TerminalSize(height, width)`
:   TerminalSize(height: int, width: int)

`TestResultWriterBase(suite)`
:   

    ### Descendants

    * ward.terminal.SimpleTestResultWrite

    ### Methods

    `output_all_test_results(self, test_results_gen, time_to_collect, fail_limit=None)`
    :

    `output_captured_stderr(self, test_result)`
    :

    `output_captured_stdout(self, test_result)`
    :

    `output_single_test_result(self, test_result)`
    :   Indicate whether a test passed, failed, was skipped etc.

    `output_test_result_summary(self, test_results, time_taken)`
    :

    `output_test_run_post_failure_summary(self, test_results)`
    :

    `output_why_test_failed(self, test_result)`
    :   Extended output shown for failing tests, may include further explanations,
        assertion error info, diffs, etc.

    `output_why_test_failed_header(self, test_result)`
    :   Printed above the failing test output