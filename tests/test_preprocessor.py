"""Tests for log preprocessor module."""

from actions_advisor.preprocessor import (
    _collapse_repeated_lines,
    _remove_ansi_codes,
    _remove_excessive_empty_lines,
    _remove_github_metadata,
    _remove_timestamps,
    preprocess_logs,
)


def test_remove_ansi_codes():
    """Test ANSI escape code removal."""
    text = "\x1b[31mError\x1b[0m: something failed\x1b[32m"
    result = _remove_ansi_codes(text)
    assert result == "Error: something failed"


def test_remove_timestamps():
    """Test timestamp removal."""
    text = "2024-01-01T10:00:00.123456Z Starting build\n2024-01-01T10:00:01.234567Z Running tests"
    result = _remove_timestamps(text)
    assert result == "Starting build\nRunning tests"


def test_remove_github_metadata():
    """Test GitHub Actions metadata removal."""
    lines = [
        "##[group]Run tests",
        "actual test output",
        "##[endgroup]",
        "::set-output name=result::failed",
        "more output",
        "::debug::Some debug info",
    ]
    result = _remove_github_metadata(lines)
    assert result == ["actual test output", "more output"]


def test_collapse_repeated_lines():
    """Test collapsing repeated lines."""
    lines = [
        "line 1",
        "line 2",
        "line 2",
        "line 3",
        "line 3",
        "line 3",
        "line 3",
        "line 4",
    ]
    result = _collapse_repeated_lines(lines)
    assert result == [
        "line 1",
        "line 2",
        "line 2",
        "line 3 (repeated 4 times)",
        "line 4",
    ]


def test_collapse_repeated_lines_exactly_three():
    """Test collapsing exactly 3 repeated lines."""
    lines = ["warning", "warning", "warning"]
    result = _collapse_repeated_lines(lines)
    assert result == ["warning (repeated 3 times)"]


def test_collapse_repeated_lines_less_than_three():
    """Test not collapsing less than 3 repeated lines."""
    lines = ["line", "line", "other"]
    result = _collapse_repeated_lines(lines)
    assert result == ["line", "line", "other"]


def test_remove_excessive_empty_lines():
    """Test removal of excessive empty lines."""
    lines = ["line 1", "", "", "", "", "line 2", "", "line 3"]
    result = _remove_excessive_empty_lines(lines)
    assert result == ["line 1", "", "", "line 2", "", "line 3"]


def test_preprocess_logs_full_pipeline():
    """Test full log preprocessing pipeline."""
    raw_logs = """2024-01-01T10:00:00.123456Z \x1b[31m##[group]Run tests\x1b[0m
2024-01-01T10:00:01.123456Z npm install
2024-01-01T10:00:02.123456Z npm WARN deprecated package@1.0.0
2024-01-01T10:00:02.123456Z npm WARN deprecated package@1.0.0
2024-01-01T10:00:02.123456Z npm WARN deprecated package@1.0.0
2024-01-01T10:00:02.123456Z npm WARN deprecated package@1.0.0
2024-01-01T10:00:03.123456Z npm test
2024-01-01T10:00:04.123456Z
2024-01-01T10:00:04.123456Z
2024-01-01T10:00:04.123456Z
2024-01-01T10:00:04.123456Z
2024-01-01T10:00:05.123456Z \x1b[31mError: Test failed\x1b[0m
2024-01-01T10:00:05.123456Z ::debug::Stack trace
2024-01-01T10:00:05.123456Z at line 42
##[endgroup]"""

    result = preprocess_logs(raw_logs)

    # Check that ANSI codes are removed
    assert "\x1b[31m" not in result
    assert "\x1b[0m" not in result

    # Check that timestamps are removed
    assert "2024-01-01T10:00" not in result

    # Check that GitHub metadata is removed
    assert "##[group]" not in result
    assert "##[endgroup]" not in result
    assert "::debug::" not in result

    # Check that repeated warnings are collapsed
    assert "npm WARN deprecated package@1.0.0 (repeated 4 times)" in result

    # Check that content is preserved
    assert "npm install" in result
    assert "npm test" in result
    assert "Error: Test failed" in result
    assert "at line 42" in result


def test_preprocess_logs_trim_to_150_lines():
    """Test that logs are trimmed to last 150 lines."""
    # Create 200 lines
    lines = [f"line {i}" for i in range(200)]
    raw_logs = "\n".join(lines)

    result = preprocess_logs(raw_logs)
    result_lines = result.split("\n")

    # Should keep last 150 lines
    assert len(result_lines) == 150
    assert "line 50" in result
    assert "line 199" in result
    assert "line 0" not in result
