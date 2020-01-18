---
path: "/modules/ward.terminal"
title: "ward.terminal"
section: "modules"
type: "apidocs"
---

## Functions

```python
get_terminal_size()
```

```python
lightblack(s: str)
```

```python
truncate(s: str, num_chars: int)
```

## Classes

### Class `SimpleTestResultWrite`

```python
SimpleTestResultWrite (suite)
```

[]

#### Methods

```python
generate_chart(self, num_passed, num_failed, num_skipped, num_xfail, num_unexp)
```

```python
output_captured_stderr(self, test_result: ward.test_result.TestResult)
```

```python
output_captured_stdout(self, test_result: ward.test_result.TestResult)
```

```python
output_test_result_summary(self, test_results: List[ward.test_result.TestResult], time_taken: float)
```

```python
output_test_run_post_failure_summary(self, test_results: List[ward.test_result.TestResult])
```

```python
print_expect_chain_item(self, expect: ward.expect.Expected)
```

```python
print_failure_equals(self, err)
```

```python
print_traceback(self, err)
```

```python
result_checkbox(self, expect)
```

### Class `TerminalSize`

```python
TerminalSize (height, width)
```

TerminalSize(height: int, width: int)

[]

### Class `TestResultWriterBase`

```python
TestResultWriterBase (suite)
```

#### Descendants

* `ward.terminal.SimpleTestResultWrite`
[]

#### Methods

```python
output_all_test_results(self, test_results_gen: Generator[ward.test_result.TestResult, NoneType, NoneType], time_to_collect: float, fail_limit: Union[int, NoneType] = None)
```

```python
output_captured_stderr(self, test_result: ward.test_result.TestResult)
```

```python
output_captured_stdout(self, test_result: ward.test_result.TestResult)
```

```python
output_single_test_result(self, test_result: ward.test_result.TestResult)
```
Indicate whether a test passed, failed, was skipped etc.

```python
output_test_result_summary(self, test_results: List[ward.test_result.TestResult], time_taken: float)
```

```python
output_test_run_post_failure_summary(self, test_results: List[ward.test_result.TestResult])
```

```python
output_why_test_failed(self, test_result: ward.test_result.TestResult)
```
Extended output shown for failing tests, may include further explanations,
assertion error info, diffs, etc.

```python
output_why_test_failed_header(self, test_result: ward.test_result.TestResult)
```
Printed above the failing test output