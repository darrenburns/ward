---
path: "/modules/ward.terminal"
title: "ward.terminal"
section: "modules"
---

Module ward.terminal
====================

#### Functions

```python
    
`get_terminal_size()`
:   
```

```python
    
`lightblack(s)`
:   
```

```python
    
`truncate(s, num_chars)`
:   
```

#### Classes

`SimpleTestResultWrite(suite)`
:   

    ### Methods

```python

```python
    
`generate_chart(self, num_passed, num_failed, num_skipped, num_xfail, num_unexp)`
:   
```

```

```python

```python
    
`output_captured_stderr(self, test_result)`
:   
```

```

```python

```python
    
`output_captured_stdout(self, test_result)`
:   
```

```

```python

```python
    
`output_test_result_summary(self, test_results, time_taken)`
:   
```

```

```python

```python
    
`output_test_run_post_failure_summary(self, test_results)`
:   
```

```

```python

```python
    
`print_expect_chain_item(self, expect)`
:   
```

```

```python

```python
    
`print_failure_equals(self, err)`
:   
```

```

```python

```python
    
`print_traceback(self, err)`
:   
```

```

```python

```python
    
`result_checkbox(self, expect)`
:   
```

```

`TerminalSize(height, width)`
:   TerminalSize(height: int, width: int)

`TestResultWriterBase(suite)`
:   

    ### Descendants

    * ward.terminal.SimpleTestResultWrite

    ### Methods

```python

```python
    
`output_all_test_results(self, test_results_gen, time_to_collect, fail_limit=None)`
:   
```

```

```python

```python
    
`output_captured_stderr(self, test_result)`
:   
```

```

```python

```python
    
`output_captured_stdout(self, test_result)`
:   
```

```

```python

```python
    
`output_single_test_result(self, test_result)`
:   Indicate whether a test passed, failed, was skipped etc.
```

```

```python

```python
    
`output_test_result_summary(self, test_results, time_taken)`
:   
```

```

```python

```python
    
`output_test_run_post_failure_summary(self, test_results)`
:   
```

```

```python

```python
    
`output_why_test_failed(self, test_result)`
:   Extended output shown for failing tests, may include further explanations,
    assertion error info, diffs, etc.
```

```

```python

```python
    
`output_why_test_failed_header(self, test_result)`
:   Printed above the failing test output
```

```