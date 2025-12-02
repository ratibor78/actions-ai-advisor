"""Tests for output formatter module."""

import os
import tempfile

from actions_advisor.formatter import (
    _format_duration,
    format_analysis,
    write_job_summary,
)
from actions_advisor.llm_client import AnalysisResult
from actions_advisor.log_fetcher import JobLog


def test_format_duration_seconds():
    """Test duration formatting for seconds only."""
    assert _format_duration(30) == "30s"
    assert _format_duration(59) == "59s"


def test_format_duration_minutes():
    """Test duration formatting for minutes."""
    assert _format_duration(60) == "1m 0s"
    assert _format_duration(125) == "2m 5s"
    assert _format_duration(3599) == "59m 59s"


def test_format_duration_hours():
    """Test duration formatting for hours."""
    assert _format_duration(3600) == "1h 0m 0s"
    assert _format_duration(3665) == "1h 1m 5s"
    assert _format_duration(7200) == "2h 0m 0s"


def test_format_duration_none():
    """Test duration formatting when None."""
    assert _format_duration(None) == "N/A"


def test_format_analysis_with_cost():
    """Test analysis formatting with cost estimation."""
    job_log = JobLog(
        job_name="build",
        step_name="Run tests",
        conclusion="failure",
        raw_logs="test logs",
        exit_code=1,
        duration_seconds=154,
    )

    result = AnalysisResult(
        analysis="## Root Cause\nTest failed\n\n## Suggested Fixes\n1. Fix the test",
        input_tokens=1000,
        output_tokens=500,
        model_used="gpt-4o-mini",
    )

    markdown = format_analysis(job_log, result, estimated_cost=0.0005)

    # Check header and callout
    assert "🔍 Actions Advisor" in markdown
    assert "**Failed:**" in markdown
    assert "`build` → `Run tests`" in markdown

    # Check horizontal metrics table
    assert "📊 Run Metrics" in markdown
    assert "| Exit Code | Duration | Job | Step |" in markdown
    assert "| `1` | 2m 34s | `build` | `Run tests` |" in markdown

    # Check analysis content
    assert "## Root Cause" in markdown
    assert "Test failed" in markdown
    assert "## Suggested Fixes" in markdown

    # Check analysis details table
    assert "💰 Analysis Details" in markdown
    assert "| **Model** | `gpt-4o-mini` |" in markdown
    assert "| **Input Tokens** | 1,000 |" in markdown
    assert "| **Output Tokens** | 500 |" in markdown
    assert "| **Est. Cost** | ~$0.0005 |" in markdown

    # Check footer
    assert "🤖 Powered by Actions Advisor" in markdown


def test_format_analysis_without_cost():
    """Test analysis formatting without cost estimation."""
    job_log = JobLog(
        job_name="lint",
        step_name="Check code",
        conclusion="failure",
        raw_logs="lint logs",
        exit_code=2,
        duration_seconds=45,
    )

    result = AnalysisResult(
        analysis="Linting errors detected",
        input_tokens=500,
        output_tokens=250,
        model_used="custom-model",
    )

    markdown = format_analysis(job_log, result, estimated_cost=None)

    # Check header
    assert "**Failed:**" in markdown
    assert "`lint` → `Check code`" in markdown

    # Check horizontal metrics table
    assert "| Exit Code | Duration | Job | Step |" in markdown
    assert "| `2` | 45s | `lint` | `Check code` |" in markdown

    # Check analysis details with N/A cost
    assert "| **Model** | `custom-model` |" in markdown
    assert "| **Input Tokens** | 500 |" in markdown
    assert "| **Output Tokens** | 250 |" in markdown
    assert "| **Est. Cost** | N/A |" in markdown


def test_format_analysis_no_exit_code():
    """Test analysis formatting when exit code is None."""
    job_log = JobLog(
        job_name="deploy",
        step_name="Deploy to prod",
        conclusion="cancelled",
        raw_logs="cancelled logs",
        exit_code=None,
        duration_seconds=None,
    )

    result = AnalysisResult(
        analysis="Job was cancelled",
        input_tokens=100,
        output_tokens=50,
        model_used="gpt-4o-mini",
    )

    markdown = format_analysis(job_log, result, estimated_cost=0.0001)

    # Check that N/A values are handled correctly in horizontal table
    assert "| Exit Code | Duration | Job | Step |" in markdown
    assert "| `N/A` | N/A | `deploy` | `Deploy to prod` |" in markdown


def test_write_job_summary_to_file(monkeypatch):
    """Test writing job summary to file."""
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
        temp_file = f.name

    try:
        monkeypatch.setenv("GITHUB_STEP_SUMMARY", temp_file)

        content = "# Test Summary\nThis is a test"
        write_job_summary(content)

        with open(temp_file) as f:
            written_content = f.read()

        assert "# Test Summary" in written_content
        assert "This is a test" in written_content
    finally:
        os.unlink(temp_file)


def test_write_job_summary_no_env_var(capsys, monkeypatch):
    """Test writing job summary when env var not set."""
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)

    content = "# Test Summary\nThis is a test"
    write_job_summary(content)

    captured = capsys.readouterr()
    assert "Job Summary" in captured.out
    assert "# Test Summary" in captured.out
    assert "This is a test" in captured.out
